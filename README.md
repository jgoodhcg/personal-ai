# Personal AI

A personal AI setup with two halves that serve different purposes:

1. **Hosted chat (`/`)** — a self-hosted Open WebUI stack on a single VPS, behind
   Tailscale-only access. This is the daily driver: every model in one place, a
   system prompt I control, and my full chat history in a local database.
2. **Retrospect (`retrospect/`)** — a local Python project that indexes my exported
   chat history and reasons over it with deep personal context. This is where I go
   for questions that need a real understanding of me, not just a fresh model.

The two halves exist together because they're two ends of the same problem. The
hosted chat is great at *having* conversations but has no memory or custom indexing
over the corpus those conversations produce. Retrospect is where that corpus gets
turned into structured, queryable self-knowledge. The long-term direction is to
feed retrospect's insight back into the hosted chat (see *Future Direction*).

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

The part that's actively growing. Fills the gap the hosted chat has: **memory and
indexing over my accumulated chat corpus.**

### Why it exists
My daily chat lives in Open WebUI, but it can't remember across conversations or
index my history. Retrospect takes exported chats (currently ChatGPT exports),
runs them through staged extraction, and builds a knowledge base I can reason over
with full personal context.

### The build pipeline
```
raw_exports/ → chats/ → extractions/ → knowledge_base/
```
Normalize exports → run extraction passes → validate against schemas → synthesize
into the knowledge base. (Full script reference lives in `retrospect/README.md`.)

### The usage loop *(new — the actual product)*
1. **Ask** a question that needs deep context (planning, self-understanding, a decision).
2. **Reason** — an agent works over the knowledge base in `retrospect/data/knowledge_base/`.
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

Close the loop: feed retrospect's knowledge base back into the hosted Open WebUI
(via RAG, a generated system prompt, or memory) so the daily interface gains the
deep context it currently lacks — replacing today's manual "write a big system
prompt by hand" process.
