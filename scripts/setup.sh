#!/bin/bash
set -euo pipefail

# Personal AI VPS Setup
# Run as root on a fresh Debian/Ubuntu VPS
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/YOURUSER/personal-ai/main/scripts/setup.sh | bash
#
# Or with variables:
#   curl -fsSL ... | ADMIN_USER=myname TS_AUTHKEY=tskey-auth-xxx bash

#############################################
# Configuration (override via environment)
#############################################

ADMIN_USER="${ADMIN_USER:-}"           # Your sudo user (will prompt if empty)
AGENT_USER="${AGENT_USER:-agent}"      # CLI tools user
REPO_URL="${REPO_URL:-}"               # Git repo URL (will prompt if empty)
TS_AUTHKEY="${TS_AUTHKEY:-}"           # Tailscale auth key (interactive if empty)
SWAP_SIZE="${SWAP_SIZE:-2G}"           # Swap file size

#############################################
# Prompts
#############################################

if [[ -z "$ADMIN_USER" ]]; then
    read -rp "Admin username (your sudo user): " ADMIN_USER
fi

if [[ -z "$REPO_URL" ]]; then
    read -rp "Git repo URL (or press enter to skip clone): " REPO_URL
fi

echo ""
echo "=== Personal AI Setup ==="
echo "Admin user:  $ADMIN_USER"
echo "Agent user:  $AGENT_USER"
echo "Repo:        ${REPO_URL:-[skip]}"
echo ""

#############################################
# 1. System Prep & Dependencies
#############################################

echo "=== Updating system ==="
apt update && apt upgrade -y

echo "=== Installing dependencies ==="
apt install -y curl git ufw fail2ban

echo "=== Configuring swap ($SWAP_SIZE) ==="
if [[ ! -f /swapfile ]]; then
    fallocate -l "$SWAP_SIZE" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap created"
else
    echo "Swap already exists, skipping"
fi

#############################################
# 2. User & SSH Hardening
#############################################

echo "=== Creating admin user: $ADMIN_USER ==="
if ! id "$ADMIN_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$ADMIN_USER"
    usermod -aG sudo "$ADMIN_USER"

    # Migrate SSH keys from root
    if [[ -f /root/.ssh/authorized_keys ]]; then
        mkdir -p "/home/$ADMIN_USER/.ssh"
        cp /root/.ssh/authorized_keys "/home/$ADMIN_USER/.ssh/"
        chown -R "$ADMIN_USER:$ADMIN_USER" "/home/$ADMIN_USER/.ssh"
        chmod 700 "/home/$ADMIN_USER/.ssh"
        chmod 600 "/home/$ADMIN_USER/.ssh/authorized_keys"
        echo "SSH keys migrated from root"
    fi
else
    echo "User $ADMIN_USER already exists"
fi

echo "=== Hardening SSH ==="
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

echo "=== Configuring firewall ==="
ufw allow ssh
ufw --force enable

#############################################
# 3. Docker
#############################################

echo "=== Installing Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
else
    echo "Docker already installed"
fi

#############################################
# 4. Node.js (for CLI tools)
#############################################

echo "=== Installing Node.js ==="
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

#############################################
# 5. Agent User (CLI tools)
#############################################

echo "=== Creating agent user: $AGENT_USER ==="
if ! id "$AGENT_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$AGENT_USER"
    usermod -aG docker "$AGENT_USER"

    # Copy SSH keys so admin can SSH as agent
    if [[ -f "/home/$ADMIN_USER/.ssh/authorized_keys" ]]; then
        mkdir -p "/home/$AGENT_USER/.ssh"
        cp "/home/$ADMIN_USER/.ssh/authorized_keys" "/home/$AGENT_USER/.ssh/"
        chown -R "$AGENT_USER:$AGENT_USER" "/home/$AGENT_USER/.ssh"
        chmod 700 "/home/$AGENT_USER/.ssh"
        chmod 600 "/home/$AGENT_USER/.ssh/authorized_keys"
    fi
else
    echo "User $AGENT_USER already exists"
    usermod -aG docker "$AGENT_USER"
fi

# Agent home structure
sudo -u "$AGENT_USER" mkdir -p "/home/$AGENT_USER"/{workspace,projects}

# Agent shell config
cat >> "/home/$AGENT_USER/.bashrc" << 'EOF'

# Load API keys
if [[ -f ~/.env ]]; then
    set -a
    source ~/.env
    set +a
fi

# Default to workspace
cd ~/workspace 2>/dev/null || true
EOF

#############################################
# 6. Tailscale
#############################################

echo "=== Installing Tailscale ==="
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "Tailscale already installed"
fi

echo "=== Connecting to Tailscale ==="
if [[ -n "$TS_AUTHKEY" ]]; then
    tailscale up --authkey "$TS_AUTHKEY"
else
    tailscale up
fi

# Fix DNS collision (hostname pointing to 127.0.0.1 breaks MagicDNS)
HOSTNAME=$(hostname)
if grep -q "127.0.1.1.*$HOSTNAME" /etc/hosts; then
    sed -i "s/127.0.1.1.*$HOSTNAME/127.0.1.1 $HOSTNAME.local/" /etc/hosts
    echo "Fixed /etc/hosts DNS collision"
fi

# Let agent user manage Tailscale serve
tailscale set --operator="$AGENT_USER"

#############################################
# 7. Clone Repo
#############################################

if [[ -n "$REPO_URL" ]]; then
    echo "=== Cloning repo ==="
    REPO_DIR="/home/$AGENT_USER/personal-ai"
    if [[ ! -d "$REPO_DIR" ]]; then
        sudo -u "$AGENT_USER" git clone "$REPO_URL" "$REPO_DIR"
    else
        echo "Repo already exists at $REPO_DIR"
    fi
fi

#############################################
# Done
#############################################

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
if [[ -z "$REPO_URL" ]]; then
echo "1. Clone repo:"
echo "   sudo -u $AGENT_USER git clone <repo-url> /home/$AGENT_USER/personal-ai"
echo ""
fi
echo "2. Configure secrets:"
echo "   sudo -u $AGENT_USER cp /home/$AGENT_USER/personal-ai/.env.example /home/$AGENT_USER/personal-ai/.env"
echo "   sudo -u $AGENT_USER nano /home/$AGENT_USER/personal-ai/.env"
echo ""
echo "3. Start services:"
echo "   cd /home/$AGENT_USER/personal-ai && sudo -u $AGENT_USER docker compose up -d"
echo ""
echo "4. Expose via Tailscale:"
echo "   tailscale serve --bg --https=443 http://localhost:3000"
echo ""
echo "5. SSH access:"
echo "   ssh $ADMIN_USER@<tailscale-ip>    # Admin (sudo)"
echo "   ssh $AGENT_USER@<tailscale-ip>    # Agent (CLI tools)"
echo ""
echo "6. Install CLI tools (as agent user):"
echo "   npm install -g @anthropic-ai/claude-code"
echo ""
