"""Shared schema and helpers for the agent-chat SQLite database.

One unified schema for all CLI agent chats (Claude Code, Codex, OpenCode,
Gemini). Each mine_<tool>.py script upserts sessions/messages here.
DB lives at retrospect/data/agent_chats.db (gitignored).
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_chats.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    tool TEXT NOT NULL,               -- claude-code | codex | opencode | gemini
    source_session_id TEXT NOT NULL,  -- native session id
    source_path TEXT,                 -- originating file (null for opencode rows)
    project_path TEXT,
    is_worktree INTEGER DEFAULT 0,
    git_branch TEXT,
    title TEXT,
    provider TEXT,                    -- anthropic | openai | google | ...
    model TEXT,                       -- last/primary model seen
    started_at TEXT,                  -- ISO8601 UTC
    ended_at TEXT,
    message_count INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_reasoning INTEGER,
    tokens_cache_read INTEGER,
    tokens_cache_write INTEGER,
    cost REAL,
    meta TEXT,                        -- JSON extras (cli version, source timestamps, ...)
    UNIQUE(tool, source_session_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    role TEXT NOT NULL,               -- user | assistant | tool | system
    ts TEXT,
    model TEXT,
    text TEXT,
    is_meta INTEGER DEFAULT 0,        -- injected instructions, caveats, info lines
    is_sidechain INTEGER DEFAULT 0,   -- subagent traffic (claude-code)
    raw TEXT,                         -- original record, verbatim JSON
    UNIQUE(session_id, idx)
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tool ON sessions(tool);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);

CREATE TABLE IF NOT EXISTS ingested_files (
    tool TEXT NOT NULL,
    path TEXT NOT NULL,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL,
    PRIMARY KEY (tool, path)
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text, content='messages', content_rowid='id'
);
"""

SESSION_COLUMNS = [
    "tool", "source_session_id", "source_path", "project_path", "is_worktree",
    "git_branch", "title", "provider", "model", "started_at", "ended_at",
    "message_count", "tokens_input", "tokens_output", "tokens_reasoning",
    "tokens_cache_read", "tokens_cache_write", "cost", "meta",
]


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def is_worktree_path(path: str | None) -> bool:
    return bool(path) and "worktree" in path.lower()


def file_unchanged(conn, tool: str, path: Path) -> bool:
    st = path.stat()
    row = conn.execute(
        "SELECT mtime, size FROM ingested_files WHERE tool = ? AND path = ?",
        (tool, str(path)),
    ).fetchone()
    return row is not None and row[0] == st.st_mtime and row[1] == st.st_size


def mark_ingested(conn, tool: str, path: Path) -> None:
    st = path.stat()
    conn.execute(
        "INSERT OR REPLACE INTO ingested_files (tool, path, mtime, size) VALUES (?, ?, ?, ?)",
        (tool, str(path), st.st_mtime, st.st_size),
    )


def replace_session(conn, session: dict, messages: list[dict]) -> None:
    """Insert or fully replace one session and its messages.

    session: dict keyed by SESSION_COLUMNS (missing keys become NULL).
    messages: dicts with role/ts/model/text/is_meta/is_sidechain/raw; idx is
    assigned by list order.
    """
    old = conn.execute(
        "SELECT id FROM sessions WHERE tool = ? AND source_session_id = ?",
        (session["tool"], session["source_session_id"]),
    ).fetchone()
    if old:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (old[0],))
        conn.execute("DELETE FROM sessions WHERE id = ?", (old[0],))

    session = dict(session, message_count=len(messages))
    if isinstance(session.get("meta"), (dict, list)):
        session["meta"] = json.dumps(session["meta"])
    cols = ", ".join(SESSION_COLUMNS)
    placeholders = ", ".join("?" for _ in SESSION_COLUMNS)
    cur = conn.execute(
        f"INSERT INTO sessions ({cols}) VALUES ({placeholders})",
        [session.get(c) for c in SESSION_COLUMNS],
    )
    sid = cur.lastrowid
    conn.executemany(
        "INSERT INTO messages (session_id, idx, role, ts, model, text, is_meta, is_sidechain, raw)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                sid, i, m.get("role", "system"), m.get("ts"), m.get("model"),
                m.get("text"), int(bool(m.get("is_meta"))),
                int(bool(m.get("is_sidechain"))), m.get("raw"),
            )
            for i, m in enumerate(messages)
        ],
    )


def rebuild_fts(conn) -> None:
    conn.execute("INSERT INTO messages_fts(messages_fts) VALUES ('rebuild')")


def finish(conn, tool: str, ingested: int, skipped: int) -> None:
    rebuild_fts(conn)
    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*), SUM(message_count) FROM sessions WHERE tool = ?", (tool,)
    ).fetchone()
    print(
        f"{tool}: ingested {ingested} session(s), skipped {skipped} unchanged; "
        f"db now has {total[0]} sessions / {total[1] or 0} messages for this tool"
    )
