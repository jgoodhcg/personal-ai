---
title: "Personal AI Roadmap"
goal: "Self-hosted AI platform with chat interface, CLI agents, and autonomous task running."
---

# Roadmap

## Current Focus

- Foundation is in progress. Immediate execution target: `roadmap/launch-readiness.md` (`ready`).
- Chat archive processing (`roadmap/chat-archive-processing.md`) entering extraction phase — schemas and prompts complete, extraction runner is next.

## Vision Notes

The platform's shape is emerging through use. What's clear: self-hosted, privacy-first, multi-provider chat via Open WebUI, Tailscale-only access. What's still forming: the relationship between the chat interface and CLI coding agents (Claude Code, Gemini CLI, OpenCode), what orchestration looks like in practice, and whether chat-driven tooling (like Open Terminal) complements or overlaps with dedicated agent workflows. The architecture is intentionally evolutionary — the foundation establishes the base; later work units will be shaped by what actually gets used.

## Work Units

- `foundation.md` (`active`): infrastructure baseline on VPS/Tailscale + Open WebUI.
- `launch-readiness.md` (`ready`): launch gating checks and hardening for Open WebUI.
- `open-terminal-worker.md` (`draft`): evaluate Open Terminal as a tailnet-only remote worker for chat-driven shell access, repo iteration, and private app previews.
- `open-responses-connection.md` (`draft`): test a dedicated Open Responses connection and decide whether OpenRouter works or direct provider access is required.
- `chat-archive-processing.md` (`ready`): process exported chat histories into RAG knowledge base with psychological and narrative analysis.
- `task-runner.md` (`draft`): scheduled automation jobs after foundation is stable.
- `dashboard.md` (`draft`): optional visibility UI for task runs.
- `custom-fork.md` (`draft`): only if upstream Open WebUI cannot meet requirements.

## Quick Ideas

Ideas not yet promoted to work units:

- Ollama for local models (resource constraints TBD)
- Mobile shortcut for quick capture
