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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
SAMPLE_DIR = RETROSPECT_ROOT / "data" / "samples"
RUNS_DIR = RETROSPECT_ROOT / "data" / "extractions" / "_runs"
ROLLOUT_DIR = RETROSPECT_ROOT / "data" / "extractions" / "_rollouts"
PASS_IDS = ("pass1_summary", "pass2_projects", "pass3_people")
DATE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})_")


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
        "--chunk-size",
        type=int,
        default=10,
        help="Number of chats per chronological chunk. Use 0 to disable chunking.",
    )
    parser.add_argument(
        "--start-chunk",
        type=int,
        default=1,
        help="1-based chunk number to start from when resuming a rollout.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Optional maximum number of chunks to execute in this invocation.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
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
        "--validation-mode",
        choices=["strict", "warn"],
        default="warn",
        help="Validation handling forwarded to extract.py. Defaults to warn for archive rollouts.",
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


def chat_sort_key(path: Path) -> tuple[str, str]:
    match = DATE_RE.search(path.name)
    date_value = match.group(1) if match else "9999-99-99"
    return date_value, path.name


def select_chat_paths(sample_size: int, seed: int) -> list[Path]:
    chats = sorted(CHAT_DIR.glob("*.md"), key=chat_sort_key)
    if sample_size <= 0:
        return chats
    if sample_size > len(chats):
        raise SystemExit(f"--sample-size {sample_size} exceeds archive size {len(chats)}")
    rng = random.Random(seed)
    return sorted(rng.sample(chats, sample_size), key=chat_sort_key)


def chunk_paths(paths: list[Path], chunk_size: int) -> list[list[Path]]:
    if chunk_size <= 0:
        return [paths]
    return [paths[index : index + chunk_size] for index in range(0, len(paths), chunk_size)]


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
        "--validation-mode",
        args.validation_mode,
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


def current_run_manifest_paths() -> set[Path]:
    return {path.resolve() for path in RUNS_DIR.glob("*/manifest.json")}


def newest_added_manifest(before: set[Path]) -> Path | None:
    added = [path for path in current_run_manifest_paths() if path not in before]
    if not added:
        return None
    return max(added, key=lambda path: path.stat().st_mtime)


def write_chunk_chat_list(rollout_path: Path, chunk_index: int, chunk_paths: list[Path]) -> Path:
    chunk_dir = rollout_path / "chunk_lists"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    path = chunk_dir / f"chunk-{chunk_index:04d}.txt"
    path.write_text(
        "\n".join(str(chat_path.relative_to(RETROSPECT_ROOT)) for chat_path in chunk_paths) + "\n",
        encoding="utf-8",
    )
    return path


def write_rollout_manifest(rollout_path: Path, manifest: dict[str, Any]) -> tuple[Path, Path]:
    rollout_path.mkdir(parents=True, exist_ok=True)
    manifest_path = rollout_path / "rollout_manifest.json"
    rerun_path = rollout_path / "failed_chats.txt"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed_paths = sorted({item["relative_path"] for item in manifest["failed_chats"]})
    rerun_path.write_text("\n".join(failed_paths) + ("\n" if failed_paths else ""), encoding="utf-8")
    return manifest_path, rerun_path


def main() -> None:
    args = parse_args()
    selected = select_chat_paths(args.sample_size, args.seed)
    if args.start_chunk < 1:
        raise SystemExit("--start-chunk must be at least 1")

    rollout_id = f"passes-1-3__{extract.slugify(args.model)}__{extract.compact_timestamp()}"
    rollout_path = ROLLOUT_DIR / rollout_id
    rollout_path.mkdir(parents=True, exist_ok=True)

    sample_manifest_path: Path | None = None
    sample_chat_list_path: Path | None = None
    if args.sample_size > 0:
        sample_manifest_path, sample_chat_list_path = write_sample_outputs(
            selected,
            args.sample_size,
            args.seed,
            args.sample_output_stem,
        )
        print(f"Selected random sample of {len(selected)} chats", flush=True)
        print(f"Sample manifest: {sample_manifest_path}", flush=True)
        print(f"Sample chat list: {sample_chat_list_path}", flush=True)
    else:
        print(f"Selected full archive: {len(selected)} chats", flush=True)

    chunks = chunk_paths(selected, args.chunk_size)
    if args.start_chunk > len(chunks):
        raise SystemExit(f"--start-chunk {args.start_chunk} exceeds total chunks {len(chunks)}")
    start_index = args.start_chunk - 1
    end_index = len(chunks) if args.max_chunks <= 0 else min(len(chunks), start_index + args.max_chunks)

    print(
        f"Running Passes 1-3 in {end_index - start_index} chunk(s) "
        f"of up to {args.chunk_size or len(selected)} chats",
        flush=True,
    )
    print(f"Rollout directory: {rollout_path}", flush=True)

    overall_exit_code = 0
    failed_chats: list[dict[str, Any]] = []
    chunk_records: list[dict[str, Any]] = []

    for chunk_number in range(start_index, end_index):
        chunk_paths_list = chunks[chunk_number]
        chunk_index = chunk_number + 1
        chat_list_file = write_chunk_chat_list(rollout_path, chunk_index, chunk_paths_list)
        command = build_command(args, chat_list_file)
        print(
            f"\n== Chunk {chunk_index}/{len(chunks)} :: {len(chunk_paths_list)} chats :: "
            f"{chunk_paths_list[0].name} -> {chunk_paths_list[-1].name} ==",
            flush=True,
        )
        before = current_run_manifest_paths()
        returncode = subprocess.run(command, cwd=RETROSPECT_ROOT).returncode
        after_manifest = newest_added_manifest(before)
        run_manifest = (
            json.loads(after_manifest.read_text(encoding="utf-8"))
            if after_manifest and after_manifest.exists()
            else None
        )
        chunk_record: dict[str, Any] = {
            "chunk_index": chunk_index,
            "chat_count": len(chunk_paths_list),
            "chat_list_file": str(chat_list_file),
            "return_code": returncode,
            "first_chat": chunk_paths_list[0].name,
            "last_chat": chunk_paths_list[-1].name,
            "run_manifest_path": str(after_manifest) if after_manifest else None,
            "status_counts": run_manifest.get("status_counts") if run_manifest else None,
            "reported_cost_total": run_manifest.get("reported_cost_total") if run_manifest else None,
            "duration_seconds": run_manifest.get("duration_seconds") if run_manifest else None,
        }
        chunk_records.append(chunk_record)
        if run_manifest:
            failed_sources = {item["source_file"] for item in run_manifest.get("failures", [])}
            warned_sources = {item["source_file"] for item in run_manifest.get("warnings", [])}
            for chat_path in chunk_paths_list:
                if chat_path.name in failed_sources or chat_path.name in warned_sources:
                    failed_chats.append(
                        {
                            "relative_path": str(chat_path.relative_to(RETROSPECT_ROOT)),
                            "chunk_index": chunk_index,
                            "status": "failed" if chat_path.name in failed_sources else "warning",
                        }
                    )
        if returncode != 0:
            overall_exit_code = 1

    rollout_manifest = {
        "rollout_id": rollout_id,
        "created_at": extract.iso_now(),
        "model": args.model,
        "selected_passes": list(PASS_IDS),
        "mode": "sample" if args.sample_size > 0 else "full_archive",
        "sample_size": args.sample_size or None,
        "seed": args.seed if args.sample_size > 0 else None,
        "sample_manifest_path": str(sample_manifest_path) if sample_manifest_path else None,
        "sample_chat_list_path": str(sample_chat_list_path) if sample_chat_list_path else None,
        "chat_count": len(selected),
        "chunk_size": args.chunk_size,
        "start_chunk": args.start_chunk,
        "max_chunks": args.max_chunks or None,
        "concurrency": args.concurrency,
        "timeout_seconds": args.timeout_seconds,
        "max_retries": args.max_retries,
        "reasoning_policy": args.reasoning_policy,
        "validation_mode": args.validation_mode,
        "chunk_count_total": len(chunks),
        "chunk_count_executed": len(chunk_records),
        "chunks": chunk_records,
        "failed_chats": failed_chats,
    }
    rollout_manifest_path, rerun_path = write_rollout_manifest(rollout_path, rollout_manifest)
    print("\n== Rollout Summary ==", flush=True)
    print(f"Chunks executed: {len(chunk_records)}", flush=True)
    print(f"Failed/warned chats: {len(failed_chats)}", flush=True)
    print(f"Rollout manifest: {rollout_manifest_path}", flush=True)
    print(f"Rerun list: {rerun_path}", flush=True)
    raise SystemExit(overall_exit_code)


if __name__ == "__main__":
    main()
