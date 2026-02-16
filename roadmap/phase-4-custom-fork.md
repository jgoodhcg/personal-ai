---
title: "Phase 4: Custom Chat Fork"
status: draft
description: "Fork Open WebUI when upstream doesn't meet needs"
tags: [area/chat, type/enhancement]
priority: low
created: 2025-02-02
updated: 2026-02-15
depends-on: [phase-1-launch-readiness.md]
---

# Phase 4: Custom Chat Fork

## Intent

Open WebUI may not do everything needed long-term. Having a fork ready allows customization while staying close to upstream.

## Specification

- Must stay mergeable with upstream (minimize divergence)
- Publish to personal GHCR
- GitHub Actions for automatic builds

Proposed approach:

1. Fork Open WebUI repo
2. Set up GitHub Actions to build and push to GHCR
3. Swap image in docker-compose.yml:

```yaml
image: ghcr.io/yourusername/open-webui:main
```

4. Periodically sync with upstream

## Validation

- [ ] Custom image builds reproducibly in CI and publishes to GHCR.
- [ ] Deployment can switch image tag without data migration issues.
- [ ] Minimal diff from upstream is documented.
- [ ] Trigger criteria are satisfied and recorded before activation.

## Scope

In scope:
- Operational fork pipeline and upgrade strategy.
- Targeted changes that unblock hard requirements.

Out of scope:
- Broad product redesign.
- Divergent long-lived fork without upstream sync discipline.

## Context

- Depends on launch-readiness outcomes in `phase-1-launch-readiness.md`.
- Decision baseline remains Open WebUI upstream unless trigger criteria are met.
- Trigger criteria reference API compatibility, mobile UX, and privacy requirements.

## Open Questions

Trigger criteria:
- Repeated unresolved GPT-5/API compatibility blockers after launch-readiness testing.
- Required mobile/browser UX gaps that cannot be addressed through configuration.
- Privacy/compliance requirement that cannot be met by upstream settings.
- Contributor capacity and skill plan if fork becomes necessary.

## Notes

Only pursue if Open WebUI genuinely doesn't work. Don't fork prematurely.
