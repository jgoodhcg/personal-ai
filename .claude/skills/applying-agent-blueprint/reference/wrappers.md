# Agent-specific wrapper templates

Optional. Thin pointers for agent-specific entrypoints (`CLAUDE.md`, `GEMINI.md`, etc.). Keep them minimal — all shared policy lives in `AGENTS.md` (`[BP-AGENT-WRAPPER]`). Create one per agent the project actually uses.

## CLAUDE.md / GEMINI.md

```markdown
# [Agent Name]

See `AGENTS.md` for project policies and operating rules.

## Agent-Specific Instructions

- [Only instructions unique to this agent — tool preferences, model-specific behavior, constraints.]
```

If an agent has nothing unique to add, the file is just the first two lines pointing at `AGENTS.md`. Do not duplicate rules from `AGENTS.md` or `AGENT_BLUEPRINT.md` here (`BP-INSTR-05`).
