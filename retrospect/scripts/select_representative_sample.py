#!/usr/bin/env python3
"""Select a minimal stratified chat sample for model cost comparison.

The default strategy is intentionally small:
- 8 chats drawn from archive size buckets
- 1 median Anthropic chat, if present and not already selected
- 1 median Z.ai chat, if present and not already selected

This yields a 10-chat sample for pricing experiments that covers:
- short, medium, long, and outlier conversations
- at least some source diversity beyond the overwhelmingly OpenAI-heavy corpus
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
OUTPUT_DIR = RETROSPECT_ROOT / "data" / "samples"
DEFAULT_BUCKET_PERCENTILES = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.0]


@dataclass(frozen=True)
class ChatStats:
    path: Path
    source: str
    message_count: int
    byte_size: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a deterministic representative chat sample"
    )
    parser.add_argument("--seed", type=int, default=20260319)
    parser.add_argument(
        "--output-stem",
        default="model-cost-minimal-sample",
        help="Stem for the emitted JSON and TXT files under data/samples/",
    )
    return parser.parse_args()


def load_chat_stats() -> list[ChatStats]:
    stats = []
    for path in sorted(CHAT_DIR.glob("*.md")):
        doc = extract.parse_chat_document(path)
        stats.append(
            ChatStats(
                path=path,
                source=doc.source,
                message_count=doc.message_count,
                byte_size=path.stat().st_size,
            )
        )
    return stats


def percentile_rows(rows: list[ChatStats], fraction: float) -> int:
    return max(1, round(len(rows) * fraction))


def bucketize(rows: list[ChatStats]) -> list[list[ChatStats]]:
    sorted_rows = sorted(rows, key=lambda item: item.byte_size)
    buckets = []
    start = 0
    for fraction in DEFAULT_BUCKET_PERCENTILES:
        end = percentile_rows(sorted_rows, fraction)
        if end <= start:
            continue
        buckets.append(sorted_rows[start:end])
        start = end
    if start < len(sorted_rows):
        buckets.append(sorted_rows[start:])
    return [bucket for bucket in buckets if bucket]


def choose_core_sample(rows: list[ChatStats], seed: int) -> list[ChatStats]:
    rng = random.Random(seed)
    selected: list[ChatStats] = []
    seen: set[Path] = set()
    for bucket in bucketize(rows):
        choice = rng.choice(bucket)
        if choice.path not in seen:
            selected.append(choice)
            seen.add(choice.path)
    return selected


def choose_source_anchor(
    rows: list[ChatStats], source: str, already_selected: set[Path]
) -> ChatStats | None:
    candidates = [row for row in rows if row.source == source and row.path not in already_selected]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.byte_size)
    return candidates[len(candidates) // 2]


def build_manifest(sample: list[ChatStats], seed: int) -> dict[str, Any]:
    by_source = defaultdict(int)
    for row in sample:
        by_source[row.source] += 1

    return {
        "name": "minimal representative pricing sample",
        "created_at": extract.iso_now(),
        "seed": seed,
        "strategy": {
            "core": "1 deterministic random pick from each archive size bucket (10th, 25th, 50th, 75th, 90th, 95th, 99th, 100th percentiles)",
            "source_anchors": [
                "Add the median Anthropic chat if not already selected",
                "Add the median Z.ai chat if not already selected"
            ]
        },
        "sample_size": len(sample),
        "source_counts": dict(sorted(by_source.items())),
        "selected_chats": [
            {
                "relative_path": str(row.path.relative_to(RETROSPECT_ROOT)),
                "source": row.source,
                "message_count": row.message_count,
                "byte_size": row.byte_size,
            }
            for row in sorted(sample, key=lambda item: item.byte_size)
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
    rows = load_chat_stats()
    sample = choose_core_sample(rows, args.seed)
    selected_paths = {row.path for row in sample}

    for source in ("anthropic", "zai"):
        anchor = choose_source_anchor(rows, source, selected_paths)
        if anchor is not None:
            sample.append(anchor)
            selected_paths.add(anchor.path)

    manifest = build_manifest(sample, args.seed)
    json_path, txt_path = write_outputs(manifest, args.output_stem)

    print(f"Selected {manifest['sample_size']} chats")
    print(f"Source counts: {manifest['source_counts']}")
    print(f"JSON manifest: {json_path}")
    print(f"Chat list: {txt_path}")
    print("\nRun sample against a model with:")
    print(
        f"./.venv/bin/python scripts/extract.py --model <model-id> --chat-list-file {txt_path}"
    )


if __name__ == "__main__":
    main()
