#!/usr/bin/env python3
"""Run retrospect extraction passes 1-3 over all chats or a random sample.

Usage (from retrospect/):
    ./.venv/bin/python scripts/run_passes_1_to_3.py --model openai/gpt-5.4-nano
    ./.venv/bin/python scripts/run_passes_1_to_3.py --model openai/gpt-5.4-nano --sample-size 25
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
SAMPLE_DIR = RETROSPECT_ROOT / "data" / "samples"
PASS_IDS = ("pass1_summary", "pass2_projects", "pass3_people")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run retrospect extraction passes 1-3 across all chats or a random sample."
    )
    parser.add_argument(
        "--model",
        required=True,
        help="OpenRouter model slug to use. This must always be provided explicitly.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=0,
        help="Optional random sample size. Omit to run all chats.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260320,
        help="Seed for deterministic random sampling when --sample-size is used.",
    )
    parser.add_argument(
        "--sample-output-stem",
        default=None,
        help="Optional stem for emitted sample manifest/list under data/samples/.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Request concurrency forwarded to extract.py.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Per-request timeout forwarded to extract.py.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retry count forwarded to extract.py.",
    )
    parser.add_argument(
        "--reasoning-policy",
        choices=["disable", "exclude", "allow"],
        default="disable",
        help="Reasoning policy forwarded to extract.py.",
    )
    parser.add_argument(
        "--provider-data-collection",
        choices=["allow", "deny"],
        default=None,
        help="Optional provider routing preference forwarded to extract.py.",
    )
    parser.add_argument(
        "--zdr-only",
        action="store_true",
        help="Restrict to ZDR endpoints if available.",
    )
    parser.add_argument(
        "--provider-sort",
        choices=["price", "throughput"],
        default=None,
        help="Optional provider sort forwarded to extract.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Forward dry-run to extract.py.",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Force new outputs even if prior files already exist.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Forward debug output to extract.py.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Forward verbose output to extract.py.",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Color mode forwarded to extract.py.",
    )
    parser.add_argument(
        "--display",
        choices=["auto", "tui", "plain"],
        default="auto",
        help="Display mode forwarded to extract.py.",
    )
    return parser.parse_args()


def select_chat_paths(sample_size: int, seed: int) -> list[Path]:
    chats = sorted(CHAT_DIR.glob("*.md"))
    if sample_size <= 0:
        return chats
    if sample_size > len(chats):
        raise SystemExit(f"--sample-size {sample_size} exceeds archive size {len(chats)}")
    rng = random.Random(seed)
    return sorted(rng.sample(chats, sample_size))


def write_sample_outputs(selected: list[Path], sample_size: int, seed: int, stem: str | None) -> tuple[Path, Path]:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    output_stem = stem or f"passes-1-3-sample-{sample_size}-{seed}"
    json_path = SAMPLE_DIR / f"{output_stem}.json"
    txt_path = SAMPLE_DIR / f"{output_stem}.txt"
    manifest: dict[str, Any] = {
        "name": "passes 1-3 random sample",
        "created_at": extract.iso_now(),
        "seed": seed,
        "sample_size": sample_size,
        "selected_chats": [
            {"relative_path": str(path.relative_to(RETROSPECT_ROOT))}
            for path in selected
        ],
    }
    json_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    txt_path.write_text(
        "\n".join(str(path.relative_to(RETROSPECT_ROOT)) for path in selected) + "\n",
        encoding="utf-8",
    )
    return json_path, txt_path


def build_command(args: argparse.Namespace, chat_list_file: Path | None) -> list[str]:
    command = [
        sys.executable,
        str(RETROSPECT_ROOT / "scripts" / "extract.py"),
        "--model",
        args.model,
        "--concurrency",
        str(args.concurrency),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--max-retries",
        str(args.max_retries),
        "--reasoning-policy",
        args.reasoning_policy,
        "--color",
        args.color,
        "--display",
        args.display,
    ]
    for pass_id in PASS_IDS:
        command.extend(["--pass", pass_id])
    if chat_list_file is not None:
        command.extend(["--chat-list-file", str(chat_list_file)])
    if args.provider_data_collection:
        command.extend(["--provider-data-collection", args.provider_data_collection])
    if args.zdr_only:
        command.append("--zdr-only")
    if args.provider_sort:
        command.extend(["--provider-sort", args.provider_sort])
    if args.dry_run:
        command.append("--dry-run")
    if args.rerun:
        command.append("--rerun")
    if args.debug:
        command.append("--debug")
    if args.verbose:
        command.append("--verbose")
    return command


def main() -> None:
    args = parse_args()
    selected = select_chat_paths(args.sample_size, args.seed)
    chat_list_file: Path | None = None

    if args.sample_size > 0:
        manifest_path, chat_list_file = write_sample_outputs(
            selected,
            args.sample_size,
            args.seed,
            args.sample_output_stem,
        )
        print(f"Selected random sample of {len(selected)} chats", flush=True)
        print(f"Sample manifest: {manifest_path}", flush=True)
        print(f"Sample chat list: {chat_list_file}", flush=True)
    else:
        print(f"Selected full archive: {len(selected)} chats", flush=True)

    command = build_command(args, chat_list_file)
    print("Running Passes 1-3 with:", flush=True)
    print("$", " ".join(command), flush=True)
    raise SystemExit(subprocess.run(command, cwd=RETROSPECT_ROOT).returncode)


if __name__ == "__main__":
    main()
