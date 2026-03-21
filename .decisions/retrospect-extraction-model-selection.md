# Retrospect Extraction Model Selection

Date: 2026-03-21

## Current Decision

Proceed with a **two-tier approach**:

1. Use **`openai/gpt-5.4-nano`** as the default bulk extractor for the archive.
2. Use a **stronger downstream model** for aggregation and layered synthesis after the corpus has been compressed.

This is a provisional decision, but it is strong enough to move the project forward now.

The strongest new evidence is a **25-chat random sample run for Passes 1-3 with `GPT-5.4 Nano`**:

- `75/75` tasks succeeded
- `87.9s` total runtime
- `$0.097108` sample cost
- rough projection: about **`$12.55`** and about **`3.16 hours`** for all `3,231` chats on Passes 1-3

The wildcard panel run adds two useful signals:

- `Mercury 2` was the strongest wildcard operationally: `12/12` tasks succeeded in about `9.1s` for about `$0.017171`.
- `Qwen3.5 397B A17B` was mostly usable at `11/12`, but still had a psych taxonomy miss.
- `GLM 5 Turbo`, `Mistral Large 3 2512`, and `MiniMax M2.5` are currently blocked by routing or reasoning-policy incompatibilities under the project defaults.

## Why

The current empirical runs show:

- `GPT-5.4 Nano` is the cleanest operational option so far.
- `GPT-5.4 Mini` and `Gemini 3 Flash Preview` are also operationally strong, but cost materially more for bulk extraction.
- `GLM 4.7 Flash` is extremely cheap, but much slower and still more brittle.
- `Gemini 3.1 Flash Lite Preview`, `GLM 4.5 Air`, and `Claude Haiku 4.5` look potentially salvageable, but currently lose on formatting reliability.
- `Claude Sonnet 4.6` remains too expensive to justify as the primary extraction model given the current psych-pass instability.
- `Mercury 2` is now a serious synthesis-side candidate because it is fast, cheap, and operationally clean on the trio, even though it is not currently the chosen bulk extractor.

For the archive-scale extraction phase, reliability and cost matter more than squeezing out a small quality gain from a more expensive model.

## Fit To Goals

### Goal 1: Open WebUI personalization

This goal primarily needs:

- broad coverage across the whole archive
- stable structured extraction
- low enough cost to run the full corpus without hesitation

That favors `GPT-5.4 Nano`.

### Goal 2: Self introspection

This goal needs:

- stronger synthesis
- better handling of ambiguity
- more room for interpretation across many conversations

That does **not** require the strongest model on every raw chat. It is better served by:

- cheap full extraction first
- aggregation into evidence-bearing intermediate artifacts
- layered synthesis passes with stronger models over compressed summaries

## Current Operating Plan

1. Run **Passes 1-3 only** across the full archive with `GPT-5.4 Nano`.
2. Run the archive **chronologically in chunks of 10 chats** so progress is easy to inspect and rerun.
3. Use aggressive concurrency for throughput, but preserve successful outputs even when some items fail.
4. Write explicit rerun lists for failures and validation issues rather than blocking the whole archive run.
5. Aggregate and compress those structured outputs.
6. Generate plain-text insight summaries from the aggregated structured corpus.
7. Recursively summarize at larger scopes until the material fits comfortably in the context window of a stronger model.
8. Use a stronger model for the final reflective / introspective synthesis.

## Unknowns Still Worth Resolving

- Human-rated quality comparison for `GPT-5.4 Nano` vs `GPT-5.4 Mini` vs `Gemini 3 Flash Preview`
- Whether `Claude Sonnet 4.6` becomes viable after rerunning under the softer psych-pass contract
- Whether lightweight repair / coercion makes the cheaper extra-small alternatives materially more usable

## Alternative Path

If the rigid psych extraction path continues to be brittle, the fallback is:

- keep full-archive extraction limited to Passes 1-3
- do psych / self-insight work at the aggregation and synthesis layers instead of forcing Pass 4 on every raw chat

That is currently the lowest-risk fallback and still supports both project goals.

## Local Model Note

Local models are worth considering as a later experiment for **synthesis**, not as the first-choice path for raw archive extraction.

On the current machine:

- Apple M3 Pro
- 36 GB unified memory
- 14-core GPU

`gpt-oss-20b` is realistically within reach locally, especially in quantized form. OpenAI describes it as an open-weight model designed for a wide range of deployment environments, with 21B total parameters and 3.6B active parameters per token. Source: [Introducing gpt-oss](https://openai.com/blog/introducing-gpt-oss/)

That said, the current recommendation is **not** to switch the extraction pipeline to local inference now. The operational bottlenecks we are dealing with are schema discipline, throughput, and evaluation clarity, not hosted-model availability.

The best local-model experiment would be:

- after structured extraction exists
- on compressed synthesis inputs
- with a notebook / report comparing local synthesis quality versus hosted synthesis quality
