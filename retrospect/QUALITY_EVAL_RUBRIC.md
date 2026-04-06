# Retrospect Quality Evaluation Rubric

This rubric is for judging the archive-scale `gpt-5.4-nano` Pass 1-3 extraction bundle for a single chat against the original normalized chat.

The evaluation target is the combined output of:
- `pass1_summary`
- `pass2_projects`
- `pass3_people`

The judge should score the extraction bundle, not rewrite it.

## Primary Decision

### `downstream_ready`

Binary decision:
- `true`: The extraction is good enough to include in aggregation without mandatory manual repair.
- `false`: The extraction has material issues that would meaningfully distort downstream aggregation or synthesis.

This is the primary field for archive-level rate estimates.

## Dimension Scores

Each dimension is scored on a 1-5 scale.

### 1. Factual Accuracy

- `1`: Major factual errors or clear contradiction of the chat
- `2`: Multiple inaccuracies or one serious misread
- `3`: Mostly accurate but with some meaningful mistakes
- `4`: Accurate with only minor issues
- `5`: Fully accurate as far as the source chat supports

### 2. Completeness

- `1`: Misses most important content
- `2`: Misses several important items
- `3`: Captures the core but omits meaningful secondary content
- `4`: Covers nearly all important content
- `5`: Thorough coverage of the important content at the intended scope

### 3. Evidence Fidelity

- `1`: Claimed evidence is unsupported, distorted, or misleading
- `2`: Evidence linkage is weak or frequently loose
- `3`: Evidence is generally grounded but sometimes imprecise
- `4`: Evidence is well grounded and appropriately specific
- `5`: Evidence linkage is consistently precise and trustworthy

### 4. Restraint

This measures resistance to overreach and hallucinated interpretation.

- `1`: Strong overreach, invention, or psychologizing beyond the chat
- `2`: Frequent unsupported inference
- `3`: Some inference drift but mostly controlled
- `4`: Well calibrated with only minor stretch
- `5`: Highly disciplined; stays close to what the chat supports

### 5. Downstream Usefulness

This measures whether the extraction is useful for later aggregation and synthesis.

- `1`: Not useful without substantial repair
- `2`: Weak signal, poor structure, or too noisy
- `3`: Usable but uneven
- `4`: Strongly useful for aggregation
- `5`: Excellent substrate for aggregation and synthesis

## Major Issue Categories

Use these when recording notable problems:
- `factual_error`
- `omission`
- `evidence_problem`
- `overreach`
- `scope_mismatch`
- `formatting_issue`
- `other`

## Pass Notes

The judge should leave a brief note for each pass:
- `pass1_summary`
- `pass2_projects`
- `pass3_people`

These notes can be short. The point is to localize where the bundle is strongest or weakest.
