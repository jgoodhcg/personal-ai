---
title: "Phase 1: Foundation"
status: active
description: "Open WebUI on VPS with Tailscale access and CLI agent environment"
tags: [area/infrastructure, type/foundation]
priority: high
created: 2025-02-02
updated: 2026-02-15
---

# Phase 1: Foundation

## Intent

Need a self-hosted AI chat interface accessible from any device, plus SSH access for running CLI agents against a shared workspace.

## Specification

- Single VPS, budget-friendly
- All data portable (SQLite, files on disk)
- Access via Tailscale only (no public exposure)
- Must support multiple AI providers (Claude, OpenAI, Gemini, xAI)

## Validation

- [x] Open WebUI runs locally via Docker Compose.
- [x] Initial provider chats validated for OpenAI and z.ai models.
- [ ] VPS provisioning validated end-to-end with Tailscale-only access.
- [ ] Agent SSH workflow validated on VPS.
- [ ] Multi-provider chat validation completed for all required providers.

## Scope

In scope:
- Provision/standardize base VPS environment.
- Stand up Open WebUI with persistent data.
- Establish Tailscale-only access pattern.
- Confirm CLI-agent workflow and workspace structure.

Out of scope:
- Custom UI or Open WebUI fork work.
- Automated task runner and dashboard features.

## Context

- Deployment structure target: `/home/agent/personal-ai/` with sibling `workspace/` and `projects/`.
- Decision artifact for current platform direction: `.decisions/chat-interface-off-the-shelf-selection.json`.
- Launch hardening and acceptance execution unit: `roadmap/phase-1-launch-readiness.md`.

## Notes

Execution order:
1. Complete this foundation unit on VPS.
2. Execute launch-readiness checks and hardening.
