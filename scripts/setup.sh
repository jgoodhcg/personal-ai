#!/usr/bin/env bash
set -euo pipefail

# Personal AI VPS bootstrap
# - Run as root on fresh Debian/Ubuntu
# - Goal: durable, Tailscale-only Open WebUI deployment

ADMIN_USER="${ADMIN_USER:-}"
AGENT_USER="${AGENT_USER:-agent}"
REPO_URL="${REPO_URL:-https://github.com/justingood/personal-ai.git}"
REPO_DIR="${REPO_DIR:-}"
TS_AUTHKEY="${TS_AUTHKEY:-}"
SWAP_SIZE="${SWAP_SIZE:-2G}"
AUTO_DEPLOY="${AUTO_DEPLOY:-true}"
ENABLE_TS_SERVE="${ENABLE_TS_SERVE:-true}"

log() {
  printf "\n==> %s\n" "$1"
}

warn() {
  printf "\n[WARN] %s\n" "$1"
}

die() {
  printf "\n[ERROR] %s\n" "$1" >&2
  exit 1
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    die "Run this script as root."
  fi
}

service_restart_ssh() {
  if systemctl list-unit-files | grep -q '^ssh\.service'; then
    systemctl restart ssh
  elif systemctl list-unit-files | grep -q '^sshd\.service'; then
    systemctl restart sshd
  else
    warn "Could not find ssh/sshd service to restart."
  fi
}

ensure_admin_user() {
  [[ -n "${ADMIN_USER}" ]] || read -rp "Admin username (sudo user): " ADMIN_USER
  [[ -n "${ADMIN_USER}" ]] || die "ADMIN_USER is required."

  if ! id "${ADMIN_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "${ADMIN_USER}"
    usermod -aG sudo "${ADMIN_USER}"
  fi

  if [[ -f /root/.ssh/authorized_keys ]]; then
    mkdir -p "/home/${ADMIN_USER}/.ssh"
    cp /root/.ssh/authorized_keys "/home/${ADMIN_USER}/.ssh/authorized_keys"
    chown -R "${ADMIN_USER}:${ADMIN_USER}" "/home/${ADMIN_USER}/.ssh"
    chmod 700 "/home/${ADMIN_USER}/.ssh"
    chmod 600 "/home/${ADMIN_USER}/.ssh/authorized_keys"
  else
    warn "No /root/.ssh/authorized_keys found. Verify ${ADMIN_USER} SSH access before hardening."
  fi
}

ensure_agent_user() {
  if ! id "${AGENT_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "${AGENT_USER}"
  fi

  usermod -aG docker "${AGENT_USER}"

  if [[ -f "/home/${ADMIN_USER}/.ssh/authorized_keys" ]]; then
    mkdir -p "/home/${AGENT_USER}/.ssh"
    cp "/home/${ADMIN_USER}/.ssh/authorized_keys" "/home/${AGENT_USER}/.ssh/authorized_keys"
    chown -R "${AGENT_USER}:${AGENT_USER}" "/home/${AGENT_USER}/.ssh"
    chmod 700 "/home/${AGENT_USER}/.ssh"
    chmod 600 "/home/${AGENT_USER}/.ssh/authorized_keys"
  fi

  sudo -u "${AGENT_USER}" mkdir -p "/home/${AGENT_USER}/workspace" "/home/${AGENT_USER}/projects"
}

configure_swap() {
  if [[ -f /swapfile ]]; then
    log "Swap already exists, skipping"
    return
  fi

  log "Configuring swap (${SWAP_SIZE})"
  fallocate -l "${SWAP_SIZE}" /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
}

install_base_packages() {
  log "Updating system packages"
  apt update
  apt upgrade -y

  log "Installing base packages"
  apt install -y curl git ufw fail2ban openssl docker.io docker-compose-v2
  systemctl enable --now docker
}

install_tailscale() {
  if command -v tailscale >/dev/null 2>&1; then
    log "Tailscale already installed"
  else
    log "Installing Tailscale"
    curl -fsSL https://tailscale.com/install.sh | sh
  fi

  systemctl enable --now tailscaled

  log "Connecting Tailscale"
  if [[ -n "${TS_AUTHKEY}" ]]; then
    tailscale up --authkey "${TS_AUTHKEY}"
  else
    tailscale up
  fi

  tailscale set --operator="${AGENT_USER}"
}

configure_ssh_hardening() {
  if [[ ! -f "/home/${ADMIN_USER}/.ssh/authorized_keys" ]]; then
    warn "Skipping SSH hardening because ${ADMIN_USER} has no authorized_keys."
    return
  fi

  log "Hardening SSH"
  sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
  sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
  service_restart_ssh
}

configure_firewall() {
  log "Configuring UFW"
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow OpenSSH
  ufw allow in on tailscale0
  ufw allow out on tailscale0
  ufw --force enable
}

clone_repo() {
  if [[ -z "${REPO_DIR}" ]]; then
    REPO_DIR="/home/${AGENT_USER}/personal-ai"
  fi

  if [[ -d "${REPO_DIR}/.git" ]]; then
    log "Repo already exists at ${REPO_DIR}"
    return
  fi

  log "Cloning repo"
  sudo -u "${AGENT_USER}" git clone "${REPO_URL}" "${REPO_DIR}"
}

prepare_env_file() {
  local env_file="${REPO_DIR}/.env"
  local example_file="${REPO_DIR}/.env.example"

  if [[ ! -f "${env_file}" ]]; then
    if [[ -f "${example_file}" ]]; then
      cp "${example_file}" "${env_file}"
    else
      touch "${env_file}"
    fi
  fi

  if grep -q '^WEBUI_SECRET_KEY=' "${env_file}"; then
    if grep -q '^WEBUI_SECRET_KEY=$' "${env_file}" || grep -q '^WEBUI_SECRET_KEY=generate-a-random-secret-here$' "${env_file}"; then
      sed -i "s|^WEBUI_SECRET_KEY=.*$|WEBUI_SECRET_KEY=$(openssl rand -hex 32)|" "${env_file}"
    fi
  else
    printf '\nWEBUI_SECRET_KEY=%s\n' "$(openssl rand -hex 32)" >> "${env_file}"
  fi

  chown "${AGENT_USER}:${AGENT_USER}" "${env_file}"
}

deploy_open_webui() {
  [[ "${AUTO_DEPLOY}" == "true" ]] || return

  log "Preparing .env"
  prepare_env_file

  log "Validating Docker Compose"
  docker compose -f "${REPO_DIR}/docker-compose.yml" config >/dev/null

  log "Starting Open WebUI"
  docker compose -f "${REPO_DIR}/docker-compose.yml" up -d

  if [[ "${ENABLE_TS_SERVE}" == "true" ]]; then
    log "Publishing HTTPS over Tailscale"
    tailscale serve --bg --https=443 http://localhost:3000
  fi
}

print_summary() {
  local node_name
  node_name="$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("Self",{}).get("DNSName","").rstrip("."))' 2>/dev/null || true)"

  cat <<EOF

=========================================
Setup complete
=========================================

Admin user:  ${ADMIN_USER}
Agent user:  ${AGENT_USER}
Repo dir:    ${REPO_DIR}

Validation:
  docker compose -f ${REPO_DIR}/docker-compose.yml ps
  tailscale status

If Tailscale Serve is enabled, open:
  https://${node_name}

If that URL is empty, run:
  tailscale status

EOF
}

main() {
  require_root
  install_base_packages
  configure_swap
  ensure_admin_user
  ensure_agent_user
  install_tailscale
  configure_ssh_hardening
  configure_firewall
  clone_repo
  deploy_open_webui
  print_summary
}

main "$@"
