#!/usr/bin/env python3
"""Render the listening script into one or more OpenAI TTS audio files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = RETROSPECT_ROOT.parent
LISTENING_ROOT = RETROSPECT_ROOT / "data" / "listening"
DEFAULT_SCRIPT_PATH = LISTENING_ROOT / "scripts" / "listening_script.md"
DEFAULT_OUTPUT_DIR = LISTENING_ROOT / "audio"
DEFAULT_MANIFEST_PATH = LISTENING_ROOT / "manifests" / "listening_render.json"
DEFAULT_SOURCE_FILES = [
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "values_and_cares.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "purpose_and_meaning.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "optimization_model.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "blind_spots_and_change_levers.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "routine_and_decision_tree.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "questions_to_ask_yourself.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "narrative_identity.md",
    RETROSPECT_ROOT / "data" / "knowledge_base" / "analysis" / "sensitive_conversation_guide.md",
]
DEFAULT_INSTRUCTIONS = "calm, grounded, reflective, direct, not overly theatrical"
STRATEGY_VERSION = "listening-audio-v1"
DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "sage"
SPEECH_ENDPOINT = "https://api.openai.com/v1/audio/speech"
MAX_API_INPUT_CHARS = 4096
DEFAULT_MAX_CHARS = 3800
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the listening script via OpenAI TTS")
    parser.add_argument(
        "--script-path",
        default=str(DEFAULT_SCRIPT_PATH),
        help="Path to the speech-ready Markdown script.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for rendered audio files.",
    )
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to write the render manifest JSON.",
    )
    parser.add_argument(
        "--source-file",
        dest="source_files",
        action="append",
        help="Source analysis file used to create the script. Repeat to override the defaults.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenAI TTS model. Default: gpt-4o-mini-tts.",
    )
    parser.add_argument(
        "--voice",
        dest="voices",
        action="append",
        help="Voice to render. Repeat to compare multiple built-in voices.",
    )
    parser.add_argument(
        "--instructions",
        default=DEFAULT_INSTRUCTIONS,
        help="Style instructions forwarded to gpt-4o-mini-tts.",
    )
    parser.add_argument(
        "--response-format",
        choices=["mp3", "opus", "aac", "flac", "wav", "pcm"],
        default="mp3",
        help="Audio format for rendered files.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help="Maximum characters per API chunk. Must stay at or below 4096.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Optional cap on rendered chunks, useful for voice preview passes.",
    )
    parser.add_argument(
        "--output-stem",
        default=None,
        help="Optional stem for output filenames. Defaults to the script stem.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="HTTP timeout per TTS request.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare chunks and manifest without calling the API.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing audio files.",
    )
    return parser.parse_args()


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def strip_markdown(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if re.match(r"^#{1,6}\s+", line):
            continue
        line = MARKDOWN_LINK_RE.sub(r"\1", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        line = line.replace("**", "")
        line = line.replace("*", "")
        line = line.replace("`", "")
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_unit(unit: str, max_chars: int) -> list[str]:
    unit = unit.strip()
    if len(unit) <= max_chars:
        return [unit]

    sentences = [part.strip() for part in SENTENCE_BOUNDARY_RE.split(unit) if part.strip()]
    if len(sentences) == 1:
        words = unit.split()
        chunks: list[str] = []
        current_words: list[str] = []
        for word in words:
            candidate = " ".join(current_words + [word]).strip()
            if current_words and len(candidate) > max_chars:
                chunks.append(" ".join(current_words))
                current_words = [word]
                continue
            current_words.append(word)
        if current_words:
            chunks.append(" ".join(current_words))
        return chunks

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if current and len(candidate) > max_chars:
            chunks.extend(split_long_unit(current, max_chars))
            current = sentence
            continue
        current = candidate
    if current:
        chunks.extend(split_long_unit(current, max_chars))
    return chunks


def chunk_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        units = split_long_unit(paragraph, max_chars)
        for unit in units:
            candidate = unit if not current else f"{current}\n\n{unit}"
            if current and len(candidate) > max_chars:
                chunks.append(current.strip())
                current = unit
                continue
            current = candidate

    if current:
        chunks.append(current.strip())
    return chunks


def build_payload(args: argparse.Namespace, *, voice: str, chunk: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "voice": voice,
        "input": chunk,
        "response_format": args.response_format,
        "speed": args.speed,
    }
    if args.instructions:
        if args.model in {"tts-1", "tts-1-hd"}:
            raise SystemExit("--instructions is only supported here for gpt-4o-mini-tts, not tts-1/tts-1-hd.")
        payload["instructions"] = args.instructions
    return payload


def render_chunk(
    api_key: str,
    payload: dict[str, Any],
    destination: Path,
    *,
    timeout_seconds: int,
) -> None:
    response = requests.post(
        SPEECH_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout_seconds,
    )
    if response.status_code >= 400:
        detail = response.text.strip()
        raise RuntimeError(f"TTS request failed with HTTP {response.status_code}: {detail[:500]}")
    destination.write_bytes(response.content)


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def absolute_strings(paths: list[Path]) -> list[str]:
    return [str(path.resolve()) for path in paths]


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = parse_args()
    if args.max_chars <= 0 or args.max_chars > MAX_API_INPUT_CHARS:
        raise SystemExit("--max-chars must be between 1 and 4096.")

    script_path = Path(args.script_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest_path).resolve()
    source_files = [Path(item).resolve() for item in (args.source_files or DEFAULT_SOURCE_FILES)]
    voices = args.voices or [DEFAULT_VOICE]

    if not script_path.exists():
        raise SystemExit(f"Script not found: {script_path}")

    script_markdown = script_path.read_text(encoding="utf-8")
    script_text = strip_markdown(script_markdown)
    all_chunks = chunk_text(script_text, args.max_chars)
    if args.max_chunks is not None:
        all_chunks = all_chunks[: args.max_chunks]

    if not all_chunks:
        raise SystemExit("Script produced no renderable text.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_stem = args.output_stem or script_path.stem
    render_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    manifest: dict[str, Any] = {
        "strategy_version": STRATEGY_VERSION,
        "rendered_at": render_time,
        "source_input_files": absolute_strings(source_files),
        "script_file": str(script_path),
        "script_markdown_chars": len(script_markdown),
        "script_render_chars": len(script_text),
        "chunk_count": len(all_chunks),
        "max_chunk_chars": args.max_chars,
        "model": args.model,
        "voices": [],
        "instructions": args.instructions,
        "response_format": args.response_format,
        "speed": args.speed,
        "api_endpoint": SPEECH_ENDPOINT,
        "dry_run": args.dry_run,
    }

    api_key = os.environ.get("OPENAI_API_KEY")
    if not args.dry_run and not api_key:
        raise SystemExit("OPENAI_API_KEY is required unless --dry-run is set.")

    for voice in voices:
        voice_entry: dict[str, Any] = {
            "voice": voice,
            "chunks": [],
        }
        for index, chunk in enumerate(all_chunks, start=1):
            suffix = f"_{voice}" if len(voices) > 1 else ""
            filename = f"{output_stem}{suffix}_part_{index:02d}.{args.response_format}"
            destination = output_dir / filename
            if destination.exists() and not args.force:
                raise SystemExit(f"Refusing to overwrite existing file without --force: {destination}")

            chunk_entry = {
                "index": index,
                "text_chars": len(chunk),
                "preview": chunk[:120],
                "output_file": str(destination),
            }

            if args.dry_run:
                chunk_entry["status"] = "dry_run"
            else:
                payload = build_payload(args, voice=voice, chunk=chunk)
                render_chunk(api_key, payload, destination, timeout_seconds=args.timeout_seconds)
                chunk_entry["status"] = "rendered"

            voice_entry["chunks"].append(chunk_entry)

        manifest["voices"].append(voice_entry)

    write_manifest(manifest_path, manifest)

    print(f"Script: {script_path}")
    print(f"Chunks: {len(all_chunks)}")
    print(f"Manifest: {manifest_path}")
    for voice in manifest["voices"]:
        rendered_files = [item["output_file"] for item in voice["chunks"]]
        print(f"Voice {voice['voice']}: {len(rendered_files)} file(s)")
        for path in rendered_files:
            print(f"  {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
