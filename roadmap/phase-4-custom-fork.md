---
title: "Phase 4: Custom Chat Fork"
status: draft
description: "Fork Open WebUI when upstream doesn't meet needs"
tags: [area/chat, type/enhancement]
priority: low
created: 2025-02-02
updated: 2026-02-08
depends-on: [phase-1-foundation.md]
---

# Phase 4: Custom Chat Fork

## Problem / Intent

Open WebUI may not do everything needed long-term. Having a fork ready allows customization while staying close to upstream.

## Constraints

- Must stay mergeable with upstream (minimize divergence)
- Publish to personal GHCR
- GitHub Actions for automatic builds

## Proposed Approach

1. Fork Open WebUI repo
2. Set up GitHub Actions to build and push to GHCR
3. Swap image in docker-compose.yml:

```yaml
image: ghcr.io/yourusername/open-webui:main
```

4. Periodically sync with upstream

## Open Questions

- What customizations would trigger this?
- Svelte/Python skills needed?

## Notes

Only pursue if Open WebUI genuinely doesn't work. Don't fork prematurely.
