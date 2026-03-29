---
title: "Chat Archive Processing"
status: active
description: "Process exported chat histories into structured extractions for self-discovery, psychological analysis, narrative potential, and RAG knowledge base"
created: 2026-03-06
updated: 2026-03-28
subproject: retrospect
tags: [knowledge-base, rag, chat-exports, self-discovery, psychology, narrative, creative]
priority: high
---

# Chat Archive Processing

## Intent

Turn years of ChatGPT, Claude, and z.ai/GLM chat exports into structured data for:

1. **Self-discovery and analysis** — surface patterns in interests, goals, behaviors, and psychology
2. **Psychological insight** — extract evidence-bearing signals that could support serious psychological interpretation
3. **Narrative and creative potential** — identify recurring tensions, fascinations, and thematic threads that could fuel storytelling
4. **Memory utility** — searchable records of media, influences, people, projects, and ideas
5. **RAG context** — feed Open WebUI's knowledge base so models have context about the user

## Data

- **Source**: 3,231 normalized conversations (2023-2026)
- **Platforms**: ChatGPT, Claude, z.ai/GLM
- **Status**: Normalization complete, chats in `retrospect/data/chats/`
- **Current extraction status**: Passes 1-3 are now complete for all `3,231` chats after the initial 2026-03-21 rollout, a large rerun on 2026-03-28, and a final 5-chat cleanup pass
- **Pipeline home**: `retrospect/` (isolated monorepo-style directory)

## Extraction Architecture

### Principle: Evidence Over Inference

To produce trustworthy psychological analysis, we separate:

- **Observed evidence** — what the user actually said or asked
- **Interpretation** — what the model thinks that may imply
- **Framework mapping** — how evidence maps onto personality frameworks

We also track the **epistemic tier** of an extraction so downstream synthesis can keep:

- **Factual memory** separate from
- **Behavioral pattern** observations, separate from
- **Interpretive hypothesis** layers, separate from
- **Speculative/playful** material

These tiers should never be collapsed in final synthesis or RAG deployment.

Every extracted item includes:
- `epistemic_tier` — factual_memory / behavioral_pattern / interpretive_hypothesis / speculative_play
- `signal` — the extracted item
- `interpretation` — what it might mean
- `evidence` — direct quotes or references
- `confidence` — how certain (low/medium/high)
- `salience` — how central to the conversation (peripheral/central/primary)
- `disconfirming_evidence` — evidence that weakens or limits the claim
- `alternative_explanations` — plausible competing interpretations
- `source_conversation_id` — traceability back to the originating chat

### Four-Pass Extraction Strategy

Each conversation is processed through **four focused extraction passes** via OpenRouter API. Multiple focused passes produce higher-quality results than a single mega-prompt.

**Pass 1: Summary + Factual Content**
- `summary` — what happened in this conversation
- `significance` — why this chat matters (if anything)
- `topics_and_interests` — subjects discussed with centrality
- `media_and_influences` — books, films, games, music, podcasts, creators, thinkers
- `technical_stack_and_skills` — languages, frameworks, tools, proficiency signals

**Pass 2: Projects, Ideas, Goals, Decisions**
- `projects_and_endeavors` — named projects with status (ideating, active, stalled, shipped, abandoned)
- `ideas_and_concepts` — one-off ideas, story fragments, game mechanics, business concepts, worldbuilding
- `goals_and_aspirations` — explicit and implicit goals, timeframe signals
- `decisions_and_crossroads` — what's being weighed, criteria, resolution status
- `open_questions` — unresolved questions or problems surfacing

**Pass 3: People, Values, Frictions**
- `people_and_relationships` — named people, relationship roles, recurring figures, influences, antagonists, collaborators
- `values_and_motivations` — principles that surface (autonomy, aesthetics, efficiency, social impact, etc.)
- `frustrations_and_blocks` — friction points, external vs. internal

**Pass 4: Psychological and Behavioral Signals**
- `emotional_tone_and_energy` — dominant affect (curious, frustrated, excited, anxious, stuck, playful)
- `cognitive_style` — how problems are approached (systematic, exploratory, analytical, intuitive, indecisive)
- `communication_style` — how requests are framed (directive, collaborative, exploratory, self-deprecating)
- `behavioral_patterns` — observable patterns in how the user engages
- `self_concept_signals` — how the user describes or positions themselves
- `defense_or_avoidance_patterns` — topics dodged, deflections, rationalizations
- `motivation_and_reward_patterns` — what seems to drive engagement
- `framework_relevant_signals` — evidence that may later map to Big Five, MBTI, Enneagram, attachment style, or other recognized frameworks

### Output Format

**JSON** with local schema validation. Provider-enforced strict schemas should be used opportunistically where they improve compliance, but the pipeline should prefer portability and successful extraction over brittle provider-specific strictness. No human reads intermediates, so optimize for:
- Programmatic aggregation
- Structured outputs with tolerant coercion / repair where needed
- Easy validation

### Derived Analysis (Cross-Conversation)

After all extractions complete, a **separate inference pass** aggregates evidence across conversations to produce:

**Personality Framework Mapping**
- `big_five` — Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism with evidence
- `mbti` — Myers-Briggs type indicators with evidence
- `enneagram` — type and wing guesses with evidence
- `attachment_style` — secure, anxious, avoidant, disorganized signals with evidence
- `astrology_guesses` — playful layer, sun/moon/rising guesses based on personality patterns
- Additional recognized frameworks can be added if evidence supports them

**Pattern Analysis**
- Recurring mood and stress patterns
- Avoidance and approach themes
- Life-domain imbalances
- Narrative identity themes
- Relationship themes
- Temporal patterns (seasonal, weekly, life-phase)
- Recurrence counts, spread across time, and cross-context consistency for any elevated claim

No trait-level or framework-level claim should be synthesized unless it shows up with meaningful support across multiple conversations and time slices. The aggregation phase should favor frequency, temporal spread, and contextual diversity over vivid single-chat anecdotes.

**Narrative and Creative Potential**
- `recurring_tensions` — unresolved conflicts, contradictions, or frictions that surface repeatedly (internal vs. external, self vs. world, desire vs. duty)
- `fascinations` — subjects, questions, or images the user returns to with unusual intensity or frequency
- `thematic_threads` — ideas that recur across contexts, not yet explored as stories but carrying narrative weight
- `personal_mythology_elements` — origin stories, transformation moments, recurring metaphors, self-narrative motifs
- `unresolved_arcs` — goals abandoned, questions unanswered, journeys interrupted — material with narrative tension
- `story_fodder` — extracted signals that, if pulled and explored, could generate compelling fiction or creative work

## Pipeline

1. **Normalize** — DONE. Python script converted all exports to uniform markdown in `retrospect/data/chats/`.

2. **Schema** — DONE. JSON Schema (draft 2020-12) definitions for all four extraction passes in `retrospect/schemas/`. Validation script in `retrospect/scripts/validate_extraction.py`.

3. **Prompts** — DONE. Jinja2 prompt templates for all four passes in `retrospect/prompts/`. Each has system and user blocks with field-level instructions aligned to schemas.

4. **Extract** — Structured extraction via OpenRouter. Near-term operating plan is to run Passes 1-3 cheaply across the entire archive first, then handle higher-level psych synthesis after aggregation and compression. Outputs to `retrospect/data/extractions/` as JSON.

5. **Aggregate** — Combine extractions into frequency-counted lists and pattern summaries in `retrospect/data/aggregated/`.

6. **Infer** — Cross-conversation derived analysis for personality frameworks and psychological patterns.
   - This layer may absorb much of the current Pass 4 burden if raw-chat psych extraction remains brittle or low value at archive scale.

7. **Synthesize** — Generate two classes of documents:
   - **Assistant-context / RAG-safe docs** in `retrospect/data/knowledge_base/assistant_context/`:
     - `personal_profile.md` — biographical facts, stable preferences, working style
     - `interest_map.md` — domains, intensity, connections, evolution
     - `goals_and_projects.md` — active/recurring/completed goals, project index
     - `working_with_me.md` — instructions for AI assistants
     - `decision_patterns.md` — practical decision habits grounded in repeated evidence
     - `media_and_influences.md` — cultural references and tastes
   - **Current status:** the first-pass assistant-context set above now exists on disk and has been manually reviewed for obvious overreach and sensitivity before upload planning.
   - **Interpretive analysis docs** in `retrospect/data/knowledge_base/analysis/`:
     - `ideas_gallery.md` — full catalog with patterns
    - `psychological_profile.md` — evidence-based personality analysis with explicit confidence and disconfirming evidence
     - `relationship_map.md` — people and social patterns
    - `narrative_potential.md` — recurring tensions, fascinations, and thematic threads with storytelling potential
   - Add a layered plain-text synthesis path:
     - summarize structured outputs into chunked evidence digests
     - summarize those digests into higher-level dossiers
     - hand the final compressed dossier to a stronger model for reflective synthesis

8. **Human review** — Manual pass over all generated documents. Delete incorrect/outdated/sensitive content. Non-optional.
   - **Current status:** the assistant-context docs have completed an initial user review and are considered acceptable for controlled Open WebUI use.

9. **Deploy** — Upload only the assistant-context documents to Open WebUI as RAG documents by default. Interpretive analysis docs require explicit opt-in after review.
   - **Current plan:** keep the six assistant-context docs as separate knowledge documents inside one Open WebUI knowledge base, use a dedicated chat folder for default context, and use a trimmed `portable_personalization` / `system-prompt` path for custom-model calibration across frequently used frontier models.

### Data Flow

```
retrospect/data/raw_exports/ → [normalize] → retrospect/data/chats/
    → [extract 4 passes] → retrospect/data/extractions/ 
    → [aggregate] → retrospect/data/aggregated/
    → [infer] → retrospect/data/inferred/ 
    → [synthesize] → retrospect/data/knowledge_base/
    → [review] → deploy to Open WebUI
```

All data lives under `retrospect/data/` (gitignored). Schemas live in `retrospect/schemas/`. Scripts live in `retrospect/scripts/`. Raw exports preserved untouched.

## Cost Estimation

- 3,231 conversations × 4 passes = 12,924 API calls
- Estimate per call varies by model choice and prompt length
- Current working assumption: full four-pass extraction with the cleanest hosted models will likely exceed the original `$20` target
- Current operating plan should reduce cost by running Passes 1-3 cheaply across all chats first, then doing layered synthesis on compressed artifacts
- Latest empirical signal: `openai/gpt-5.4-nano` completed a 25-chat random sample for Passes 1-3 with `75/75` successes in `87.9s` for `$0.097108`, projecting to about **`$12.55`** and about **`3.16 hours`** for the full archive at similar settings
- The first full Pass 1-3 rollout later failed mostly due to `HTTP 402` credit exhaustion rather than schema or architectural problems, so cost monitoring now matters most during rerun completion

## Validation

- [x] Extraction schema defined and validated
- [x] Smoke tests and trio panel runs produce valid outputs for at least one clean baseline model
- [ ] Random quality-evaluation sample selected with a documented target confidence / margin-of-error rationale
- [ ] Frontier adjudicator model(s) rate sampled chats against the original chat plus `gpt-5.4-nano` outputs
- [ ] Human-in-the-loop ratings completed for a smaller calibration subset
- [ ] Agreement / disagreement between adjudicator models and human ratings summarized
- [ ] Each pass extracts target fields correctly
- [ ] Evidence is verbatim or turn-referenced and confidence is calibrated
- [ ] Negative-space reporting is populated for low-signal conversations
- [ ] Aggregation deduplicates and counts correctly
- [ ] Derived analysis produces framework mappings with evidence, disconfirming evidence, and recurrence thresholds
- [ ] Sample evaluation rubric captures false positives for Pass 3 and Pass 4
- [x] Synthesized docs are factual and cited
- [x] Human review completed before any upload
- [ ] Documents searchable in Open WebUI RAG

## Current Operating Decision

- **Bulk extraction model:** `openai/gpt-5.4-nano`
- **Bulk extraction scope:** run **Passes 1-3** across all chats first
- **Execution shape:** run the archive **chronologically in chunks of 10 chats**
- **Concurrency posture:** use the highest practical request concurrency the provider tolerates cleanly; optimize for throughput rather than manual babysitting
- **Failure handling:** keep successful outputs, record failed items and validation issues, and produce explicit rerun lists instead of blocking the whole archive run
- **Resume strategy:** resume by rerunning the saved failed-chat list with `extract.py`; do not restart the archive rollout by chunk index
- **Psych/introspection path:** treat deeper psych insight as an aggregation and synthesis problem unless a later Pass 4 path proves clearly valuable and operationally stable
- **Likely stronger synthesis candidates:** `openai/gpt-5.4-mini` and `google/gemini-3-flash-preview`
- **Assistant-context deployment shape:** use the reviewed six-document assistant-context set as a single Open WebUI knowledge base, keep documents separate for cleaner retrieval, and reserve deeper personal context for local/private workflows rather than broad provider-facing prompts
- **Portable cross-model calibration:** maintain a separate non-sensitive `portable_personalization.md` and derived `system-prompt.md` for custom models used outside the richer local knowledge-base flow

This reflects the current empirical tradeoff: `gpt-5.4-nano` is the best blend of cost, runtime, and output correctness so far, while stronger hosted models can be reserved for smaller, compressed downstream contexts.

The initial full Pass 1-3 run has already been exercised successfully enough to validate the rollout shape. The near-term goal is to finish the rerun backlog and move on to aggregation rather than redesign extraction.

## Extraction Quality Analysis

Before treating the `gpt-5.4-nano` archive outputs as a settled substrate for aggregation, run a focused quality-analysis pass:

- Select a random sample sized to be statistically meaningful for archive-level quality estimation
- Give each sampled case to one or more frontier adjudicator models with both the original chat and the corresponding nano extraction outputs
- Have adjudicators rate extraction quality on a brief rubric such as factual accuracy, completeness, evidence fidelity, overreach, and usefulness
- Use a smaller subset of that sample for manual human scoring to calibrate the model judges
- Compare model-judge ratings against each other and against the human subset, then record the findings in `retrospect/data/reports/`

This analysis should inform whether prompt/schema revisions are needed before deeper aggregation and synthesis work.

## Scope

### In Scope
- One-shot migration of existing chat archive
- CLI-based extraction scripts
- JSON intermediate format
- Evidence-based psychological analysis
- Personality framework inference

### Out of Scope (for now)
- Ongoing capture pipeline
- Direct database writes
- UI for exploration
- Real-time analysis

### Deferred to Aggregation Phase
- Learning trajectory / mind changes
- Contradiction detection across conversations
- Temporal pattern analysis and time-sliced summaries

### Brief Additional Candidates
- A dedicated decision-pattern layer across repeated tradeoff discussions
- Recurring places, communities, and organizations
- Health, body, and energy themes if privacy review says they are worth keeping
- Stronger cross-chat entity resolution for people, projects, and media

## Value Targets

The extraction effort aims to produce five kinds of value:

1. **Memory value** — media, influences, people, projects, ideas you won't remember on demand
2. **Behavior value** — what you actually spend attention on, pursue, avoid, revisit
3. **Psychology value** — how you think, feel, cope, decide, attach, and self-narrate
4. **Identity value** — the recurring shape of your interests, motivations, taste, and personal mythology
5. **Creative value** — tensions, fascinations, and thematic threads that could fuel storytelling or creative work

The primary product is not "a personality type." The primary product is a high-trust evidence base that supports memory recall, working-context documents, pattern detection, and carefully bounded interpretive synthesis.

## Context

- Daily chat usage over ~3 years
- Mix of technical work, creative projects, personal reflection, learning, and casual conversation
- Psychological analysis is evidence-based, not clinical diagnosis
- All sensitive data stays gitignored

## Next Steps

1. ~~Define JSON schema for each extraction pass~~ — DONE
2. ~~Build extraction prompts for each pass~~ — DONE
3. ~~Build extraction runner script (`retrospect/scripts/extract.py`)~~ — DONE
4. ~~Smoke test extraction and model-panel harness~~ — DONE
5. ~~Run initial trio comparison across extra-small and smaller candidates~~ — DONE
6. ~~Execute the first full-archive Pass 1-3 rollout with `openai/gpt-5.4-nano` in chronological 10-chat chunks, preserving successes and collecting rerun lists~~ — DONE
7. ~~Resume from the saved rerun list and complete Passes 1-3 for the full archive~~ — DONE
8. Build the extraction quality-analysis workflow
   - select the random evaluation sample and preserve the sample manifest
   - run one or more frontier adjudicator models on original-chat plus nano-output pairs
   - score a smaller human-reviewed subset for calibration
   - summarize rating distributions and judge agreement in `retrospect/data/reports/`
9. Build aggregation script (`retrospect/scripts/aggregate.py`)
   - deduplicate entities
   - add recurrence counts, temporal spread, and cross-context consistency scoring
   - produce compression-ready evidence digests
10. Build layered synthesis pipeline
   - plain-text summaries over aggregated evidence
   - recursive compression until one-context-window dossiers exist
   - final reflective synthesis with a stronger model
11. Reassess Pass 4
   - either rerun it selectively on high-signal subsets
   - or replace most of its value with aggregation-time and synthesis-time psychological analysis
12. Build inference script (`retrospect/scripts/infer.py`)
    - require disconfirming evidence and time-sliced checks for elevated claims
13. Build synthesis script (`retrospect/scripts/synthesize.py`)
    - split assistant-context outputs from interpretive-analysis outputs
