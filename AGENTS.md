# AGENTS

Follows `AGENT_BLUEPRINT.md` (version: 2026-07-05)

## Project Overview

Self-hosted AI platform on a single VPS. Open WebUI for chat interface, SSH access for CLI agents (claude-code, gemini-cli, etc.), and future task automation. Docker-based, SQLite for storage, Tailscale for access.

## Stack

- Bash + shell scripts
- Docker Compose
- SQLite (Open WebUI persistent data)
- Single VPS deployment with Tailscale-only access

## Environment

- Version manager: Docker Compose
- Version file: `docker-compose.yml`
- Lockfile: none
- Setup: `docker compose config`

## Commit Trailer Template

Store a template, not concrete runtime values. Fill it at commit time using `references/commit-attribution.md`.

```text
Co-authored-by: [AI_PRODUCT_NAME] <[AI_PRODUCT_EMAIL]>
AI-Provider: [AI_PROVIDER]
AI-Product: [AI_PRODUCT_LINE]
AI-Model: [AI_MODEL]
```

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

## CLI Chat Mining

Local CLI agent session logs are mined into `retrospect/data/agent_chats.db`
(gitignored, sensitive). Rules:

- Refresh by running each `retrospect/scripts/mine_*.py` with `python3` from
  `retrospect/scripts/`; all are idempotent and safe to rerun. `chat_db.py` is a
  shared module, not an entrypoint.
- Never make API/LLM calls from the mining scripts — parsing is mechanical only.
- Read-only toward source logs (`~/.claude`, `~/.codex`, `~/.local/share/opencode`,
  `~/.gemini`) — never modify or delete them.
- Do not remove `cleanupPeriodDays` from `~/.claude/settings.json`; it prevents
  Claude Code from deleting old transcripts.
- Query results from the DB contain personal chat content — treat as sensitive;
  never paste bulk content into committed files.

## Knowledge Base

Tool: Roam Research.

When asked to generate a Roam summary or thread, use the `roam-thread-summary` skill. The user pastes AI-assisted readings, threads, and summaries into Roam as nested bullet outlines. When asked to produce Roam content, output a copy-paste-ready bullet tree and preserve a local copy under `retrospect/data/knowledge_base/` (gitignored — see Sensitive Data Handling).

### Attribution / parent block

Nest AI-generated thread summaries under this parent block:

- `- [[ai-thread]] [[<model-id>]] [[personal-ai]]`

Use the exact runtime model in `<model-id>`. Only add tool refs (`[[codex-cli]]`, `[[claude-code]]`, `[[gemini-cli]]`, `[[opencode]]`) or other `[[Page Name]]` refs when the user asks.

### Tarot reading artifacts

The user keeps tarot readings in Roam with a stable convention — mirror it:

- Header block tags: `[[tarot]]`, the moon phase (e.g. `[[moon/full]]`), a source/thread marker, and the model — e.g. `- [[tarot]] [[moon/full]] [[chatgpt-thread]] [[gpt-5.2]] 04:02`. For agent-generated readings, use `[[ai-thread]] [[<model-id>]] [[personal-ai]]` in place of the chat-thread/model tags. Append an `HH:MM` timestamp when known.
- Card references use Roam path refs:
  - Minors: `[[tarot/card/<suit>/<rank>]]` — suits `wand` | `cup` | `sword` | `pentacle`; ranks `ace`, `two`…`ten`, `page`, `knight`, `queen`, `king`.
  - Majors: `[[tarot/card/<name>]]` — e.g. `[[tarot/card/sun]]`, `[[tarot/card/magician]]`.
  - Mark reversed cards with the word `reversed` after the ref, not in the path.
- Typical nested sections (use what fits): **Spread** (placement names + what each represents), **Cards drawn**, the user's own interpretation, the assistant interpretation/synthesis, and a **Core takeaway**. Free-form sections (*Meta-insight*, *Placement conundrum*, etc.) are welcome when relevant.

## Sensitive Data Handling

This repo is **public on GitHub**. Anything committed is public and stays in history forever (purging requires a force-push rewrite plus, for full removal, a GitHub Support request).

Sensitive paths — never commit, never `git add -f`, never override the ignore:

- `retrospect/data/` — chat archives, raw exports, knowledge base, evaluations, personal context, mined CLI chat DB (`agent_chats.db`)
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

- Blueprint policy: `AGENT_BLUEPRINT.md`
- Commit attribution: `references/commit-attribution.md`
- User profile guidance: `references/user-profile.md`
- Example ready work unit: `references/work-unit-example.md`
- For executable work units, see `roadmap/index.md`
- For deployment and usage context, see `README.md`

## Key Files

- `docker-compose.yml` — Service definitions
- `.env` — API keys and secrets (not tracked)
- `knowledge/` — Markdown files for RAG (gitignored, sensitive)
- `scripts/setup.sh` — VPS provisioning script
- `retrospect/scripts/chat_db.py` + `mine_*.py` — CLI agent chat mining into `retrospect/data/agent_chats.db`

## User Profile

See `.agent-profile.md` (git-ignored) for interaction preferences. Create on project init or alignment.
