# AGENTS

Follows AGENT_BLUEPRINT.md

## Project Overview

Self-hosted AI platform on a single VPS. Open WebUI for chat interface, SSH access for CLI agents (claude-code, gemini-cli, etc.), and future task automation. Docker-based, SQLite for storage, Tailscale for access.

## Stack

- Bash + shell scripts
- Docker Compose
- SQLite (Open WebUI persistent data)
- Single VPS deployment with Tailscale-only access

## Commit Trailer Template

Store a template, not concrete runtime values.

```text
Co-authored-by: [AI_PRODUCT_NAME] <[AI_PRODUCT_EMAIL]>
AI-Provider: [AI_PROVIDER]
AI-Product: [AI_PRODUCT_LINE]
AI-Model: [AI_MODEL]
```

Template rules:
- `AI_PRODUCT_LINE` must be one of: `codex|claude|gemini|opencode`.
- Determine `AI_PRODUCT_LINE` from current session:
  - Codex or ChatGPT coding agent -> `codex`
  - Claude -> `claude`
  - Gemini -> `gemini`
  - OpenCode -> `opencode` (regardless underlying provider/model, including z.ai)
- Determine `AI_PROVIDER` and `AI_MODEL` from runtime model metadata.
- `AI_PRODUCT_EMAIL` may follow a project pattern such as `[AI_PRODUCT_LINE]@ai.example.com`.
- Fill this template at commit time; do not persist filled values in `AGENTS.md`.

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

## Decision Artifacts

- For high-impact or irreversible decisions, record a decision matrix in `.decisions/[name].json`.
- Use `matrix-reloaded` format for structured comparison.
- Do not run `matrix-reloaded` CLI commands from agent sessions; use project-provided matrix instructions/schema.
- Optional: add `.decisions/[name].md` for human-readable narrative context.
- Treat the JSON decision matrix as the authoritative record.

## References

- For operating model, see `AGENT_BLUEPRINT.md`
- For decision records and optional matrix format, see `AGENT_BLUEPRINT.md` section `Decision Artifacts [BP-DECISIONS]`.
- For executable work units, see `roadmap/index.md`
- For deployment and usage context, see `README.md`

## Key Files

- `docker-compose.yml` — Service definitions
- `.env` — API keys and secrets (not tracked)
- `knowledge/` — Markdown files for RAG
- `scripts/setup.sh` — VPS provisioning script
