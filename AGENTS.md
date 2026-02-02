# AGENTS

Follows AGENT_BLUEPRINT.md

## Project Overview

Self-hosted AI platform on a single VPS. Open WebUI for chat interface, SSH access for CLI agents (claude-code, gemini-cli, etc.), and future task automation. Docker-based, SQLite for storage, Tailscale for access.

## Validation Commands

| Level | Command | When |
|-------|---------|------|
| 1 | `docker compose config` | After docker-compose.yml changes |
| 2 | `docker compose up --dry-run` | Before deploying |
| 3 | `docker compose ps` | Verify running services |

## Allowed Commands

- `docker compose up -d` — Start services
- `docker compose down` — Stop services
- `docker compose logs` — View logs
- `docker compose pull` — Update images
- `tailscale status` — Check Tailscale connection

## Require Confirmation

- `docker compose down -v` — Removes volumes (data loss)
- `scripts/setup.sh` — Modifies system (creates users, installs packages)
- Any `rm` commands in data/ or knowledge/

## Never Run

- `docker system prune` — Could remove needed images/volumes
- Commands that expose ports publicly (only Tailscale access)

## Project-Specific Rules

- All persistent data lives in `data/` (gitignored)
- Knowledge base in `knowledge/` is version controlled
- No secrets in repo — use .env (copy from .env.example)
- VPS access via Tailscale only, no public ports

## Key Files

- `docker-compose.yml` — Service definitions
- `.env` — API keys and secrets (not tracked)
- `knowledge/` — Markdown files for RAG
- `scripts/setup.sh` — VPS provisioning script
