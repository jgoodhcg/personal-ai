---
title: "Personal AI Roadmap"
goal: "Self-hosted AI platform with chat interface, CLI agents, and autonomous task running."
---

# Roadmap

## Current Focus

- Phase 1 foundation is in progress.
- Immediate execution target: `roadmap/phase-1-launch-readiness.md` (`ready`) to harden launch with API/mobile/privacy acceptance checks.

## Vision Notes

The platform's shape is emerging through use. What's clear: self-hosted, privacy-first, multi-provider chat via Open WebUI, Tailscale-only access. What's still forming: the relationship between the chat interface and CLI coding agents (Claude Code, Gemini CLI, OpenCode), what orchestration looks like in practice, and whether chat-driven tooling (like Open Terminal) complements or overlaps with dedicated agent workflows. The architecture is intentionally evolutionary -- Phase 1 establishes the foundation; later phases will be shaped by what actually gets used.

## Work Units

- `phase-1-foundation.md` (`active`): infrastructure baseline on VPS/Tailscale + Open WebUI.
- `phase-1-launch-readiness.md` (`ready`): launch gating checks and hardening for Open WebUI.
- `phase-1-chat-archive-processing.md` (`ready`): process exported chat histories into RAG knowledge base.
- `phase-2-task-runner.md` (`draft`): scheduled automation jobs after foundation is stable.
- `phase-3-dashboard.md` (`draft`): optional visibility UI for task runs.
- `phase-4-custom-fork.md` (`draft`): only if upstream Open WebUI cannot meet requirements.

## Quick Ideas

Ideas not yet promoted to work units:

- Ollama for local models (resource constraints TBD)
- Mobile shortcut for quick capture
- Open Terminal (Open WebUI native integration) -- gives the chat model real shell access for ad-hoc tasks (file ops, scripts, package installs) directly from the chat UI. Interesting but cutting-edge; revisit after it stabilizes. Open question: Docker mode (isolated container, duplicates env) vs bare metal (real VPS access, higher risk)? See: https://docs.openwebui.com/features/extensibility/open-terminal/
