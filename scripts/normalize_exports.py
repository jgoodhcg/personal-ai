#!/usr/bin/env python3
"""Normalize chat exports from ChatGPT, Claude, and z.ai into uniform markdown files.

Usage:
    python scripts/normalize_exports.py [--dry-run] [--limit N]

Reads from raw_exports/{openai,anthropic,zai}/
Writes to chats/ as individual markdown files with YAML frontmatter.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "raw_exports"
OUTPUT_DIR = PROJECT_ROOT / "chats"


def slugify(text: str, max_len: int = 60) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def format_message(role: str, content: str) -> str:
    label = role.capitalize()
    return f"## {label}\n\n{content.strip()}\n"


# --- OpenAI ---

def walk_openai_tree(mapping: dict, current_node: str) -> list[dict]:
    """Walk from root to current_node to get linear message list."""
    # Build path from current_node back to root
    path = []
    node_id = current_node
    while node_id:
        node = mapping.get(node_id)
        if not node:
            break
        path.append(node)
        node_id = node.get("parent")
    path.reverse()

    messages = []
    for node in path:
        msg = node.get("message")
        if not msg:
            continue
        role = msg.get("author", {}).get("role", "")
        if role not in ("user", "assistant"):
            continue
        content_obj = msg.get("content", {})
        if content_obj.get("content_type") != "text":
            continue
        parts = content_obj.get("parts", [])
        text_parts = [p for p in parts if isinstance(p, str) and p.strip()]
        if not text_parts:
            continue
        messages.append({"role": role, "content": "\n\n".join(text_parts)})
    return messages


def parse_openai(raw_dir: Path) -> list[dict]:
    conversations = []
    export_dirs = [d for d in raw_dir.iterdir() if d.is_dir()]
    for export_dir in export_dirs:
        for json_file in sorted(export_dir.glob("conversations-*.json")):
            with open(json_file) as f:
                data = json.load(f)
            for conv in data:
                conv_id = conv.get("conversation_id", conv.get("id", ""))
                title = conv.get("title", "Untitled")
                create_time = conv.get("create_time")
                mapping = conv.get("mapping", {})
                current_node = conv.get("current_node")

                if not mapping or not current_node:
                    continue

                messages = walk_openai_tree(mapping, current_node)
                if not messages:
                    continue

                dt = datetime.fromtimestamp(create_time, tz=timezone.utc) if create_time else None
                conversations.append({
                    "id": conv_id,
                    "source": "openai",
                    "title": title,
                    "date": dt.strftime("%Y-%m-%d") if dt else "unknown",
                    "message_count": len(messages),
                    "messages": messages,
                })
    return conversations


# --- Anthropic ---

def parse_anthropic(raw_dir: Path) -> list[dict]:
    conversations = []
    export_dirs = [d for d in raw_dir.iterdir() if d.is_dir()]
    for export_dir in export_dirs:
        conv_file = export_dir / "conversations.json"
        if not conv_file.exists():
            continue
        with open(conv_file) as f:
            data = json.load(f)
        for conv in data:
            conv_id = conv.get("uuid", "")
            title = conv.get("name", "Untitled")
            created = conv.get("created_at", "")
            chat_messages = conv.get("chat_messages", [])

            messages = []
            for msg in chat_messages:
                role = msg.get("sender", "")
                if role not in ("human", "assistant"):
                    continue
                text = msg.get("text", "")
                if not text.strip():
                    continue
                normalized_role = "user" if role == "human" else "assistant"
                messages.append({"role": normalized_role, "content": text})

            if not messages:
                continue

            dt = None
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    pass

            conversations.append({
                "id": conv_id,
                "source": "anthropic",
                "title": title,
                "date": dt.strftime("%Y-%m-%d") if dt else "unknown",
                "message_count": len(messages),
                "messages": messages,
            })
    return conversations


# --- z.ai ---

def walk_zai_tree(messages_dict: dict, current_id: str) -> list[dict]:
    """Walk from root to current_id to get linear message list."""
    path = []
    node_id = current_id
    while node_id:
        node = messages_dict.get(node_id)
        if not node:
            break
        path.append(node)
        node_id = node.get("parentId")
    path.reverse()

    messages = []
    for node in path:
        role = node.get("role", "")
        if role not in ("user", "assistant"):
            continue
        content = node.get("content", "")
        if not content or not content.strip():
            continue
        messages.append({"role": role, "content": content})
    return messages


def parse_zai(raw_dir: Path) -> list[dict]:
    conversations = []
    for json_file in raw_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = [data]
        for conv in data:
            conv_id = conv.get("id", "")
            title = conv.get("title", "Untitled")
            created = conv.get("created_at")
            chat = conv.get("chat", {})
            history = chat.get("history", {})
            messages_dict = history.get("messages", {})
            current_id = history.get("currentId")

            if not messages_dict or not current_id:
                continue

            messages = walk_zai_tree(messages_dict, current_id)
            if not messages:
                continue

            dt = None
            if isinstance(created, (int, float)):
                dt = datetime.fromtimestamp(created, tz=timezone.utc)
            elif isinstance(created, str):
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    pass

            conversations.append({
                "id": conv_id,
                "source": "zai",
                "title": title,
                "date": dt.strftime("%Y-%m-%d") if dt else "unknown",
                "message_count": len(messages),
                "messages": messages,
            })
    return conversations


# --- Output ---

def write_markdown(conv: dict, output_dir: Path) -> Path:
    slug = slugify(conv["title"])
    filename = f"{conv['id']}_{conv['source']}_{conv['date']}_{slug}.md"
    filepath = output_dir / filename

    frontmatter = (
        f"---\n"
        f"id: \"{conv['id']}\"\n"
        f"source: {conv['source']}\n"
        f"date: {conv['date']}\n"
        f"title: \"{conv['title']}\"\n"
        f"message_count: {conv['message_count']}\n"
        f"---\n\n"
    )

    body = "\n\n".join(
        format_message(m["role"], m["content"]) for m in conv["messages"]
    )

    filepath.write_text(frontmatter + body, encoding="utf-8")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Normalize chat exports")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    parser.add_argument("--limit", type=int, default=0, help="Limit total conversations processed")
    args = parser.parse_args()

    parsers = {
        "openai": (RAW_DIR / "openai", parse_openai),
        "anthropic": (RAW_DIR / "anthropic", parse_anthropic),
        "zai": (RAW_DIR / "zai", parse_zai),
    }

    all_conversations = []
    for source, (raw_dir, parse_fn) in parsers.items():
        if not raw_dir.exists():
            print(f"Skipping {source}: {raw_dir} not found")
            continue
        convs = parse_fn(raw_dir)
        print(f"{source}: {len(convs)} conversations")
        all_conversations.extend(convs)

    if args.limit:
        all_conversations = all_conversations[:args.limit]

    print(f"\nTotal: {len(all_conversations)} conversations")

    if args.dry_run:
        print("Dry run — no files written")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for conv in all_conversations:
        write_markdown(conv, OUTPUT_DIR)
        written += 1

    print(f"Wrote {written} files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
