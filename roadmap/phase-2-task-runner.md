---
title: "Phase 2: Task Runner"
status: draft
description: "Cron-scheduled Python scripts for automated daily/weekly tasks"
tags: [area/automation, type/feature]
priority: medium
created: 2025-02-02
updated: 2026-02-08
depends-on: [phase-1-foundation.md]
---

# Phase 2: Task Runner

## Problem / Intent

Automate recurring information gathering and analysis tasks. Get daily digests and weekly reports without manual prompting.

## Constraints

- Must run on same VPS (resource-aware)
- Output as markdown to `logs/`
- Read-only access to knowledge base

## Proposed Approach

Docker container with Python scripts, scheduled via cron or container-native scheduling.

Example tasks:
- Daily: news digest, inbox summary
- Weekly: project audits, dependency checks

```yaml
services:
  tasks:
    build: ./tasks
    volumes:
      - ./knowledge:/knowledge:ro
      - ./logs:/logs
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Open Questions

- Scheduling: cron inside container vs external trigger?
- Notification system for failures?
- Which tasks to build first?

## Notes

Deferred until Phase 1 is stable.
