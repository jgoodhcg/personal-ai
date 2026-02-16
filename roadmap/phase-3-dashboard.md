---
title: "Phase 3: Dashboard"
status: draft
description: "Minimal web UI for task visibility and log viewing"
tags: [area/ui, type/feature]
priority: low
created: 2025-02-02
updated: 2026-02-15
depends-on: [phase-2-task-runner.md]
---

# Phase 3: Dashboard

## Intent

Visibility into automated task runs without SSH. See what ran, what's upcoming, and browse logs.

## Specification

- Separate from chat UI (different concerns)
- Read-only view of logs/
- Minimal — not a full admin panel

Provide a lightweight web UI that:
- Lists recent task runs.
- Shows upcoming scheduled jobs.
- Provides a read-only log viewer.

## Validation

- [ ] Dashboard loads over Tailscale and is mobile-browser usable.
- [ ] Recent run list reflects on-disk log artifacts.
- [ ] Log viewer is read-only.
- [ ] No cross-coupling with chat service configuration.

## Scope

In scope:
- Read-only operational visibility for automated tasks.

Out of scope:
- Full admin control plane.
- Chat interface replacement.

## Context

- Depends on task output conventions from `phase-2-task-runner.md`.
- Must follow Tailscale-only access rule from `AGENTS.md`.

## Open Questions

- Tech stack? Static site vs dynamic app?
- Auth? Tailscale-only might be sufficient.
- Worth building vs just reading logs via SSH?
