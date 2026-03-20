#!/usr/bin/env python3
"""Run a fixed chat sample across a model panel and emit review templates."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any

import extract
import validate_extraction


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = RETROSPECT_ROOT / "config" / "model_catalog.json"
SAMPLE_DIR = RETROSPECT_ROOT / "data" / "samples"
EVAL_DIR = RETROSPECT_ROOT / "data" / "evaluations"
GROUP_ORDER = ("extra_small", "smaller", "flagship", "wildcard")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
TASK_START_RE = re.compile(r"^→\s+(\w+)\s+(.*)$")
TASK_RESULT_RE = re.compile(r"^([✓✗↷·])\s+(\d{2})/(\d{2})\s+(\w+)(?:\s+(.*?))?\s+(\d+(?:\.\d+)?)s$")
SUMMARY_VALUE_RE = re.compile(r"^([A-Za-z][A-Za-z ]+):\s+(.*)$")
SPINNER_FRAMES = ("|", "/", "-", "\\")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a model panel on a fixed chat list")
    parser.add_argument(
        "--sample-manifest",
        default=str(SAMPLE_DIR / "model-eval-trio.json"),
        help="Path to the trio sample manifest JSON",
    )
    parser.add_argument(
        "--catalog",
        default=str(CATALOG_PATH),
        help="Path to the model catalog JSON",
    )
    parser.add_argument(
        "--group",
        action="append",
        choices=list(GROUP_ORDER),
        help="Limit runs to one or more model groups",
    )
    parser.add_argument(
        "--model",
        dest="models",
        action="append",
        help="Limit runs to one or more resolved model IDs",
    )
    parser.add_argument(
        "--output-stem",
        default="model-panel-trio",
        help="Name for the evaluation bundle under data/evaluations/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands and prepare templates without executing model runs",
    )
    parser.add_argument(
        "--provider-data-collection",
        choices=["allow", "deny"],
        default=None,
        help="Forward provider data collection routing preference to extract.py",
    )
    parser.add_argument(
        "--zdr-only",
        action="store_true",
        help="Restrict runs to OpenRouter ZDR endpoints if available",
    )
    parser.add_argument(
        "--provider-sort",
        choices=["price", "throughput"],
        default=None,
        help="Optional provider sort for OpenRouter routing",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=90,
        help="Per-request timeout forwarded to extract.py for panel runs.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Retry count forwarded to extract.py for panel runs.",
    )
    parser.add_argument(
        "--request-concurrency",
        type=int,
        default=2,
        help="Per-model request concurrency forwarded to extract.py.",
    )
    parser.add_argument(
        "--model-concurrency",
        type=int,
        default=2,
        help="How many models to run in parallel.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse prior extraction outputs instead of forcing fresh model runs.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print full underlying commands and request more verbose extractor output.",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Colorize panel output. Extract child processes inherit this setting.",
    )
    parser.add_argument(
        "--display",
        choices=["auto", "tui", "plain"],
        default="auto",
        help="How to render panel progress. 'tui' shows a live dashboard, 'plain' prints completion lines.",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Deprecated alias; panel runs force fresh extraction outputs by default.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_models(catalog: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    models = catalog["models"]
    if args.group:
        models = [item for item in models if item["group"] in args.group]
    if args.models:
        allowed = set(args.models)
        models = [item for item in models if item["resolved_id"] in allowed]
    return models


def build_command(
    args: argparse.Namespace,
    model_id: str,
    chat_list_path: Path,
    debug_log_file: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(RETROSPECT_ROOT / "scripts" / "extract.py"),
        "--model",
        model_id,
        "--chat-list-file",
        str(chat_list_path),
        "--concurrency",
        str(args.request_concurrency),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--max-retries",
        str(args.max_retries),
        "--color",
        "always" if use_color(args.color) else "never",
        "--debug-log-file",
        str(debug_log_file),
    ]
    if args.provider_data_collection:
        command.extend(["--provider-data-collection", args.provider_data_collection])
    if args.zdr_only:
        command.append("--zdr-only")
    if args.provider_sort:
        command.extend(["--provider-sort", args.provider_sort])
    if args.debug:
        command.append("--debug")
        command.append("--verbose")
    elif should_use_tui(args):
        command.append("--verbose")
    if args.rerun or not args.reuse_existing:
        command.append("--rerun")
    return command


def parse_manifest_path(stdout: str) -> str | None:
    match = re.search(r"Manifest:\s+(.*)", plain(stdout))
    return match.group(1).strip() if match else None


def use_color(color_mode: str) -> bool:
    if color_mode == "always":
        return True
    if color_mode == "never" or os.getenv("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def style(text: str, code: str, *, color_mode: str) -> str:
    if not use_color(color_mode):
        return text
    return f"\033[{code}m{text}\033[0m"


def short_model_label(model: dict[str, Any]) -> str:
    return model.get("label") or model["resolved_id"]


def plain(text: str) -> str:
    return ANSI_RE.sub("", text)


def pretty_group(group: str) -> str:
    return group.replace("_", " ")


def should_use_tui(args: argparse.Namespace) -> bool:
    if args.display == "tui":
        return True
    if args.display == "plain":
        return False
    return sys.stdout.isatty() and not args.debug and not args.dry_run


def reader_thread(stream: Any, queue: Queue[tuple[str, str]]) -> None:
    for line in iter(stream.readline, ""):
        queue.put(("line", plain(line.rstrip("\n"))))
    queue.put(("eof", ""))


def format_seconds(value: float | None) -> str:
    if value is None:
        return "0.0s"
    if value < 60:
        return f"{value:.1f}s"
    minutes, seconds = divmod(value, 60)
    return f"{int(minutes)}m {seconds:04.1f}s"


def progress_bar(completed: int, total: int, width: int = 16) -> str:
    if total <= 0:
        total = 1
    filled = round((completed / total) * width)
    return "█" * filled + "·" * (width - filled)


def parse_task_start(line: str) -> tuple[str, str] | None:
    match = TASK_START_RE.match(line)
    if not match:
        return None
    return match.group(1), match.group(2)


def parse_task_result(line: str) -> dict[str, Any] | None:
    match = TASK_RESULT_RE.match(line)
    if not match:
        return None
    symbol, completed, total, pass_name, label, duration = match.groups()
    status_map = {"✓": "success", "✗": "failed", "↷": "skipped", "·": "dry_run"}
    return {
        "status": status_map.get(symbol, "unknown"),
        "completed": int(completed),
        "total": int(total),
        "pass_name": pass_name,
        "label": (label or "").strip(),
        "duration_seconds": float(duration),
    }


def extract_live_status(line: str) -> tuple[str, str] | None:
    parsed = parse_task_start(line)
    if parsed is not None:
        return parsed
    result = parse_task_result(line)
    if result is None:
        return None
    return result["pass_name"], result["label"]


def summarize_current_tasks(tasks: list[tuple[str, str]], limit: int = 2) -> str:
    if not tasks:
        return "idle"
    shown = [f"{task_pass}:{label}" if label else task_pass for task_pass, label in tasks[:limit]]
    if len(tasks) > limit:
        shown.append(f"+{len(tasks) - limit}")
    return " | ".join(shown)


def style_status(status: str, *, color_mode: str) -> str:
    mapping = {
        "queued": ("queued", "2"),
        "running": ("running", "1;36"),
        "success": ("done", "1;32"),
        "failed": ("failed", "1;31"),
        "dry_run": ("dry", "1;36"),
    }
    text, code = mapping.get(status, (status, "1;37"))
    return style(text, code, color_mode=color_mode)


def render_live_board(
    args: argparse.Namespace,
    state_map: dict[str, dict[str, Any]],
    *,
    total_models: int,
    started_clock: float,
) -> str:
    spinner = SPINNER_FRAMES[int((time.perf_counter() - started_clock) * 8) % len(SPINNER_FRAMES)]
    completed_models = sum(1 for state in state_map.values() if state["status"] in {"success", "failed", "dry_run"})
    lines = [
        style(
            (
                f"{spinner} Model Panel  "
                f"{completed_models}/{total_models} models  "
                f"elapsed {format_seconds(time.perf_counter() - started_clock)}  "
                f"model_concurrency={args.model_concurrency}  request_concurrency={args.request_concurrency}"
            ),
            "1;36",
            color_mode=args.color,
        ),
        "",
    ]
    ordered_states = sorted(state_map.values(), key=lambda item: item["index"])
    for state in ordered_states:
        elapsed = time.perf_counter() - state["started_clock"] if state.get("started_clock") else 0.0
        completed = state.get("completed_tasks", 0)
        total = state.get("total_tasks", 0)
        bar = progress_bar(completed, total)
        lines.append(
            " ".join(
                [
                    f"[{state['index']}/{total_models}]".ljust(6),
                    state["label"][:26].ljust(26),
                    style_status(state["status"], color_mode=args.color).ljust(7),
                    f"{completed:02d}/{total:02d}" if total else "00/00",
                    bar,
                    format_seconds(elapsed).rjust(8),
                    summarize_current_tasks(state.get("current_tasks", [])),
                ]
            )
        )
        if state.get("last_error"):
            lines.append(f"      {style(state['last_error'], '31', color_mode=args.color)}")
    return "\n".join(lines)


def write_quality_template(
    path: Path,
    sample_manifest: dict[str, Any],
    models: list[dict[str, Any]],
    run_results: list[dict[str, Any]],
) -> None:
    run_by_model = {item["model"]: item for item in run_results}
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "model",
                "group",
                "chat_label",
                "chat_path",
                "pass_id",
                "run_status",
                "run_manifest_path",
                "factual_accuracy",
                "evidence_quality",
                "false_positive_risk",
                "completeness",
                "synthesis_utility",
                "notes",
            ],
        )
        writer.writeheader()
        for model in models:
            run = run_by_model.get(model["resolved_id"], {})
            for chat in sample_manifest["selected_chats"]:
                for pass_id in validate_extraction.PASS_SCHEMAS:
                    writer.writerow(
                        {
                            "model": model["resolved_id"],
                            "group": model["group"],
                            "chat_label": chat["label"],
                            "chat_path": chat["relative_path"],
                            "pass_id": pass_id,
                            "run_status": run.get("status", "pending"),
                            "run_manifest_path": run.get("manifest_path", ""),
                            "factual_accuracy": "",
                            "evidence_quality": "",
                            "false_positive_risk": "",
                            "completeness": "",
                            "synthesis_utility": "",
                            "notes": "",
                        }
                    )


def write_privacy_template(
    path: Path,
    models: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    platform_note = (
        "OpenRouter docs say prompts/responses are not stored unless prompt logging is enabled; metadata is retained. "
        "Provider retention is endpoint-based. Use provider.data_collection=deny and provider.zdr=true where possible."
    )
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "model",
                "group",
                "requested_data_collection_policy",
                "requested_zdr_only",
                "requested_provider_sort",
                "openrouter_platform_note",
                "model_page_data_policy_tag",
                "provider_endpoint_policy",
                "zdr_available",
                "retention_risk_score",
                "notes",
            ],
        )
        writer.writeheader()
        for model in models:
            writer.writerow(
                {
                    "model": model["resolved_id"],
                    "group": model["group"],
                    "requested_data_collection_policy": args.provider_data_collection or "",
                    "requested_zdr_only": str(args.zdr_only).lower(),
                    "requested_provider_sort": args.provider_sort or "",
                    "openrouter_platform_note": platform_note,
                    "model_page_data_policy_tag": "",
                    "provider_endpoint_policy": "",
                    "zdr_available": "",
                    "retention_risk_score": "",
                    "notes": "",
                }
            )


def main() -> None:
    args = parse_args()
    sample_manifest = load_json(Path(args.sample_manifest))
    catalog = load_json(Path(args.catalog))
    models = selected_models(catalog, args)
    if not models:
        raise SystemExit("No models selected")

    chat_list_path = Path(args.sample_manifest).with_suffix(".txt")
    if not chat_list_path.exists():
        raise SystemExit(f"Expected chat list file next to manifest: {chat_list_path}")

    evaluation_name = f"{extract.compact_timestamp()}__{args.output_stem}"
    bundle_dir = EVAL_DIR / evaluation_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = bundle_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    bundle_started_at = extract.iso_now()
    bundle_started_clock = time.perf_counter()
    run_results: list[dict[str, Any]] = []
    total_models = len(models)
    print(
        style(
            (
                f"== Model Panel :: {total_models} model(s), trio sample, "
                f"model_concurrency={args.model_concurrency}, "
                f"request_concurrency={args.request_concurrency} =="
            ),
            "1;36",
            color_mode=args.color,
        ),
        flush=True,
    )
    if args.dry_run:
        for model_index, model in enumerate(models, start=1):
            banner = (
                f"[{model_index}/{total_models}] "
                f"{short_model_label(model)} "
                f"[{pretty_group(model['group'])}]"
            )
            model_slug = extract.slugify(model["resolved_id"])
            debug_log_file = logs_dir / f"{model_slug}.log"
            print(style(f"\n== {banner} ==", "1;35", color_mode=args.color), flush=True)
            print(
                style(
                    f"log: logs/{debug_log_file.name}",
                    "2",
                    color_mode=args.color,
                ),
                flush=True,
            )
            command = build_command(args, model["resolved_id"], chat_list_path, debug_log_file)
            print("$", " ".join(command), flush=True)
            run_results.append(
                {
                    "model": model["resolved_id"],
                    "group": model["group"],
                    "label": short_model_label(model),
                    "index": model_index,
                    "total_models": total_models,
                    "status": "dry_run",
                    "manifest_path": None,
                    "debug_log_file": str(debug_log_file),
                    "stdout": None,
                    "stderr": None,
                    "returncode": 0,
                }
            )
    else:
        use_tui = should_use_tui(args)
        state_map: dict[str, dict[str, Any]] = {}
        pending: list[dict[str, Any]] = []
        running: dict[str, dict[str, Any]] = {}
        for model_index, model in enumerate(models, start=1):
            model_slug = extract.slugify(model["resolved_id"])
            debug_log_file = logs_dir / f"{model_slug}.log"
            command = build_command(args, model["resolved_id"], chat_list_path, debug_log_file)
            state = {
                "model": model["resolved_id"],
                "group": model["group"],
                "label": short_model_label(model),
                "index": model_index,
                "debug_log_file": str(debug_log_file),
                "command": command,
                "status": "queued",
                "completed_tasks": 0,
                "total_tasks": 12,
                "current_tasks": [],
                "last_error": None,
                "started_at": None,
                "completed_at": None,
                "started_clock": None,
                "stdout_lines": [],
                "manifest_path": None,
                "returncode": None,
                "duration_seconds": None,
            }
            state_map[model["resolved_id"]] = state
            pending.append(state)

        render_started = False

        def print_board() -> None:
            nonlocal render_started
            board = render_live_board(
                args,
                state_map,
                total_models=total_models,
                started_clock=bundle_started_clock,
            )
            if render_started:
                sys.stdout.write("\x1b[H\x1b[J")
            render_started = True
            sys.stdout.write(board + "\n")
            sys.stdout.flush()

        while pending or running:
            while pending and len(running) < max(1, args.model_concurrency):
                state = pending.pop(0)
                process = subprocess.Popen(
                    state["command"],
                    cwd=RETROSPECT_ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                )
                assert process.stdout is not None
                queue: Queue[tuple[str, str]] = Queue()
                thread = Thread(target=reader_thread, args=(process.stdout, queue), daemon=True)
                thread.start()
                state["process"] = process
                state["queue"] = queue
                state["reader_thread"] = thread
                state["started_at"] = extract.iso_now()
                state["started_clock"] = time.perf_counter()
                state["status"] = "running"
                running[state["model"]] = state

            progress_changed = False
            completed_models: list[dict[str, Any]] = []
            for state in list(running.values()):
                queue = state["queue"]
                while True:
                    try:
                        event_type, payload = queue.get_nowait()
                    except Empty:
                        break
                    progress_changed = True
                    if event_type == "line":
                        line = payload
                        state["stdout_lines"].append(line)
                        task_start = parse_task_start(line)
                        if task_start is not None:
                            state["current_tasks"].append(task_start)
                        task_result = parse_task_result(line)
                        if task_result is not None:
                            state["completed_tasks"] = task_result["completed"]
                            state["total_tasks"] = task_result["total"]
                            target = (task_result["pass_name"], task_result["label"])
                            if target in state["current_tasks"]:
                                state["current_tasks"].remove(target)
                            elif state["current_tasks"]:
                                state["current_tasks"].pop(0)
                            if task_result["status"] == "failed":
                                state["last_error"] = None
                        elif line.startswith("Manifest: "):
                            state["manifest_path"] = line.split("Manifest: ", 1)[1].strip()
                        elif line.startswith("  "):
                            state["last_error"] = line.strip()
                    elif event_type == "eof":
                        break

                process = state["process"]
                if process.poll() is not None and state.get("completed_at") is None:
                    state["completed_at"] = extract.iso_now()
                    state["duration_seconds"] = round(
                        time.perf_counter() - state["started_clock"], 3
                    )
                    state["returncode"] = process.returncode
                    state["status"] = "success" if process.returncode == 0 else "failed"
                    state["stdout"] = "\n".join(state["stdout_lines"])
                    completed_models.append(state)
                    running.pop(state["model"], None)

            if use_tui:
                print_board()
                time.sleep(0.12)
            elif progress_changed:
                for state in completed_models:
                    status = "ok" if state["returncode"] == 0 else "failed"
                    color = "1;32" if state["returncode"] == 0 else "1;31"
                    print(
                        style(
                            (
                                f"Completed model: {state['label']} "
                                f"({status}) in {state['duration_seconds']:.3f}s"
                            ),
                            color,
                            color_mode=args.color,
                        ),
                        flush=True,
                    )

        if use_tui:
            print_board()

        for state in state_map.values():
            if state.get("stdout_lines") is not None:
                run_results.append(
                    {
                        "model": state["model"],
                        "group": state["group"],
                        "label": state["label"],
                        "index": state["index"],
                        "total_models": total_models,
                        "status": state["status"],
                        "manifest_path": state["manifest_path"],
                        "debug_log_file": state["debug_log_file"],
                        "started_at": state["started_at"],
                        "completed_at": state["completed_at"],
                        "duration_seconds": state["duration_seconds"],
                        "returncode": state["returncode"],
                        "stdout": state.get("stdout"),
                        "stderr": None,
                    }
                )

    run_results = sorted(run_results, key=lambda item: item.get("index", 0))

    bundle_completed_at = extract.iso_now()
    bundle_duration_seconds = time.perf_counter() - bundle_started_clock
    bundle_manifest = {
        "name": "model panel trio evaluation",
        "created_at": bundle_started_at,
        "completed_at": bundle_completed_at,
        "duration_seconds": round(bundle_duration_seconds, 3),
        "sample_manifest": str(Path(args.sample_manifest)),
        "chat_list_file": str(chat_list_path),
        "provider_preferences": {
            "data_collection": args.provider_data_collection,
            "zdr_only": args.zdr_only,
            "sort": args.provider_sort,
        },
        "models": [model["resolved_id"] for model in models],
        "run_results": run_results,
    }
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(bundle_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    write_quality_template(
        bundle_dir / "quality_scores.csv",
        sample_manifest,
        models,
        run_results,
    )
    write_privacy_template(bundle_dir / "privacy_review.csv", models, args)

    print(f"\nEvaluation bundle: {bundle_dir}")
    print(f"Bundle manifest: {bundle_dir / 'bundle_manifest.json'}")
    print(f"Bundle duration seconds: {bundle_duration_seconds:.3f}")
    print(f"Quality template: {bundle_dir / 'quality_scores.csv'}")
    print(f"Privacy template: {bundle_dir / 'privacy_review.csv'}")


if __name__ == "__main__":
    main()
