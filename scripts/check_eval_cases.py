#!/usr/bin/env python3
"""Validate the process evaluation corpus and registry contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def validate(path: Path, schema_path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{path}: {error.message}" for error in validator.iter_errors(data)]


def main() -> int:
    errors: list[str] = []
    case_schema = ROOT / "evals/case.schema.json"
    case_ids: set[str] = set()
    for path in sorted((ROOT / "evals/cases").glob("*.yaml")):
        errors.extend(validate(path, case_schema))
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        case_id = data.get("id")
        if case_id in case_ids:
            errors.append(f"{path}: duplicate case ID {case_id}")
        case_ids.add(case_id)

    registry_path = ROOT / "extensions/index.yaml"
    errors.extend(validate(registry_path, ROOT / "schemas/extension-registry-v1.schema.json"))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    entries = registry.get("entries", [])
    entry_ids = {entry.get("id") for entry in entries}
    if len(entry_ids) != len(entries):
        errors.append("extensions/index.yaml: duplicate entry ID")
    for entry in entries:
        for dependency in entry.get("composes", []):
            if dependency not in entry_ids:
                errors.append(f"extensions/index.yaml: {entry.get('id')} composes unknown {dependency}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(case_ids)} evaluation cases and {len(entries)} extension entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
