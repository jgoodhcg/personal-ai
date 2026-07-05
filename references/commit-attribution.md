---
title: "Commit Attribution Reference"
blueprint_section: "BP-WF-COMMIT"
---

# Commit Attribution

Load this file only at commit time, when filling the trailer template from `AGENTS.md`. Core commit rules (approval, presentation, never persisting runtime values) live in `AGENT_BLUEPRINT.md` `[BP-WF-COMMIT]`.

## Co-authored-by Resolution

Derive `Co-authored-by` from the **model name**, not the tool. Use this resolution order:

1. **Tier 1 — Brand match** (case-insensitive match against model name):
   - `codex` in model name → `Codex <codex@users.noreply.github.com>`
   - `claude` in model name → `Claude <claude@users.noreply.github.com>`
   - `gemini` in model name → `Gemini <google-gemini@users.noreply.github.com>`
   - `glm` in model name → `GLM <zai-org@users.noreply.github.com>`
2. **Tier 2 — Provider fallback** (when model name has no brand match):
   - OpenAI → `OpenAI <openai@users.noreply.github.com>`
   - Anthropic → `Anthropic <anthropics@users.noreply.github.com>`
   - Google → `Google <google-gemini@users.noreply.github.com>`
   - Zhipu → `Zhipu <zai-org@users.noreply.github.com>`
   - Mistral → `Mistral <mistralai@users.noreply.github.com>`
   - Meta → `Meta <meta-llama@users.noreply.github.com>`
   - DeepSeek → `DeepSeek <deepseek-ai@users.noreply.github.com>`
3. **Tier 3 — Unknown** (provider not listed): `{Provider Name} <{github-org}@users.noreply.github.com>` — look up the provider's GitHub org. If truly unknown: `AI Agent <noreply@users.noreply.github.com>`

## Provider / Product / Model Values

- `AI_PRODUCT_LINE` must be one of `codex|claude|gemini|opencode`, determined from the current session:
  - Codex or ChatGPT coding agent → `codex`
  - Claude Code → `claude`
  - Gemini CLI → `gemini`
  - OpenCode → `opencode` (regardless of underlying provider/model, including z.ai)
- Determine `AI-Provider` and `AI-Model` from the most specific authoritative source, in order:
  1. active session/runtime metadata exposed by the tool
  2. tool-owned local config that controls the current session
  3. visible UI labels, only if no better source is available
- Do not down-convert a specific runtime model to a marketing label. Example: if Codex Desktop shows `GPT-5` in the UI but `~/.codex/config.toml` for the active session contains `model = "gpt-5.4"`, use `AI-Model: gpt-5.4`.
- Trailers when committing:
  - `Co-authored-by: [resolved name] <[resolved email]>`
  - `AI-Provider: [runtime provider name]` (optional; include only if known)
  - `AI-Product: [runtime product line]` (optional; include only if known)
  - `AI-Model: [runtime model name]` (optional; include only if known)

## Multi-Model Attribution

When more than one AI model contributed to the work being committed, attribute all participating models.

**Trigger — user-initiated:** interpret any statement that conveys "also credit model X" as a trigger — there is no required phrase (e.g. "also attribute gemini", "credit sonnet too, it helped earlier"). When triggered, ask the user to confirm which model(s) to add if not already specified by name.

**Trigger — agent-suggested:** when there is evidence of a model switch during the current session (session metadata, tool context, or the user mentioning prior work with another model), the agent **may** ask:

> "It looks like [other model] also contributed to this work. Want me to include it in the commit attribution?"

Do **not** auto-add additional attribution without user confirmation.

**Resolution rules:**
- Resolve each additional model's `Co-authored-by` using the same tiered lookup (Tier 1 → 2 → 3) above.
- Each attributed model gets its own `Co-authored-by` line; the **primary model** (the one performing the commit) is always listed first.
- `AI-Provider`, `AI-Product`, and `AI-Model` are comma-separated, primary model first; deduplicate values within each trailer.
- `AI-Product` reflects the **tool**, not the model — if both models were used within OpenCode, both entries are `opencode`.

**Example** — committing from OpenCode (claude-opus-4-6) after also using Gemini 2.5 Pro:

```text
Co-authored-by: Claude <claude@users.noreply.github.com>
Co-authored-by: Gemini <google-gemini@users.noreply.github.com>
AI-Provider: Anthropic, Google
AI-Product: opencode, opencode
AI-Model: claude-opus-4-6, gemini-2.5-pro
```
