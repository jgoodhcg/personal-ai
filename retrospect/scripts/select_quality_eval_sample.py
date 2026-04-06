#!/usr/bin/env python3
"""Select deterministic quality-evaluation samples for archive extraction review."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
OUTPUT_DIR = RETROSPECT_ROOT / "data" / "samples"
CONFIDENCE_LEVEL = 0.95
Z_95 = 1.96


@dataclass(frozen=True)
class ChatRow:
    path: Path
    source: str
    year: str
    message_count: int
    byte_size: int
    size_bucket: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select deterministic quality-evaluation samples."
    )
    parser.add_argument("--seed", type=int, default=20260328)
    parser.add_argument("--main-size", type=int, default=200)
    parser.add_argument("--compare-size", type=int, default=25)
    parser.add_argument("--human-size", type=int, default=5)
    parser.add_argument(
        "--output-stem",
        default="quality-eval",
        help="Stem for emitted manifests under data/samples/",
    )
    return parser.parse_args()


def load_docs() -> list[tuple[Path, extract.ChatDocument]]:
    rows = []
    for path in sorted(CHAT_DIR.glob("*.md")):
        rows.append((path, extract.parse_chat_document(path)))
    return rows


def quantile_thresholds(values: list[int], fractions: list[float]) -> list[int]:
    sorted_values = sorted(values)
    thresholds = []
    for fraction in fractions:
        index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * fraction)))
        thresholds.append(sorted_values[index])
    return thresholds


def classify_size(byte_size: int, thresholds: list[int]) -> str:
    labels = ("small", "medium", "large", "xlarge")
    for index, threshold in enumerate(thresholds):
        if byte_size <= threshold:
            return labels[index]
    return labels[-1]


def build_rows() -> list[ChatRow]:
    docs = load_docs()
    thresholds = quantile_thresholds(
        [path.stat().st_size for path, _doc in docs],
        [0.25, 0.50, 0.75, 1.0],
    )
    rows = []
    for path, doc in docs:
        year = doc.date[:4] if len(doc.date) >= 4 and doc.date[:4].isdigit() else "unknown"
        byte_size = path.stat().st_size
        rows.append(
            ChatRow(
                path=path,
                source=doc.source,
                year=year,
                message_count=doc.message_count,
                byte_size=byte_size,
                size_bucket=classify_size(byte_size, thresholds),
            )
        )
    return rows


def proportional_allocation(group_sizes: dict[str, int], sample_size: int) -> dict[str, int]:
    total = sum(group_sizes.values())
    if sample_size <= 0 or total <= 0:
        return {key: 0 for key in group_sizes}
    if sample_size >= total:
        return dict(group_sizes)

    allocation = {key: 0 for key in group_sizes}
    remainders: list[tuple[float, str]] = []
    assigned = 0

    for key, count in group_sizes.items():
        ideal = (count / total) * sample_size
        base = min(count, math.floor(ideal))
        allocation[key] = base
        assigned += base
        remainders.append((ideal - base, key))

    remaining = sample_size - assigned
    for _fraction, key in sorted(remainders, reverse=True):
        if remaining <= 0:
            break
        if allocation[key] >= group_sizes[key]:
            continue
        allocation[key] += 1
        remaining -= 1

    if remaining > 0:
        for key in sorted(group_sizes):
            if remaining <= 0:
                break
            spare = group_sizes[key] - allocation[key]
            if spare <= 0:
                continue
            take = min(spare, remaining)
            allocation[key] += take
            remaining -= take

    return allocation


def group_key(row: ChatRow) -> str:
    return f"{row.source}|{row.year}|{row.size_bucket}"


def stratified_sample(rows: list[ChatRow], sample_size: int, seed: int) -> list[ChatRow]:
    if sample_size <= 0:
        return []
    if sample_size >= len(rows):
        return sorted(rows, key=lambda item: item.path.name)

    grouped: dict[str, list[ChatRow]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)

    group_sizes = {key: len(items) for key, items in grouped.items()}
    allocation = proportional_allocation(group_sizes, sample_size)
    rng = random.Random(seed)
    selected: list[ChatRow] = []

    for key, count in sorted(allocation.items()):
        if count <= 0:
            continue
        picks = rng.sample(grouped[key], count)
        selected.extend(picks)

    selected.sort(key=lambda item: item.path.name)
    return selected


def margin_of_error_percent(population_size: int, sample_size: int) -> float | None:
    if sample_size <= 0 or population_size <= 1:
        return None
    p = 0.5
    base = math.sqrt((p * (1 - p)) / sample_size)
    finite_correction = math.sqrt((population_size - sample_size) / (population_size - 1))
    return Z_95 * base * finite_correction * 100


def sample_stats(rows: list[ChatRow]) -> dict[str, Any]:
    source_counts = Counter(row.source for row in rows)
    year_counts = Counter(row.year for row in rows)
    bucket_counts = Counter(row.size_bucket for row in rows)
    return {
        "source_counts": dict(sorted(source_counts.items())),
        "year_counts": dict(sorted(year_counts.items())),
        "size_bucket_counts": dict(sorted(bucket_counts.items())),
    }


def build_manifest(
    *,
    name: str,
    rows: list[ChatRow],
    parent_name: str | None,
    seed: int,
    population_size: int,
) -> dict[str, Any]:
    return {
        "name": name,
        "created_at": extract.iso_now(),
        "seed": seed,
        "parent_sample": parent_name,
        "confidence_level": CONFIDENCE_LEVEL,
        "worst_case_margin_of_error_percent": margin_of_error_percent(population_size, len(rows)),
        "strategy": {
            "selection": "proportional stratified random sample",
            "strata": ["source", "year", "size_bucket"],
            "size_bucket_basis": "global byte-size quartiles of normalized chats"
        },
        "sample_size": len(rows),
        "population_size": population_size,
        "stats": sample_stats(rows),
        "selected_chats": [
            {
                "relative_path": str(row.path.relative_to(RETROSPECT_ROOT)),
                "source": row.source,
                "year": row.year,
                "message_count": row.message_count,
                "byte_size": row.byte_size,
                "size_bucket": row.size_bucket,
            }
            for row in rows
        ],
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_chat_list(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        "\n".join(item["relative_path"] for item in manifest["selected_chats"]) + "\n",
        encoding="utf-8",
    )


def emit_sample(output_stem: str, suffix: str, manifest: dict[str, Any]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / f"{output_stem}-{suffix}.json"
    txt_path = OUTPUT_DIR / f"{output_stem}-{suffix}.txt"
    write_manifest(json_path, manifest)
    write_chat_list(txt_path, manifest)
    return json_path, txt_path


def print_manifest_summary(label: str, manifest: dict[str, Any], json_path: Path, txt_path: Path) -> None:
    margin = manifest["worst_case_margin_of_error_percent"]
    margin_text = f"{margin:.1f}%" if isinstance(margin, float) else "n/a"
    print(
        f"{label}: size={manifest['sample_size']} "
        f"confidence={manifest['confidence_level']:.0%} "
        f"worst_case_margin={margin_text}"
    )
    print(f"  json: {json_path}")
    print(f"  list: {txt_path}")
    print(f"  strata: {manifest['stats']}")


def main() -> None:
    args = parse_args()
    if args.compare_size > args.main_size:
        raise SystemExit("--compare-size cannot exceed --main-size")
    if args.human_size > args.compare_size:
        raise SystemExit("--human-size cannot exceed --compare-size")

    rows = build_rows()
    main_rows = stratified_sample(rows, args.main_size, args.seed)
    compare_rows = stratified_sample(main_rows, args.compare_size, args.seed + 1)
    human_rows = stratified_sample(compare_rows, args.human_size, args.seed + 2)

    main_manifest = build_manifest(
        name="quality evaluation main sample",
        rows=main_rows,
        parent_name=None,
        seed=args.seed,
        population_size=len(rows),
    )
    compare_manifest = build_manifest(
        name="quality evaluation multi-model subset",
        rows=compare_rows,
        parent_name=main_manifest["name"],
        seed=args.seed + 1,
        population_size=len(rows),
    )
    human_manifest = build_manifest(
        name="quality evaluation human-review subset",
        rows=human_rows,
        parent_name=compare_manifest["name"],
        seed=args.seed + 2,
        population_size=len(rows),
    )

    main_json, main_txt = emit_sample(args.output_stem, f"main-{args.main_size}", main_manifest)
    compare_json, compare_txt = emit_sample(
        args.output_stem,
        f"compare-{args.compare_size}",
        compare_manifest,
    )
    human_json, human_txt = emit_sample(
        args.output_stem,
        f"human-{args.human_size}",
        human_manifest,
    )

    print_manifest_summary("Main", main_manifest, main_json, main_txt)
    print_manifest_summary("Compare", compare_manifest, compare_json, compare_txt)
    print_manifest_summary("Human", human_manifest, human_json, human_txt)


if __name__ == "__main__":
    main()
