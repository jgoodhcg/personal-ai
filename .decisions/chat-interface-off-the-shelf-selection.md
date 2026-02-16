# Decision: Off-the-Shelf Chat Interface Selection

**Status:** proposed  
**Date:** 2026-02-15

## Context

Choose a chat interface platform that supports project goals:
- Self-hosted on a single VPS
- Multiple providers/models
- Strong privacy posture and controllable data handling
- Usable history import and history analysis workflows
- Reliable mobile browser experience on phone screen sizes
- Fast launch with manageable operations

## Options

### Open WebUI
- Pros: Fastest launch path, simple operations, local SQLite history, good analysis access.
- Cons: GPT-5/API behavior may require endpoint/config tuning.

### LibreChat
- Pros: Strong multi-provider support, good fallback for API-compatibility issues.
- Cons: Heavier operational footprint than Open WebUI.

### AnythingLLM
- Pros: Strong document/RAG orientation.
- Cons: Weaker fit for chat-platform-first launch goals.

### LobeChat
- Pros: Modern UX and extensibility.
- Cons: Heavier infrastructure requirements for current stage.

### Build simple custom UI
- Pros: Maximum control over privacy, API strategy, and analytics.
- Cons: Slowest path to launch; highest implementation burden.

## Decision

Use **Open WebUI** as the launch platform, with **LibreChat** as fallback if GPT-5/API compatibility remains blocked after focused testing.

## Consequences

- Faster launch and lower ops risk now.
- Preserve ability to switch if compatibility issues persist.
- Defer custom UI investment until requirements justify the build cost.

See authoritative matrix: `.decisions/chat-interface-off-the-shelf-selection.json`.
