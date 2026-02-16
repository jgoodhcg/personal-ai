---
title: "Phase 2: Task Runner"
status: draft
description: "Cron-scheduled Python scripts for automated daily/weekly tasks"
tags: [area/automation, type/feature]
priority: medium
created: 2025-02-02
updated: 2026-02-15
depends-on: [phase-1-launch-readiness.md]
---

# Phase 2: Task Runner

## Intent

Automate recurring information gathering and analysis tasks. Get daily digests and weekly reports without manual prompting.

## Specification

- Must run on the same VPS with bounded resource usage.
- Output markdown artifacts to `logs/`.
- Use read-only access to `knowledge/`.
- Run on a schedule (cron or equivalent) with clear job definitions.

Initial task candidates:
- Daily: news digest, inbox summary.
- Weekly: project audits, dependency checks.

Reference service shape:

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

## Validation

- [ ] One daily task runs on schedule and writes expected markdown output.
- [ ] One weekly task runs on schedule and writes expected markdown output.
- [ ] Task runner cannot mutate `knowledge/` (read-only mount enforced).
- [ ] Failure path produces actionable logs.

## Scope

In scope:
- Scheduling and running recurring automation scripts.
- Writing outputs to durable markdown logs.

Out of scope:
- UI/dashboard for task visualization.
- Complex orchestration beyond a single VPS scheduler pattern.

## Context

- Depends on launch-readiness completion: `phase-1-launch-readiness.md`.
- Expected data inputs: `knowledge/`.
- Expected outputs: `logs/`.

## Open Questions

- Scheduling: cron inside container vs external trigger?
- Notification system for failures?
- Which tasks to build first?
