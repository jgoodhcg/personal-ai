---
name: applying-agent-blueprint
description: Scaffolds and aligns a project's agent operating files (AGENTS.md, roadmap/, optional CLAUDE.md/GEMINI.md, .agent-profile.md) from the Agent Blueprint standard. Use when setting up agent policy for a new or existing repo, creating or updating AGENTS.md, adopting AGENT_BLUEPRINT.md, or running an alignment/compliance check against the blueprint.
---

# Applying the Agent Blueprint

This skill executes the blueprint's adoption (`[BP-ADOPT]`) and alignment (`[BP-ALIGN]`) flows. The **rules and rationale live in `AGENT_BLUEPRINT.md`** — read it for any rule you are unsure about. This file is the operator: it decides the mode, drives the steps, and points to the templates and rubric you need at each step.

Core principle while generating files: **reference the blueprint, do not restate it** (`BP-INSTR-05`). Generated `AGENTS.md` should point to `AGENT_BLUEPRINT.md` for shared rules, not paste them in.

## Prerequisite

`AGENT_BLUEPRINT.md` must exist at the repo root, with its `references/` companion directory alongside it (commit attribution, user profile guidance, work unit example). If either is missing, copy them from the Agent Blueprint source before continuing (`[BP-ADOPT]` steps 1–2). Everything below assumes they are present.

## Decide the mode

- **No `AGENTS.md`, or it is missing required sections → Scaffold.**
- **`AGENTS.md` exists and references the blueprint → Align.**

When both could apply (partial setup), Scaffold the missing pieces, then Align.

## Scaffold workflow

Copy this checklist into your response and check items off as you go:

```
Scaffold progress:
- [ ] 1. Detect the project (stack, version file, lockfile, validation commands)
- [ ] 2. Gather gaps from the user (only what detection cannot answer)
- [ ] 3. Write AGENTS.md from the template
- [ ] 4. Create roadmap/ (index.md + _template.md)
- [ ] 5. Optional files (wrappers, profile, design system)
- [ ] 6. Validate with check.sh; fix until green
```

**1. Detect the project.** Inspect the repo to fill as much of `AGENTS.md` as possible without asking: language/runtime, version file (`.nvmrc`, `.python-version`, `rust-toolchain.toml`, …), lockfile, and the format/build/test/e2e commands. For a mature repo, run the git reconnaissance in [reference/recon.md](reference/recon.md) to ground project-specific rules in real churn/bug/ownership risk rather than convention.

**2. Gather gaps.** Ask the user only for what you could not detect — typically the commit-trailer identity policy, "Never Run" entries, data-sensitivity constraints, and interaction profile. Ask a few targeted questions; do not extrapolate uncertain requirements (mirror the roadmap `Brain Dump to Ready` discipline).

**3. Write `AGENTS.md`** from [reference/agents-template.md](reference/agents-template.md), filled from steps 1–2. Set the blueprint `version:` reference to the current `AGENT_BLUEPRINT.md` frontmatter `version`. Store a trailer **template**, never concrete runtime values (`BP-CORE-09`).

**4. Create `roadmap/`** from [reference/roadmap-templates.md](reference/roadmap-templates.md): `roadmap/index.md` (required — its existence marks a compatible project, `BP-CORE-02`) and `roadmap/_template.md`. Document the work-unit ID digit width in `AGENTS.md` if not the default of 3.

**5. Optional files** (offer; create only what the user wants):
- Thin `CLAUDE.md` / `GEMINI.md` wrappers → [reference/wrappers.md](reference/wrappers.md).
- Git-ignored `.agent-profile.md` → [reference/profile-template.md](reference/profile-template.md). Also add it to `.gitignore`.
- Visual UI project → offer the design system; point to `DESIGN_SYSTEM_GUIDE.md` (`[BP-DESIGN]`). Skip for CLIs, libraries, and backends.

**6. Validate.** Run `scripts/check.sh` from the repo root. Fix every FAIL and re-run until it passes (generate → validate → fix).

## Align workflow

For a repo that already follows the blueprint. Copy this checklist:

```
Align progress:
- [ ] 1. Run check.sh for a fast structural baseline
- [ ] 2. Compare AGENTS.md + roadmap/ against the rule list
- [ ] 3. Emit the Alignment Report (exact format)
- [ ] 4. Apply minimal patches; re-run check.sh
```

Use [reference/alignment.md](reference/alignment.md) for the rule-check list and the **required** report format — reproduce that format exactly (`[BP-ALIGN-REPORT]`). Keep patches minimal and scoped; do not redesign working policy.

## Degrees of freedom

- **High (judgment):** detecting the stack, deciding which optional files fit, wording project-specific rules. Use the repo's reality.
- **Low (exact, do not improvise):** work-unit frontmatter fields, blueprint rule IDs, the commit-trailer template shape, and the Alignment Report format. Copy these verbatim from the templates and the blueprint.

## Note: template sync

`reference/*.md` mirror the templates embedded in `AGENT_BLUEPRINT.md`, which are kept inline to preserve the blueprint's one-file portability. If you change a template in either place, mirror it in the other. `check.sh` verifies structure, not template prose, so it will not catch wording drift.
