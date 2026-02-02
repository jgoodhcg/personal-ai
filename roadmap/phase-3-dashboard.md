---
title: "Phase 3: Dashboard"
status: idea
description: "Minimal web UI for task visibility and log viewing"
tags: [area/ui, type/feature]
priority: low
created: 2025-02-02
updated: 2025-02-02
depends-on: [phase-2-task-runner.md]
---

# Phase 3: Dashboard

## Problem / Intent

Visibility into automated task runs without SSH. See what ran, what's upcoming, and browse logs.

## Constraints

- Separate from chat UI (different concerns)
- Read-only view of logs/
- Minimal — not a full admin panel

## Proposed Approach

Lightweight web UI (maybe static site generator or simple Python/Node app) that:
- Lists recent task runs
- Shows upcoming scheduled jobs
- Provides log viewer

## Open Questions

- Tech stack? Static site vs dynamic app?
- Auth? Tailscale-only might be sufficient.
- Worth building vs just reading logs via SSH?

## Notes

Low priority. May not be needed if log files are sufficient.
