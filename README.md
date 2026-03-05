# Personal AI

Self-hosted AI platform on a single VPS. Open WebUI for chat, SSH access for CLI agents.

## Quick Start

```bash
# On a fresh Debian/Ubuntu VPS, as root:
curl -fsSL https://raw.githubusercontent.com/YOURUSER/personal-ai/main/scripts/setup.sh | bash
```

Or clone first, then run:
```bash
git clone https://github.com/YOURUSER/personal-ai.git
bash personal-ai/scripts/setup.sh
```

## After Setup

```bash
# Configure Open WebUI secret
cp .env.example .env
nano .env

# Start Open WebUI
docker compose up -d

# Expose via Tailscale
tailscale serve --bg --https=443 http://localhost:3000
```

Access at `https://<vps-name>.<tailnet>.ts.net`

## Structure

```
/home/agent/
├── personal-ai/        # This repo
│   ├── docker-compose.yml
│   ├── .env            # API keys (not tracked)
│   └── data/           # Open WebUI data (not tracked)
├── workspace/          # Scratchpad for CLI agents
└── projects/           # Clone repos here
```

## Users

| User | Purpose |
|------|---------|
| `<admin>` | sudo access, system maintenance |
| `agent` | CLI tools (claude-code, etc.), no sudo |

## CLI Tools

SSH as agent, then install what you need:

```bash
npm install -g @anthropic-ai/claude-code
```
