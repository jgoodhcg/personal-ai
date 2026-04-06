# Codex Prompt: Build Open WebUI Upload Docs From Existing Summaries

Use this prompt in Codex Desktop when you want it to synthesize upload-ready knowledge documents from the archive extraction outputs that already exist in this repo.

## Prompt

```md
You are working inside `/Users/justingood/projects/personal-ai`.

Your task is to build the **assistant-context / RAG-safe knowledge documents** envisioned in the archive-processing roadmap, using the extraction summaries that already exist in the repo as the primary source material.

Do not propose a plan only. Do the work: inspect the relevant files, synthesize the documents, write them to disk, and then summarize what you produced.

## Goal

Create these upload-ready Markdown documents under:

- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/personal_profile.md`
- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/interest_map.md`
- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/goals_and_projects.md`
- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/working_with_me.md`
- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/decision_patterns.md`
- `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/media_and_influences.md`

These are intended for later upload into Open WebUI as knowledge/RAG documents, so they must be concise, factual, and safe to retrieve into future agent conversations.

## Output Requirements

For each document:

- write clean Markdown for direct upload
- optimize for retrieval quality, not literary prose
- prefer short sections and dense factual bullets
- include a short `Confidence notes` section at the end
- include a short `Source notes` section with representative chat file references
- do not include internal process commentary, eval metrics, or pipeline chatter

## Primary Inputs

Use these as the main source set:

- roadmap target shape: `/Users/justingood/projects/personal-ai/roadmap/chat-archive-processing.md`
- extraction run anchor: `/Users/justingood/projects/personal-ai/retrospect/data/extractions/_runs/20260328T050245Z__openai-gpt-5.4-nano/manifest.json`
- pass 1 summaries: `/Users/justingood/projects/personal-ai/retrospect/data/extractions/pass1_summary/openai-gpt-5.4-nano/`
- pass 2 projects: `/Users/justingood/projects/personal-ai/retrospect/data/extractions/pass2_projects/openai-gpt-5.4-nano/`
- pass 3 people: `/Users/justingood/projects/personal-ai/retrospect/data/extractions/pass3_people/openai-gpt-5.4-nano/`

Use these quality guardrails:

- rubric: `/Users/justingood/projects/personal-ai/retrospect/QUALITY_EVAL_RUBRIC.md`
- quality eval summary: `/Users/justingood/projects/personal-ai/retrospect/data/evaluations/20260328T191527Z__quality-eval/analysis_report.md`
- detailed judgments when needed: `/Users/justingood/projects/personal-ai/retrospect/data/evaluations/quality_judgments/openai-gpt-5.4/`

Use raw chats as a secondary verification source when needed:

- `/Users/justingood/projects/personal-ai/retrospect/data/chats/`

## Trust Policy

The existing extraction outputs are useful but imperfect. Treat them as **candidate evidence**, not ground truth.

Follow these rules:

1. Use `pass1_summary` and `pass2_projects` as the primary synthesis substrate.
2. Treat `pass3_people` as low-trust. Only use it for:
   - clearly named real people
   - plainly explicit recurring relationship facts
   - directly stated preferences or interaction patterns that are also supported elsewhere
3. Do not rely on `pass3_people` for inferred motivations, values, identity claims, or psychology unless you verify against raw chats and see repeated support across time.
4. For any high-impact claim, verify against raw chats before including it. High-impact means:
   - stable identity claims
   - long-term goals
   - working style instructions
   - sensitive personal facts
   - relationship claims
5. Omit weak, one-off, or speculative claims instead of forcing completeness.
6. Never include secrets, tokens, API keys, private credentials, or quoted sensitive values.

## Synthesis Rules

Build the documents for **high-trust assistant use**, not deep psychological analysis.

Include:

- stable preferences that recur across chats
- active or recurring projects
- durable goals and constraints
- recurring technical domains and interests
- practical guidance for how to work well with the user
- decision habits only when supported across multiple chats or clearly repeated patterns
- media and influences only when they recur or are explicitly important

Avoid or exclude:

- speculative psychologizing
- unsupported motivations
- one-off hobby guesses
- assistant-suggested facts presented as user facts
- overfitted significance labels
- health, sexual, financial, or highly sensitive details unless they are clearly central, repeated, and appropriate for assistant context

## Preferred Document Shape

Use this approximate style:

### `personal_profile.md`
- who the user appears to be in practical terms
- stable preferences and recurring constraints
- recurring work domains
- things that seem durable enough to remember

### `interest_map.md`
- major domains of interest
- subtopics
- rough intensity / recurrence wording such as `high`, `medium`, `emerging`
- notable cross-links between interests

### `goals_and_projects.md`
- active projects
- recurring goals
- paused / abandoned projects only if clearly recurrent or important
- open loops worth remembering

### `working_with_me.md`
- how to help effectively
- preferred interaction style
- default assumptions to avoid
- when to be concise vs detailed
- what kinds of outputs are most useful

### `decision_patterns.md`
- recurring ways the user evaluates tradeoffs
- common optimization targets
- recurring blockers or anti-patterns
- only include patterns with repeated evidence

### `media_and_influences.md`
- recurring books, games, thinkers, software, creators, artistic references, and conceptual influences
- organize by domain
- note recurrence or significance only when supported

## Citation Style

Inside each doc, include a short `Source notes` section with representative file references such as:

- `/Users/justingood/projects/personal-ai/retrospect/data/chats/<chat-file>.md`

Do not over-cite every bullet inline. Keep the docs readable. Use source-note sections to show provenance.

## Implementation Instructions

1. Read the roadmap section that defines the assistant-context documents.
2. Read the quality analysis report and internalize the failure modes.
3. Inspect the extraction directories for `openai-gpt-5.4-nano`.
4. Aggregate recurring signals across the extraction JSONs.
5. Verify high-impact or uncertain claims against raw chat files.
6. Create `/Users/justingood/projects/personal-ai/retrospect/data/knowledge_base/assistant_context/` if it does not exist.
7. Write the six Markdown documents.
8. Keep them compact enough to be practical as Open WebUI uploads.
9. After writing, give a short summary of what was created, what was intentionally excluded, and any obvious follow-up gaps.

## Important Guardrail

If the evidence is thin, prefer a sparse and boring document over an impressive but speculative one.
```

## Suggested Use

Paste the prompt above into Codex Desktop as-is.

If you want a stricter variant, add this sentence at the end:

`Do not include any claim unless it is supported by at least two separate chats or by one unusually explicit chat that clearly states a durable preference, goal, or constraint.`
