---
title: "Open Terminal Worker"
status: draft
description: "Evaluate Open Terminal as a tailnet-only remote agent worker connected to Open WebUI"
tags: [area/infrastructure, area/agents, type/evaluation]
priority: medium
created: 2026-04-06
updated: 2026-04-06
depends-on: [foundation.md, launch-readiness.md]
---

# Open Terminal Worker

## Intent

Decide whether Open Terminal should become the chat-driven remote execution layer for this platform: a shell-capable worker reachable from Open WebUI, running on the same tailnet, with access to persistent repo workspaces and optional CLI coding agents.

## Specification

- Evaluate Open Terminal in Docker mode only.
- Compare two deployment shapes:
  - same droplet and same Docker Compose stack as Open WebUI
  - separate worker node on the tailnet
- Define the minimum safe storage layout for persistent repos and agent workspaces.
- Determine whether additional CLI agents belong inside the worker image or remain SSH-driven workflows outside Open Terminal.
- Document the access pattern for previewing web apps started by the worker:
  - Open Terminal port proxy
  - Tailscale Serve/Funnel alternatives, if needed

Prototype acceptance target:
- Open WebUI can connect to a private Open Terminal instance over the tailnet.
- A model can clone a repo into a persistent workspace, run commands, and start a local preview server without exposing public ports.

## Validation

- [ ] A draft architecture decision exists comparing same-droplet vs separate-worker deployment.
- [ ] `docker compose config` passes with any prototype Compose changes.
- [ ] `docker compose up --dry-run` passes for the prototype stack.
- [ ] Open WebUI can reach the Open Terminal endpoint using a private network path.
- [ ] A test repo can be cloned into a persistent workspace and still be present after container restart.
- [ ] A preview web app started from the worker is reachable remotely through the intended private access path.
- [ ] Security notes are captured for filesystem mounts, API key handling, and whether Docker socket access is prohibited.

## Scope

In scope:
- Architectural evaluation and a limited prototype.
- Docker Compose integration if same-droplet remains a serious option.
- Storage, networking, and security boundary definition.

Out of scope:
- Full production rollout for multiple users.
- Bare-metal Open Terminal deployment.
- Building a full autonomous orchestration layer around Open Terminal.

## Context

- Current baseline stack is in `docker-compose.yml` and centers on Open WebUI plus SearXNG.
- Foundation target is a Tailscale-only VPS with SSH access for CLI agents.
- Open question: whether Open Terminal complements or overlaps with Codex / Claude Code / Gemini CLI workflows already expected on the host.
- The likely decision hinge is isolation: convenience of same-droplet Compose vs cleaner blast-radius separation with a dedicated worker node.

## Open Questions

- Should Open Terminal live in the existing Compose stack or on a separate tailnet worker by default?
- Should repo storage be bind-mounted from the host or held in Docker-managed volumes?
- Is installing external CLI coding agents inside the worker operationally worth the auth and maintenance overhead?
- Is Open Terminal's port proxy sufficient, or is Tailscale Serve a better default for long-lived preview apps?
