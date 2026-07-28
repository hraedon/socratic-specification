"""Spec smell checker — heuristic under-probing detector (debate 004 pilot).

Standalone module that analyzes a spec.yaml for likely under-probed translations.
Produces advisory warnings, not errors. Does not block synthesis.

Usage:
    python scripts/spec_smells.py spec.yaml
    python scripts/spec_smells.py tests/fixtures/valid-spec-v2.yaml --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


@dataclass
class Smell:
    check: str
    severity: str
    location: str
    text: str
    suggestion: str


ABSOLUTE_WORDS = re.compile(
    r"\b(all|every|always|never|any|no)\b", re.IGNORECASE
)
SCOPE_QUALIFIERS = re.compile(
    r"\b(in scope|out of scope|for this|limited to|only|when|if|unless|except|"
    r"defined|bounded|restricted|up to|at most|at least)\b",
    re.IGNORECASE,
)
SINGLE_NUMBER_NFR = re.compile(r"\b\d+(\.\d+)?\s*(ms|s|sec|seconds?|mb|gb|kb|%)\b", re.IGNORECASE)
NFR_CONTEXT = re.compile(
    r"\b(under load|concurrent|users?|requests?|per second|p95|p99|median|"
    r"average|which operation|for the)\b",
    re.IGNORECASE,
)
SECURITY_WORDS = re.compile(r"\b(secure|safe|protect|encrypt|auth)\b", re.IGNORECASE)
SECURITY_MECHANISMS = re.compile(
    r"\b(https|tls|bcrypt|argon|rbac|oauth|jwt|token|password hash|audit log|"
    r"role.based|mfa|2fa|csrf|csp|hmac)\b",
    re.IGNORECASE,
)
STATE_ENTITIES = re.compile(
    r"\b(order|task|job|request|ticket|workflow|process|submission|application|"
    r"registration|enrollment|payment|invoice)\b",
    re.IGNORECASE,
)
STATE_TRANSITIONS = re.compile(
    r"\b(state|status|transition|pending|active|completed|cancelled|failed|"
    r"shipped|delivered|approved|rejected|in.progress)\b",
    re.IGNORECASE,
)
ROLE_WORDS = re.compile(r"\b(admin|user|operator|manager|editor|viewer|guest|member)\b", re.IGNORECASE)
ROLE_DEFINITIONS = re.compile(
    r"\b(permission|role|access control|rbac|can view|can edit|can delete|"
    r"authorized|restricted to|distinguished by)\b",
    re.IGNORECASE,
)


def _collect_text_blocks(spec: dict) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            blocks.append((path, obj))

    walk(spec)
    return blocks


def check_unqualified_absolutes(spec: dict) -> list[Smell]:
    smells = []
    for path, text in _collect_text_blocks(spec):
        if "provenance" in path or "glossary" in path:
            continue
        for match in ABSOLUTE_WORDS.finditer(text):
            context_start = max(0, match.start() - 40)
            context_end = min(len(text), match.end() + 40)
            context = text[context_start:context_end]
            if not SCOPE_QUALIFIERS.search(context):
                smells.append(Smell(
                    check="unqualified_absolute",
                    severity="info",
                    location=path,
                    text=text[:120],
                    suggestion=f"'{match.group()}' used without bounded scope — consider defining the set",
                ))
                break
    return smells


def check_single_number_nfrs(spec: dict) -> list[Smell]:
    smells = []
    nfr = spec.get("nfr", {})
    if not isinstance(nfr, dict):
        return smells
    for key, value in nfr.items():
        if not isinstance(value, str):
            continue
        numbers = SINGLE_NUMBER_NFR.findall(value)
        if len(numbers) == 1 and not NFR_CONTEXT.search(value):
            smells.append(Smell(
                check="single_number_nfr",
                severity="warning",
                location=f"nfr.{key}",
                text=value[:120],
                suggestion="Single number without load/operation context — which operation, under what conditions?",
            ))
    return smells


def check_missing_state_machines(spec: dict) -> list[Smell]:
    smells = []
    all_text = " ".join(text for _, text in _collect_text_blocks(spec))
    entities_found = set()
    for match in STATE_ENTITIES.finditer(all_text):
        entities_found.add(match.group().lower())
    if entities_found and not STATE_TRANSITIONS.search(all_text):
        smells.append(Smell(
            check="missing_state_machine",
            severity="warning",
            location="(document-wide)",
            text=f"Entities implying state: {', '.join(sorted(entities_found))}",
            suggestion="These entities typically have lifecycle states — define transitions or record as assumption",
        ))
    return smells


def check_implicit_roles(spec: dict) -> list[Smell]:
    smells = []
    all_text = " ".join(text for _, text in _collect_text_blocks(spec))
    roles_found = set()
    for match in ROLE_WORDS.finditer(all_text):
        roles_found.add(match.group().lower())
    if roles_found and not ROLE_DEFINITIONS.search(all_text):
        smells.append(Smell(
            check="implicit_roles",
            severity="info",
            location="(document-wide)",
            text=f"Actors mentioned: {', '.join(sorted(roles_found))}",
            suggestion="Roles mentioned without permission boundaries — define access or record as assumption",
        ))
    return smells


def check_vacuous_security(spec: dict) -> list[Smell]:
    smells = []
    for path, text in _collect_text_blocks(spec):
        if SECURITY_WORDS.search(text) and not SECURITY_MECHANISMS.search(text):
            smells.append(Smell(
                check="vacuous_security",
                severity="warning",
                location=path,
                text=text[:120],
                suggestion="Security language without specific mechanism — what threat model?",
            ))
            break
    return smells


def check_assumption_ratio(spec: dict) -> list[Smell]:
    smells = []
    frs = spec.get("functional_requirements", [])
    assumptions = spec.get("assumptions", [])
    if isinstance(assumptions, list) and isinstance(frs, list):
        if len(frs) > 0 and len(assumptions) > len(frs) * 0.5:
            smells.append(Smell(
                check="assumption_ratio",
                severity="info",
                location="assumptions",
                text=f"{len(assumptions)} assumptions vs {len(frs)} functional requirements",
                suggestion="High assumption-to-requirement ratio may indicate under-probing",
            ))
    return smells


ALL_CHECKS = [
    check_unqualified_absolutes,
    check_single_number_nfrs,
    check_missing_state_machines,
    check_implicit_roles,
    check_vacuous_security,
    check_assumption_ratio,
]


def run_smell_checks(spec: dict) -> list[Smell]:
    smells: list[Smell] = []
    for check in ALL_CHECKS:
        smells.extend(check(spec))
    return smells


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Spec smell checker (debate 004 pilot)")
    parser.add_argument("spec", type=Path, help="Path to spec.yaml")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    if not args.spec.exists():
        print(f"error: {args.spec} not found", file=sys.stderr)
        return 1

    with args.spec.open() as f:
        spec = yaml.safe_load(f)

    if not isinstance(spec, dict):
        print(f"error: {args.spec} is not a YAML mapping", file=sys.stderr)
        return 1

    smells = run_smell_checks(spec)

    if args.json:
        print(json.dumps([asdict(s) for s in smells], indent=2))
    else:
        if not smells:
            print(f"{args.spec}: no smells detected")
        else:
            print(f"{args.spec}: {len(smells)} smell(s) detected\n")
            for s in smells:
                print(f"  [{s.severity}] {s.check} @ {s.location}")
                print(f"    text: {s.text}")
                print(f"    → {s.suggestion}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
