---
title: "Chat Archive Processing"
status: ready
description: "Process exported chat histories into structured extractions for self-discovery, psychological analysis, and RAG knowledge base"
created: 2026-03-06
updated: 2026-03-07
tags: [knowledge-base, rag, chat-exports, self-discovery, psychology]
priority: high
---

# Chat Archive Processing

## Intent

Turn years of ChatGPT, Claude, and z.ai/GLM chat exports into structured data for:

1. **Self-discovery and analysis** — surface patterns in interests, goals, behaviors, and psychology
2. **Psychological insight** — extract evidence-bearing signals that could support serious psychological interpretation
3. **Memory utility** — searchable records of media, influences, people, projects, and ideas
4. **RAG context** — feed Open WebUI's knowledge base so models have context about the user

## Data

- **Source**: 3,231 normalized conversations (2023-2026)
- **Platforms**: ChatGPT, Claude, z.ai/GLM
- **Status**: Normalization complete, chats in `chats/` directory

## Extraction Architecture

### Principle: Evidence Over Inference

To produce trustworthy psychological analysis, we separate:

- **Observed evidence** — what the user actually said or asked
- **Interpretation** — what the model thinks that may imply
- **Framework mapping** — how evidence maps onto personality frameworks

Every extracted item includes:
- `signal` — the extracted item
- `interpretation` — what it might mean
- `evidence` — direct quotes or references
- `confidence` — how certain (low/medium/high)
- `salience` — how central to the conversation (peripheral/central/primary)
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

**JSON** with strict schema validation. No human reads intermediates, so optimize for:
- Programmatic aggregation
- Schema-constrained structured output (better model performance)
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

## Pipeline

1. **Normalize** — DONE. Python script converted all exports to uniform markdown in `chats/`.

2. **Extract** — Four-pass extraction per conversation via OpenRouter. Outputs to `extractions/` as JSON.

3. **Aggregate** — Combine extractions into frequency-counted lists and pattern summaries in `aggregated/`.

4. **Infer** — Cross-conversation derived analysis for personality frameworks and psychological patterns.

5. **Synthesize** — Generate knowledge base documents in `knowledge_base/`:
   - `personal_profile.md` — biographical facts, cognitive style, values
   - `interest_map.md` — domains, intensity, connections, evolution
   - `goals_and_projects.md` — active/recurring/completed goals, project index
   - `working_with_me.md` — instructions for AI assistants
   - `decision_patterns.md` — how decisions are approached
   - `ideas_gallery.md` — full catalog with patterns
   - `media_and_influences.md` — cultural references and tastes
   - `psychological_profile.md` — evidence-based personality analysis
   - `relationship_map.md` — people and social patterns

6. **Human review** — Manual pass over all generated documents. Delete incorrect/outdated/sensitive content. Non-optional.

7. **Deploy** — Upload knowledge base documents to Open WebUI as RAG documents.

### Data Flow

```
raw_exports/ → [normalize] → chats/ → [extract 4 passes] → extractions/ 
    → [aggregate] → aggregated/ → [infer] → inferred/ 
    → [synthesize] → knowledge_base/ → [review] → deploy to Open WebUI
```

All data directories are gitignored. Scripts are committed. Raw exports preserved untouched.

## Cost Estimation

- 3,231 conversations × 4 passes = 12,924 API calls
- Estimate per call varies by model choice and prompt length
- Target: under $20 total for all extraction phases
- Monitor costs during initial 100-chat sample run

## Validation

- [ ] Extraction schema defined and validated
- [ ] Sample run of 100 conversations produces valid JSON
- [ ] Each pass extracts target fields correctly
- [ ] Evidence and confidence fields populated
- [ ] Aggregation deduplicates and counts correctly
- [ ] Derived analysis produces framework mappings with evidence
- [ ] Synthesized docs are factual and cited
- [ ] Human review completed before any upload
- [ ] Documents searchable in Open WebUI RAG

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
- Temporal pattern analysis

## Value Targets

The extraction effort aims to produce four kinds of value:

1. **Memory value** — media, influences, people, projects, ideas you won't remember on demand
2. **Behavior value** — what you actually spend attention on, pursue, avoid, revisit
3. **Psychology value** — how you think, feel, cope, decide, attach, and self-narrate
4. **Identity value** — the recurring shape of your interests, motivations, taste, and personal mythology

## Context

- Daily chat usage over ~3 years
- Mix of technical work, creative projects, personal reflection, learning, and casual conversation
- Psychological analysis is evidence-based, not clinical diagnosis
- All sensitive data stays gitignored

## Next Steps

1. Define JSON schema for each extraction pass
2. Build extraction prompts for each pass
3. Run cost estimate on 100-chat sample
4. Build extraction runner script
5. Execute full extraction
6. Build aggregation and inference scripts
