# Retrospect

`retrospect/` is the chat-archive processing subproject. It turns exported chat history into structured extractions that can later be aggregated, interpreted, synthesized into knowledge-base documents, and selectively loaded into RAG.

## Current Components

- `scripts/normalize_exports.py` normalizes raw platform exports into one-markdown-file-per-chat under `data/chats/`
- `scripts/extract.py` runs the four extraction passes against normalized chats and writes validated JSON outputs under `data/extractions/`
- `scripts/validate_extraction.py` validates extraction JSON against the schemas in `schemas/`
- `scripts/select_representative_sample.py` creates a small deterministic sample for model-pricing experiments under `data/samples/`
- `scripts/select_eval_trio.py` creates a fixed small/medium/large trio for empirical cross-model runs
- `scripts/select_quality_eval_sample.py` creates deterministic `200 / 25 / 5` quality-evaluation samples under `data/samples/`
- `scripts/analyze_model_costs.py` projects sample and full-archive costs across the model catalog and writes reports under `data/reports/`
- `scripts/run_model_panel.py` runs a fixed chat list across a model panel and emits manual quality/privacy review templates
- `scripts/run_quality_eval.py` asks one or more judge models to score existing Pass 1-3 extraction bundles against the original chats
- `scripts/render_model_panel_report.py` renders a static HTML review report from the latest model-panel bundle
- `QUALITY_EVAL_RUBRIC.md` defines the scoring rubric used for automated and human extraction review
- `prompts/` contains the Jinja prompt templates for each extraction pass
- `schemas/` contains the JSON Schemas that define the extraction contract
- `config/model_catalog.json` tracks the current model shortlist, pricing, and resolution notes for renamed or missing SKUs

## CLI Agent Chat Mining

A second corpus alongside the hosted-chat exports: local CLI agent session logs
(Claude Code, Codex, OpenCode, Gemini CLI) mined into one SQLite database at
`data/agent_chats.db` (gitignored). One idempotent script per tool plus a shared
module — no API/LLM calls, purely mechanical parsing:

- `scripts/chat_db.py` — shared schema (`sessions`, `messages`, FTS5 index,
  ingest ledger) and upsert helpers; not run directly
- `scripts/mine_claude.py` — `~/.claude/projects/**/*.jsonl` (titles, git
  branch, per-message model, token usage)
- `scripts/mine_codex.py` — `~/.codex/sessions/` (dated JSONL + 2025-era legacy
  flat JSON)
- `scripts/mine_opencode.py` — row-copy from OpenCode's own SQLite DB (titles,
  tokens, cost)
- `scripts/mine_gemini.py` — `~/.gemini/tmp/*/chats/`; project paths recovered
  by sha256-matching `~/.gemini/projects.json` entries
- `scripts/mine_claude_legacy.py` — recovers pre-cleanup Claude Code history:
  full 2025 sessions from the v0.2.x `~/.claude/__store.db`, plus prompt-only
  day-sessions from `~/.claude/history.jsonl` for the deleted window (flagged
  `meta.prompt_only`)

Refresh everything (safe to rerun anytime; unchanged files are skipped):

```bash
cd retrospect/scripts
for s in mine_claude mine_codex mine_opencode mine_gemini mine_claude_legacy; do
  python3 $s.py
done
```

Schema notes: `sessions` carries tool, provider, model, project path,
`is_worktree`, git branch, title, timestamps, token totals, and cost (OpenCode
only). `messages` keeps flattened text plus the verbatim source record in `raw`,
with `is_meta`/`is_sidechain` flags for filtering. Full-text search via
`messages_fts` (`SELECT ... FROM messages_fts WHERE messages_fts MATCH '...'`).
Claude Code transcript cleanup is disabled via `cleanupPeriodDays` in
`~/.claude/settings.json` so the source logs stop expiring. See
`roadmap/cli-chat-mining.md` for design and history.

## Data Directory

All working data for this subproject lives under `retrospect/data/`. It is intentionally separated into pipeline stages.

### Current Layout

- `data/raw_exports/`
  Untouched source exports from each platform.
  Current provider subdirectories include `openai/`, `anthropic/`, and `zai/`.

- `data/chats/`
  Normalized markdown conversations produced by `normalize_exports.py`.
  Each file contains YAML frontmatter plus alternating `## User` / `## Assistant` message blocks.
  Filename shape:
  `conversation-id_source_yyyy-mm-dd_slug.md`

- `data/extractions/`
  Structured JSON extraction outputs produced by `extract.py`.
  Organized by extraction pass, then by model slug:
  `data/extractions/<pass_id>/<model_slug>/...json`

- `data/extractions/_runs/`
  Run-level bookkeeping for extraction jobs.
  Each run gets its own directory:
  `data/extractions/_runs/<timestamp>__<model_slug>/`
  The run directory contains a `manifest.json` with:
  - selected passes
  - chat/task counts
  - success/failure counts
  - token estimates
  - reported token usage
  - reported cost
  - failure summaries

- `data/samples/`
  Deterministic sample manifests and newline-delimited chat lists for model-comparison runs.

- `data/reports/`
  Generated cost-analysis markdown reports and other local analysis artifacts.
  This now includes the static HTML model-panel review report.

- `data/agent_chats.db`
  Unified SQLite database of local CLI agent sessions (see *CLI Agent Chat
  Mining* above). Rebuildable from the source logs at any time.

### Extraction Output Layout

Each extraction file represents:

- one normalized chat
- one extraction pass
- one model
- one run

Filename shape:
`<chat-stem>__<run-id>.json`

Example path:
`data/extractions/pass4_psych/google-gemini-2.0-flash-001/<chat-stem>__<run-id>.json`

Each JSON file contains the pass-specific structured fields plus a `metadata` object with:

- `source_conversation_id`
- `source_file`
- `pass_id`
- `model`
- `extracted_at`

## Planned Pipeline Stages

These later-stage directories are part of the roadmap but may not exist yet:

- `data/aggregated/`
  Cross-chat rollups, counts, deduped lists, and pattern summaries

- `data/inferred/`
  Higher-level derived analysis built from aggregated evidence

- `data/knowledge_base/`
  Final synthesized documents for assistant context and interpretive analysis

## Intended Flow

```text
data/raw_exports/
  -> data/chats/
  -> data/extractions/
  -> data/aggregated/
  -> data/inferred/
  -> data/knowledge_base/
```

## Typical Commands

From `retrospect/`:

```bash
./.venv/bin/python scripts/normalize_exports.py
./.venv/bin/python scripts/extract.py --model google/gemini-2.0-flash-001 --limit 5
./.venv/bin/python scripts/validate_extraction.py data/extractions/
./.venv/bin/python scripts/select_representative_sample.py
./.venv/bin/python scripts/select_eval_trio.py
./.venv/bin/python scripts/select_quality_eval_sample.py
./.venv/bin/python scripts/analyze_model_costs.py
./.venv/bin/python scripts/run_model_panel.py --group smaller
./.venv/bin/python scripts/run_quality_eval.py --model openai/gpt-5.4
./.venv/bin/python scripts/render_model_panel_report.py
```
