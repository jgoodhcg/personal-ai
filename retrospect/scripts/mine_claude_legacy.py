#!/usr/bin/env python3
"""Recover legacy Claude Code history into agent_chats.db.

Two sources, both survivors of Claude Code's transcript cleanup:

1. ~/.claude/__store.db — v0.2.x-era SQLite store with full message content
   (Apr-May 2025). Ingested as normal sessions.
2. ~/.claude/history.jsonl — typed prompts only (no assistant side). Grouped
   into synthetic prompt-only sessions per project per day, ingested ONLY for
   dates before the earliest surviving full transcript, so they fill the
   deleted gap without duplicating real sessions. Flagged meta.prompt_only.

Run: python3 retrospect/scripts/mine_claude_legacy.py
"""

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import chat_db
from mine_claude import flatten_content

TOOL = "claude-code"
STORE_DB = Path.home() / ".claude" / "__store.db"
HISTORY = Path.home() / ".claude" / "history.jsonl"


def iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ingest_store(conn) -> int:
    if not STORE_DB.exists():
        return 0
    src = sqlite3.connect(f"file:{STORE_DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    count = 0
    for sess in src.execute(
        "SELECT session_id, cwd, version, MIN(timestamp) t0, MAX(timestamp) t1 "
        "FROM base_messages GROUP BY session_id"
    ):
        messages, model, cost = [], None, 0.0
        for b in src.execute(
            "SELECT b.*, u.message u_msg, u.tool_use_result, a.message a_msg, a.model a_model, a.cost_usd "
            "FROM base_messages b "
            "LEFT JOIN user_messages u ON u.uuid = b.uuid "
            "LEFT JOIN assistant_messages a ON a.uuid = b.uuid "
            "WHERE b.session_id = ? ORDER BY b.timestamp, b.uuid",
            (sess["session_id"],),
        ):
            raw_json = b["u_msg"] or b["a_msg"]
            if not raw_json:
                continue
            try:
                msg = json.loads(raw_json)
            except json.JSONDecodeError:
                continue
            if b["a_model"]:
                model = b["a_model"]
                cost += b["cost_usd"] or 0.0
            messages.append({
                "role": msg.get("role") or b["message_type"],
                "ts": iso(b["timestamp"]),
                "model": b["a_model"],
                "text": flatten_content(msg.get("content")),
                "is_sidechain": bool(b["isSidechain"]),
                "raw": raw_json,
            })
        if not messages:
            continue
        chat_db.replace_session(conn, {
            "tool": TOOL,
            "source_session_id": sess["session_id"],
            "source_path": str(STORE_DB),
            "project_path": sess["cwd"],
            "is_worktree": int(chat_db.is_worktree_path(sess["cwd"])),
            "provider": "anthropic",
            "model": model,
            "started_at": iso(sess["t0"]),
            "ended_at": iso(sess["t1"]),
            "cost": cost or None,
            "meta": {"legacy_store": True, "cli_version": sess["version"]},
        }, messages)
        count += 1
    src.close()
    return count


def ingest_history(conn) -> int:
    if not HISTORY.exists():
        return 0
    # Only fill dates before the earliest surviving full transcript.
    row = conn.execute(
        "SELECT MIN(started_at) FROM sessions WHERE tool = ? "
        "AND (meta IS NULL OR meta NOT LIKE '%prompt_only%') "
        "AND (meta IS NULL OR meta NOT LIKE '%legacy_store%')",
        (TOOL,),
    ).fetchone()
    cutoff = row[0] or "9999"

    groups = defaultdict(list)  # (project, date) -> entries
    for line in open(HISTORY, errors="replace"):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("timestamp")
        if not ts:
            continue
        when = iso(ts / 1000)
        if when >= cutoff:
            continue
        groups[(e.get("project") or "(unknown)", when[:10])].append((when, e))

    count = 0
    for (project, day), entries in sorted(groups.items()):
        entries.sort(key=lambda pair: pair[0])
        messages = [{
            "role": "user",
            "ts": when,
            "text": e.get("display", ""),
            "raw": json.dumps(e),
        } for when, e in entries]
        chat_db.replace_session(conn, {
            "tool": TOOL,
            "source_session_id": f"history-{day}-{project.replace('/', '-')}",
            "source_path": str(HISTORY),
            "project_path": None if project == "(unknown)" else project,
            "is_worktree": int(chat_db.is_worktree_path(project)),
            "title": f"(prompt-only) {day}",
            "provider": "anthropic",
            "started_at": entries[0][0],
            "ended_at": entries[-1][0],
            "meta": {"prompt_only": True},
        }, messages)
        count += 1
    return count


def main():
    conn = chat_db.connect()
    n_store = ingest_store(conn)
    n_hist = ingest_history(conn)
    chat_db.rebuild_fts(conn)
    conn.commit()
    print(f"legacy: {n_store} full sessions from __store.db, {n_hist} prompt-only day-sessions from history.jsonl")


if __name__ == "__main__":
    main()
