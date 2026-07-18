#!/usr/bin/env python3
"""Ingest Claude Code session logs (~/.claude/projects/**/*.jsonl) into agent_chats.db.

Incremental: unchanged files (mtime+size) are skipped; changed files fully
replace their session's rows. Run: python3 retrospect/scripts/mine_claude.py
"""

import json
from pathlib import Path

import chat_db

TOOL = "claude-code"
ROOT = Path.home() / ".claude" / "projects"

META_MARKERS = ("<local-command-caveat>", "<command-name>", "<system-reminder>")


def flatten_content(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        btype = block.get("type")
        if btype == "text":
            parts.append(block.get("text", ""))
        elif btype == "thinking":
            parts.append(f"[thinking] {block.get('thinking', '')}")
        elif btype == "tool_use":
            parts.append(f"[tool_use:{block.get('name')}] {json.dumps(block.get('input', {}))}")
        elif btype == "tool_result":
            inner = block.get("content")
            if isinstance(inner, list):
                inner = "\n".join(b.get("text", "") for b in inner if isinstance(b, dict))
            parts.append(f"[tool_result] {inner or ''}")
        elif btype == "image":
            parts.append("[image]")
        else:
            parts.append(f"[{btype}]")
    return "\n".join(parts)


def ingest_file(conn, path: Path) -> None:
    messages = []
    title = model = cwd = branch = started = ended = version = None
    tokens = {"input": 0, "output": 0, "reasoning": 0, "cache_read": 0, "cache_write": 0}

    with open(path, errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            rtype = r.get("type")
            if rtype == "ai-title":
                title = r.get("aiTitle") or title
                continue
            if rtype not in ("user", "assistant"):
                continue
            msg = r.get("message") or {}
            ts = r.get("timestamp")
            started = started or ts
            ended = ts or ended
            cwd = cwd or r.get("cwd")
            branch = branch or r.get("gitBranch")
            version = version or r.get("version")
            if rtype == "assistant":
                model = msg.get("model") or model
                usage = msg.get("usage") or {}
                tokens["input"] += usage.get("input_tokens", 0) or 0
                tokens["output"] += usage.get("output_tokens", 0) or 0
                tokens["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
                tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0
            text = flatten_content(msg.get("content"))
            is_meta = bool(r.get("isMeta")) or any(m in text[:200] for m in META_MARKERS)
            messages.append({
                "role": msg.get("role") or rtype,
                "ts": ts,
                "model": msg.get("model"),
                "text": text,
                "is_meta": is_meta,
                "is_sidechain": bool(r.get("isSidechain")),
                "raw": line.strip(),
            })

    if not messages:
        return
    chat_db.replace_session(conn, {
        "tool": TOOL,
        "source_session_id": path.stem,
        "source_path": str(path),
        "project_path": cwd,
        "is_worktree": int(chat_db.is_worktree_path(cwd) or "worktrees" in path.parent.name),
        "git_branch": branch,
        "title": title,
        "provider": "anthropic",
        "model": model,
        "started_at": started,
        "ended_at": ended,
        "tokens_input": tokens["input"],
        "tokens_output": tokens["output"],
        "tokens_cache_read": tokens["cache_read"],
        "tokens_cache_write": tokens["cache_write"],
        "meta": {"cli_version": version},
    }, messages)


def main():
    conn = chat_db.connect()
    ingested = skipped = 0
    for path in sorted(ROOT.glob("*/*.jsonl")):
        if chat_db.file_unchanged(conn, TOOL, path):
            skipped += 1
            continue
        ingest_file(conn, path)
        chat_db.mark_ingested(conn, TOOL, path)
        ingested += 1
    chat_db.finish(conn, TOOL, ingested, skipped)


if __name__ == "__main__":
    main()
