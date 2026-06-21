# Alignment rubric and report

For aligning a repo that already follows the blueprint (`[BP-ALIGN]`). Check the rules below, then emit the report in the **exact** format at the bottom (`[BP-ALIGN-REPORT]`). Run `scripts/check.sh` first for a fast structural baseline.

## Rule check

Verify each and record PASS/FAIL with one line of evidence:

| Rule | Check |
|------|-------|
| BP-CORE-01 | `AGENTS.md` exists and references `AGENT_BLUEPRINT.md` |
| BP-CORE-02 | `roadmap/index.md` exists |
| BP-CORE-03 | Each `roadmap/[ID]-[slug].md` opens with valid YAML frontmatter (required fields present) |
| BP-CORE-05 | Policy states commits happen only after user approval |
| BP-CORE-06 | Alignment responses use this report format |
| BP-CORE-09 | `AGENTS.md` stores a trailer **template**, not concrete co-author/provider/model values |
| BP-RM-DOR | Every `ready` work unit satisfies the Definition of Ready (Intent, Specification, Validation, Scope, Context concrete; no Open Questions) |
| BP-RM-FRONTMATTER | Frontmatter includes title, status, description, created, updated, tags, priority |

Status lives in frontmatter, not prose. `done`/`dropped` units belong in `roadmap/archived/`.

## Patch discipline

Propose a **minimal** patch plan for each FAIL. Apply focused edits, then run the project's validation commands and re-run `check.sh`. Do not redesign working policy or expand scope.

## Required report format (reproduce exactly)

```markdown
# Alignment Report

## Blueprint
- Version: [e.g. 2026-06-14]

## Rule Check
| Rule ID | Status (PASS/FAIL) | Evidence | Action |
|---|---|---|---|
| BP-CORE-01 | PASS | `AGENTS.md` references blueprint | n/a |

## Patch Plan
1. [minimal change]

## Applied Changes
- `[file path]`: [what changed]

## Validation
- `[command]`: [pass/fail + brief output]

## Open Questions
- [only unresolved decisions]
```
