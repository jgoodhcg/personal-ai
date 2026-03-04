---
version: "1.4.5"
---

# Agent Blueprint

Immutable reference for consistent agent behavior across projects. Copy into any project and reference from `AGENTS.md`.

---

## Core Invariants

Use these IDs in alignment reports for deterministic, machine-checkable outcomes.

**MUST**
- `BP-CORE-01` `AGENTS.md` exists and references `AGENT_BLUEPRINT.md`.
- `BP-CORE-02` `roadmap/index.md` exists.
- `BP-CORE-03` Work in progress lives in `roadmap/*.md` with valid frontmatter.
- `BP-CORE-04` Agents execute `ready` work units autonomously and self-validate before returning.
- `BP-CORE-05` Commits happen only after explicit user approval.
- `BP-CORE-06` Alignment responses use the required report format in this blueprint.
- `BP-CORE-09` `AGENTS.md` stores a commit trailer template (placeholders), not concrete co-author/provider/model values.

**SHOULD**
- `BP-CORE-07` Keep policy lean; prefer references over duplicated rules.
- `BP-CORE-08` Capture AI commit identity once per repo in `AGENTS.md` to avoid repeated prompts.
- `BP-CORE-10` Capture user interaction profile in `AGENTS.md` on project init or alignment.

---

## Safety [BP-SAFE]

Confirm before running destructive commands, installing dependencies, or taking actions outside the repo.

---

## Workflow [BP-WF]

### Operating Model [BP-WF-OPS]

1. **Take direction** from a `roadmap/*.md` work unit, issue, or user request.
2. **If input is a brain dump**, create a draft work unit and clarify until scope and validation are concrete.
3. **Execute autonomously** once scope is clear; do not stop after each small step.
4. **Self-validate end-to-end** before returning: run required checks, create missing tests when needed, and run E2E for UI changes.
5. **Return to the user only when** done and validated, stuck, or blocked on an irreversible/high-impact decision.

### Validation [BP-WF-VAL]

Projects define validation commands in `AGENTS.md`. Run them liberally:

- **Format/Lint** — fast, safe, run after changes
- **Build/Compile** — catches type and syntax errors
- **Unit tests** — run before declaring logic complete
- **E2E tests** — run after UI changes (start required services if approved)

Work through the validation hierarchy. Escalate only when lower levels pass.

### Guardrails [BP-WF-GUARD]

- Run validation after changes.
- If a command is not on the allowlist, ask.
- Keep changes minimal and focused; avoid unrelated improvements.
- For critical logic changes, review `git diff` before declaring completion.

### Commits [BP-WF-COMMIT]

- Commit only after user approval.
- Before committing, present: proposed commit message, files included, and validation results.
- Read the commit trailer template from `AGENTS.md`.
- If missing, ask once before first commit in a repo.
- Never hardcode runtime values (`Co-authored-by`, `AI-Provider`, `AI-Product`, `AI-Model`) in `AGENTS.md`.
- Use product-line contributor identities for `Co-authored-by`:
  - `codex`: `Codex <codex@users.noreply.github.com>`
  - `claude`: `Claude <claude@users.noreply.github.com>`
  - `gemini`: `Gemini <google-gemini@users.noreply.github.com>`
  - `opencode`: `GLM <zai-org@users.noreply.github.com>`
- Derive `AI-Provider` and `AI-Model` from runtime context at commit time.
- Include trailers when committing:
  - `Co-authored-by: [runtime product identity] <[runtime product email]>`
  - `AI-Provider: [runtime provider name]` (optional; include only if known)
  - `AI-Product: [runtime product line]` (optional; include only if known)
  - `AI-Model: [runtime model name]` (optional; include only if known)

### User Profile [BP-WF-PROFILE]

Calibrate agent interactions based on user context. Store in a git-ignored file (e.g., `.agent-profile.md`) referenced from `AGENTS.md`.

**Prompting conditions:**
1. **No profile exists** → Prompt to create one
2. **Profile exists but incomplete** (missing fields from current blueprint guidance) → Prompt to fill gaps
3. **Profile complete** → Ask if user wants to update

**Profile dimensions:**
- Experience level (beginner/intermediate/advanced per domain)
- Familiar languages/frameworks
- Explanation preference (brief/standard/thorough; explain unknowns/ask first)
- Communication style (code-focused/narrative/casual/formal; high-level vs drill-down)
- Team context (solo/collaborative; target audience if relevant)

**Sample questions:**
- "What's your experience level with [project's primary domain]?"
- "Which languages/frameworks are you comfortable with?"
- "Do you prefer brief confirmations or detailed explanations?"
- "Should I explain things you may not know, or ask first?"
- "Any communication preferences (formal/casual, code vs prose, high-level first)?"
- "Is this solo work or a team project?"

**Calibration:**
- Explain more for beginners; assume familiarity for experts
- Match explanation depth to stated preference
- Adapt communication style to user's preference
- Consider team context for commit/message conventions

**When to check:**
- Project initialization
- Alignment/compliance requests when blueprint is re-applied

---

## Adoption [BP-ADOPT]

1. Copy this file as `AGENT_BLUEPRINT.md`.
2. Create `AGENTS.md` using the template below.
3. Create `roadmap/index.md`.
4. Optionally create agent-specific wrappers (`CLAUDE.md`, `GEMINI.md`, etc.) using the wrapper template.

Agent-specific files (`CLAUDE.md`, `GEMINI.md`, etc.) are optional and should be thin pointers to `AGENTS.md`.

---

## Alignment Contract [BP-ALIGN]

- `AGENTS.md` is the project policy entrypoint and references this blueprint.
- `roadmap/` is the canonical place for scoped work units and execution prompts.
- A `ready` work unit is executable without additional clarification.
- Keep policy lean: prefer references over duplicated instructions.

### Align Project With This Blueprint

When asked to align a project:
1. Compare `AGENTS.md` and `roadmap/` against this blueprint.
2. Report gaps and propose a minimal patch plan.
3. Apply focused edits and run project validation commands.
4. Return with completed changes plus any remaining questions.

### Required Alignment Report Format [BP-ALIGN-REPORT]

Use this format exactly:

```markdown
# Alignment Report

## Blueprint
- Version: [e.g. 1.3.0]

## Rule Check
| Rule ID | Status (PASS/FAIL) | Evidence | Action |
|---|---|---|---|
| BP-CORE-01 | PASS | `AGENTS.md` references blueprint | n/a |

## Patch Plan
1. [minimal change]
2. [minimal change]

## Applied Changes
- `[file path]`: [what changed]

## Validation
- `[command]`: [pass/fail + brief output]

## Open Questions
- [only unresolved decisions]
```

---

## AGENTS.md Template [BP-AGENTS-TPL]

```markdown
# AGENTS

Follows `AGENT_BLUEPRINT.md` (version: [BLUEPRINT_VERSION])

## Project Overview

[One paragraph: what this is, language/framework, key domains.]

## Stack

- [Language + version]
- [Framework/runtime]
- [Database]
- [Infra/deploy target]

## Commit Trailer Template

Store a template, not concrete runtime values.

```text
Co-authored-by: [AI_PRODUCT_NAME] <[AI_PRODUCT_EMAIL]>
AI-Provider: [AI_PROVIDER]
AI-Product: [AI_PRODUCT_LINE]
AI-Model: [AI_MODEL]
```

Template rules:
- `AI_PRODUCT_LINE` must be one of: `codex|claude|gemini|opencode`.
- Determine `AI_PRODUCT_LINE` from current session:
  - Codex or ChatGPT coding agent -> `codex`
  - Claude -> `claude`
  - Gemini -> `gemini`
  - OpenCode -> `opencode` (regardless underlying provider/model, including z.ai)
- Determine `AI_PROVIDER` and `AI_MODEL` from runtime model metadata.
- `AI_PRODUCT_NAME` and `AI_PRODUCT_EMAIL` format:
  - `codex` -> `Codex <codex@users.noreply.github.com>`
  - `claude` -> `Claude <claude@users.noreply.github.com>`
  - `gemini` -> `Gemini <google-gemini@users.noreply.github.com>`
  - `opencode` -> `GLM <zai-org@users.noreply.github.com>`
- Fill this template at commit time; do not persist filled values in `AGENTS.md`.

## Validation Commands

| Level | Command | When |
|-------|---------|------|
| 1 | `[format/lint]` | After every change |
| 2 | `[build/compile]` | After code changes |
| 3 | `[test]` | Before completing work |
| 4 | `[e2e]` | After UI changes |

## Allowed Commands

- `[command]` — [what it does]

## Require Confirmation

- `[command]` — [why]

## Never Run

- `[command]` — [why]

## Project-Specific Rules

- [constraints, data sensitivity, architectural boundaries]

## Decision Artifacts

- For high-impact or irreversible decisions, record a decision matrix in `.decisions/[name].json`.
- Use `matrix-reloaded` format for structured comparison.
- Do not run `matrix-reloaded` CLI commands from agent sessions; use project-provided matrix instructions/schema.
- Optional: add `.decisions/[name].md` for human-readable narrative context.
- Treat the JSON decision matrix as the authoritative record.

## References

- For [topic], see `[doc path]`
- For decision records and optional matrix format, see `AGENT_BLUEPRINT.md` section `Decision Artifacts [BP-DECISIONS]`.

## Key Files

- `[path]` — [purpose]

## User Profile (optional)

See `.agent-profile.md` (git-ignored) for interaction preferences. Create on project init or alignment.
```

---

## Agent-Specific Wrapper Template [BP-AGENT-WRAPPER]

Optional. Create thin pointers for agent-specific entrypoints (`CLAUDE.md`, `GEMINI.md`, etc.):

```markdown
# [Agent Name]

See `AGENTS.md` for project policies and operating rules.

## Agent-Specific Instructions

- [Instruction specific to this agent, if any]
- [e.g., tool preferences, model-specific behavior, constraints]
```

Keep minimal. Defer to `AGENTS.md` for all shared policy.

---

## Roadmap [BP-RM]

This is the core execution model. Work units are prompts for autonomous agent work.

### Structure

```
roadmap/
├── index.md       # Project overview and directory of work units
├── _template.md   # Starting point for new work units
├── *.md           # Individual work unit files (with frontmatter)
└── archived/      # Completed or dropped work units
```

### Work Unit Frontmatter [BP-RM-FRONTMATTER]

Every work unit file **must** begin with YAML frontmatter for machine parsing:

```yaml
---
title: "Feature Name"
status: draft | ready | active | done | dropped
description: "One-line summary of what this work unit accomplishes"
created: 2024-01-15
updated: 2024-01-20
tags: []
priority: medium                      # high | medium | low
---
```

**Required fields:**
- `title` — Display name for the work unit
- `status` — Current state (see Status Definitions below)
- `description` — One-line summary
- `created` — Date work unit was created (YYYY-MM-DD)
- `updated` — Date of last modification (YYYY-MM-DD)
- `tags` — Array for categorization and filtering
- `priority` — high | medium | low (default: medium)

### Status Definitions

| Status | Meaning | Kanban Column |
|--------|---------|---------------|
| `draft` | Brain dump captured; has open questions | Backlog |
| `ready` | Clarified and executable as-is | Backlog |
| `active` | Currently being worked on | In Progress |
| `done` | Shipped and working | Done |
| `dropped` | Decided not to pursue | (hidden) |

### Legacy Status Migration [BP-RM-MIGRATION]

When aligning older projects:

| Legacy Status | New Status | Migration Rule |
|---|---|---|
| `idea` | `draft` | Keep open questions in `Open Questions`. |
| `planned` | `ready` | Ensure Definition of Ready checklist passes. |
| `paused` | `active` | Keep status `active` and add blocked context in `Context`. |
| `done` | `done` | No change. |
| `dropped` | `dropped` | No change. |

### Definition of Ready [BP-RM-DOR]

A work unit can be marked `ready` only if all are true:
- `Intent` states what and why.
- `Specification` is concrete and testable.
- `Validation` includes concrete checks (tests/e2e/visual as relevant).
- `Scope` explicitly defines boundaries.
- `Context` points to key files/constraints.
- `Open Questions` is empty or removed.

If any item is missing, status must remain `draft`.

### index.md Template

```markdown
---
title: "Project Name Roadmap"
goal: "One sentence: what this project exists to achieve."
---

# Roadmap

## Current Focus

[What is actively being worked on right now.]

## Work Units

See individual `*.md` files in this directory. Use `draft` while clarifying and `ready` when autonomous execution can begin.

## Quick Ideas

Ideas not yet promoted to work units:

- [Idea that doesn't need a file yet]
- [Another idea]
```

### _template.md

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

### Brain Dump to Ready Workflow

When creating a new work unit from a brain dump:
1. Create the file with status `draft`.
2. Ask clarifying questions until scope and validation are concrete.
3. Do not extrapolate uncertain requirements; ask instead.
4. Once questions are resolved, update status to `ready`.
5. A `ready` work unit should be a complete prompt an agent can execute without further clarification.

### Rules

- `roadmap/index.md` existence identifies a compatible project.
- Every work unit file must have valid YAML frontmatter.
- Status lives in frontmatter, not in prose.
- Keep work units concrete enough to execute and validate.
- When a work unit reaches `done` or `dropped`, move the file to `archived/`.
- Update the `updated` field whenever you modify a work unit.

---

## Decision Artifacts [BP-DECISIONS]

Optional. Use for high-impact or irreversible decisions, or when revisiting the same decision.

### Structure

Every decision has a JSON matrix file. Optionally add a markdown companion for narrative context.

```
.decisions/
├── database-choice.json     # Required: authoritative matrix-reloaded decision record
├── database-choice.md       # Optional: human-readable summary
└── auth-strategy.json
```

### JSON Matrix (required)

For each decision, add a `.json` file using `matrix-reloaded` format. Do not execute `matrix-reloaded` CLI commands from agent sessions; use project-provided instructions/schema for the expected JSON structure. The JSON matrix is the authoritative decision record.

### Markdown Format (optional)

```markdown
# Decision: [Title]

**Status:** proposed | accepted | superseded | rejected
**Date:** YYYY-MM-DD

## Context

[Why this decision is needed.]

## Options

### Option A
- Pros: [...]
- Cons: [...]

### Option B
- Pros: [...]
- Cons: [...]

## Decision

[What was chosen and why.]

## Consequences

[What changes. What to watch for.]
```

---

## Knowledge Base Integration [BP-KB]

Optional. For projects where AI-generated summaries should be captured in external knowledge tools (Roam Research, Obsidian, Notion, etc.).

### Enable in AGENTS.md

Add a `## Knowledge Base` section to `AGENTS.md` with tool-specific conventions. When present, agents generate structured output ready to paste into the user's knowledge base.

### Thread Summary Format

All AI-generated content must be nested under a parent attribution block:

1. **Tool** — e.g., `[[opencode]]`, `[[claude-code]]`, `[[gemini-cli]]`, `[[codex-cli]]`
2. **Model** — the exact model that generated the content
3. **Thread marker** — `[[ai-thread]]`
4. **Project tag** — e.g., `[[project-name]]`

### Roam Research Example

Store in `AGENTS.md`:

```markdown
## Knowledge Base

Tool: Roam Research

When asked to generate a Roam summary or thread:
- Parent block: `- [[<tool>]] [[<model-id>]] [[ai-thread]] [[<project-name>]]`
- Tool names: `opencode` | `claude-code` | `gemini-cli` | `codex-cli`
- Page refs: only include `[[Page Name]]` if explicitly instructed
- Sections: ask user what they want (chronological, functional, Q&A)
```

Output structure:

```
- [[opencode]] [[glm-5]] [[ai-thread]] [[agent-blueprint]]
    - Summary
        - Investigated stale cache issue in `src/cache.ts:142`
    - Files Changed
        - `src/cache.ts` - added TTL validation
    - Next Steps
        - Consider integration tests for cache invalidation
```

### Other Tools

Adapt the format for tool conventions:
- **Obsidian**: Use `#tags` and `[[wikilinks]]` with YAML frontmatter if desired
- **Notion**: Use nested bullet structure with database-compatible formatting
- **Logseq**: Similar to Roam with `[[bracket]]` syntax

---

## Design System [BP-DESIGN]

For projects with visual UI, use `DESIGN_SYSTEM_GUIDE.md` to establish consistent interface patterns.
The guide should use concrete, testable values (tokens/patterns), not only subjective descriptions.

If this project requires visual design and no design system exists:
1. Ask the user if they want to establish a design system.
2. If yes, copy `DESIGN_SYSTEM_GUIDE.md` into the project.
3. Follow its workflow to capture decisions in `.interface-design/system.md`.

Skip for CLI tools, libraries, backends, or other non-visual projects.
