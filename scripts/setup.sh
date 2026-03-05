#!/usr/bin/env bash
set -euo pipefail

# Personal AI VPS bootstrap
# - Run as root on fresh Debian/Ubuntu
# - Goal: durable, Tailscale-only Open WebUI deployment

PROJECT_USER="${PROJECT_USER:-}"
REPO_URL="${REPO_URL:-https://github.com/jgoodhcg/personal-ai.git}"
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

prompt() {
  printf "%s" "$1"
}

set_sshd_config_value() {
  local key="$1"
  local value="$2"
  local config_file="/etc/ssh/sshd_config"

  if grep -Eq "^[#[:space:]]*${key}[[:space:]]+" "${config_file}"; then
    sed -i "s|^[#[:space:]]*${key}[[:space:]].*|${key} ${value}|" "${config_file}"
  else
    printf '\n%s %s\n' "${key}" "${value}" >> "${config_file}"
  fi
}

die() {
  printf "\n[ERROR] %s\n" "$1" >&2
  exit 1
}

run_as_user() {
  local user="$1"
  shift

  if command -v runuser >/dev/null 2>&1; then
    runuser -u "${user}" -- "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo -u "${user}" "$@"
    return
  fi

  die "Need runuser or sudo to execute commands as ${user}."
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

ensure_project_user() {
  if [[ -z "${PROJECT_USER}" ]]; then
    if [[ ! -t 0 ]]; then
      die "PROJECT_USER is required for non-interactive runs."
    fi

    read -rp "Project username: " PROJECT_USER
  fi

  [[ -n "${PROJECT_USER}" ]] || die "PROJECT_USER is required."
  [[ "${PROJECT_USER}" != "root" ]] || die "PROJECT_USER must be a non-root username."

  if ! id "${PROJECT_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "${PROJECT_USER}"
  fi

  usermod -aG sudo,docker "${PROJECT_USER}"

  if [[ -f /root/.ssh/authorized_keys ]]; then
    mkdir -p "/home/${PROJECT_USER}/.ssh"
    cp /root/.ssh/authorized_keys "/home/${PROJECT_USER}/.ssh/authorized_keys"
    chown -R "${PROJECT_USER}:${PROJECT_USER}" "/home/${PROJECT_USER}/.ssh"
    chmod 700 "/home/${PROJECT_USER}/.ssh"
    chmod 600 "/home/${PROJECT_USER}/.ssh/authorized_keys"
  else
    warn "No /root/.ssh/authorized_keys found. Verify ${PROJECT_USER} SSH access before hardening."
  fi
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
  apt install -y curl git ufw fail2ban openssl python3 sudo docker.io docker-compose-v2
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
    log "Using Tailscale auth key"
    tailscale up --authkey "${TS_AUTHKEY}"
  else
    warn "No TS_AUTHKEY provided. Tailscale will print a login URL for browser-based sign-in."
    warn "If device approval is enabled in your tailnet, approve this server in the Tailscale admin console after sign-in."

    if [[ ! -t 0 ]]; then
      die "TS_AUTHKEY is required for non-interactive runs. Set TS_AUTHKEY or rerun in an interactive shell."
    fi

    prompt "Press Enter to continue with interactive Tailscale login..."
    read -r _
    tailscale up
  fi

  tailscale set --operator="${PROJECT_USER}"
}

configure_ssh_hardening() {
  if [[ ! -f "/home/${PROJECT_USER}/.ssh/authorized_keys" ]]; then
    warn "Skipping SSH hardening because ${PROJECT_USER} has no authorized_keys."
    return
  fi

  log "Hardening SSH"
  set_sshd_config_value "PasswordAuthentication" "no"
  set_sshd_config_value "PermitRootLogin" "no"
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
    REPO_DIR="/home/${PROJECT_USER}/personal-ai"
  fi

  if [[ -d "${REPO_DIR}/.git" ]]; then
    log "Repo already exists at ${REPO_DIR}"
    return
  fi

  if [[ -e "${REPO_DIR}" ]]; then
    die "REPO_DIR exists but is not a git repo: ${REPO_DIR}"
  fi

  log "Cloning repo"
  run_as_user "${PROJECT_USER}" git clone "${REPO_URL}" "${REPO_DIR}"
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

  chown "${PROJECT_USER}:${PROJECT_USER}" "${env_file}"
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

Project user: ${PROJECT_USER}
Repo dir:     ${REPO_DIR}

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
  ensure_project_user
  install_tailscale
  configure_ssh_hardening
  configure_firewall
  clone_repo
  deploy_open_webui
  print_summary
}

main "$@"
