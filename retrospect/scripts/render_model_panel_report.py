#!/usr/bin/env python3
"""Render a static HTML review report for the latest model panel bundle."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path
from typing import Any

import analyze_model_costs as amc


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = RETROSPECT_ROOT.parent
DATA_DIR = RETROSPECT_ROOT / "data"
CONFIG_DIR = RETROSPECT_ROOT / "config"
DECISIONS_DIR = REPO_ROOT / ".decisions"
EVALUATIONS_DIR = DATA_DIR / "evaluations"
REPORTS_DIR = DATA_DIR / "reports"
CATALOG_PATH = CONFIG_DIR / "model_catalog.json"
DECISION_PATH = DECISIONS_DIR / "retrospect-extraction-model-selection.json"
TRIO_PATH = DATA_DIR / "samples" / "model-eval-trio.json"
SAMPLE_MANIFEST_PATH = DATA_DIR / "samples" / "model-cost-minimal-sample.json"
MANIFEST_RE = re.compile(r"Manifest:\s+(.*)")
TASK_RE = re.compile(r"^[✓✗↷·] \d+/\d+ (\w+)\s+(.*?)\s+([0-9]+\.[0-9]+)s$")
GROUP_ORDER = ("extra_small", "smaller", "flagship", "wildcard")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a static HTML report for the latest model panel bundle")
    parser.add_argument(
        "--bundle",
        help="Optional explicit evaluation bundle directory. Defaults to latest *model-panel-trio bundle.",
    )
    parser.add_argument(
        "--output",
        default=str(REPORTS_DIR / "model-panel-review.html"),
        help="Output HTML path.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_bundle() -> Path | None:
    bundles = sorted(EVALUATIONS_DIR.glob("*__model-panel-trio"))
    return bundles[-1] if bundles else None


def manifest_path_from_result(result: dict[str, Any]) -> Path | None:
    direct = result.get("manifest_path")
    if direct:
        return Path(direct)
    stdout = result.get("stdout") or ""
    match = MANIFEST_RE.search(stdout)
    return Path(match.group(1).strip()) if match else None


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pretty_group(group: str) -> str:
    return group.replace("_", " ")


def short_chat_label(relative_path: str) -> str:
    stem = Path(relative_path).stem
    parts = stem.split("_", 3)
    label = parts[3] if len(parts) >= 4 else stem
    return label.replace("-", " ")


def money(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.{digits}f}"


def collect_summary_rows(
    bundle_manifest: dict[str, Any],
    catalog_by_model: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in bundle_manifest["run_results"]:
        model = result["model"]
        manifest_path = manifest_path_from_result(result)
        run_manifest = load_json(manifest_path) if manifest_path and manifest_path.exists() else {}
        status_counts = run_manifest.get("status_counts", {})
        success_count = status_counts.get("success", 0)
        failed_count = status_counts.get("failed", 0)
        task_count = run_manifest.get("task_count", 0)
        row = {
            "group": catalog_by_model[model]["group"],
            "label": catalog_by_model[model]["label"],
            "model": model,
            "status": result.get("status", "unknown"),
            "runtime_seconds": float(result.get("duration_seconds") or 0.0),
            "success_count": success_count,
            "failed_count": failed_count,
            "task_count": task_count,
            "success_rate": (success_count / task_count) if task_count else None,
            "sample_cost_usd": run_manifest.get("reported_cost_total"),
            "prompt_tokens": run_manifest.get("actual_prompt_tokens"),
            "completion_tokens": run_manifest.get("actual_completion_tokens"),
            "manifest_path": str(manifest_path) if manifest_path else "",
            "log_file": result.get("debug_log_file", ""),
        }
        rows.append(row)
    rows.sort(key=lambda item: (GROUP_ORDER.index(item["group"]), item["runtime_seconds"]))
    return rows


def parse_task_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    pending_index: int | None = None
    previous_elapsed = 0.0
    symbol_to_status = {
        "✓": "success",
        "✗": "failed",
        "↷": "skipped",
        "·": "dry_run",
    }
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if pending_index is not None and line.startswith("  "):
            events[pending_index]["error"] = line.strip()
            pending_index = None
            continue
        if not line:
            continue
        symbol = line[0]
        status = symbol_to_status.get(symbol)
        if not status:
            pending_index = None
            continue
        match = TASK_RE.match(line)
        if not match:
            pending_index = None
            continue
        elapsed_seconds = float(match.group(3))
        event = {
            "status": status,
            "pass_label": match.group(1),
            "chat_short_label": match.group(2).strip(),
            "elapsed_seconds": elapsed_seconds,
            "task_duration_seconds": max(0.0, elapsed_seconds - previous_elapsed),
            "error": None,
        }
        events.append(event)
        previous_elapsed = elapsed_seconds
        pending_index = len(events) - 1 if status == "failed" else None
    return events


def collect_chat_breakdown(
    bundle_manifest: dict[str, Any],
    trio_manifest: dict[str, Any],
    catalog_by_model: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    trio_items = []
    trio_by_short_label: dict[str, dict[str, Any]] = {}
    for item in trio_manifest["selected_chats"]:
        enriched = dict(item)
        enriched["short_label"] = short_chat_label(item["relative_path"])
        trio_items.append(enriched)
        trio_by_short_label[enriched["short_label"]] = enriched

    per_chat: dict[str, list[dict[str, Any]]] = {item["label"]: [] for item in trio_items}
    for result in bundle_manifest["run_results"]:
        events = parse_task_events(result.get("stdout") or "")
        model_meta = catalog_by_model[result["model"]]
        bucket: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            bucket.setdefault(event["chat_short_label"], []).append(event)
        for short_label, chat_events in bucket.items():
            trio_item = trio_by_short_label.get(short_label)
            if not trio_item:
                continue
            failures = [event for event in chat_events if event["status"] == "failed"]
            per_chat[trio_item["label"]].append(
                {
                    "group": model_meta["group"],
                    "label": model_meta["label"],
                    "model": result["model"],
                    "success_count": sum(1 for event in chat_events if event["status"] == "success"),
                    "failure_count": len(failures),
                    "task_count": len(chat_events),
                    "runtime_seconds": sum(event["task_duration_seconds"] for event in chat_events),
                    "failed_passes": ", ".join(event["pass_label"] for event in failures) or "none",
                    "error_preview": failures[0]["error"] if failures else "",
                }
            )

    breakdown = []
    for item in trio_items:
        rows = per_chat[item["label"]]
        rows.sort(key=lambda row: (GROUP_ORDER.index(row["group"]), row["runtime_seconds"]))
        breakdown.append({"chat": item, "rows": rows})
    return breakdown


def collect_projection_rows(summary_rows: list[dict[str, Any]], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    archive_chat_paths = sorted((RETROSPECT_ROOT / "data" / "chats").glob("*.md"))
    sample_manifest = load_json(SAMPLE_MANIFEST_PATH)
    sample_chat_paths = [
        RETROSPECT_ROOT / item["relative_path"] for item in sample_manifest["selected_chats"]
    ]
    archive_totals = amc.compute_prompt_totals(archive_chat_paths)
    sample_totals = amc.compute_prompt_totals(sample_chat_paths)

    empirical: dict[str, dict[str, Any]] = {}
    for row in summary_rows:
        if not row["manifest_path"]:
            continue
        manifest = load_json(Path(row["manifest_path"]))
        empirical[row["model"]] = {
            "path": row["manifest_path"],
            "chat_count": manifest.get("chat_count"),
            "task_count": manifest.get("task_count"),
            "actual_prompt_tokens": manifest.get("actual_prompt_tokens"),
            "actual_completion_tokens": manifest.get("actual_completion_tokens"),
            "reported_cost_total": manifest.get("reported_cost_total"),
        }

    active_models = [
        model
        for model in catalog["models"]
        if model["resolved_id"] is not None
        and model["input_cost_per_million"] is not None
        and model["output_cost_per_million"] is not None
    ]
    rows = amc.build_projection_rows(active_models, archive_totals, sample_totals, empirical)
    rows.sort(key=lambda item: item["archive_cost_heuristic"])
    return rows


def collect_completion_counts(
    quality_rows: list[dict[str, str]],
    privacy_rows: list[dict[str, str]],
) -> tuple[int, int]:
    quality_completed = sum(
        1
        for row in quality_rows
        if any((row.get(key) or "").strip() for key in [
            "factual_accuracy",
            "evidence_quality",
            "false_positive_risk",
            "completeness",
            "synthesis_utility",
        ])
    )
    privacy_completed = sum(
        1
        for row in privacy_rows
        if any((row.get(key) or "").strip() for key in [
            "model_page_data_policy_tag",
            "provider_endpoint_policy",
            "zdr_available",
            "retention_risk_score",
            "notes",
        ])
    )
    return quality_completed, privacy_completed


def collect_quality_summary(quality_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    metrics = [
        "factual_accuracy",
        "evidence_quality",
        "false_positive_risk",
        "completeness",
        "synthesis_utility",
    ]
    per_model: dict[str, dict[str, Any]] = {}
    for row in quality_rows:
        model = row["model"]
        parsed_values: dict[str, float] = {}
        found_any = False
        for metric in metrics:
            value = (row.get(metric) or "").strip()
            if not value:
                continue
            try:
                numeric = float(value)
            except ValueError:
                continue
            parsed_values[metric] = numeric
            found_any = True
        if not found_any:
            continue
        bucket = per_model.setdefault(
            model,
            {"count": 0, "sums": {metric: 0.0 for metric in metrics}, "filled": {metric: 0 for metric in metrics}},
        )
        for metric, numeric in parsed_values.items():
            bucket["sums"][metric] += numeric
            bucket["filled"][metric] += 1
        bucket["count"] += 1

    rows = []
    for model, data in per_model.items():
        averages = {}
        for metric in metrics:
            filled = data["filled"][metric]
            averages[metric] = (data["sums"][metric] / filled) if filled else None
        valid_avgs = [value for value in averages.values() if value is not None]
        overall = sum(valid_avgs) / len(valid_avgs) if valid_avgs else None
        rows.append(
            {
                "model": model,
                "overall": overall,
                **averages,
            }
        )
    return rows


def status_chip(text: str, tone: str) -> str:
    return f'<span class="chip chip-{tone}">{html.escape(text)}</span>'


def tone_for_status(status: str) -> str:
    return {
        "success": "green",
        "failed": "red",
        "dry_run": "blue",
    }.get(status, "yellow")


def render_summary_cards(
    bundle_manifest: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, str]],
    privacy_rows: list[dict[str, str]],
) -> str:
    successful_models = sum(1 for row in summary_rows if row["status"] == "success")
    avg_runtime = sum(row["runtime_seconds"] for row in summary_rows) / len(summary_rows) if summary_rows else 0.0
    quality_completed, privacy_completed = collect_completion_counts(quality_rows, privacy_rows)
    cards = [
        ("Bundle runtime", f"{bundle_manifest['duration_seconds']:.1f}s"),
        ("Models run", str(len(summary_rows))),
        ("Successful models", str(successful_models)),
        ("Average per-model runtime", f"{avg_runtime:.1f}s"),
        ("Quality rows completed", f"{quality_completed}/{len(quality_rows)}"),
        ("Privacy rows completed", f"{privacy_completed}/{len(privacy_rows)}"),
    ]
    return "".join(
        f'<div class="card"><div class="k">{html.escape(label)}</div><div class="v">{html.escape(value)}</div></div>'
        for label, value in cards
    )

def render_summary_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(pretty_group(row['group']))}</td>"
            f"<td>{html.escape(row['label'])}</td>"
            f"<td>{status_chip(row['status'], tone_for_status(row['status']))}</td>"
            f"<td>{row['success_count']}/{row['task_count']}</td>"
            f"<td>{row['runtime_seconds']:.1f}s</td>"
            f"<td>{money(row['sample_cost_usd'], 6)}</td>"
            f"<td>{row['prompt_tokens'] or 'n/a'}</td>"
            f"<td>{row['completion_tokens'] or 'n/a'}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>group</th><th>model</th><th>status</th><th>tasks</th>"
        "<th>runtime</th><th>sample cost</th><th>prompt tokens</th><th>completion tokens</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def render_bar_chart(
    rows: list[dict[str, Any]],
    value_key: str,
    title: str,
    value_fmt: str,
    *,
    max_value: float | None = None,
) -> str:
    resolved_max = max_value if max_value is not None else max(
        (float(row.get(value_key) or 0.0) for row in rows),
        default=0.0,
    )
    resolved_max = resolved_max or 1.0
    bars = []
    for row in rows:
        value = float(row.get(value_key) or 0.0)
        width = (value / resolved_max) * 100
        bars.append(
            "<div class=\"bar-row\">"
            f"<div class=\"bar-label\">{html.escape(row['label'])}</div>"
            f"<div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:{width:.2f}%\"></div></div>"
            f"<div class=\"bar-value\">{value_fmt.format(value)}</div>"
            "</div>"
        )
    return f"<section><h3>{html.escape(title)}</h3>{''.join(bars)}</section>"


def render_grouped_bar_sections(
    rows: list[dict[str, Any]],
    *,
    title: str,
    value_key: str,
    value_fmt: str,
    description: str,
    include_empty_note: str,
) -> str:
    sections = [f"<section class=\"panel\"><h2>{html.escape(title)}</h2><p>{html.escape(description)}</p>"]
    global_max = max((float(row.get(value_key) or 0.0) for row in rows), default=0.0) or 1.0
    grouped = {group: [] for group in GROUP_ORDER}
    for row in rows:
        grouped[row["group"]].append(row)
    for group in GROUP_ORDER:
        group_rows = sorted(
            grouped[group],
            key=lambda item: float(item.get(value_key) or 0.0),
        )
        sections.append(f"<div class=\"cohort-block\"><h3>{html.escape(pretty_group(group))}</h3>")
        if group_rows:
            sections.append(
                render_bar_chart(
                    group_rows,
                    value_key,
                    f"{pretty_group(group)} cohort",
                    value_fmt,
                    max_value=global_max,
                )
            )
        else:
            sections.append(f"<p class=\"muted-note\">{html.escape(include_empty_note)}</p>")
        sections.append("</div>")
    sections.append("</section>")
    return "".join(sections)


def render_chat_breakdown(chat_breakdown: list[dict[str, Any]]) -> str:
    sections = ["<section class=\"panel\"><h2>Representative Chat Sets</h2><p>Each section below breaks the panel run apart by the representative small / medium / large chat instead of collapsing everything into one trio summary.</p>"]
    for block in chat_breakdown:
        chat = block["chat"]
        rows = block["rows"]
        body = []
        for row in rows:
            body.append(
                "<tr>"
                f"<td>{html.escape(pretty_group(row['group']))}</td>"
                f"<td>{html.escape(row['label'])}</td>"
                f"<td>{row['success_count']}/{row['task_count']}</td>"
                f"<td>{row['runtime_seconds']:.1f}s</td>"
                f"<td>{html.escape(row['failed_passes'])}</td>"
                f"<td>{html.escape(row['error_preview'] or '—')}</td>"
                "</tr>"
            )
        sections.append(
            "<div class=\"chat-block\">"
            f"<h3>{html.escape(chat['label'])}</h3>"
            f"<p><strong>{html.escape(chat['title'])}</strong><br><code>{html.escape(chat['relative_path'])}</code></p>"
            "<table><thead><tr>"
            "<th>group</th><th>model</th><th>passes ok</th><th>runtime</th><th>failed passes</th><th>error preview</th>"
            "</tr></thead><tbody>"
            + "".join(body)
            + "</tbody></table></div>"
        )
    sections.append("</section>")
    return "".join(sections)


def render_projection_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td>{html.escape(pretty_group(row['group']))}</td>"
            f"<td>{html.escape(row['label'])}</td>"
            f"<td>{money(row['archive_cost_heuristic'])}</td>"
            f"<td>{money(row['sample_cost_empirical'], 6) if row['sample_cost_empirical'] is not None else 'n/a'}</td>"
            f"<td>{money(row['archive_cost_empirical']) if row['archive_cost_empirical'] is not None else 'n/a'}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>group</th><th>model</th><th>archive heuristic</th><th>sample empirical</th><th>archive empirical</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def render_decision_preview(matrix: dict[str, Any]) -> str:
    criteria = "".join(f"<li>{html.escape(item['name'])}</li>" for item in matrix["criteria"])
    return (
        f"<p><strong>Options:</strong> {len(matrix['options'])}</p>"
        f"<p><strong>Criteria:</strong> {len(matrix['criteria'])}</p>"
        f"<ul>{criteria}</ul>"
    )


def render_quality_framework(quality_rows: list[dict[str, str]]) -> str:
    quality_summary = collect_quality_summary(quality_rows)
    rubric = """
    <table>
      <thead><tr><th>dimension</th><th>what it means</th><th>1</th><th>3</th><th>5</th></tr></thead>
      <tbody>
        <tr><td>factual accuracy</td><td>Are extracted claims grounded and correct?</td><td>frequent mistakes</td><td>mixed / usable</td><td>clean and trustworthy</td></tr>
        <tr><td>evidence quality</td><td>Do quotes and references support the claim?</td><td>weak / vague</td><td>some support</td><td>precise and strong</td></tr>
        <tr><td>false positive control</td><td>Does the model avoid overclaiming, especially in Pass 3/4?</td><td>overclaims often</td><td>mixed</td><td>careful and calibrated</td></tr>
        <tr><td>completeness</td><td>Did it catch the important material without obvious gaps?</td><td>misses major content</td><td>adequate</td><td>comprehensive</td></tr>
        <tr><td>synthesis utility</td><td>Will this be useful downstream for aggregation / RAG docs?</td><td>low utility</td><td>moderate utility</td><td>high utility</td></tr>
      </tbody>
    </table>
    """
    if not quality_summary:
        return (
            "<section class=\"panel\">"
            "<h2>Quality Rating Framework</h2>"
            "<p>No manual rubric scores are filled yet. Use the 1-5 scheme below in <code>quality_scores.csv</code>, then rerender this report to get per-model quality rollups.</p>"
            f"{rubric}"
            "<p class=\"muted-note\">Recommended overall quality rating: mean of the five rubric dimensions, then interpret it alongside operational reliability rather than hiding failures inside one number.</p>"
            "</section>"
        )

    body = []
    for row in sorted(quality_summary, key=lambda item: (item["overall"] is None, -(item["overall"] or 0))):
        def fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "n/a"
        body.append(
            "<tr>"
            f"<td>{html.escape(row['model'])}</td>"
            f"<td>{fmt(row['overall'])}</td>"
            f"<td>{fmt(row['factual_accuracy'])}</td>"
            f"<td>{fmt(row['evidence_quality'])}</td>"
            f"<td>{fmt(row['false_positive_risk'])}</td>"
            f"<td>{fmt(row['completeness'])}</td>"
            f"<td>{fmt(row['synthesis_utility'])}</td>"
            "</tr>"
        )
    return (
        "<section class=\"panel\">"
        "<h2>Quality Rating Framework</h2>"
        "<p>Manual quality scores are present. The table below rolls them up by model while keeping the rubric visible.</p>"
        "<table><thead><tr><th>model</th><th>overall</th><th>accuracy</th><th>evidence</th><th>false-positive control</th><th>completeness</th><th>synthesis utility</th></tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
        f"{rubric}"
        "</section>"
    )


def render_html(
    *,
    bundle_dir: Path,
    bundle_manifest: dict[str, Any],
    trio_manifest: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    projection_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, str]],
    privacy_rows: list[dict[str, str]],
    decision_matrix: dict[str, Any] | None,
) -> str:
    chat_breakdown = collect_chat_breakdown(bundle_manifest, trio_manifest, {item["resolved_id"]: item for item in load_json(CATALOG_PATH)["models"]})
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Retrospect Model Panel Review</title>
  <style>
    :root {{
      --bg: #f6f1e8;
      --paper: #fffdf9;
      --ink: #1f2328;
      --muted: #6a6f75;
      --line: #d7cfc2;
      --accent: #235347;
      --accent-soft: #dcebe6;
      --good: #2f7d4c;
      --warn: #b7791f;
      --bad: #b53a2d;
      --blue: #2962a3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #efe3cf 0, transparent 32%),
        linear-gradient(180deg, #f7f2ea 0%, #f2ece2 100%);
    }}
    .wrap {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    h1, h2, h3 {{ margin: 0 0 12px; line-height: 1.1; }}
    h1 {{ font-size: 40px; letter-spacing: -0.03em; }}
    h2 {{ font-size: 22px; margin-top: 32px; }}
    h3 {{ font-size: 16px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    p, li {{ line-height: 1.5; }}
    .hero {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 28px;
      box-shadow: 0 18px 50px rgba(71, 53, 29, 0.08);
    }}
    .hero p {{ color: var(--muted); margin: 8px 0 0; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 20px;
    }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
    }}
    .card .k {{
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .card .v {{
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px;
      margin-top: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      color: var(--blue);
      word-break: break-all;
    }}
    .chip {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .chip-green {{ background: #def3e6; color: var(--good); }}
    .chip-yellow {{ background: #f8ebcf; color: var(--warn); }}
    .chip-red {{ background: #f8d8d3; color: var(--bad); }}
    .chip-blue {{ background: #d8e8fb; color: var(--blue); }}
    .bar-row {{
      display: grid;
      grid-template-columns: 240px 1fr 100px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }}
    .bar-label {{
      font-size: 14px;
      font-weight: 600;
    }}
    .bar-track {{
      height: 12px;
      background: #ece3d4;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #c76d2d 0%, #235347 100%);
    }}
    .bar-value {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--muted);
    }}
    .split {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      margin-top: 18px;
    }}
    .cohort-block {{
      margin-top: 18px;
    }}
    .chat-block {{
      margin-top: 22px;
      padding-top: 8px;
      border-top: 1px solid var(--line);
    }}
    .muted-note {{
      color: var(--muted);
    }}
    @media (max-width: 960px) {{
      .grid, .split {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; }}
      .bar-value {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Retrospect Model Panel Review</h1>
      <p>Latest bundle: <code>{html.escape(str(bundle_dir))}</code></p>
      <p>Bundle runtime: <strong>{bundle_manifest['duration_seconds']:.1f}s</strong></p>
      <div class="grid">{render_summary_cards(bundle_manifest, summary_rows, quality_rows, privacy_rows)}</div>
    </section>

    <div class="split">
      <section class="panel">
        <h2>Representative Chat Set</h2>
        <p>The panel uses a fixed three-chat sample: one curated small chat, one medium chat, and one large chat.</p>
        <table><thead><tr><th>slot</th><th>title</th><th>size</th><th>path</th></tr></thead><tbody>
        {"".join(
            "<tr>"
            f"<td>{html.escape(item['label'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{item['byte_size']}</td>"
            f"<td><code>{html.escape(item['relative_path'])}</code></td>"
            "</tr>"
            for item in trio_manifest["selected_chats"]
        )}
        </tbody></table>
      </section>
      <section class="panel">
        <h2>Decision Matrix Preview</h2>
        {render_decision_preview(decision_matrix) if decision_matrix else '<p>No decision matrix found yet.</p>'}
      </section>
    </div>

    <section class="panel">
      <h2>Empirical Model Summary</h2>
      {render_summary_table(summary_rows)}
    </section>

    {render_grouped_bar_sections(
        summary_rows,
        title="Empirical Runtime By Cohort",
        value_key="runtime_seconds",
        value_fmt="{:.1f}s",
        description="Runtime bars use actual measured trio-run wall-clock time. Cohorts without completed runs stay empty until those runs exist.",
        include_empty_note="No runtime data yet for this cohort."
    )}

    {render_grouped_bar_sections(
        projection_rows,
        title="Projected Full-Archive Cost By Cohort",
        value_key="archive_cost_heuristic",
        value_fmt="${:.2f}",
        description="Cost bars use the current heuristic full-archive projection for every model in the catalog.",
        include_empty_note="No catalog entries in this cohort."
    )}

    {render_chat_breakdown(chat_breakdown)}

    {render_quality_framework(quality_rows)}

    <section class="panel">
      <h2>Cost Projections</h2>
      {render_projection_table(projection_rows)}
    </section>
  </div>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    bundle_dir = Path(args.bundle) if args.bundle else latest_bundle()
    if bundle_dir is None:
        raise SystemExit("No model-panel bundle found. Run scripts/run_model_panel.py first.")

    bundle_manifest = load_json(bundle_dir / "bundle_manifest.json")
    trio_manifest = load_json(TRIO_PATH)
    catalog = load_json(CATALOG_PATH)
    catalog_by_model = {item["resolved_id"]: item for item in catalog["models"]}
    quality_rows = load_csv_rows(bundle_dir / "quality_scores.csv")
    privacy_rows = load_csv_rows(bundle_dir / "privacy_review.csv")
    decision_matrix = load_json(DECISION_PATH) if DECISION_PATH.exists() else None

    summary_rows = collect_summary_rows(bundle_manifest, catalog_by_model)
    projection_rows = collect_projection_rows(summary_rows, catalog)

    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = (RETROSPECT_ROOT / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_html(
            bundle_dir=bundle_dir,
            bundle_manifest=bundle_manifest,
            trio_manifest=trio_manifest,
            summary_rows=summary_rows,
            projection_rows=projection_rows,
            quality_rows=quality_rows,
            privacy_rows=privacy_rows,
            decision_matrix=decision_matrix,
        ),
        encoding="utf-8",
    )

    print(f"Bundle: {bundle_dir}")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
