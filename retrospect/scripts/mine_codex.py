#!/usr/bin/env python3
"""Ingest Codex CLI session logs into agent_chats.db.

Covers both formats:
- New: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl (typed {timestamp,type,payload} lines)
- Legacy (2025-era): ~/.codex/sessions/rollout-*.json (single JSON {session, items})

Incremental by file mtime+size. Run: python3 retrospect/scripts/mine_codex.py
"""

import json
from pathlib import Path

import chat_db

TOOL = "codex"
ROOT = Path.home() / ".codex" / "sessions"

META_PREFIXES = (
    "# AGENTS.md instructions",
    "<user_instructions>",
    "<environment_context>",
    "<ENVIRONMENT_CONTEXT>",
)


def flatten_content(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict):
            parts.append(block.get("text") or f"[{block.get('type')}]")
        else:
            parts.append(str(block))
    return "\n".join(parts)


def item_to_message(item: dict, ts, raw: str) -> dict | None:
    """Map a response item (shared between old and new formats) to a message row."""
    itype = item.get("type")
    if itype == "message":
        text = flatten_content(item.get("content"))
        return {
            "role": item.get("role", "user"),
            "ts": ts,
            "text": text,
            "is_meta": text.startswith(META_PREFIXES),
            "raw": raw,
        }
    if itype in ("function_call", "custom_tool_call", "local_shell_call"):
        name = item.get("name", itype)
        args = item.get("arguments") or item.get("input") or json.dumps(item.get("action", {}))
        return {"role": "tool", "ts": ts, "text": f"[tool_use:{name}] {args}", "raw": raw}
    if itype in ("function_call_output", "custom_tool_call_output"):
        out = item.get("output")
        if isinstance(out, dict):
            out = out.get("content") or json.dumps(out)
        return {"role": "tool", "ts": ts, "text": f"[tool_result] {out or ''}", "raw": raw}
    if itype == "reasoning":
        summary = item.get("summary") or []
        text = "\n".join(
            s.get("text", "") for s in summary if isinstance(s, dict)
        ) or item.get("content") or ""
        text = flatten_content(text) if not isinstance(text, str) else text
        if not text:
            return None
        return {"role": "assistant", "ts": ts, "text": f"[thinking] {text}", "is_meta": 1, "raw": raw}
    return None


def ingest_jsonl(conn, path: Path) -> None:
    messages = []
    sess_id = path.stem
    cwd = model = started = ended = version = None
    tokens = None

    with open(path, errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = r.get("timestamp")
            payload = r.get("payload") or {}
            rtype = r.get("type")
            if rtype == "session_meta":
                sess_id = payload.get("id") or sess_id
                cwd = payload.get("cwd") or cwd
                version = payload.get("cli_version")
                started = payload.get("timestamp") or ts
                continue
            if rtype == "turn_context":
                cwd = payload.get("cwd") or cwd
                model = payload.get("model") or model
                continue
            if rtype == "event_msg" and payload.get("type") == "token_count":
                tokens = (payload.get("info") or {}).get("total_token_usage") or tokens
                continue
            if rtype == "response_item":
                msg = item_to_message(payload, ts, line.strip())
                if msg:
                    messages.append(msg)
                    started = started or ts
                    ended = ts or ended

    if not messages:
        return
    tokens = tokens or {}
    save_session(conn, path, sess_id, cwd, model, started, ended, version, tokens, messages)


def ingest_legacy_json(conn, path: Path) -> None:
    try:
        data = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return
    sess = data.get("session") or {}
    ts = sess.get("timestamp")
    messages = []
    for item in data.get("items") or []:
        msg = item_to_message(item, None, json.dumps(item))
        if msg:
            messages.append(msg)
    if not messages:
        return
    save_session(conn, path, sess.get("id") or path.stem, sess.get("cwd"),
                 sess.get("model"), ts, ts, None, {}, messages)


def save_session(conn, path, sess_id, cwd, model, started, ended, version, tokens, messages):
    chat_db.replace_session(conn, {
        "tool": TOOL,
        "source_session_id": sess_id,
        "source_path": str(path),
        "project_path": cwd,
        "is_worktree": int(chat_db.is_worktree_path(cwd)),
        "provider": "openai",
        "model": model,
        "started_at": started,
        "ended_at": ended,
        "tokens_input": tokens.get("input_tokens"),
        "tokens_output": tokens.get("output_tokens"),
        "tokens_reasoning": tokens.get("reasoning_output_tokens"),
        "tokens_cache_read": tokens.get("cached_input_tokens"),
        "meta": {"cli_version": version},
    }, messages)


def main():
    conn = chat_db.connect()
    ingested = skipped = 0
    files = sorted(ROOT.rglob("rollout-*.jsonl")) + sorted(ROOT.glob("rollout-*.json"))
    for path in files:
        if chat_db.file_unchanged(conn, TOOL, path):
            skipped += 1
            continue
        if path.suffix == ".jsonl":
            ingest_jsonl(conn, path)
        else:
            ingest_legacy_json(conn, path)
        chat_db.mark_ingested(conn, TOOL, path)
        ingested += 1
    chat_db.finish(conn, TOOL, ingested, skipped)


if __name__ == "__main__":
    main()
