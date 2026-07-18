---
title: "CLI Agent Chat Mining"
status: active
description: "Mine local CLI agent session logs (Claude Code, Codex, OpenCode, Gemini) into one SQLite database for analysis"
created: 2026-07-08
updated: 2026-07-18
subproject: retrospect
tags: [knowledge-base, chat-exports, sqlite, claude-code, codex, opencode, gemini]
priority: medium
---

# CLI Agent Chat Mining

## Intent

The chat-archive-processing effort covers exported *hosted* chats (ChatGPT, Claude, z.ai). This covers the other corpus: local agentic-CLI session logs already sitting on disk. Consolidate them into one SQLite database with a uniform schema so raw SQL (and later, the retrospect extraction pipeline) can run across all of them. Priority order: Claude Code > Codex > OpenCode > Gemini.

## Source Inventory (verified on disk, 2026-07-08)

| Tool | Location | Format | Volume |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<dashed-cwd>/<session-uuid>.jsonl` | JSONL, typed records | 42 files, 33 MB |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (new) + flat `rollout-*.json` in sessions root (2025-era legacy) | JSONL `{timestamp, type, payload}` | 312 files, 233 MB |
| OpenCode | `~/.local/share/opencode/opencode.db` | **already SQLite** (`session`, `message`, `part` tables; `message.data` is JSON) | 242 sessions, 6,343 messages |
| Gemini | `~/.gemini/tmp/<project-hash>/chats/session-*.json` | single JSON `{sessionId, projectHash, startTime, lastUpdated, messages[]}` | 64 chats |

Format notes from sampling:

- **Claude Code**: one file per session. Message lines have `type: user|assistant`, `message.{role,content}` (content is string or content-block array), plus rich envelope fields: `uuid`, `parentUuid`, `timestamp`, `cwd`, `gitBranch`, `sessionId`, `version`, `isSidechain`, `isMeta`. Non-message lines (`mode`, `permission-mode`, `file-history-snapshot`, etc.) are skippable. Sidechain (subagent) messages share the file — keep them, flag them.
- **Codex**: `session_meta` line carries `id`, `cwd`, `cli_version`, and the full injected instructions blob (huge — don't store as a message). Subsequent lines are typed payloads (`response_item` etc.) containing user/assistant/tool items. Legacy 2025 flat `.json` files use an older shape; handle with a second parser or defer.
- **OpenCode**: no parsing needed — read its DB directly and map rows. `message.data` JSON holds role/content; `session` has title, directory, model, token/cost columns worth carrying over. A legacy `storage/` JSON tree exists but the DB appears authoritative.
- **Gemini**: trivially small; messages are `{id, timestamp, type, content}` where `type` includes `user`, `gemini`, `info`. Project hash is opaque — no cwd recovery unless mapped via `~/.gemini/projects.json`.

## Specification

Implemented 2026-07-08 as one script per tool (stdlib-only Python) plus a shared module, all in `retrospect/scripts/`:

- `chat_db.py` — schema, upsert/replace helpers, FTS rebuild, ingest ledger
- `mine_claude.py`, `mine_codex.py` (new JSONL + legacy flat JSON), `mine_opencode.py` (row-copy from its DB), `mine_gemini.py` (project paths recovered by sha256-matching `~/.gemini/projects.json` entries against the tmp dir hashes)
- `mine_claude_legacy.py` — recovers what survived Claude Code's 30-day transcript cleanup: 5 full sessions (Apr–May 2025) from the v0.2.x-era `~/.claude/__store.db`, plus prompt-only per-project/per-day synthetic sessions from `~/.claude/history.jsonl` for dates before the earliest surviving full transcript (flagged `meta.prompt_only`). `cleanupPeriodDays: 99999` set in `~/.claude/settings.json` on 2026-07-09 to stop further deletion.

Output DB: `retrospect/data/agent_chats.db` (gitignored via `retrospect/data/`). No LLM calls anywhere — mechanical flattening only; every message keeps its verbatim source record in `raw`. Sessions carry tool, provider, model, project_path, is_worktree (path heuristic), git branch (claude), title (claude + opencode), start/end timestamps, token totals, and cost (opencode only — the only tool that persists it).

Initial ingest: claude-code 40 sessions / 5.5k msgs, codex 295 / 51.7k, opencode 242 / 6.3k, gemini 55 / 1.5k. Reruns skip unchanged files. Note: codex and gemini have fewer sessions than files because resumed sessions share an id across files; latest file wins.

### Schema

```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,             -- 'claude' | 'codex' | 'opencode' | 'gemini'
  source_session_id TEXT NOT NULL,  -- native id
  source_path TEXT,                 -- originating file (null for opencode)
  project_path TEXT,                -- cwd/directory when known
  git_branch TEXT,
  title TEXT,                       -- opencode has it; others null or derived later
  model TEXT,
  started_at TEXT,                  -- ISO8601 UTC
  ended_at TEXT,
  message_count INTEGER,
  meta TEXT,                        -- JSON: cli_version, tokens/cost (opencode), etc.
  UNIQUE(source, source_session_id)
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  idx INTEGER NOT NULL,             -- order within session
  role TEXT NOT NULL,               -- 'user' | 'assistant' | 'tool' | 'system'
  ts TEXT,
  text TEXT,                        -- extracted plain text (see below)
  is_sidechain INTEGER DEFAULT 0,
  is_meta INTEGER DEFAULT 0,        -- caveats, command wrappers, injected reminders
  raw TEXT,                         -- original JSON record, verbatim
  UNIQUE(session_id, idx)
);

CREATE VIRTUAL TABLE messages_fts USING fts5(text, content='messages', content_rowid='id');
```

Text extraction: flatten content blocks to plain text — `text` blocks verbatim; tool calls as `[tool: Name] <one-line input summary>`; tool results truncated to ~2k chars. Full fidelity always survives in `raw`, so extraction can be conservative and revised later by re-deriving from `raw` without re-reading source files.

### Meta/noise handling

Mark rather than drop: `<local-command-caveat>`, `<command-name>` wrappers, `isMeta` records, Gemini `info` lines, and messages whose text starts with `<system-reminder>` get `is_meta = 1`. Analysis queries filter on it; nothing is lost.

### Incrementality / idempotence

- Per-file ingest ledger: `ingested_files(path, mtime, size)`. Skip unchanged files; on change, delete that session's rows and re-ingest the file (sessions are file-scoped everywhere, so this is clean and simple — no per-message diffing).
- OpenCode: re-ingest sessions whose `time_updated` exceeds the stored value.
- Whole run is safe to re-execute anytime; `--source claude` etc. limits scope.

### Adapters (build in this order)

1. `claude` — highest value, cleanest format.
2. `codex` — new JSONL format first; legacy flat `.json` files behind a `--codex-legacy` flag or a follow-up.
3. `opencode` — row-copy from its DB.
4. `gemini` — smallest, last.

## Validation

- [ ] `sqlite3 cli_chats.db 'SELECT source, COUNT(*) FROM sessions GROUP BY source'` matches the file/row counts above (± skipped empty sessions, reported by the script)
- [ ] Spot-check one session per source: message order, roles, timestamps, and text match the raw log
- [ ] FTS query returns hits across all four sources
- [ ] Second consecutive run ingests zero files (idempotence)
- [ ] Sidechain/meta flags verified on a known Claude session with subagents

## Scope

**In:** the four sources above, unified schema, plain-text extraction, FTS, incremental re-runs.

**Out (for now):**
- Any LLM extraction/analysis passes — this is ingestion only; the retrospect extraction pipeline can point at this DB later
- Normalizing tool-call semantics across tools beyond the flat-text summary
- Codex legacy 2025 flat-JSON files (defer unless cheap)
- Ongoing capture daemon/hooks — rerunning the script is the capture mechanism
- Merging with the hosted-chat corpus in `retrospect/data/chats/` (a later `sources` bridge, not this unit)

## Context

- Sibling effort: [chat-archive-processing](chat-archive-processing.md) — same analysis goals, hosted exports; this DB should eventually feed the same extraction passes
- Agentic logs are noisy (tool output dominates bytes); the `text` column + `is_meta`/role filters are what make analysis tractable
- All output under `retrospect/data/` (gitignored), consistent with existing convention

## Open Questions (draft only)

- Keep full tool results in `raw` only, or also a `tool_output` side table? (Default: raw-only until a query needs it.)
- Worktree sessions in Claude (`...-worktrees-...` project dirs): treat as distinct project_path or normalize to the parent repo?
- Include Claude Code sessions' token/cost data if derivable from assistant records' `usage` fields?
