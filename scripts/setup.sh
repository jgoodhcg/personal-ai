#!/bin/bash
set -euo pipefail

# Personal AI VPS Setup
# Run as root on a fresh VPS

echo "=== Installing Docker ==="
curl -fsSL https://get.docker.com | sh

echo "=== Installing Tailscale ==="
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

echo "=== Creating agent user ==="
useradd -m -s /bin/bash agent
usermod -aG docker agent

echo "=== Setting up agent home ==="
sudo -u agent mkdir -p /home/agent/{workspace,projects}

echo "=== Configuring agent shell ==="
cat >> /home/agent/.bashrc << 'EOF'

# Load API keys
if [ -f ~/.env ]; then
    set -a
    source ~/.env
    set +a
fi

# Default to workspace
cd ~/workspace 2>/dev/null || true
EOF

echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Clone repo:        sudo -u agent git clone <repo-url> /home/agent/personal-ai"
echo "2. Copy env file:     sudo -u agent cp /home/agent/personal-ai/.env.example /home/agent/personal-ai/.env"
echo "3. Edit secrets:      sudo -u agent nano /home/agent/personal-ai/.env"
echo "4. Start services:    cd /home/agent/personal-ai && sudo -u agent docker compose up -d"
echo "5. Expose via TS:     tailscale serve --bg https / http://localhost:3000"
echo ""
echo "SSH as agent user for CLI tools (claude-code, etc.)"
