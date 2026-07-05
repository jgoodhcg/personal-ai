---
name: roam-thread-summary
description: Generate a Roam Research "ai thread" block summary of the current session, ready to paste into daily notes. Use when the user asks for a Roam summary, an "ai thread", or to capture the current session in Roam.
---

# Roam Research Thread Summaries

When asked to generate a Roam summary or "ai thread", output a block structure ready to paste into daily notes.

## Required Structure

Nest all AI-generated content under a parent attribution block that includes, in order:

1. `[[ai-thread]]` — marks this as AI-generated content
2. `[[<model-id>]]` — the exact model ID of the current session; take it from the running session, never from an example or an earlier summary
3. `[[<project>]]` — the project this session belongs to. Use the project's declared Roam tag if `AGENTS.md` specifies one; otherwise use the repository/directory name. If it genuinely cannot be determined, ask the user before generating.

```
- [[ai-thread]] [[<model-id>]] [[<project>]]
    - <content nested here>
```

## Formatting Conventions

- **Ticket / issue references**: use page refs — `[[5593]]` or `#5593`
- **Other page refs** (tool, topic): only include `[[Page Name]]` refs if explicitly instructed

## Section Structure

The organization under the thread block is flexible. Before generating, ask the user what sections they want. Common patterns:

- Chronological phases (e.g., "Initial investigation", "Root cause", "Solution")
- Functional sections (e.g., "Summary", "Files Changed", "Key Decisions", "Next Steps")
- Q&A style (topic headers with responses nested under each)

## Example Output

(`[[<model-id>]]` and `[[<project>]]` are shown literally here; substitute the current session's model ID and project.)

```
- [[ai-thread]] [[<model-id>]] [[<project>]]
    - Summary
        - Investigated [[5593]] — stale cache entries in `src/services/cache.ts:142`
    - Files Changed
        - `src/services/cache.ts` — added TTL validation
        - `src/utils/storage.ts` — fixed race condition in write path
    - Next Steps
        - Consider integration tests for cache invalidation
```

## Output Format

Output **only** the Roam block — no preamble or trailing commentary (no "Here's the block…" lead-in, no closing remarks). Begin the reply at the `- [[ai-thread]]` line. Plain text, not in a code block, so `/copy` yields a clean, directly-pasteable block.
