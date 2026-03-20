# Retrospect

`retrospect/` is the chat-archive processing subproject. It turns exported chat history into structured extractions that can later be aggregated, interpreted, synthesized into knowledge-base documents, and selectively loaded into RAG.

## Current Components

- `scripts/normalize_exports.py` normalizes raw platform exports into one-markdown-file-per-chat under `data/chats/`
- `scripts/extract.py` runs the four extraction passes against normalized chats and writes validated JSON outputs under `data/extractions/`
- `scripts/validate_extraction.py` validates extraction JSON against the schemas in `schemas/`
- `scripts/select_representative_sample.py` creates a small deterministic sample for model-pricing experiments under `data/samples/`
- `scripts/select_eval_trio.py` creates a fixed small/medium/large trio for empirical cross-model runs
- `scripts/analyze_model_costs.py` projects sample and full-archive costs across the model catalog and writes reports under `data/reports/`
- `scripts/run_model_panel.py` runs a fixed chat list across a model panel and emits manual quality/privacy review templates
- `scripts/render_model_panel_report.py` renders a static HTML review report from the latest model-panel bundle
- `prompts/` contains the Jinja prompt templates for each extraction pass
- `schemas/` contains the JSON Schemas that define the extraction contract
- `config/model_catalog.json` tracks the current model shortlist, pricing, and resolution notes for renamed or missing SKUs

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
./.venv/bin/python scripts/analyze_model_costs.py
./.venv/bin/python scripts/run_model_panel.py --group smaller
./.venv/bin/python scripts/render_model_panel_report.py
```
