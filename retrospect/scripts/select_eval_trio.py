#!/usr/bin/env python3
"""Select a fixed small/medium/large trio for empirical model comparison runs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
OUTPUT_DIR = RETROSPECT_ROOT / "data" / "samples"
TARGETS = [
    ("small", 0.25),
    ("medium", 0.50),
    ("large", 0.95),
]
CURATED_OVERRIDES = {
    # The small slot is intentionally curated rather than purely percentile-picked.
    # This keeps the trio more useful for evaluating Pass 3 / Pass 4 quality.
    "small": "data/chats/c55158a3-8f2a-4bf6-9472-1cb92eff3178_openai_2024-02-29_artificial-soul-challenging-views.md",
}


@dataclass(frozen=True)
class ChatStats:
    path: Path
    source: str
    title: str
    message_count: int
    byte_size: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select a deterministic eval trio")
    parser.add_argument(
        "--output-stem",
        default="model-eval-trio",
        help="Stem for the emitted trio manifest and chat list",
    )
    return parser.parse_args()


def load_rows() -> list[ChatStats]:
    rows = []
    for path in sorted(CHAT_DIR.glob("*.md")):
        doc = extract.parse_chat_document(path)
        rows.append(
            ChatStats(
                path=path,
                source=doc.source,
                title=doc.title,
                message_count=doc.message_count,
                byte_size=path.stat().st_size,
            )
        )
    return rows


def pick_closest(rows: list[ChatStats], fraction: float, used: set[Path]) -> ChatStats:
    sorted_rows = sorted(rows, key=lambda item: item.byte_size)
    target_index = min(len(sorted_rows) - 1, max(0, round((len(sorted_rows) - 1) * fraction)))
    candidates = sorted(
        (row for row in sorted_rows if row.path not in used),
        key=lambda row: abs(sorted_rows.index(row) - target_index),
    )
    if not candidates:
        raise ValueError("No remaining chats available for trio selection")
    return candidates[0]


def build_manifest(selected: list[tuple[str, ChatStats]]) -> dict[str, Any]:
    return {
        "name": "empirical model comparison trio",
        "created_at": extract.iso_now(),
        "strategy": {
            "small": "chat closest to the 25th percentile by byte size",
            "medium": "chat closest to the 50th percentile by byte size",
            "large": "chat closest to the 95th percentile by byte size"
        },
        "selected_chats": [
            {
                "label": label,
                "relative_path": str(row.path.relative_to(RETROSPECT_ROOT)),
                "source": row.source,
                "title": row.title,
                "message_count": row.message_count,
                "byte_size": row.byte_size,
            }
            for label, row in selected
        ],
    }


def write_outputs(manifest: dict[str, Any], output_stem: str) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / f"{output_stem}.json"
    txt_path = OUTPUT_DIR / f"{output_stem}.txt"
    json_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    txt_path.write_text(
        "\n".join(item["relative_path"] for item in manifest["selected_chats"]) + "\n",
        encoding="utf-8",
    )
    return json_path, txt_path


def main() -> None:
    args = parse_args()
    rows = load_rows()
    row_by_path = {str(row.path.relative_to(RETROSPECT_ROOT)): row for row in rows}
    used: set[Path] = set()
    selected: list[tuple[str, ChatStats]] = []

    for label, fraction in TARGETS:
        override = CURATED_OVERRIDES.get(label)
        if override:
            row = row_by_path[override]
        else:
            row = pick_closest(rows, fraction, used)
        selected.append((label, row))
        used.add(row.path)

    manifest = build_manifest(selected)
    json_path, txt_path = write_outputs(manifest, args.output_stem)

    print(f"JSON manifest: {json_path}")
    print(f"Chat list: {txt_path}")
    for item in manifest["selected_chats"]:
        print(
            f"{item['label']:>6}  {item['byte_size']:>7} bytes  {item['source']:<10}  {item['relative_path']}"
        )


if __name__ == "__main__":
    main()
