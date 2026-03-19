#!/usr/bin/env python3
"""Run a fixed chat sample across a model panel and emit review templates."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import extract
import validate_extraction


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = RETROSPECT_ROOT / "config" / "model_catalog.json"
SAMPLE_DIR = RETROSPECT_ROOT / "data" / "samples"
EVAL_DIR = RETROSPECT_ROOT / "data" / "evaluations"


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
        choices=["smaller", "flagship", "wildcard"],
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
        "--reuse-existing",
        action="store_true",
        help="Reuse prior extraction outputs instead of forcing fresh model runs.",
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


def build_command(args: argparse.Namespace, model_id: str, chat_list_path: Path) -> list[str]:
    command = [
        sys.executable,
        str(RETROSPECT_ROOT / "scripts" / "extract.py"),
        "--model",
        model_id,
        "--chat-list-file",
        str(chat_list_path),
        "--concurrency",
        "1",
    ]
    if args.provider_data_collection:
        command.extend(["--provider-data-collection", args.provider_data_collection])
    if args.zdr_only:
        command.append("--zdr-only")
    if args.provider_sort:
        command.extend(["--provider-sort", args.provider_sort])
    if args.rerun or not args.reuse_existing:
        command.append("--rerun")
    return command


def parse_manifest_path(stdout: str) -> str | None:
    match = re.search(r"Manifest:\s+(.*)", stdout)
    return match.group(1).strip() if match else None


def run_streaming(command: list[str], cwd: Path) -> tuple[int, str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None

    lines: list[str] = []
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line)

    returncode = process.wait()
    return returncode, "".join(lines)


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

    run_results: list[dict[str, Any]] = []
    for model in models:
        command = build_command(args, model["resolved_id"], chat_list_path)
        print("$", " ".join(command))
        if args.dry_run:
            run_results.append(
                {
                    "model": model["resolved_id"],
                    "status": "dry_run",
                    "manifest_path": None,
                    "stdout": None,
                    "stderr": None,
                    "returncode": 0,
                }
            )
            continue

        print(f"Running model: {model['resolved_id']}", flush=True)
        returncode, combined_output = run_streaming(command, RETROSPECT_ROOT)
        manifest_path = parse_manifest_path(combined_output)
        print(
            f"Completed model: {model['resolved_id']} "
            f"({'ok' if returncode == 0 else 'failed'})",
            flush=True,
        )
        run_results.append(
            {
                "model": model["resolved_id"],
                "status": "success" if returncode == 0 else "failed",
                "manifest_path": manifest_path,
                "returncode": returncode,
                "stdout": combined_output,
                "stderr": None,
            }
        )

    bundle_manifest = {
        "name": "model panel trio evaluation",
        "created_at": extract.iso_now(),
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
    print(f"Quality template: {bundle_dir / 'quality_scores.csv'}")
    print(f"Privacy template: {bundle_dir / 'privacy_review.csv'}")


if __name__ == "__main__":
    main()
