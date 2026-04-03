---
title: "Open Responses Connection Trial"
status: draft
description: "Test a dedicated Open Responses connection in Open WebUI and determine whether OpenRouter supports the required path or a direct provider connection is needed"
created: 2026-04-02
updated: 2026-04-02
tags: [area/chat, area/providers, type/integration]
priority: medium
depends-on: [foundation.md]
---

# Open Responses Connection Trial

## Intent

Evaluate whether Open WebUI's experimental Open Responses connection is a practical way to enable newer provider-native agent behaviors for selected models without disrupting the existing chat setup.

## Specification

1. Create a separate Open WebUI connection dedicated to `Open Responses` testing rather than changing the primary OpenAI-compatible connection in place.
2. Test at least one target model through that connection and verify basic chat behavior, tool-calling behavior, and any model selection or endpoint quirks.
3. Determine whether OpenRouter supports the required Open Responses path cleanly for the target model(s), or whether a direct provider connection is required.
4. Record the known-good setup shape:
- provider/base URL
- auth source
- API type
- target model IDs
- observed limitations or incompatibilities

## Validation

- [ ] Open WebUI can save and use a dedicated `Open Responses` connection.
- [ ] At least one target model completes a basic chat successfully over that connection.
- [ ] At least one agentic/tool-oriented behavior is tested and documented.
- [ ] OpenRouter compatibility is confirmed or ruled out for the target configuration.
- [ ] If OpenRouter is not sufficient, the direct-provider fallback path is documented.
- [ ] Known-good settings and caveats are captured in project docs or roadmap notes.

## Scope

In scope:
- Connection-level experimentation inside Open WebUI.
- Provider routing comparison for this specific API mode.
- Documentation of what works and what fails.

Out of scope:
- Reworking the whole provider strategy.
- Migrating all models to `Open Responses`.
- Building custom proxy code or an Open WebUI fork.

## Context

- Open WebUI currently runs from `docker-compose.yml`.
- Launch validation already calls out GPT-5 class model testing in `roadmap/launch-readiness.md`.
- Current questions came from trying to distinguish Open WebUI-native web tools from provider-hosted browsing/tooling.

## Open Questions (draft only)

- Does OpenRouter expose a sufficiently compatible Open Responses path for the desired models?
- If OpenRouter works, are there feature gaps versus going direct to the provider?
- Which models are worth testing first: `gpt-5.4` only, or a wider set?
- Should the result become a standing secondary connection, or remain an experiment?
