---
title: "Open WebUI Launch Readiness"
status: ready
description: "Harden and validate Open WebUI for production launch on single VPS with mobile/browser/API/privacy acceptance checks"
tags: [area/infrastructure, area/chat, type/release]
priority: high
created: 2026-02-15
updated: 2026-02-15
depends-on: [foundation.md]
---

# Open WebUI Launch Readiness

## Intent

Complete concrete launch gates so Open WebUI can be used as the production chat interface with acceptable API compatibility, privacy posture, and mobile browser usability.

## Specification

1. Deployment hardening:
- Pin Open WebUI image to a stable release tag (no floating `:main`).
- Keep access Tailscale-only (no public exposure).
- Ensure persistent data remains in `data/`.

2. Provider/API acceptance:
- Validate required model routes for current providers.
- Explicitly test GPT-5 class models and document any required endpoint/provider settings.
- Record known-good model IDs/config in project docs.

3. History workflows:
- Validate at least one real import/export flow.
- Confirm analysis path (export JSON and/or SQLite query) is workable.

4. Privacy and observability checks:
- Confirm telemetry-related env settings match desired posture.
- Confirm expected outbound network behavior (provider APIs only).

5. Mobile browser acceptance:
- Verify usability at common phone widths.
- Confirm critical flows on mobile browser: open app, pick model, send prompt, continue thread, review history.

## Validation

- [ ] `docker compose config` passes after config updates.
- [ ] `docker compose up --dry-run` passes.
- [ ] `docker compose ps` shows healthy running service(s).
- [ ] GPT-5 test passes without endpoint mismatch errors.
- [ ] Import/export test completed with notes on limitations.
- [ ] History analysis smoke test completed.
- [ ] Mobile browser checks completed on at least two viewport profiles.
- [ ] Privacy/telemetry settings reviewed and documented.

## Scope

In scope:
- Launch hardening and acceptance for Open WebUI in current architecture.
- Documentation of known-good operational settings.

Out of scope:
- Building a custom chat UI.
- Forking Open WebUI.
- Building task runner or dashboard.

## Context

- Decision basis: `.decisions/chat-interface-off-the-shelf-selection.json`.
- Base deployment: `docker-compose.yml`.
- Operational policy and constraints: `AGENTS.md`.
- Foundation dependency: `roadmap/foundation.md`.
