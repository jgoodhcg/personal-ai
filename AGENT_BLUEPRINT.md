---
version: "2026-07-04"
---

# Agent Blueprint

Reference for consistent agent behavior across projects. Copy into any project and reference from `AGENTS.md`. Do not edit a project's copy; propose changes in the `agent-blueprint` repo and re-sync.

---

## Core Invariants

Use these IDs in alignment reports for deterministic, machine-checkable outcomes.

**MUST**
- `BP-CORE-01` `AGENTS.md` exists and references `AGENT_BLUEPRINT.md`.
- `BP-CORE-02` `roadmap/index.md` exists.
- `BP-CORE-03` Work in progress lives in `roadmap/` work unit files with valid frontmatter.
- `BP-CORE-04` Agents execute `ready` work units autonomously and self-validate before returning.
- `BP-CORE-05` Commits happen only after explicit user approval.
- `BP-CORE-06` Alignment responses use the required report format in this blueprint.
- `BP-CORE-09` `AGENTS.md` stores a commit trailer template (placeholders), not concrete co-author/provider/model values.
- `BP-CORE-11` On conflicting instructions, apply the precedence order in `[BP-PRECEDENCE]`.

**SHOULD**
- `BP-CORE-07` Keep policy lean; prefer references over duplicated rules. A rule that restates blueprint or `AGENTS.md` text verbatim is a FAIL in alignment reports. See `[BP-INSTR]`.
- `BP-CORE-08` Capture AI commit identity once per repo in `AGENTS.md` to avoid repeated prompts.
- `BP-CORE-10` Capture user interaction profile in `AGENTS.md` on project init or alignment.

---

## Instruction Precedence [BP-PRECEDENCE]

When instructions conflict, resolve in this order (highest wins):

1. Explicit live user direction in the current session.
2. The active roadmap work unit's scope and specification.
3. `AGENTS.md` project policy. Agent wrapper files (`CLAUDE.md`, `GEMINI.md`, etc.) rank here when they carry agent-specific instructions.
4. `AGENT_BLUEPRINT.md` defaults.
5. Persistent memory and stored user profiles — background context only; they inform tone and defaults but never override the levels above.

Safety `[BP-SAFE]` is a gate, not a rank: destructive, irreversible, or out-of-repo actions still require confirmation even when a higher-precedence source requests them.

State precedence explicitly because unresolved instruction conflicts measurably reduce instruction-following ([IFScale], arXiv:2507.11538).

---

## Safety [BP-SAFE]

Confirm before running destructive commands, installing dependencies, or taking actions outside the repo.

---

## Instruction Design [BP-INSTR]

How to author `AGENTS.md` and work units so agents actually follow them. Instruction-following accuracy declines as the number of active instructions rises ([IFScale]), and models attend most to the start and end of a file and least to the middle ([Lost in the Middle], arXiv:2307.03172). Write to those constraints:

- `BP-INSTR-01` Keep the active instruction set small. Split rules into layered files loaded on demand; a work unit must not restate blueprint or `AGENTS.md` rules. (density)
- `BP-INSTR-02` Order by importance. Put MUST invariants and precedence at the top of a file and easily-forgotten operational rules near the end; never bury load-bearing rules in the middle. (primacy/recency)
- `BP-INSTR-03` One instruction, one checkable outcome. Write each rule so compliance is verifiable; prefer concrete, testable criteria over adjectives. (reduces omission under load)
- `BP-INSTR-04` Prefer positive, specific instructions ("do X, with criterion Y"). Reserve prohibitions for named, recurring failure modes — e.g. the `Never Run` list — rather than blanket "don't." (positive + targeted-negative supervision)
- `BP-INSTR-05` Reference over restate. Link to the canonical rule instead of copying it; duplication raises density and drifts out of sync. (reinforces `BP-CORE-07`)
- `BP-INSTR-06` Write rules in the imperative with the trigger condition first: "When X, do Y." Condition-action phrasing makes the rule matchable at the moment it applies. (retrieval at point of use)
- `BP-INSTR-07` For any format agents must produce, include one filled-in example alongside the schema or template. A worked example constrains output better than field descriptions alone. (few-shot > schema)
- `BP-INSTR-08` Keep rationale out of the instruction stream. Justification aimed at humans (history, comparisons, persuasion) belongs in a README or companion doc; keep at most one line of "why" per rule. (density)

---

## Environment [BP-ENV]

Reproducible environments prevent "works on my machine" failures. Pin versions, commit lockfiles, and document setup.

### Version Pinning [BP-ENV-PIN]

If the project uses a language runtime, pin the version in a file committed to the repo. Use a format that version managers read automatically:

| Ecosystem | Version file | Manager(s) |
|-----------|-------------|------------|
| Node | `.nvmrc` or `.node-version` | nvm, fnm, volta, mise |
| Python | `.python-version` or `pyproject.toml` `[project.requires-python]` | uv, pyenv, mise |
| Rust | `rust-toolchain.toml` | rustup |
| Go | `go.mod` (`go` directive) | built-in |
| Clojure | `deps.edn` (`:deps` versions) | Clojure CLI |
| Bun | `package.json` `engines.bun` | bun |
| Multi-language | `.tool-versions` | mise, asdf |

### Lockfiles [BP-ENV-LOCK]

Commit lockfiles. They make dependency resolution deterministic across machines and CI.

Common lockfiles: `package-lock.json` / `bun.lockb` / `yarn.lock`, `uv.lock` / `poetry.lock`, `Cargo.lock`, `go.sum`, `deps-lock.json` (Deno).

If the ecosystem has a lockfile, commit it. When installing dependencies, use the lockfile-respecting command (e.g. `npm ci` not `npm install`, `uv sync` not `uv pip install`).

### Setup Command [BP-ENV-SETUP]

Document a single command (or short sequence) that bootstraps the environment from scratch. Store it in the `## Environment` section of `AGENTS.md` so agents can self-bootstrap.

---

## Workflow [BP-WF]

### Operating Model [BP-WF-OPS]

1. **Take direction** from a `roadmap/` work unit file, issue, or user request.
2. **If input is a brain dump**, create a draft work unit and clarify until scope and validation are concrete.
3. **Execute autonomously** once scope is clear; do not stop after each small step.
4. **Self-validate end-to-end** before returning: run required checks, create missing tests when needed, and run E2E for UI changes.
5. **Return to the user only when** done and validated, stuck, or blocked on an irreversible/high-impact decision.

### Validation [BP-WF-VAL]

Projects define validation commands in `AGENTS.md`:

- **Format/Lint** — run after every change
- **Build/Compile** — run after code changes
- **Unit tests** — run before declaring logic complete
- **E2E tests** — run after UI changes (start required services if approved)

Work through the validation hierarchy. Escalate only when lower levels pass.

### Guardrails [BP-WF-GUARD]

- Run validation after changes.
- Follow the execution policy defined in `AGENTS.md`.
- Keep changes minimal and focused; avoid unrelated improvements.
- For critical logic changes, review `git diff` before declaring completion.

### Commits [BP-WF-COMMIT]

- Commit only after user approval.
- Before committing, present: proposed commit message, files included, and validation results.
- Read the commit trailer template from `AGENTS.md`; if missing, ask once before the first commit in a repo.
- Never persist runtime values (`Co-authored-by`, `AI-Provider`, `AI-Product`, `AI-Model`) in `AGENTS.md`; fill them at commit time from session metadata.
- When filling trailers, resolve co-author identity, provider/model values, and multi-model attribution per `references/commit-attribution.md` (copied alongside this blueprint). When more than one model contributed, attribute all of them per that reference — never auto-add a second model without user confirmation.

### User Profile [BP-WF-PROFILE]

Calibrate agent interactions based on user context. Store in a git-ignored file (e.g., `.agent-profile.md`) referenced from `AGENTS.md`.

**Response calibration (default):** Lead with the conclusion, support after. Match response length to the task — proportionate over exhaustive. The live conversation outranks the stored profile (see `[BP-PRECEDENCE]`). Store per-user specifics (response modes, explanation depth, domains) in the profile file, not here.

**Prompting conditions** (check at project initialization and on alignment runs):
1. **No profile exists** → Prompt to create one
2. **Profile exists but incomplete** (missing fields from current blueprint guidance) → Prompt to fill gaps
3. **Profile complete** → Ask if user wants to update

Profile dimensions, interview questions, and calibration guidance live in `references/user-profile.md` (copied alongside this blueprint); load it only when creating or updating a profile.

---

## Adoption [BP-ADOPT]

1. Copy this file as `AGENT_BLUEPRINT.md`.
2. Copy the `references/` directory alongside it (commit attribution, user profile guidance, work unit example).
3. Create `AGENTS.md` using the template below.
4. Create `roadmap/index.md`.
5. Optionally create agent-specific wrappers (`CLAUDE.md`, `GEMINI.md`, etc.) using the wrapper template.

Agent-specific files (`CLAUDE.md`, `GEMINI.md`, etc.) are optional and should be thin pointers to `AGENTS.md`.

---

## Versioning [BP-VERSION]

Use date-based versions, not semantic versioning.

**Format:** `YYYY-MM-DD` with an optional `.N` suffix for same-day releases.

```
2026-03-07        ← first release of the day
2026-03-07.1      ← second release same day
2026-03-07.2      ← third, etc.
```

Date versions are honest, monotonically increasing, and require zero decision overhead. (Fuller rationale: `README.md`.)

**Rules:**
- The frontmatter `version` field in this blueprint and companion documents uses this scheme.
- `AGENTS.md` and other files that reference the blueprint version should reflect the same date string.
- When adopting this blueprint in a new project, date-based versioning is the recommended default. Teams with existing conventions may keep them, but should document the choice.
- Agents should not spend time debating version bumps. Update the date, move on.

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
- Version: [e.g. 2026-03-07]

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

````markdown
# AGENTS

Follows `AGENT_BLUEPRINT.md` (version: [BLUEPRINT_VERSION])

## Project Overview

[One paragraph: what this is, language/framework, key domains.]

## Stack

- [Language + version]
- [Framework/runtime]
- [Database]
- [Infra/deploy target]

## Environment

- Version manager: [e.g. uv, nvm, mise, rustup, or "built-in"]
- Version file: [e.g. `.python-version`, `.nvmrc`, `rust-toolchain.toml`]
- Lockfile: [e.g. `uv.lock`, `package-lock.json`, `Cargo.lock`]
- Setup: `[single bootstrap command, e.g. "uv sync", "npm ci", "cargo build"]`

## Commit Trailer Template

Store a template, not concrete runtime values. Fill it at commit time using the resolution rules in `references/commit-attribution.md`.

```text
Co-authored-by: [AI_PRODUCT_NAME] <[AI_PRODUCT_EMAIL]>
AI-Provider: [AI_PROVIDER]
AI-Product: [AI_PRODUCT_LINE]
AI-Model: [AI_MODEL]
```

## Validation Commands

| Level | Command | When |
|-------|---------|------|
| 1 | `[format/lint]` | After every change |
| 2 | `[build/compile]` | After code changes |
| 3 | `[test]` | Before completing work |
| 4 | `[e2e]` | After UI changes |

## Execution Modes

- `roadmap/` is the canonical planning surface.
- If roadmap work unit files use numeric IDs, document the digit width used by this repo in `AGENTS.md` (blueprint default: 3).
- Validation commands are defined above and applied when relevant.
- Keep changes minimal and scoped to the requested work unit.
- Require user confirmation before `git commit`, installs, upgrades, or network calls with external side effects.
- It is acceptable to stop for clarification when scope is ambiguous.

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
````

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
├── [ID]-[slug].md # Individual work unit files (with frontmatter)
└── archived/      # Completed or dropped work units
```

Non-work-unit helper files such as `index.md` and `_template.md` remain unnumbered.

### Work Unit Filenames [BP-RM-FILES]

Roadmap work unit files should use `[ID]-[slug].md`.

- `ID` is a stable numeric identifier used for reference and sorting only.
- Assign IDs sequentially and never change them once assigned.
- IDs do not encode priority, status, or anything beyond initial creation-order assignment.
- Zero-padding is required for lexical sorting.
- Default width is 3 digits.
- Repos may choose a different digit width and should document it in `AGENTS.md`.

### Numbering Alignment Guidance [BP-RM-FILES-ALIGN]

When adopting numbered work unit filenames in an existing repo:

1. Assign IDs by `created` date when present.
2. If `created` is missing, preserve the current logical or file order.
3. Rename work unit files in both `roadmap/` and `roadmap/archived/`.
4. Update internal references after renaming.
5. Do not renumber existing work units after IDs are assigned.

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

See individual `[ID]-[slug].md` files in this directory. Use `draft` while clarifying and `ready` when autonomous execution can begin.

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

### Example

A filled-in `ready` work unit lives at `references/work-unit-example.md` (copied alongside this blueprint). Match its concreteness — especially in `Specification` and `Validation` — when promoting a work unit from `draft`.

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

The `roam-thread-summary` skill (`.claude/skills/roam-thread-summary/`) is the canonical generator; it emits a paste-ready block. Its required parent attribution block is:

1. **Thread marker** — `[[ai-thread]]`
2. **Model** — `[[<model-id>]]`, the exact model of the current session
3. **Project** — `[[<project>]]`, the project's declared Roam tag or repository name

Add optional refs only when the user asks: **tool** (`[[claude-code]]`, `[[opencode]]`, `[[gemini-cli]]`, `[[codex-cli]]`) or topic pages.

### Roam Research Example

Store in `AGENTS.md`:

```markdown
## Knowledge Base

Tool: Roam Research

When asked to generate a Roam summary or thread, use the `roam-thread-summary` skill:
- Required parent block: `- [[ai-thread]] [[<model-id>]] [[<project-name>]]`
- Optional refs (only if instructed): tool (`opencode` | `claude-code` | `gemini-cli` | `codex-cli`), topic pages
- Sections: ask user what they want (chronological, functional, Q&A)
```

Output structure:

```
- [[ai-thread]] [[glm-5]] [[agent-blueprint]]
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
