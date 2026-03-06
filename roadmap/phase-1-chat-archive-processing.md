---
title: "Chat Archive Processing"
status: ready
description: "Process exported chat histories into a structured knowledge base for Open WebUI RAG"
created: 2026-03-06
updated: 2026-03-06
tags: [knowledge-base, rag, chat-exports]
priority: high
---

# Chat Archive Processing

## Intent

Turn years of ChatGPT, Claude, and z.ai/GLM chat exports into a searchable, structured personal knowledge base. The output feeds Open WebUI's RAG system so models have context about the user's interests, goals, projects, preferences, and ideas.

## Specification

### Pipeline

1. **Normalize** — Python script converts all exports (ChatGPT `conversations.json`, Claude JSON, GLM JSON) into uniform markdown files with YAML frontmatter. One file per conversation in `chats/`.

2. **Extract** — Batch script sends each conversation to a mid-range model (via OpenRouter) and saves structured YAML to `extractions/`. Two passes per conversation:
   - General extraction: summary, topics, interests, goals, preferences, personal facts, decisions, frustrations, open questions
   - Ideas extraction: every idea mentioned with type, status, development level, excitement, novelty

3. **Aggregate** — Script reads all extraction YAML and produces consolidated frequency-counted lists in `aggregated/` (topics, interests, goals, preferences, projects, ideas catalog, timeline, etc.)

4. **Synthesize** — Using a strong model, generate knowledge base documents in `knowledge_base/`:
   - `personal_profile.md` — biographical facts, cognitive style, values
   - `interest_map.md` — domains, intensity, connections, evolution
   - `goals_and_projects.md` — active/recurring/completed goals, project index
   - `working_with_me.md` — direct instructions for AI assistants (response format, detail level, common mistakes to avoid)
   - `decision_patterns.md` — how decisions are approached, recurring traps
   - `ideas_gallery.md` — full catalog with lost gems, zombie ideas, genealogy, patterns

5. **Human review** — Manual pass over all generated documents. Delete incorrect/outdated/sensitive content. This is non-optional.

6. **Deploy** — Upload knowledge base documents to Open WebUI as RAG documents.

### Data flow

All data directories are gitignored. Scripts are committed. Raw exports are preserved untouched.

```
raw_exports/ → [normalize] → chats/ → [extract] → extractions/ → [aggregate] → aggregated/ → [synthesize] → knowledge_base/
```

### Cost target

Under $5 total for OpenRouter API calls across all phases.

## Validation

- [ ] Normalizer handles all three export formats
- [ ] Extraction produces valid YAML for a sample batch
- [ ] Aggregation deduplicates and counts correctly
- [ ] Synthesized docs are factual and cited
- [ ] Human review completed before any upload
- [ ] Documents searchable in Open WebUI RAG

## Scope

- One-shot migration, not an ongoing pipeline (for now)
- No direct database writes or memory injection initially
- No UI — all CLI scripts
- Platform-agnostic output (markdown/YAML), uploaded manually to Open WebUI

## Context

- Chat exports are from daily use over a few years (hundreds to low thousands of conversations)
- Export formats: ChatGPT `conversations.json`, Claude JSON, z.ai/GLM JSON
- All sensitive data stays gitignored and on the VPS volume
- Future work: interactive query tool, temporal analysis, ongoing capture pipeline
