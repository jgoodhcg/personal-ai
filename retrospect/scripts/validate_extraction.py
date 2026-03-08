#!/usr/bin/env python3
"""Validate extraction JSON files against their schemas.

Usage (from retrospect/):
    uv run python scripts/validate_extraction.py <file_or_dir> [--pass PASS_ID]
    uv run python scripts/validate_extraction.py data/extractions/some_file.json
    uv run python scripts/validate_extraction.py data/extractions/ --pass pass1_summary

Validates JSON extraction output against the appropriate schema.
The pass is determined from the file's metadata.pass_id field, or can be
overridden with --pass.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, RefResolver
except ImportError:
    print("Missing dependency: pip install jsonschema")
    print("Or: uv add jsonschema")
    sys.exit(1)

RETROSPECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = RETROSPECT_ROOT / "schemas"

PASS_SCHEMAS = {
    "pass1_summary": "pass1_summary.json",
    "pass2_projects": "pass2_projects.json",
    "pass3_people": "pass3_people.json",
    "pass4_psych": "pass4_psych.json",
}


def load_schema(pass_id: str) -> dict:
    schema_file = SCHEMA_DIR / PASS_SCHEMAS[pass_id]
    with open(schema_file) as f:
        return json.load(f)


def build_resolver() -> RefResolver:
    """Build a resolver that can follow $ref to _definitions.json."""
    defs_path = SCHEMA_DIR / "_definitions.json"
    with open(defs_path) as f:
        definitions = json.load(f)

    store = {
        "_definitions.json": definitions,
    }
    for pass_id, filename in PASS_SCHEMAS.items():
        schema_path = SCHEMA_DIR / filename
        with open(schema_path) as f:
            store[filename] = json.load(f)

    return RefResolver(
        base_uri=f"file://{SCHEMA_DIR}/",
        referrer=definitions,
        store=store,
    )


def validate_file(filepath: Path, pass_id_override: str | None = None) -> list[str]:
    """Validate a single JSON file. Returns list of error messages."""
    with open(filepath) as f:
        data = json.load(f)

    pass_id = pass_id_override or data.get("metadata", {}).get("pass_id")
    if not pass_id:
        return [f"Cannot determine pass_id for {filepath}. Use --pass to specify."]

    if pass_id not in PASS_SCHEMAS:
        return [
            f"Unknown pass_id '{pass_id}'. Expected one of: {list(PASS_SCHEMAS.keys())}"
        ]

    schema = load_schema(pass_id)
    resolver = build_resolver()
    validator = Draft202012Validator(schema, resolver=resolver)

    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.path) or "(root)"
        errors.append(f"  {path}: {error.message}")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate extraction JSON against schemas"
    )
    parser.add_argument("target", type=Path, help="JSON file or directory to validate")
    parser.add_argument(
        "--pass",
        dest="pass_id",
        choices=list(PASS_SCHEMAS.keys()),
        help="Override pass_id detection",
    )
    args = parser.parse_args()

    if args.target.is_file():
        files = [args.target]
    elif args.target.is_dir():
        files = sorted(args.target.glob("**/*.json"))
    else:
        print(f"Error: {args.target} not found")
        sys.exit(1)

    if not files:
        print(f"No JSON files found in {args.target}")
        sys.exit(1)

    total_errors = 0
    for filepath in files:
        errors = validate_file(filepath, args.pass_id)
        if errors:
            print(f"FAIL {filepath.name}")
            for e in errors:
                print(e)
            total_errors += len(errors)
        else:
            print(f"OK   {filepath.name}")

    print(f"\n{len(files)} files checked, {total_errors} errors")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
