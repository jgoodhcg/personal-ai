#!/usr/bin/env python3
"""Run structured quality evaluations against existing Pass 1-3 extraction bundles."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from jinja2 import Template
from jsonschema import Draft202012Validator

import extract


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = RETROSPECT_ROOT.parent
PROMPT_PATH = RETROSPECT_ROOT / "prompts" / "quality_eval_rating.md.j2"
SCHEMA_PATH = RETROSPECT_ROOT / "schemas" / "quality_eval_rating.json"
SAMPLE_DIR = RETROSPECT_ROOT / "data" / "samples"
CATALOG_PATH = RETROSPECT_ROOT / "config" / "model_catalog.json"
EXTRACTIONS_ROOT = RETROSPECT_ROOT / "data" / "extractions"
EVAL_ROOT = RETROSPECT_ROOT / "data" / "evaluations"
JUDGMENT_ROOT = EVAL_ROOT / "quality_judgments"
RUBRIC_VERSION = "2026-03-28"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


@dataclass(frozen=True)
class EvalTask:
    model: str
    label: str
    chat_path: Path


@dataclass
class EvalResult:
    task: EvalTask
    status: str
    output_path: str | None = None
    error: str | None = None
    prompt_tokens_estimate: int = 0
    completion_tokens_estimate: int = 0
    prompt_tokens_actual: int | None = None
    completion_tokens_actual: int | None = None
    total_tokens_actual: int | None = None
    reported_cost: float | None = None
    duration_seconds: float = 0.0


@dataclass
class ModelState:
    label: str
    total_tasks: int
    completed_tasks: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    dry_run: int = 0
    active: dict[str, float] = field(default_factory=dict)
    status: str = "queued"
    started_clock: float | None = None
    last_error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality evaluations on extraction outputs")
    parser.add_argument(
        "--sample-manifest",
        default=str(SAMPLE_DIR / "quality-eval-main-200.json"),
        help="Path to a quality-eval sample manifest JSON",
    )
    parser.add_argument(
        "--catalog",
        default=str(CATALOG_PATH),
        help="Optional model catalog JSON used to resolve nicer labels",
    )
    parser.add_argument(
        "--model",
        dest="models",
        action="append",
        required=True,
        help="Judge model slug. Repeat to compare multiple models.",
    )
    parser.add_argument(
        "--extraction-model",
        default="openai/gpt-5.4-nano",
        help="Model slug whose Pass 1-3 extractions should be judged.",
    )
    parser.add_argument(
        "--output-stem",
        default="quality-eval",
        help="Bundle name stem under data/evaluations/",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent judgment requests across all models.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="HTTP timeout per judgment request.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retry count for failed requests.",
    )
    parser.add_argument(
        "--provider-data-collection",
        choices=["allow", "deny"],
        default=None,
        help="Restrict routing based on provider data-collection policy.",
    )
    parser.add_argument(
        "--zdr-only",
        action="store_true",
        help="Restrict routing to Zero Data Retention endpoints only.",
    )
    parser.add_argument(
        "--provider-sort",
        choices=["price", "throughput"],
        default=None,
        help="Optional provider sort preference for OpenRouter routing.",
    )
    parser.add_argument(
        "--reasoning-policy",
        choices=["disable", "exclude", "allow"],
        default="disable",
        help="How to handle model reasoning output.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional sampling temperature sent to the judge model.",
    )
    parser.add_argument(
        "--avg-output-tokens",
        type=int,
        default=900,
        help="Completion-token estimate used for dry runs and manifests.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate work without making API calls.",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Force new judgments even if prior outputs already exist.",
    )
    parser.add_argument(
        "--display",
        choices=["auto", "tui", "plain"],
        default="auto",
        help="How to render quality-eval progress.",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Colorize console output.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extra debug details for failures.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog_labels(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    catalog = load_json(path)
    return {item["resolved_id"]: item.get("label") or item["resolved_id"] for item in catalog["models"]}


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


def should_use_tui(args: argparse.Namespace) -> bool:
    if args.display == "tui":
        return True
    if args.display == "plain":
        return False
    return sys.stdout.isatty() and not args.debug and not args.dry_run


def format_seconds(value: float | None) -> str:
    if value is None:
        return "0.0s"
    if value < 60:
        return f"{value:.1f}s"
    minutes, seconds = divmod(value, 60)
    return f"{int(minutes)}m {seconds:04.1f}s"


def compose_bar(completed: int, total: int, width: int = 14) -> str:
    if total <= 0:
        total = 1
    fraction = max(0.0, min(1.0, completed / total))
    if completed >= total:
        return "[" + "=" * width + "]"
    filled = int(fraction * width)
    pointer = ">" if filled < width else "="
    remainder = max(0, width - filled - (1 if filled < width else 0))
    return "[" + "=" * filled + pointer + " " * remainder + "]"


def docker_status_text(status: str) -> tuple[str, str]:
    mapping = {
        "queued": ("Waiting", "2"),
        "running": ("Evaluating", "1;36"),
        "success": ("Done", "1;32"),
        "failed": ("Failed", "1;31"),
        "dry_run": ("Dry run", "1;36"),
    }
    return mapping.get(status, (status, "1;37"))


def render_board(
    args: argparse.Namespace,
    state_map: dict[str, ModelState],
    *,
    started_clock: float,
    completed_tasks: int,
    total_tasks: int,
) -> str:
    spinner = SPINNER_FRAMES[int((time.perf_counter() - started_clock) * 10) % len(SPINNER_FRAMES)]
    header = style(
        (
            f"{spinner} quality-eval  "
            f"{completed_tasks}/{total_tasks} judgments  "
            f"elapsed {format_seconds(time.perf_counter() - started_clock)}  "
            f"concurrency={args.concurrency}"
        ),
        "1;36",
        color_mode=args.color,
    )
    lines = [header, ""]
    for model_id, state in state_map.items():
        status_text, status_code = docker_status_text(state.status)
        model_elapsed = (
            time.perf_counter() - state.started_clock if state.started_clock is not None else 0.0
        )
        lines.append(
            "  ".join(
                [
                    state.label[:28].ljust(28),
                    style(status_text.ljust(10), status_code, color_mode=args.color),
                    compose_bar(state.completed_tasks, state.total_tasks),
                    f"{state.completed_tasks:03d}/{state.total_tasks:03d}",
                    format_seconds(model_elapsed).rjust(8),
                ]
            )
        )
        for chat_name, task_started in list(state.active.items())[:3]:
            task_elapsed = time.perf_counter() - task_started
            lines.append(
                "    "
                + "  ".join(
                    [
                        chat_name[:28].ljust(28),
                        style("Judging".ljust(10), "36", color_mode=args.color),
                        format_seconds(task_elapsed),
                    ]
                )
            )
        if state.last_error:
            lines.append("    " + style(state.last_error, "31", color_mode=args.color))
    return "\n".join(lines)


def first_line(text: str) -> str:
    return text.splitlines()[0] if text else ""


@lru_cache(maxsize=None)
def read_prompt_blocks() -> tuple[str, str]:
    template_text = PROMPT_PATH.read_text(encoding="utf-8")

    def extract_block(name: str) -> str:
        pattern = re.compile(
            rf"{{%\s*block\s+{re.escape(name)}\s*%}}(.*?){{%\s*endblock\s*%}}",
            re.DOTALL,
        )
        match = pattern.search(template_text)
        if not match:
            raise ValueError(f"Missing '{name}' block in {PROMPT_PATH}")
        return match.group(1).strip()

    return extract_block("system"), extract_block("user")


@lru_cache(maxsize=None)
def load_eval_schema() -> dict[str, Any]:
    return load_json(SCHEMA_PATH)


@lru_cache(maxsize=None)
def schema_without_metadata() -> dict[str, Any]:
    schema = json.loads(json.dumps(load_eval_schema()))
    schema["properties"].pop("metadata", None)
    schema["required"] = [item for item in schema.get("required", []) if item != "metadata"]
    return schema


@lru_cache(maxsize=None)
def validator() -> Draft202012Validator:
    return Draft202012Validator(load_eval_schema())


def load_sample_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if "selected_chats" not in manifest:
        raise ValueError(f"Invalid sample manifest: {path}")
    return manifest


def sample_chat_paths(manifest: dict[str, Any]) -> list[Path]:
    paths = []
    for item in manifest["selected_chats"]:
        relative = item["relative_path"]
        candidate = (RETROSPECT_ROOT / relative).resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Chat file not found: {relative}")
        paths.append(candidate)
    return paths


def latest_extraction_path(pass_id: str, model_slug: str, chat_stem: str) -> Path:
    pass_dir = EXTRACTIONS_ROOT / pass_id / model_slug
    candidates = sorted(pass_dir.glob(f"{chat_stem}__*.json"))
    if not candidates:
        raise FileNotFoundError(
            f"Missing extraction output for {pass_id} / {model_slug} / {chat_stem}"
        )
    return candidates[-1]


def load_extraction_bundle(chat_path: Path, extraction_model_slug: str) -> dict[str, Any]:
    chat_stem = chat_path.stem
    bundle = {}
    for pass_id in ("pass1_summary", "pass2_projects", "pass3_people"):
        bundle[pass_id] = load_json(latest_extraction_path(pass_id, extraction_model_slug, chat_stem))
    return bundle


def build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    }


def build_payload(
    args: argparse.Namespace,
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    provider_preferences: dict[str, Any] = {"require_parameters": True}
    if args.provider_data_collection:
        provider_preferences["data_collection"] = args.provider_data_collection
    if args.zdr_only:
        provider_preferences["zdr"] = True
    if args.provider_sort:
        provider_preferences["sort"] = args.provider_sort

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "provider": provider_preferences,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "quality_eval_rating",
                "strict": True,
                "schema": schema_without_metadata(),
            },
        },
    }
    if args.reasoning_policy == "disable":
        payload["reasoning"] = {"enabled": False, "exclude": True}
    elif args.reasoning_policy == "exclude":
        payload["reasoning"] = {"exclude": True}
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    return payload


def request_completion(args: argparse.Namespace, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, args.max_retries + 1):
        try:
            response = requests.post(
                extract.OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=args.timeout_seconds,
            )
        except requests.RequestException as exc:
            last_error = f"request error: {exc}"
        else:
            if response.ok:
                return response.json()
            last_error = extract.extract_http_error(response)
            if response.status_code not in extract.RETRYABLE_STATUS_CODES:
                break
        if attempt < args.max_retries:
            time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(last_error or "OpenRouter request failed")


def judgment_path(model_slug: str, chat_stem: str, run_id: str) -> Path:
    return JUDGMENT_ROOT / model_slug / f"{chat_stem}__{run_id}.json"


def existing_judgment_path(model_slug: str, chat_stem: str) -> Path | None:
    path = JUDGMENT_ROOT / model_slug
    if not path.exists():
        return None
    candidates = sorted(path.glob(f"{chat_stem}__*.json"))
    return candidates[-1] if candidates else None


def render_prompts(
    *,
    chat: extract.ChatDocument,
    extraction_model: str,
    bundle: dict[str, Any],
) -> tuple[str, str]:
    system_template, user_template = read_prompt_blocks()
    context = {
        "conversation": chat.conversation_text,
        "conversation_id": chat.conversation_id,
        "source_file": chat.path.name,
        "extraction_model": extraction_model,
        "pass1_json": json.dumps(bundle["pass1_summary"], indent=2, ensure_ascii=False),
        "pass2_json": json.dumps(bundle["pass2_projects"], indent=2, ensure_ascii=False),
        "pass3_json": json.dumps(bundle["pass3_people"], indent=2, ensure_ascii=False),
    }
    return (
        Template(system_template).render(**context).strip(),
        Template(user_template).render(**context).strip(),
    )


async def evaluate_task(
    args: argparse.Namespace,
    task: EvalTask,
    *,
    run_id: str,
    headers: dict[str, str],
    extraction_model_slug: str,
    semaphore: asyncio.Semaphore,
    state_map: dict[str, ModelState],
) -> EvalResult:
    model_slug = extract.slugify(task.model)
    existing = existing_judgment_path(model_slug, task.chat_path.stem)
    try:
        chat_doc = extract.parse_chat_document(task.chat_path)
        bundle = load_extraction_bundle(task.chat_path, extraction_model_slug)
        system_prompt, user_prompt = render_prompts(
            chat=chat_doc,
            extraction_model=args.extraction_model,
            bundle=bundle,
        )
        prompt_estimate = extract.estimate_tokens(system_prompt) + extract.estimate_tokens(user_prompt)
    except Exception as exc:
        return EvalResult(
            task=task,
            status="failed",
            error=str(exc),
            completion_tokens_estimate=args.avg_output_tokens,
        )

    if not args.rerun and existing is not None:
        return EvalResult(
            task=task,
            status="skipped",
            output_path=str(existing),
            prompt_tokens_estimate=prompt_estimate,
            completion_tokens_estimate=args.avg_output_tokens,
        )

    if args.dry_run:
        return EvalResult(
            task=task,
            status="dry_run",
            output_path=str(judgment_path(model_slug, task.chat_path.stem, run_id)),
            prompt_tokens_estimate=prompt_estimate,
            completion_tokens_estimate=args.avg_output_tokens,
        )

    payload = build_payload(
        args,
        model=task.model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    state = state_map[task.model]
    task_started = time.perf_counter()

    async with semaphore:
        state.status = "running"
        state.started_clock = state.started_clock or task_started
        state.active[task.chat_path.name] = task_started
        try:
            response_json = await asyncio.to_thread(request_completion, args, headers, payload)
            message = response_json["choices"][0]["message"]
            response_text = extract.strip_code_fences(extract.extract_response_text(message))
            judged = json.loads(response_text)
        except Exception as exc:
            state.last_error = first_line(str(exc))
            state.active.pop(task.chat_path.name, None)
            return EvalResult(
                task=task,
                status="failed",
                error=str(exc),
                prompt_tokens_estimate=prompt_estimate,
                completion_tokens_estimate=args.avg_output_tokens,
                duration_seconds=time.perf_counter() - task_started,
            )

    judged["metadata"] = {
        "source_conversation_id": chat_doc.conversation_id,
        "source_file": chat_doc.path.name,
        "judge_model": task.model,
        "extraction_model": args.extraction_model,
        "rubric_version": RUBRIC_VERSION,
        "judged_at": extract.iso_now(),
    }

    errors = [
        f"{'.'.join(str(part) for part in error.path) or '(root)'}: {error.message}"
        for error in sorted(validator().iter_errors(judged), key=lambda item: list(item.path))
    ]
    state.active.pop(task.chat_path.name, None)
    if errors:
        state.last_error = first_line("; ".join(errors))
        return EvalResult(
            task=task,
            status="failed",
            error="; ".join(errors),
            prompt_tokens_estimate=prompt_estimate,
            completion_tokens_estimate=args.avg_output_tokens,
            duration_seconds=time.perf_counter() - task_started,
        )

    output_path = judgment_path(model_slug, task.chat_path.stem, run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(judged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    usage = response_json.get("usage", {})
    return EvalResult(
        task=task,
        status="success",
        output_path=str(output_path),
        prompt_tokens_estimate=prompt_estimate,
        completion_tokens_estimate=args.avg_output_tokens,
        prompt_tokens_actual=extract.usage_number(usage, "prompt_tokens", "input_tokens"),
        completion_tokens_actual=extract.usage_number(usage, "completion_tokens", "output_tokens"),
        total_tokens_actual=extract.usage_number(usage, "total_tokens"),
        reported_cost=extract.usage_cost(usage),
        duration_seconds=time.perf_counter() - task_started,
    )


def write_scores_csv(path: Path, results: list[EvalResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "judge_model",
                "chat_path",
                "status",
                "downstream_ready",
                "overall_score",
                "confidence",
                "factual_accuracy",
                "completeness",
                "evidence_fidelity",
                "restraint",
                "downstream_usefulness",
                "major_issue_count",
                "output_path",
                "error",
            ],
        )
        writer.writeheader()
        for result in results:
            row = {
                "judge_model": result.task.model,
                "chat_path": str(result.task.chat_path.relative_to(RETROSPECT_ROOT)),
                "status": result.status,
                "downstream_ready": "",
                "overall_score": "",
                "confidence": "",
                "factual_accuracy": "",
                "completeness": "",
                "evidence_fidelity": "",
                "restraint": "",
                "downstream_usefulness": "",
                "major_issue_count": "",
                "output_path": result.output_path or "",
                "error": result.error or "",
            }
            if result.status in {"success", "skipped"} and result.output_path:
                payload = load_json(Path(result.output_path))
                row.update(
                    {
                        "downstream_ready": payload["overall"]["downstream_ready"],
                        "overall_score": payload["overall"]["overall_score"],
                        "confidence": payload["overall"]["confidence"],
                        "factual_accuracy": payload["dimensions"]["factual_accuracy"],
                        "completeness": payload["dimensions"]["completeness"],
                        "evidence_fidelity": payload["dimensions"]["evidence_fidelity"],
                        "restraint": payload["dimensions"]["restraint"],
                        "downstream_usefulness": payload["dimensions"]["downstream_usefulness"],
                        "major_issue_count": len(payload["major_issues"]),
                    }
                )
            writer.writerow(row)


def write_human_template(path: Path, sample_manifest: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "chat_path",
                "downstream_ready",
                "overall_score",
                "confidence",
                "factual_accuracy",
                "completeness",
                "evidence_fidelity",
                "restraint",
                "downstream_usefulness",
                "major_issues",
                "pass1_note",
                "pass2_note",
                "pass3_note",
                "summary",
            ],
        )
        writer.writeheader()
        for item in sample_manifest["selected_chats"]:
            writer.writerow({"chat_path": item["relative_path"]})


async def run() -> int:
    args = parse_args()
    extract.load_dotenv(REPO_ROOT / ".env")
    if not args.dry_run and "OPENROUTER_API_KEY" not in os.environ:
        raise SystemExit("OPENROUTER_API_KEY is required for quality evaluation runs")

    sample_manifest_path = Path(args.sample_manifest).expanduser()
    if not sample_manifest_path.is_absolute():
        sample_manifest_path = (RETROSPECT_ROOT / sample_manifest_path).resolve()
    sample_manifest = load_sample_manifest(sample_manifest_path)
    chat_paths = sample_chat_paths(sample_manifest)
    catalog_labels = load_catalog_labels(Path(args.catalog))

    tasks = [
        EvalTask(
            model=model,
            label=catalog_labels.get(model, model),
            chat_path=chat_path,
        )
        for model in args.models
        for chat_path in chat_paths
    ]

    state_map = {
        model: ModelState(
            label=catalog_labels.get(model, model),
            total_tasks=len(chat_paths),
        )
        for model in args.models
    }

    run_id = f"{extract.compact_timestamp()}__quality-eval"
    bundle_dir = EVAL_ROOT / f"{extract.compact_timestamp()}__{args.output_stem}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    started_clock = time.perf_counter()
    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    headers = build_headers() if not args.dry_run else {}

    print(
        style(
            f"== Quality Eval :: {len(args.models)} model(s), {len(chat_paths)} chats, concurrency={args.concurrency} ==",
            "1;36",
            color_mode=args.color,
        ),
        flush=True,
    )

    coroutines = [
        evaluate_task(
            args,
            task,
            run_id=run_id,
            headers=headers,
            extraction_model_slug=extract.slugify(args.extraction_model),
            semaphore=semaphore,
            state_map=state_map,
        )
        for task in tasks
    ]

    results: list[EvalResult] = []
    render_started = False
    use_tui = should_use_tui(args)

    def print_board() -> None:
        nonlocal render_started
        completed = len(results)
        board = render_board(
            args,
            state_map,
            started_clock=started_clock,
            completed_tasks=completed,
            total_tasks=len(tasks),
        )
        if render_started:
            sys.stdout.write("\x1b[H\x1b[J")
        render_started = True
        sys.stdout.write(board + "\n")
        sys.stdout.flush()

    for future in asyncio.as_completed(coroutines):
        result = await future
        results.append(result)
        state = state_map[result.task.model]
        state.completed_tasks += 1
        state.status = "running"
        if result.status == "success":
            state.success += 1
        elif result.status == "failed":
            state.failed += 1
            state.last_error = first_line(result.error or "")
        elif result.status == "skipped":
            state.skipped += 1
        elif result.status == "dry_run":
            state.dry_run += 1
        if state.completed_tasks >= state.total_tasks:
            if state.failed:
                state.status = "failed"
            elif state.dry_run and not state.success and not state.skipped:
                state.status = "dry_run"
            else:
                state.status = "success"

        if use_tui:
            print_board()
        else:
            line = (
                f"{result.task.label} :: {result.task.chat_path.name} :: "
                f"{result.status} :: {result.duration_seconds:.2f}s"
            )
            color = "32" if result.status in {"success", "skipped", "dry_run"} else "31"
            print(style(line, color, color_mode=args.color), flush=True)

    if use_tui:
        print_board()

    results.sort(key=lambda item: (item.task.model, item.task.chat_path.name))
    scores_csv = bundle_dir / "judge_scores.csv"
    write_scores_csv(scores_csv, results)
    write_human_template(bundle_dir / "human_review_template.csv", sample_manifest)

    status_counts: dict[str, int] = {}
    for item in results:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    bundle_manifest = {
        "name": "quality evaluation bundle",
        "created_at": extract.iso_now(),
        "duration_seconds": round(time.perf_counter() - started_clock, 3),
        "sample_manifest": str(sample_manifest_path),
        "sample_size": len(chat_paths),
        "judge_models": args.models,
        "extraction_model": args.extraction_model,
        "rubric_version": RUBRIC_VERSION,
        "status_counts": status_counts,
        "results": [
            {
                "judge_model": item.task.model,
                "chat_path": str(item.task.chat_path.relative_to(RETROSPECT_ROOT)),
                "status": item.status,
                "output_path": item.output_path,
                "error": item.error,
                "duration_seconds": round(item.duration_seconds, 3),
                "reported_cost": item.reported_cost,
            }
            for item in results
        ],
    }
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps(bundle_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nEvaluation bundle: {bundle_dir}")
    print(f"Bundle manifest: {bundle_dir / 'bundle_manifest.json'}")
    print(f"Judge scores CSV: {scores_csv}")
    print(f"Human review template: {bundle_dir / 'human_review_template.csv'}")
    return 1 if status_counts.get("failed", 0) else 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
