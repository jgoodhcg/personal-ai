#!/usr/bin/env python3
"""Ingest OpenCode sessions from its own SQLite DB (~/.local/share/opencode/opencode.db)
into agent_chats.db.

Incremental: sessions whose time_updated matches what we stored are skipped.
Run: python3 retrospect/scripts/mine_opencode.py
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import chat_db

TOOL = "opencode"
SOURCE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def iso(ms) -> str | None:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def flatten_parts(parts: list[dict]) -> str:
    out = []
    for p in parts:
        ptype = p.get("type")
        if ptype == "text":
            out.append(p.get("text", ""))
        elif ptype == "reasoning":
            if p.get("text"):
                out.append(f"[thinking] {p['text']}")
        elif ptype == "tool":
            state = p.get("state") or {}
            inp = json.dumps(state.get("input", {}))
            res = state.get("output") or ""
            out.append(f"[tool_use:{p.get('tool')}] {inp}")
            if res:
                out.append(f"[tool_result] {res}")
        elif ptype in ("step-start", "step-finish", "snapshot", "patch"):
            continue
        else:
            out.append(f"[{ptype}]")
    return "\n".join(out)


def main():
    conn = chat_db.connect()
    src = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    existing = {}
    for sid, meta in conn.execute(
        "SELECT source_session_id, meta FROM sessions WHERE tool = ?", (TOOL,)
    ):
        try:
            existing[sid] = json.loads(meta or "{}").get("source_time_updated")
        except json.JSONDecodeError:
            pass

    ingested = skipped = 0
    for s in src.execute("SELECT * FROM session"):
        if existing.get(s["id"]) == s["time_updated"]:
            skipped += 1
            continue

        messages = []
        providers, model = set(), s["model"]
        for m in src.execute(
            "SELECT * FROM message WHERE session_id = ? ORDER BY time_created, id", (s["id"],)
        ):
            data = json.loads(m["data"])
            parts = [
                json.loads(p["data"])
                for p in src.execute(
                    "SELECT data FROM part WHERE message_id = ? ORDER BY id", (m["id"],)
                )
            ]
            if data.get("providerID"):
                providers.add(data["providerID"])
            model = data.get("modelID") or model
            text = flatten_parts(parts)
            if not text and data.get("role") not in ("user", "assistant"):
                continue
            messages.append({
                "role": data.get("role", "system"),
                "ts": iso((data.get("time") or {}).get("created") or m["time_created"]),
                "model": data.get("modelID"),
                "text": text,
                "raw": json.dumps({"message": data, "parts": parts}),
            })

        if not messages:
            skipped += 1
            continue
        chat_db.replace_session(conn, {
            "tool": TOOL,
            "source_session_id": s["id"],
            "source_path": str(SOURCE_DB),
            "project_path": s["directory"],
            "is_worktree": int(chat_db.is_worktree_path(s["directory"])),
            "title": s["title"],
            "provider": ",".join(sorted(providers)) or None,
            "model": model,
            "started_at": iso(s["time_created"]),
            "ended_at": iso(s["time_updated"]),
            "tokens_input": s["tokens_input"],
            "tokens_output": s["tokens_output"],
            "tokens_reasoning": s["tokens_reasoning"],
            "tokens_cache_read": s["tokens_cache_read"],
            "tokens_cache_write": s["tokens_cache_write"],
            "cost": s["cost"],
            "meta": {"source_time_updated": s["time_updated"], "slug": s["slug"], "agent": s["agent"]},
        }, messages)
        ingested += 1

    src.close()
    chat_db.finish(conn, TOOL, ingested, skipped)


if __name__ == "__main__":
    main()
