# AGENTS.md template

Fill the bracketed placeholders from project detection and the user interview. Delete sections that do not apply. Keep it lean — link to `AGENT_BLUEPRINT.md` for shared rules instead of pasting them (`BP-CORE-07`, `BP-INSTR-05`).

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

## Environment

- Version manager: [uv | nvm | mise | rustup | built-in]
- Version file: [.python-version | .nvmrc | rust-toolchain.toml | …]
- Lockfile: [uv.lock | package-lock.json | Cargo.lock | …]
- Setup: `[single bootstrap command]`

## Commit Trailer Template

Store a template, not concrete runtime values (`BP-CORE-09`).

​```text
Co-authored-by: [AI_PRODUCT_NAME] <[AI_PRODUCT_EMAIL]>
AI-Provider: [AI_PROVIDER]
AI-Product: [AI_PRODUCT_LINE]
AI-Model: [AI_MODEL]
​```

- `AI_PRODUCT_LINE` ∈ `codex | claude | gemini | opencode`, derived from the current tool.
- `AI_PROVIDER` / `AI_MODEL`: runtime-derived at commit time (prefer session metadata > tool config > UI label).
- `AI_PRODUCT_NAME` / `AI_PRODUCT_EMAIL`: resolved from the model name via the tiered lookup in `references/commit-attribution.md`.
- Fill at commit time; never persist filled values here. Multi-model commits: see `references/commit-attribution.md`.

## Validation Commands

| Level | Command | When |
|-------|---------|------|
| 1 | `[format/lint]` | After every change |
| 2 | `[build/compile]` | After code changes |
| 3 | `[test]` | Before completing work |
| 4 | `[e2e]` | After UI changes |

## Execution Modes

See `AGENT_BLUEPRINT.md` `Execution Modes` for the full policy.

- `roadmap/` is the canonical planning surface; the referenced work unit is the source of scope.
- Work-unit IDs use [3]-digit zero-padded prefixes: `[ID]-[slug].md`.
- Apply the validation commands above when their triggers fire.
- Keep changes minimal and scoped to the requested work unit.
- Require user confirmation before `git commit`, dependency install/upgrade, and network side effects.
- Stopping for clarification when scope is ambiguous is acceptable.

## Never Run

- `[command]` — [why]

## Project-Specific Rules

- [constraints, data sensitivity, architectural boundaries — ground these in detection + recon]

## References

- For operating rules, see `AGENT_BLUEPRINT.md`.
- For work units and execution prompts, see `roadmap/`.
- For decision records, see `AGENT_BLUEPRINT.md` `[BP-DECISIONS]`.

## Key Files

- `[path]` — [purpose]

## User Profile (optional)

See `.agent-profile.md` (git-ignored) for interaction preferences.
```

Note: in the real file, the trailer fence is a normal ```` ``` ```` block; the zero-width characters above only prevent nesting issues inside this template-of-a-template.
