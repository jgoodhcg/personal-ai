---
title: "Phase 1: Foundation"
status: active
description: "Open WebUI on VPS with Tailscale access and CLI agent environment"
tags: [area/infrastructure, type/foundation]
priority: high
created: 2025-02-02
updated: 2025-02-02
---

# Phase 1: Foundation

## Problem / Intent

Need a self-hosted AI chat interface accessible from any device, plus SSH access for running CLI agents against a shared workspace.

## Constraints

- Single VPS, budget-friendly
- All data portable (SQLite, files on disk)
- Access via Tailscale only (no public exposure)
- Must support multiple AI providers (Claude, OpenAI, Gemini, xAI)

## Proposed Approach

1. Provision VPS with Docker and Tailscale
2. Create `agent` user for CLI access
3. Deploy Open WebUI via docker-compose
4. Expose via `tailscale serve`
5. Set up knowledge base directory for RAG

## Checklist

- [ ] Provision VPS
- [ ] Run setup.sh
- [ ] Configure .env with API keys
- [ ] Start Open WebUI
- [ ] Verify Tailscale access
- [ ] Test chat with each provider
- [ ] SSH as agent, verify CLI tools work
- [ ] Add initial knowledge base files

## Open Questions

None currently.

## Notes

Structure decided: repo lives at `/home/agent/personal-ai/`, with `workspace/` and `projects/` as siblings outside the repo.
