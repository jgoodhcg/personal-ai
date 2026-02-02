# Personal AI 

A self-hosted AI platform on a single VPS. Daily conversational interface, CLI agent access, and future expansion to autonomous task running. Everything runs in Docker for portability.

## Philosophy

- Data outlives applications. Storage decisions matter.
- Files on disk > databases when possible. SQLite when not.
- Composition over monoliths. Swap components freely.
- One VPS, one backup target, full portability.

---

## Immediate Goal

Scaffold a minimal VPS setup that runs Open WebUI in Docker with:

- SQLite database (single file, portable)
- Persistent volumes for data and future knowledge base
- Environment-based configuration for API keys
- Ready for Tailscale Serve exposure
- SSH access for agentic CLI tools

---

## Project Structure

```
personal-ai/
├── docker-compose.yml
├── .env.example                # Template for secrets
├── .gitignore                  # Ignore .env, data/, workspace/
├── data/                       # Open WebUI persistent storage (gitignored)
├── knowledge/                  # Shared markdown files (tracked)
│   └── .gitkeep
├── workspace/                  # Shared home for CLI agents (gitignored)
└── scripts/
    └── setup.sh                # Initial VPS setup (docker, tailscale, user)
```

---

## Components

### Chat Interface (Phase 1 - Now)

Open WebUI via public container. Swap for custom fork later.

- Multi-provider (Claude, OpenAI, Gemini, xAI, local)
- RAG over knowledge base
- SQLite for history
- Mobile and desktop access via Tailscale

```yaml
# docker-compose.yml
services:
  chat:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - ./data:/app/backend/data
      - ./knowledge:/app/backend/data/docs
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
    restart: unless-stopped
```

### CLI Agent Environment (Phase 1 - Now)

SSH access for running agentic tools against the workspace.

**Tools:** claude-code, gemini-cli, codex-cli, opencode

```bash
# VPS user setup
useradd -m -s /bin/bash agent

# Agent home structure
/home/agent/
├── .config/                    # CLI tool configs
├── .env                        # Shared API keys (sourced in .bashrc)
├── workspace/                  # Mounted in containers too
└── projects/                   # Clone repos here for agentic work
```

```bash
# In agent's .bashrc
set -a
source ~/.env
set +a
cd ~/workspace
```

CLI tools run on the host directly — no container needed. Interactive SSH sessions.

### Knowledge Base (Phase 1 - Now)

Markdown files describing preferences, projects, context.

- Injected into chat via RAG
- Read by future task scripts
- Version controlled

```
knowledge/
├── about-me.md
├── preferences.md
└── projects/
    └── project-x.md
```

### Task Runner (Phase 2 - Future)

Cron-scheduled Python scripts.

- Daily: news digest, inbox summary
- Weekly: project audits, dependency checks
- Writes markdown to logs/

```yaml
# Future addition to docker-compose.yml
services:
  tasks:
    build: ./tasks
    volumes:
      - ./knowledge:/knowledge:ro
      - ./logs:/logs
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Dashboard (Phase 3 - Future)

Minimal web UI for task visibility.

- Recent runs, upcoming jobs
- Log viewer
- Separate from chat UI

### Custom Chat Fork (Phase 4 - Future)

When upstream doesn't do what you need.

```yaml
# Swap one line when ready
image: ghcr.io/yourusername/open-webui:main
```

- Published to personal GHCR
- Synced with upstream periodically
- GitHub Actions for automatic builds

---

## Setup Script Outline

```bash
#!/bin/bash
# scripts/setup.sh

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Create agent user
useradd -m -s /bin/bash agent
usermod -aG docker agent

# Create directories
mkdir -p /home/agent/workspace
mkdir -p /opt/personal-ai/{data,knowledge,logs}
chown -R agent:agent /home/agent
chown -R agent:agent /opt/personal-ai

# Symlink workspace
ln -s /opt/personal-ai/workspace /home/agent/workspace

# Expose via Tailscale
tailscale serve --bg https / http://localhost:3000
```

---

## Environment Variables

```bash
# .env.example
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
XAI_API_KEY=...
WEBUI_SECRET_KEY=your-random-secret-here
```

---

## Backup Strategy

Single target: `/opt/personal-ai/`

```
/opt/personal-ai/
├── data/webui.db              # All chat history
├── knowledge/                  # All context files
└── logs/                       # All task outputs
```

```bash
# Simple backup
tar -czf personal-ai-backup-$(date +%Y%m%d).tar.gz /opt/personal-ai/
```

---

## Migration Path

### Chat History Import

ChatGPT, Claude, Gemini exports can be converted to Open WebUI import format:

```
POST /api/v1/chats/import
Content-Type: application/json

{
  "chats": [
    {
      "chat": { "history": { "messages": {...} } },
      "created_at": 1234567890
    }
  ]
}
```

### Switching Chat Interfaces

If Open WebUI doesn't work out:

1. Export all chats via API
2. Convert to new format
3. Swap container in docker-compose.yml
4. Knowledge base and task runner unchanged

---

## Open Questions

- [ ] How to handle file attachments in chat (stored where?)
- [ ] Vector DB choice for RAG (default ChromaDB vs alternatives)
- [ ] Ollama for local models — worth running on same VPS?
- [ ] Notification system for task failures
