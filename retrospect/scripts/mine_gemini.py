#!/usr/bin/env python3
"""Ingest Gemini CLI chats (~/.gemini/tmp/<project-hash>/chats/session-*.json)
into agent_chats.db.

Project paths are recovered by sha256-hashing known project dirs from
~/.gemini/projects.json. Incremental by file mtime+size.
Run: python3 retrospect/scripts/mine_gemini.py
"""

import hashlib
import json
from pathlib import Path

import chat_db

TOOL = "gemini"
ROOT = Path.home() / ".gemini" / "tmp"
PROJECTS_FILE = Path.home() / ".gemini" / "projects.json"

ROLE_MAP = {"user": "user", "gemini": "assistant", "info": "system", "error": "system"}


def hash_to_path_map() -> dict[str, str]:
    mapping = {}
    try:
        projects = json.loads(PROJECTS_FILE.read_text()).get("projects", {})
    except (OSError, json.JSONDecodeError):
        return mapping
    for path in projects:
        mapping[hashlib.sha256(path.encode()).hexdigest()] = path
    return mapping


def ingest_file(conn, path: Path, project_path: str | None) -> None:
    try:
        data = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        return
    raw_msgs = data.get("messages") or []
    messages = []
    for m in raw_msgs:
        mtype = m.get("type", "info")
        text = m.get("content", "")
        if not isinstance(text, str):
            text = "\n".join(
                b.get("text", json.dumps(b)) if isinstance(b, dict) else str(b)
                for b in (text if isinstance(text, list) else [text])
            )
        if m.get("thoughts"):
            thoughts = "\n".join(
                f"[thinking] {t.get('subject', '')}: {t.get('description', '')}"
                for t in m["thoughts"] if isinstance(t, dict)
            )
            text = f"{thoughts}\n{text}" if text else thoughts
        messages.append({
            "role": ROLE_MAP.get(mtype, "system"),
            "ts": m.get("timestamp"),
            "model": m.get("model"),
            "text": text,
            "is_meta": mtype not in ("user", "gemini"),
            "raw": json.dumps(m),
        })
    if not messages:
        return
    chat_db.replace_session(conn, {
        "tool": TOOL,
        "source_session_id": data.get("sessionId") or path.stem,
        "source_path": str(path),
        "project_path": project_path,
        "is_worktree": int(chat_db.is_worktree_path(project_path)),
        "provider": "google",
        "model": next((m.get("model") for m in raw_msgs if m.get("model")), None),
        "started_at": data.get("startTime"),
        "ended_at": data.get("lastUpdated"),
        "meta": {"project_hash": data.get("projectHash")},
    }, messages)


def main():
    conn = chat_db.connect()
    hashes = hash_to_path_map()
    ingested = skipped = 0
    for path in sorted(ROOT.glob("*/chats/session-*.json")):
        if chat_db.file_unchanged(conn, TOOL, path):
            skipped += 1
            continue
        ingest_file(conn, path, hashes.get(path.parent.parent.name))
        chat_db.mark_ingested(conn, TOOL, path)
        ingested += 1
    chat_db.finish(conn, TOOL, ingested, skipped)


if __name__ == "__main__":
    main()
