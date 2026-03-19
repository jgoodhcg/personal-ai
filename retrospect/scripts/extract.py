#!/usr/bin/env python3
"""Run structured extraction passes over normalized chats via OpenRouter.

Usage (from retrospect/):
    uv run python scripts/extract.py --model google/gemini-2.0-flash-001 --limit 5
    uv run python scripts/extract.py --model openai/gpt-4o-mini --pass pass4_psych --limit 100
    uv run python scripts/extract.py --model google/gemini-2.0-flash-001 --dry-run --limit 100

Reads normalized chats from data/chats/.
Writes validated extraction outputs to data/extractions/<pass>/<model_slug>/.
Writes run manifests and failure artifacts to data/extractions/_runs/<run_id>/.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
import yaml
from jinja2 import Template
from jsonschema import Draft202012Validator
from yaml import YAMLError

import validate_extraction


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = RETROSPECT_ROOT.parent
CHAT_DIR = RETROSPECT_ROOT / "data" / "chats"
PROMPT_DIR = RETROSPECT_ROOT / "prompts"
SCHEMA_DIR = RETROSPECT_ROOT / "schemas"
OUTPUT_ROOT = RETROSPECT_ROOT / "data" / "extractions"
RUNS_DIR = OUTPUT_ROOT / "_runs"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PASS_PROMPTS = {
    "pass1_summary": "pass1_summary.md.j2",
    "pass2_projects": "pass2_projects.md.j2",
    "pass3_people": "pass3_people.md.j2",
    "pass4_psych": "pass4_psych.md.j2",
}

DEFAULT_OUTPUT_TOKENS = {
    "pass1_summary": 450,
    "pass2_projects": 700,
    "pass3_people": 700,
    "pass4_psych": 900,
}

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ChatDocument:
    path: Path
    conversation_id: str
    source: str
    title: str
    date: str
    message_count: int
    conversation_text: str


@dataclass(frozen=True)
class ExtractionTask:
    chat: ChatDocument
    pass_id: str


@dataclass
class TaskResult:
    task: ExtractionTask
    status: str
    output_path: str | None = None
    error: str | None = None
    prompt_tokens_estimate: int = 0
    completion_tokens_estimate: int = 0
    prompt_tokens_actual: int | None = None
    completion_tokens_actual: int | None = None
    total_tokens_actual: int | None = None
    reported_cost: float | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def compact_timestamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-").lower()


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured chat data from normalized conversations"
    )
    parser.add_argument("--model", required=True, help="OpenRouter model slug")
    parser.add_argument(
        "--pass",
        dest="pass_ids",
        action="append",
        choices=list(validate_extraction.PASS_SCHEMAS.keys()),
        help="Extraction pass to run. Repeat to select multiple passes. Defaults to all.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit chats processed")
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N chats after sorting. Useful for sampling batches.",
    )
    parser.add_argument(
        "--chat",
        dest="chat_paths",
        action="append",
        help="Specific chat markdown file to process. Repeatable.",
    )
    parser.add_argument(
        "--chat-list-file",
        dest="chat_list_file",
        help="Path to a newline-delimited list of chat files to process.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent API calls",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate work and projected cost without making API calls",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Allow new outputs even if the pass/model already has extracted files",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature sent to the model",
    )
    parser.add_argument(
        "--base-url",
        default=OPENROUTER_URL,
        help="Override the OpenRouter chat completions URL",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="HTTP timeout per request",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retry count for retryable HTTP errors",
    )
    parser.add_argument(
        "--avg-output-tokens",
        type=int,
        default=0,
        help="Override the default completion-token estimate used in dry runs",
    )
    parser.add_argument(
        "--input-cost-per-million",
        type=float,
        default=None,
        help="Optional prompt-token rate for dry-run cost estimation",
    )
    parser.add_argument(
        "--output-cost-per-million",
        type=float,
        default=None,
        help="Optional completion-token rate for dry-run cost estimation",
    )
    parser.add_argument(
        "--app-url",
        default=os.getenv("OPENROUTER_HTTP_REFERER"),
        help="Optional HTTP-Referer sent to OpenRouter",
    )
    parser.add_argument(
        "--app-name",
        default=os.getenv("OPENROUTER_APP_TITLE", "personal-ai-retrospect"),
        help="Optional X-Title sent to OpenRouter",
    )
    parser.add_argument(
        "--response-healing",
        action="store_true",
        help="Enable OpenRouter's response-healing plugin",
    )
    return parser.parse_args()


@lru_cache(maxsize=None)
def read_prompt_blocks(pass_id: str) -> tuple[str, str]:
    prompt_path = PROMPT_DIR / PASS_PROMPTS[pass_id]
    template_text = prompt_path.read_text(encoding="utf-8")

    def extract_block(name: str) -> str:
        pattern = re.compile(
            rf"{{%\s*block\s+{re.escape(name)}\s*%}}(.*?){{%\s*endblock\s*%}}",
            re.DOTALL,
        )
        match = pattern.search(template_text)
        if not match:
            raise ValueError(f"Missing '{name}' block in {prompt_path}")
        return match.group(1).strip()

    return extract_block("system"), extract_block("user")


def render_prompt(pass_id: str, chat: ChatDocument) -> tuple[str, str]:
    system_template, user_template = read_prompt_blocks(pass_id)
    context = {
        "conversation": chat.conversation_text,
        "conversation_id": chat.conversation_id,
        "source_file": chat.path.name,
    }
    system_prompt = Template(system_template).render(**context).strip()
    user_prompt = Template(user_template).render(**context).strip()
    return system_prompt, user_prompt


def parse_chat_document(path: Path) -> ChatDocument:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path} is missing YAML frontmatter")

    metadata = parse_frontmatter(match.group(1))
    conversation_body = match.group(2).strip()
    conversation_text = annotate_turns(conversation_body)

    return ChatDocument(
        path=path,
        conversation_id=str(metadata.get("id", path.stem)),
        source=str(metadata.get("source", "unknown")),
        title=str(metadata.get("title", path.stem)),
        date=str(metadata.get("date", "unknown")),
        message_count=int(metadata.get("message_count", 0)),
        conversation_text=conversation_text,
    )


def parse_frontmatter(frontmatter_text: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(frontmatter_text) or {}
        if isinstance(loaded, dict):
            return loaded
    except YAMLError:
        pass

    # Some normalized chats contain unescaped quotes in title values.
    # Fall back to a tolerant line-based parser for this narrow frontmatter shape.
    parsed: dict[str, Any] = {}
    for line in frontmatter_text.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        if value.isdigit():
            parsed[key] = int(value)
        else:
            parsed[key] = value
    return parsed


def annotate_turns(body: str) -> str:
    heading_pattern = re.compile(r"(?m)^## (User|Assistant)\n\n")
    matches = list(heading_pattern.finditer(body))
    if not matches:
        return body.strip()

    turns = []
    for index, match in enumerate(matches, start=1):
        role = match.group(1)
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(body)
        content = body[start:end].strip()
        if not content:
            continue
        turns.append(f"## {role} turn {index}\n\n{content}")
    return "\n\n".join(turns).strip()


@lru_cache(maxsize=None)
def load_schema_document(filename: str) -> dict[str, Any]:
    path = SCHEMA_DIR / filename
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def strip_runtime_metadata(schema: dict[str, Any]) -> dict[str, Any]:
    model_schema = copy.deepcopy(schema)
    properties = model_schema.get("properties", {})
    properties.pop("metadata", None)
    required = model_schema.get("required", [])
    model_schema["required"] = [item for item in required if item != "metadata"]
    return model_schema


@lru_cache(maxsize=None)
def flatten_schema_for_model(pass_id: str) -> dict[str, Any]:
    root_filename = validate_extraction.PASS_SCHEMAS[pass_id]
    schema_store = {
        "_definitions.json": load_schema_document("_definitions.json"),
        root_filename: strip_runtime_metadata(load_schema_document(root_filename)),
    }

    for filename in validate_extraction.PASS_SCHEMAS.values():
        schema_store.setdefault(filename, load_schema_document(filename))

    def resolve_pointer(document: Any, fragment: str) -> Any:
        if not fragment:
            return document
        if not fragment.startswith("/"):
            raise ValueError(f"Unsupported ref fragment: #{fragment}")
        current = document
        for raw_part in fragment.lstrip("/").split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            current = current[part]
        return current

    def resolve_ref(ref: str, current_file: str) -> tuple[Any, str]:
        filename, _, fragment = ref.partition("#")
        target_file = filename or current_file
        target_doc = schema_store[target_file]
        target = copy.deepcopy(resolve_pointer(target_doc, fragment))
        return target, target_file

    def flatten(node: Any, current_file: str) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                resolved, resolved_file = resolve_ref(node["$ref"], current_file)
                merged = {**resolved, **{k: v for k, v in node.items() if k != "$ref"}}
                return flatten(merged, resolved_file)

            flattened = {}
            for key, value in node.items():
                if key in {"$id", "$schema"}:
                    continue
                flattened[key] = flatten(value, current_file)
            return flattened

        if isinstance(node, list):
            return [flatten(item, current_file) for item in node]

        return node

    return flatten(schema_store[root_filename], root_filename)


def build_output_path(task: ExtractionTask, model_slug: str, run_id: str) -> Path:
    pass_dir = OUTPUT_ROOT / task.pass_id / model_slug
    filename = f"{task.chat.path.stem}__{run_id}.json"
    return pass_dir / filename


def existing_output_path(task: ExtractionTask, model_slug: str) -> Path | None:
    pass_dir = OUTPUT_ROOT / task.pass_id / model_slug
    if not pass_dir.exists():
        return None
    candidates = sorted(pass_dir.glob(f"{task.chat.path.stem}__*.json"))
    return candidates[-1] if candidates else None


def usage_number(usage: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = usage.get(key)
        if value is not None:
            return int(value)
    return None


def usage_cost(usage: dict[str, Any]) -> float | None:
    value = usage.get("cost")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_response_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
        joined = "".join(parts).strip()
        if joined:
            return joined

    raise ValueError(f"Unsupported response content shape: {type(content).__name__}")


def strip_code_fences(text: str) -> str:
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return fenced.group(1).strip() if fenced else text


@lru_cache(maxsize=None)
def validator_for_pass(pass_id: str) -> Draft202012Validator:
    schema = validate_extraction.load_schema(pass_id)
    resolver = validate_extraction.build_resolver()
    return Draft202012Validator(schema, resolver=resolver)


def validate_output(payload: dict[str, Any], pass_id: str) -> list[str]:
    validator = validator_for_pass(pass_id)

    errors = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return errors


def build_headers(args: argparse.Namespace) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    }
    if args.app_url:
        headers["HTTP-Referer"] = args.app_url
    if args.app_name:
        headers["X-Title"] = args.app_name
    return headers


def build_payload(
    args: argparse.Namespace,
    pass_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": args.temperature,
        "provider": {"require_parameters": True},
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": pass_id,
                "strict": True,
                "schema": schema,
            },
        },
    }
    if args.response_healing:
        payload["plugins"] = [{"id": "response-healing"}]
    return payload


def request_completion(
    args: argparse.Namespace,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    last_error: str | None = None

    for attempt in range(1, args.max_retries + 1):
        try:
            response = requests.post(
                args.base_url,
                headers=headers,
                json=payload,
                timeout=args.timeout_seconds,
            )
        except requests.RequestException as exc:
            last_error = f"request error: {exc}"
        else:
            if response.ok:
                return response.json()

            last_error = extract_http_error(response)
            if response.status_code not in RETRYABLE_STATUS_CODES:
                break

        if attempt < args.max_retries:
            time.sleep(min(2 ** (attempt - 1), 8))

    raise RuntimeError(last_error or "OpenRouter request failed")


def extract_http_error(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = response.text

    if isinstance(body, dict):
        if isinstance(body.get("error"), dict):
            message = body["error"].get("message") or body["error"].get("code")
            if message:
                return f"HTTP {response.status_code}: {message}"
        if isinstance(body.get("error"), str):
            return f"HTTP {response.status_code}: {body['error']}"
        if isinstance(body.get("message"), str):
            return f"HTTP {response.status_code}: {body['message']}"
    return f"HTTP {response.status_code}: {response.text[:500]}"


def write_failure_artifact(
    run_dir: Path,
    task: ExtractionTask,
    suffix: str,
    payload: dict[str, Any],
) -> None:
    failures_dir = run_dir / "failures" / task.pass_id
    failures_dir.mkdir(parents=True, exist_ok=True)
    path = failures_dir / f"{task.chat.path.stem}__{suffix}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def execute_task(
    args: argparse.Namespace,
    task: ExtractionTask,
    *,
    run_id: str,
    run_dir: Path,
    headers: dict[str, str],
    model_slug: str,
    semaphore: asyncio.Semaphore,
    model_schemas: dict[str, dict[str, Any]],
) -> TaskResult:
    system_prompt, user_prompt = render_prompt(task.pass_id, task.chat)
    estimated_prompt_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    estimated_completion_tokens = (
        args.avg_output_tokens or DEFAULT_OUTPUT_TOKENS[task.pass_id]
    )

    if not args.rerun:
        prior_output = existing_output_path(task, model_slug)
        if prior_output is not None:
            return TaskResult(
                task=task,
                status="skipped",
                output_path=str(prior_output),
                prompt_tokens_estimate=estimated_prompt_tokens,
                completion_tokens_estimate=estimated_completion_tokens,
            )

    if args.dry_run:
        return TaskResult(
            task=task,
            status="dry_run",
            output_path=str(build_output_path(task, model_slug, run_id)),
            prompt_tokens_estimate=estimated_prompt_tokens,
            completion_tokens_estimate=estimated_completion_tokens,
        )

    payload = build_payload(
        args,
        task.pass_id,
        system_prompt,
        user_prompt,
        model_schemas[task.pass_id],
    )

    async with semaphore:
        try:
            response_json = await asyncio.to_thread(request_completion, args, headers, payload)
            message = response_json["choices"][0]["message"]
            response_text = strip_code_fences(
                normalize_response_text(message.get("content"))
            )
            extracted = json.loads(response_text)
        except Exception as exc:
            write_failure_artifact(
                run_dir,
                task,
                "request-error",
                {
                    "error": str(exc),
                    "request_payload": payload,
                },
            )
            return TaskResult(
                task=task,
                status="failed",
                error=str(exc),
                prompt_tokens_estimate=estimated_prompt_tokens,
                completion_tokens_estimate=estimated_completion_tokens,
            )

    extraction_timestamp = iso_now()
    extracted["metadata"] = {
        "source_conversation_id": task.chat.conversation_id,
        "source_file": task.chat.path.name,
        "pass_id": task.pass_id,
        "model": args.model,
        "extracted_at": extraction_timestamp,
    }

    validation_errors = validate_output(extracted, task.pass_id)
    if validation_errors:
        write_failure_artifact(
            run_dir,
            task,
            "validation-error",
            {
                "validation_errors": validation_errors,
                "output": extracted,
                "request_payload": payload,
            },
        )
        return TaskResult(
            task=task,
            status="failed",
            error="; ".join(validation_errors),
            prompt_tokens_estimate=estimated_prompt_tokens,
            completion_tokens_estimate=estimated_completion_tokens,
        )

    output_path = build_output_path(task, model_slug, run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(extracted, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    usage = response_json.get("usage", {})
    return TaskResult(
        task=task,
        status="success",
        output_path=str(output_path),
        prompt_tokens_estimate=estimated_prompt_tokens,
        completion_tokens_estimate=estimated_completion_tokens,
        prompt_tokens_actual=usage_number(usage, "prompt_tokens", "input_tokens"),
        completion_tokens_actual=usage_number(
            usage, "completion_tokens", "output_tokens"
        ),
        total_tokens_actual=usage_number(usage, "total_tokens"),
        reported_cost=usage_cost(usage),
    )


def discover_chat_paths(args: argparse.Namespace) -> list[Path]:
    if args.chat_paths or args.chat_list_file:
        listed_paths = list(args.chat_paths or [])
        if args.chat_list_file:
            list_path = Path(args.chat_list_file).expanduser()
            if not list_path.is_absolute():
                list_path = (RETROSPECT_ROOT / list_path).resolve()
            if not list_path.exists():
                raise FileNotFoundError(f"Chat list file not found: {args.chat_list_file}")
            for raw_line in list_path.read_text(encoding="utf-8").splitlines():
                stripped = raw_line.strip()
                if stripped and not stripped.startswith("#"):
                    listed_paths.append(stripped)

        paths = [Path(path).expanduser() for path in listed_paths]
        resolved = []
        for path in paths:
            candidate = path if path.is_absolute() else (RETROSPECT_ROOT / path)
            if not candidate.exists():
                raise FileNotFoundError(f"Chat file not found: {path}")
            resolved.append(candidate.resolve())
        return sorted(resolved)

    all_paths = sorted(CHAT_DIR.glob("*.md"))
    if args.offset:
        all_paths = all_paths[args.offset :]
    if args.limit:
        all_paths = all_paths[: args.limit]
    return all_paths


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_cost_per_million: float | None,
    output_cost_per_million: float | None,
) -> float | None:
    if input_cost_per_million is None or output_cost_per_million is None:
        return None
    prompt_cost = (prompt_tokens / 1_000_000) * input_cost_per_million
    completion_cost = (completion_tokens / 1_000_000) * output_cost_per_million
    return prompt_cost + completion_cost


def build_manifest(
    *,
    args: argparse.Namespace,
    run_id: str,
    started_at: str,
    completed_at: str,
    tasks: list[ExtractionTask],
    results: list[TaskResult],
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    pass_summary: dict[str, dict[str, Any]] = {}

    estimated_prompt_tokens = sum(item.prompt_tokens_estimate for item in results)
    estimated_completion_tokens = sum(item.completion_tokens_estimate for item in results)
    actual_prompt_tokens = sum(item.prompt_tokens_actual or 0 for item in results)
    actual_completion_tokens = sum(item.completion_tokens_actual or 0 for item in results)
    actual_total_tokens = sum(item.total_tokens_actual or 0 for item in results)
    reported_cost_total = sum(item.reported_cost or 0 for item in results)

    for item in results:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
        pass_bucket = pass_summary.setdefault(
            item.task.pass_id,
            {"success": 0, "failed": 0, "skipped": 0, "dry_run": 0},
        )
        pass_bucket[item.status] = pass_bucket.get(item.status, 0) + 1

    estimated_cost = estimate_cost(
        estimated_prompt_tokens,
        estimated_completion_tokens,
        args.input_cost_per_million,
        args.output_cost_per_million,
    )

    failures = [
        {
            "pass_id": item.task.pass_id,
            "source_file": item.task.chat.path.name,
            "error": item.error,
        }
        for item in results
        if item.status == "failed"
    ]

    return {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "mode": "dry_run" if args.dry_run else "extract",
        "model": args.model,
        "model_slug": slugify(args.model),
        "selected_passes": args.pass_ids or list(validate_extraction.PASS_SCHEMAS.keys()),
        "chat_count": len({task.chat.path for task in tasks}),
        "task_count": len(tasks),
        "status_counts": status_counts,
        "pass_summary": pass_summary,
        "estimated_prompt_tokens": estimated_prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "estimated_cost": estimated_cost,
        "estimated_cost_units": (
            "same currency units as --input-cost-per-million/--output-cost-per-million"
            if estimated_cost is not None
            else None
        ),
        "actual_prompt_tokens": actual_prompt_tokens or None,
        "actual_completion_tokens": actual_completion_tokens or None,
        "actual_total_tokens": actual_total_tokens or None,
        "reported_cost_total": reported_cost_total or None,
        "reported_cost_units": "OpenRouter reported cost" if reported_cost_total else None,
        "failures": failures,
        "chat_preview": [task.chat.path.name for task in tasks[:20]],
    }


def print_summary(manifest: dict[str, Any]) -> None:
    print(f"\nRun ID: {manifest['run_id']}")
    print(f"Mode: {manifest['mode']}")
    print(f"Model: {manifest['model']}")
    print(f"Chats: {manifest['chat_count']}")
    print(f"Tasks: {manifest['task_count']}")
    print(f"Status counts: {json.dumps(manifest['status_counts'], sort_keys=True)}")
    print(
        "Estimated tokens:"
        f" prompt={manifest['estimated_prompt_tokens']}"
        f" completion={manifest['estimated_completion_tokens']}"
    )
    if manifest["estimated_cost"] is not None:
        print(f"Estimated cost: {manifest['estimated_cost']:.4f}")
    if manifest["actual_total_tokens"] is not None:
        print(
            "Actual tokens:"
            f" prompt={manifest['actual_prompt_tokens']}"
            f" completion={manifest['actual_completion_tokens']}"
            f" total={manifest['actual_total_tokens']}"
        )
    if manifest["reported_cost_total"] is not None:
        print(f"Reported cost total: {manifest['reported_cost_total']:.6f}")


async def run() -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = parse_args()

    selected_passes = args.pass_ids or list(validate_extraction.PASS_SCHEMAS.keys())
    args.pass_ids = selected_passes

    if not args.dry_run and not os.getenv("OPENROUTER_API_KEY"):
        print(
            "Missing OPENROUTER_API_KEY. Export it or add it to the repo .env file.",
            file=sys.stderr,
        )
        return 1

    chat_paths = discover_chat_paths(args)
    if not chat_paths:
        print("No chat files selected.", file=sys.stderr)
        return 1

    chats = [parse_chat_document(path) for path in chat_paths]
    tasks = [
        ExtractionTask(chat=chat, pass_id=pass_id)
        for chat in chats
        for pass_id in selected_passes
    ]

    run_id = f"{compact_timestamp()}__{slugify(args.model)}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    model_slug = slugify(args.model)
    model_schemas = {
        pass_id: flatten_schema_for_model(pass_id) for pass_id in selected_passes
    }
    headers = build_headers(args) if not args.dry_run else {}

    print(
        f"Selected {len(chats)} chats, {len(tasks)} tasks"
        f" across passes: {', '.join(selected_passes)}"
    )
    if args.dry_run:
        print("Dry run enabled. No API calls will be made.")

    started_at = iso_now()
    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    coroutines = [
        execute_task(
            args,
            task,
            run_id=run_id,
            run_dir=run_dir,
            headers=headers,
            model_slug=model_slug,
            semaphore=semaphore,
            model_schemas=model_schemas,
        )
        for task in tasks
    ]

    results: list[TaskResult] = []
    for index, future in enumerate(asyncio.as_completed(coroutines), start=1):
        result = await future
        results.append(result)
        print(
            f"[{index}/{len(tasks)}] {result.status:<7} {result.task.pass_id} "
            f"{result.task.chat.path.name}"
        )
        if result.error:
            print(f"  error: {result.error}")

    completed_at = iso_now()
    manifest = build_manifest(
        args=args,
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        tasks=tasks,
        results=results,
    )
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print_summary(manifest)
    print(f"Manifest: {manifest_path}")

    if manifest["status_counts"].get("failed", 0):
        return 1
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
