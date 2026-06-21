# AGENTS

Follows `AGENT_BLUEPRINT.md` (version: 2026-06-17)

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
  - Claude Code -> `claude`
  - Gemini CLI -> `gemini`
  - OpenCode -> `opencode` (regardless underlying provider/model, including z.ai)
- Determine `AI_PROVIDER` and `AI_MODEL` from runtime model metadata.
- Resolve `AI_PRODUCT_NAME` and `AI_PRODUCT_EMAIL` from the **model name** using the tiered resolution order defined in `AGENT_BLUEPRINT.md` section `Commits [BP-WF-COMMIT]`.
- Fill this template at commit time; do not persist filled values in `AGENTS.md`.

## Validation Commands

| Level | Command | When |
|-------|---------|------|
| 1 | `docker compose config` | After docker-compose.yml changes |
| 2 | `docker compose up --dry-run` | Before deploying |
| 3 | `docker compose ps` | Verify running services |

## Allowed Commands

- `docker compose config` — Validate Compose file syntax and interpolation
- `docker compose up --dry-run` — Preview deployment actions without starting containers
- `docker compose ps` — Inspect running service state
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

## Sensitive Data Handling

This repo is **public on GitHub**. Anything committed is public and stays in history forever (purging requires a force-push rewrite plus, for full removal, a GitHub Support request).

Sensitive paths — never commit, never `git add -f`, never override the ignore:

- `retrospect/data/` — chat archives, raw exports, knowledge base, evaluations, personal context
- `data/`, `logs/` — runtime persistent data
- `knowledge/`, `knowledge_base/`, `personalization/` — RAG corpora and personal profiles
- `.env`, `.agent-profile.md` — secrets and personal config

Before staging:

- Never use `git add -A` or `git add .`. Stage explicit paths.
- If a path isn't already in `.gitignore` and looks personal (transcripts, profiles, prompts derived from private chats, API keys), stop and confirm with the user before adding.
- When in doubt run `git check-ignore -v <path>` to verify ignore coverage.
- New sensitive directories should get an explicit `.gitignore` entry before any files land in them.

## Decision Artifacts

- For high-impact or irreversible decisions, record a decision matrix in `.decisions/[name].json`.
- Use `matrix-reloaded` format for structured comparison.
- Do not run `matrix-reloaded` CLI commands from agent sessions; use project-provided matrix instructions/schema.
- Optional: add `.decisions/[name].md` for human-readable narrative context.
- Treat the JSON decision matrix as the authoritative record.

## References

- For operating model, see `AGENT_BLUEPRINT.md`
- For decision records, see `AGENT_BLUEPRINT.md` section `Decision Artifacts [BP-DECISIONS]`
- For executable work units, see `roadmap/index.md`
- For deployment and usage context, see `README.md`

## Key Files

- `docker-compose.yml` — Service definitions
- `.env` — API keys and secrets (not tracked)
- `knowledge/` — Markdown files for RAG (gitignored, sensitive)
- `scripts/setup.sh` — VPS provisioning script

## User Profile

See `.agent-profile.md` (git-ignored) for interaction preferences. Create on project init or alignment.
