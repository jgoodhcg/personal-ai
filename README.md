# Personal AI

A personal AI setup with two **independent** halves. They are not connected today;
understanding how they differ — and don't yet talk to each other — is the key to
this repo.

1. **Hosted chat (`/`)** — a self-hosted Open WebUI stack on a single VPS, behind
   Tailscale-only access. My daily driver, used to consolidate away from provider
   chat UIs into one app: random questions, thought exploration, and the early
   seeds of projects. Projects that get real graduate out of here into git repos
   and CLI agentic tools on my laptop.
2. **Retrospect (`retrospect/`)** — a laptop-only Python project (never run on the
   VPS) that indexed an export of my **ChatGPT** history and built a knowledge base
   from it. This is where I go for anything needing deep context about me.

### How they relate today (important for future agents)
- The two halves **do not share data automatically.** Open WebUI has never been
  exported and its database has never been read by retrospect.
- Retrospect's corpus is a **stale, one-time ChatGPT export** — the newest chat in
  it is several months old, since I switched to Open WebUI for daily use.
- Retrospect produced KB documents *and* system-prompt drafts. **The only artifact
  I actually use in Open WebUI is the system prompt.** The rest of the knowledge
  base is currently used only by **CLI agentic tools locally** (e.g. Claude Code)
  for deeper, personalized questions.

### Where I want this to go
An ongoing system that **continuously builds a better index and personal profile
over time** — and lets me interact with it from either Open WebUI or a CLI agentic
interface — instead of today's stale one-shot export plus a hand-built system
prompt. See *Future Direction*.

---

## Part 1 — Hosted Chat (Open WebUI on a VPS)

The deployment side. Mostly stable; I only run it locally when changing
`docker-compose.yml`, and otherwise it lives on the VPS.

### Stack
- Open WebUI (`chat`) + SearXNG (web search), via Docker Compose
- SQLite for storage, Chroma for RAG vectors (under `data/`, gitignored)
- Tailscale for access — not public internet exposure

### Command Reference
*(bootstrap, compose validation, and common ops — preserved from prior README)*
- Bootstrap a fresh Debian/Ubuntu VPS with `scripts/setup.sh` (`TS_AUTHKEY` or
  interactive Tailscale login)
- `docker compose config` / `up --dry-run` / `ps` to validate
- `docker compose up -d` / `down` / `logs -f chat` / `pull` for routine ops

### First Run
- Tailscale auth key vs. interactive login; device approval notes
- The setup script creates one non-root project user and clones the repo

### Deploying Updates
- SSH in over Tailscale, `git pull --ff-only`, validate, `pull`, `up -d`
- `down` not needed for image updates; SearXNG settings-merge note
- `PROJECT_USER` substitution note

### Notes
- `data/` holds persistent Open WebUI state and stays out of git
- `.env` is local-only; copy from `.env.example`
- Prefer a downloaded script over `curl | bash` for TTY-sensitive prompts

---

## Part 2 — Retrospect (Personal-Context Engine)

Laptop-only. Indexes my chat history to support deep-context conversations about me.

### Why it exists
Provider/chat interfaces have no durable memory or custom indexing over my history.
Retrospect took a one-time **ChatGPT export**, ran it through staged extraction, and
built a knowledge base I can reason over with full personal context.

### What was actually done (vs. aspiration)
- A few one-shot runs indexed and summarized the ChatGPT export and synthesized
  **knowledge base documents** and **system-prompt drafts**.
- **Used in production:** only the generated **system prompt**, pasted into Open WebUI.
- **Used locally:** the KB and chat index, queried ad hoc via **CLI agentic tools**.
- **Not yet built:** any ongoing/incremental indexing of *hosted* chats. That
  corpus is frozen at the ChatGPT export. Open WebUI chats are *not* ingested.
- **New (July 2026):** a second, refreshable corpus — **CLI agent chat mining**.
  Local session logs from Claude Code, Codex, OpenCode, and Gemini CLI are mined
  into one SQLite database (`retrospect/data/agent_chats.db`) by per-tool scripts
  in `retrospect/scripts/` (`mine_*.py`). Unified schema (tool, provider, model,
  project, tokens, worktree flag, full message text + FTS), idempotent reruns,
  plus a legacy recovery path for Claude Code history that predates its
  transcript cleanup. Not yet scheduled; refreshed by rerunning the scripts.
  See `retrospect/README.md` and `roadmap/cli-chat-mining.md`.

### The build pipeline
```
raw_exports/ → chats/ → extractions/ → knowledge_base/
```
Normalize exports → run extraction passes → validate against schemas → synthesize
into the knowledge base. (Full script reference lives in `retrospect/README.md`.)

### The usage loop (current, manual)
1. **Ask** a question that needs deep context (planning, self-understanding, a decision)
   from a CLI agentic tool on the laptop.
2. **Reason** — the agent works over the knowledge base in `retrospect/data/knowledge_base/`.
3. **Persist** the durable insight back into the knowledge base so it compounds.

### Where captured insight goes *(convention)*
- `assistant_context/` — durable facts/preferences about me (taste, influences)
- `analysis/` — deeper reflections (values, narrative identity, blind spots)
- `.decisions/` — concrete choices with rationale
- topic folders (e.g. `tarot/`) — session artifacts

### Knowledge boundary
Everything under any `data/` directory is sensitive and gitignored — the code,
prompts, schemas, and decision/roadmap docs are tracked; the chat content,
extractions, and personal knowledge base are not.

---

## Future Direction

Move from a **stale one-shot export + hand-built system prompt** to an **ongoing,
compounding index and personal profile** that I can interact with from either Open
WebUI or a CLI agentic interface. Open questions being explored:
- How to keep the corpus current (e.g. read Open WebUI's chat DB instead of relying
  on a months-old ChatGPT export).
- Where the indexing/agentic work should run (laptop vs. on the VPS next to Open WebUI).
- How insight flows back into daily use (system prompt regeneration, RAG, or an
  agent that queries the index on demand).

These are unsettled. Nothing here is wired up yet.
