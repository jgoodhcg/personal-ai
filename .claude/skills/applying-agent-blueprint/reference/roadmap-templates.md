# Roadmap templates

Create both files. `roadmap/index.md` is required — its existence marks a blueprint-compatible project (`BP-CORE-02`). Work-unit files are `[ID]-[slug].md` with zero-padded IDs (default 3 digits); `index.md` and `_template.md` stay unnumbered.

## roadmap/index.md

```markdown
---
title: "[Project Name] Roadmap"
goal: "One sentence: what this project exists to achieve."
---

# Roadmap

## Current Focus

[What is actively being worked on right now.]

## Work Units

See individual `[ID]-[slug].md` files in this directory. Use `draft` while clarifying and `ready` when autonomous execution can begin.

## Quick Ideas

Ideas not yet promoted to work units:

- [Idea that doesn't need a file yet]
```

## roadmap/_template.md

```markdown
---
title: "Work Unit Title"
status: draft | ready | active | done | dropped
description: "One line"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
priority: high | medium | low
---

# Work Unit Title

## Intent

[What this accomplishes and why it matters.]

## Specification

[Concrete description of the change. What exists after this is done.]

## Validation

[How to know it's done:]
- [ ] Tests to create/pass
- [ ] E2E flows to run
- [ ] Visual criteria (reference style guide if applicable)

## Scope

[What's not included. Boundaries to prevent drift.]

## Context

[Pointers to relevant files, prior decisions, or constraints.]

## Open Questions (draft only)

[Unresolved items. Clear this section before moving to ready.]
```

## Definition of Ready

A unit may be `ready` only when Intent, Specification, Validation, Scope, and Context are concrete and Open Questions is empty (`[BP-RM-DOR]`). Otherwise keep it `draft`.
