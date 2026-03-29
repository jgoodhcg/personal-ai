---
title: "Analysis Audio Synthesis"
status: draft
description: "Synthesize the interpretive analysis corpus into a single listening dossier, an audio-first script, and rendered speech using OpenAI TTS."
created: 2026-03-29
updated: 2026-03-29
tags: [retrospect, analysis, audio, tts, synthesis]
priority: medium
---

# Analysis Audio Synthesis

## Intent

Turn the current interpretive analysis corpus into a form that is easier to revisit repeatedly:

1. one consolidated reading artifact
2. one audio-oriented script
3. one or more rendered audio files

The goal is not to upload this material to Open WebUI knowledge. The goal is to create a private reflective asset that can be read or listened to on demand.

## Specification

Build a small synthesis pipeline for the existing files in `retrospect/data/knowledge_base/analysis/`.

### Source corpus

Use these as the source layer:

- `retrospect/data/knowledge_base/analysis/values_and_cares.md`
- `retrospect/data/knowledge_base/analysis/purpose_and_meaning.md`
- `retrospect/data/knowledge_base/analysis/optimization_model.md`
- `retrospect/data/knowledge_base/analysis/blind_spots_and_change_levers.md`
- `retrospect/data/knowledge_base/analysis/routine_and_decision_tree.md`
- `retrospect/data/knowledge_base/analysis/questions_to_ask_yourself.md`
- `retrospect/data/knowledge_base/analysis/narrative_identity.md`
- `retrospect/data/knowledge_base/analysis/sensitive_conversation_guide.md`
- optionally `retrospect/data/knowledge_base/analysis/personality_frameworks.md` only as a low-trust appendix or hypothesis source

### New artifact location

Do not place the new outputs inside `retrospect/data/knowledge_base/analysis/`.

Create a separate private artifact tree:

`retrospect/data/listening/`

Suggested shape:

- `retrospect/data/listening/dossiers/`
- `retrospect/data/listening/scripts/`
- `retrospect/data/listening/audio/`
- `retrospect/data/listening/manifests/`

### Deliverables

#### 1. Consolidated listening dossier

Create one synthesis file such as:

- `retrospect/data/listening/dossiers/listening_dossier.md`

This should be a compressed, coherent merge of the analysis corpus, not a raw concatenation.

Recommended sections:

1. core values and cares
2. optimization target
3. recurring tensions and blind spots
4. purpose and meaning
5. routine and decision guidance
6. open questions for the next season

This file should stay in Markdown and remain readable as a standalone artifact.

#### 2. Audio-first script

Create one speech-ready script such as:

- `retrospect/data/listening/scripts/listening_script.md`

This is derived from the dossier, but rewritten for listening:

- fewer bullets
- more paragraph flow
- repetition used intentionally
- smoother transitions
- explicit uncertainty where the evidence is interpretive rather than factual

The script should sound like a coherent guided reflective monologue, not like notes being read aloud.

#### 3. Rendered audio

Render the script to one or more audio files such as:

- `retrospect/data/listening/audio/listening_script.mp3`
- `retrospect/data/listening/audio/listening_script_part_01.mp3`
- `retrospect/data/listening/audio/listening_script_part_02.mp3`

Splitting is acceptable and likely preferable because OpenAI's `audio/speech` endpoint currently accepts a maximum input length of 4096 characters per request.

#### 4. Render manifest

Write a small machine-readable manifest such as:

- `retrospect/data/listening/manifests/listening_render.json`

This should record:

- source input files
- synthesis prompt or strategy version
- script file path(s)
- TTS model
- voice
- instructions
- response format
- render timestamp
- chunk ordering if multi-part

## OpenAI TTS Plan

Use OpenAI's Audio API `audio/speech` endpoint for rendering.

Current API assumptions to encode:

- prefer `gpt-4o-mini-tts`
- use built-in voices first
- use `instructions` only with `gpt-4o-mini-tts`, not `tts-1` or `tts-1-hd`
- default output format should be `mp3` unless there is a concrete reason to preserve a lossless format
- chunk long scripts before render rather than trying to overstuff the endpoint

Initial default render settings:

- model: `gpt-4o-mini-tts`
- response format: `mp3`
- speed: `1.0`
- voice: choose after a short comparison pass
- instructions: calm, grounded, reflective, direct, not overly theatrical

Potential follow-up:

- render the same script with 2-3 voices and keep a simple preference note
- keep voice instructions versioned in the manifest for reproducibility

## Implementation Plan

1. Define the exact source set from the current `analysis/` corpus.
2. Create `retrospect/data/listening/` with dossier/script/audio/manifest subdirectories.
3. Build the first merged dossier by synthesizing the selected source docs into one coherent Markdown file.
4. Rewrite the dossier into an audio-first script.
5. Add a small rendering script, likely under `retrospect/scripts/`, to:
   - read the speech script
   - chunk it safely for the OpenAI TTS input limit
   - call the OpenAI Audio API
   - write audio files and a manifest
6. Do one voice comparison pass on a short excerpt before rendering the full script.
7. Render the first full listening version.
8. Review the result for:
   - script quality
   - voice fit
   - chunk boundaries
   - whether the runtime is short enough to be replayable

## Validation

How to know this work unit is done:

- [ ] `retrospect/data/listening/` exists with the planned subdirectories
- [ ] one consolidated dossier exists outside the `analysis/` directory
- [ ] one script exists that is clearly optimized for listening rather than reading
- [ ] one render script exists and can call OpenAI TTS successfully
- [ ] at least one audio output is produced and saved locally
- [ ] a manifest records render parameters and source provenance
- [ ] the final audio is subjectively listenable and not obviously note-like or fragmented

## Scope

In scope:

- private reflective listening assets
- consolidation of the existing analysis corpus
- one practical audio render path using OpenAI TTS

Out of scope:

- uploading these analysis artifacts into Open WebUI knowledge
- automatic recurring re-rendering
- public publishing workflows
- voice cloning or custom voices
- replacing the original `analysis/` files

## Context

- The existing interpretive corpus already lives in `retrospect/data/knowledge_base/analysis/`.
- The assistant-context docs are separate and intentionally shallower; they are not the source for this listening artifact.
- The roadmap already anticipates a future layered synthesis script in `retrospect/scripts/synthesize.py`, but this work unit can begin with a narrower file-level implementation.
- OpenAI's TTS docs indicate the `audio/speech` endpoint supports `gpt-4o-mini-tts`, `tts-1`, and `tts-1-hd`, with a 4096-character input limit and built-in voices suitable for first-pass narration.

## Open Questions (draft only)

- What should the target runtime be for the first version: ~12 minutes, ~18 minutes, or ~25 minutes?
- Should the script be written in second person ("you") or in a closer reflective narrator voice?
- Should `personality_frameworks.md` be excluded entirely from the first audio pass to keep the script more grounded?
- Should the render script also emit a stitched full file if multi-part rendering is used?
