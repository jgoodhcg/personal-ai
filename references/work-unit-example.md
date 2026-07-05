---
title: "Export saved items as Markdown"
status: ready
description: "Add a CLI command that exports saved feed items to one Markdown file per item"
created: 2026-07-02
updated: 2026-07-02
tags: [export, cli]
priority: medium
---

<!-- Example work unit (BP-INSTR-07). This is reference material, not real work.
     It shows the concreteness a `ready` work unit needs — especially in
     Specification and Validation. -->

# Export saved items as Markdown

## Intent

Saved items are trapped in SQLite; the user wants them in their notes tool. A one-shot export command unblocks that without building a sync integration.

## Specification

- New CLI command: `bun run export --out <dir>` (default `./export`).
- Exports every item with interaction state `saved`, one file per item, named `YYYY-MM-DD-[slug].md` from the item's published date and title.
- Each file contains YAML frontmatter (`title`, `url`, `source`, `saved_at`) followed by the stored summary and excerpt.
- Re-running overwrites existing files idempotently; nothing else in the DB changes.
- Errors on a single item are logged and skipped; the command exits non-zero only if zero items export.

## Validation

- [ ] Unit test: exporter produces expected filename and frontmatter for a fixture item.
- [ ] Unit test: item with missing published date falls back to `saved_at`.
- [ ] Manual: run against the real DB, open two exported files, confirm frontmatter parses.
- [ ] `bun test` and lint pass.

## Scope

- No import, no sync, no watch mode, no non-`saved` states.
- No changes to the schema or the deck UI.

## Context

- Interaction states: `src/db/schema.ts` (`interactions` table).
- Existing CLI entrypoint pattern: `src/cli/ingest.ts`.
- Slugify helper already exists in `src/lib/slug.ts` — reuse, don't add a dependency.
