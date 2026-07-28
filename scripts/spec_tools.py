#!/usr/bin/env python3
"""Validate and render Socratic specification artifacts.

The YAML artifact is canonical. Markdown files are deterministic generated views.
Structural schemas catch malformed records; semantic checks catch broken references,
coverage gaps, and readiness claims that cannot be true.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
STANDARD_CONSUMER_LAYERS = {
    "parser",
    "domain_model",
    "persistence",
    "api",
    "browser",
    "validation",
    "comparison_hashing",
    "export",
    "documentation",
}
REVIEW_COVERAGE_FIELDS = {
    "invariant_coverage",
    "consumer_coverage",
    "compatibility_coverage",
    "fr_ac_coverage",
    "work_package_coverage",
    "verification_coverage",
    "quality_gate_coverage",
    "adversarial_coverage",
}


class ArtifactError(ValueError):
    """A user-correctable artifact validation error."""


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ArtifactError(f"{path}: cannot read YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactError(f"{path}: top level must be a mapping")
    return value


def canonical_fingerprint(data: dict[str, Any]) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _format_json_path(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{_format_json_path(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def _duplicate_errors(items: list[dict[str, Any]], field: str, label: str) -> list[str]:
    counts = Counter(item.get(field) for item in items)
    return [f"duplicate {label}: {value}" for value, count in counts.items() if value and count > 1]


def _unknown_refs(refs: Iterable[str], known: set[str], context: str) -> list[str]:
    return [f"{context} references unknown ID {ref}" for ref in refs if ref not in known]


def validate_spec_semantics(data: dict[str, Any], *, ready: bool = False) -> list[str]:
    errors: list[str] = []
    meta = data.get("meta", {})
    revision = meta.get("revision")
    parent = meta.get("parent_fingerprint")
    if revision == 1 and parent not in (None, ""):
        errors.append("meta.parent_fingerprint must be null on revision 1")
    if isinstance(revision, int) and revision > 1 and not parent:
        errors.append("meta.parent_fingerprint is required after revision 1")

    frs = data.get("functional_requirements", [])
    acs = data.get("acceptance_criteria", [])
    rules = data.get("business_rules", [])
    risks = data.get("risks", [])
    errors.extend(_duplicate_errors(frs, "id", "FR ID"))
    errors.extend(_duplicate_errors(acs, "id", "AC ID"))
    errors.extend(_duplicate_errors(rules, "id", "business-rule ID"))
    errors.extend(_duplicate_errors(risks, "id", "risk ID"))

    fr_ids = {item.get("id") for item in frs if item.get("id")}
    ac_ids = {item.get("id") for item in acs if item.get("id")}
    mvp_ids = set(data.get("mvp", {}).get("fr_ids", []))
    errors.extend(_unknown_refs(mvp_ids, fr_ids, "mvp.fr_ids"))
    flagged_mvp = {item.get("id") for item in frs if item.get("mvp") is True}
    if flagged_mvp != mvp_ids:
        errors.append(
            "mvp.fr_ids must exactly match functional_requirements with mvp: true "
            f"(list={sorted(mvp_ids)}, flags={sorted(flagged_mvp)})"
        )

    for item in data.get("mvp", {}).get("architectural_prerequisites", []):
        errors.extend(_unknown_refs([item.get("fr_id")], fr_ids, "architectural prerequisite"))

    ac_coverage: set[str] = set()
    for ac in acs:
        refs = ac.get("fr_ids", [])
        ac_coverage.update(refs)
        errors.extend(_unknown_refs(refs, fr_ids, f"{ac.get('id', 'acceptance criterion')}.fr_ids"))
    missing_mvp_ac = mvp_ids - ac_coverage
    if missing_mvp_ac:
        errors.append(f"MVP FRs without acceptance criteria: {sorted(missing_mvp_ac)}")

    phases = data.get("work_decomposition", {}).get("value_phases", [])
    errors.extend(_duplicate_errors(phases, "phase", "value phase"))
    for phase in phases:
        errors.extend(_unknown_refs(phase.get("fr_ids", []), fr_ids, f"value phase {phase.get('phase')}") )
    if phases:
        phase_one = next((set(p.get("fr_ids", [])) for p in phases if p.get("phase") == 1), None)
        if phase_one is None:
            errors.append("work_decomposition.value_phases must include phase 1")
        elif phase_one != mvp_ids:
            errors.append("value phase 1 FRs must exactly match mvp.fr_ids")

    for hint in data.get("work_decomposition", {}).get("dependency_hints", []):
        subject = hint.get("fr_id")
        errors.extend(_unknown_refs([subject], fr_ids, "dependency hint"))
        refs = list(hint.get("requires", [])) + list(hint.get("parallel_with", []))
        errors.extend(_unknown_refs(refs, fr_ids, f"dependency hint {subject}"))
        if subject in refs:
            errors.append(f"dependency hint {subject} cannot reference itself")

    if ready:
        blocking = [
            q.get("question", "<unnamed>")
            for q in data.get("open_questions", [])
            if q.get("category") == "blocked"
        ]
        if blocking:
            errors.append(f"blocking open questions remain: {blocking}")
        undecided = [
            d.get("decision", "<unnamed>")
            for d in data.get("high_coupling_decisions", [])
            if not d.get("status")
        ]
        if undecided:
            errors.append(f"high-coupling decisions without status: {undecided}")

    # Keep the local variables visible to future validator additions and prevent
    # accidental removal of AC uniqueness checks as the schema evolves.
    _ = ac_ids
    return errors


def _cycle_errors(graph: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    errors: list[str] = []

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            start = path.index(node)
            errors.append("work-package dependency cycle: " + " -> ".join(path[start:] + [node]))
            return
        if node in visited:
            return
        visiting.add(node)
        for child in graph.get(node, []):
            visit(child, path + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])
    return sorted(set(errors))


def validate_work_plan_semantics(
    data: dict[str, Any], *, artifact_path: Path | None = None, ready: bool = False, handoff: bool = False
) -> list[str]:
    errors: list[str] = []
    invariants = data.get("invariants", [])
    contracts = data.get("changed_contracts", [])
    packages = data.get("work_packages", [])
    verification = data.get("verification", [])

    for items, field, label in (
        (invariants, "id", "invariant ID"),
        (contracts, "id", "contract ID"),
        (packages, "id", "work-package ID"),
        (verification, "id", "verification ID"),
    ):
        errors.extend(_duplicate_errors(items, field, label))

    invariant_ids = {item.get("id") for item in invariants if item.get("id")}
    contract_ids = {item.get("id") for item in contracts if item.get("id")}
    package_ids = {item.get("id") for item in packages if item.get("id")}
    verify_ids = {item.get("id") for item in verification if item.get("id")}
    target_intent = set(data.get("phase_plan", {}).get("intent_ids", []))
    known_intent: set[str] = set()
    known_acceptance: set[str] = set()
    required_acceptance: set[str] = set()

    source = data.get("source", {})
    declared_source = source.get("artifact_path")
    source_path: Path | None = None
    if declared_source:
        candidate = Path(declared_source)
        candidates = [candidate] if candidate.is_absolute() else [Path.cwd() / candidate]
        if artifact_path is not None and not candidate.is_absolute():
            candidates.append(artifact_path.parent / candidate)
        source_path = next((item for item in candidates if item.exists()), None)
    if source_path is None:
        errors.append(f"source artifact does not exist: {declared_source}")
    else:
        try:
            source_data = load_yaml(source_path)
            actual_fingerprint = canonical_fingerprint(source_data)
            if source.get("artifact_fingerprint") != actual_fingerprint:
                errors.append(
                    "source.artifact_fingerprint does not match the canonical source "
                    f"({source.get('artifact_fingerprint')} != {actual_fingerprint})"
                )
            if source.get("artifact_kind") == "spec":
                frs = source_data.get("functional_requirements", [])
                criteria = source_data.get("acceptance_criteria", [])
                known_intent = {item.get("id") for item in frs if item.get("id")}
                known_acceptance = {item.get("id") for item in criteria if item.get("id")}
                phase_number = data.get("phase_plan", {}).get("target_value_phase")
                phase = next(
                    (
                        item
                        for item in source_data.get("work_decomposition", {}).get("value_phases", [])
                        if item.get("phase") == phase_number
                    ),
                    None,
                )
                if phase is None:
                    errors.append(f"source spec has no value phase {phase_number}")
                else:
                    expected_intent = set(phase.get("fr_ids", []))
                    if target_intent != expected_intent:
                        errors.append(
                            "phase_plan.intent_ids must exactly match the source value phase "
                            f"({sorted(target_intent)} != {sorted(expected_intent)})"
                        )
                required_acceptance = {
                    item.get("id")
                    for item in criteria
                    if set(item.get("fr_ids", [])) & target_intent
                }
            elif source.get("artifact_kind") == "change_spec":
                criteria = source_data.get("acceptance_criteria", [])
                known_intent = {item.get("id") for item in criteria if item.get("id")}
                known_acceptance = set(known_intent)
                required_acceptance = set(known_intent)
                if target_intent != known_intent:
                    errors.append(
                        "phase_plan.intent_ids must exactly match change-spec acceptance IDs "
                        f"({sorted(target_intent)} != {sorted(known_intent)})"
                    )
                if data.get("phase_plan", {}).get("target_value_phase") != 0:
                    errors.append("change-spec work plans use target_value_phase: 0")
        except ArtifactError as exc:
            errors.append(str(exc))

    errors.extend(_unknown_refs(target_intent, known_intent, "phase_plan.intent_ids"))

    covered_intent: set[str] = set()
    covered_acceptance: set[str] = set()
    for package in packages:
        package_id = package.get("id", "<package>")
        package_intent = package.get("intent_ids", [])
        package_acceptance = package.get("acceptance_criteria_ids", [])
        covered_intent.update(package_intent)
        covered_acceptance.update(package_acceptance)
        errors.extend(_unknown_refs(package_intent, known_intent, package_id))
        errors.extend(_unknown_refs(package_acceptance, known_acceptance, package_id))
        errors.extend(_unknown_refs(package.get("invariant_ids", []), invariant_ids, package_id))
        errors.extend(_unknown_refs(package.get("contract_ids", []), contract_ids, package_id))
        errors.extend(_unknown_refs(package.get("owns_contracts", []), contract_ids, package_id))
        errors.extend(_unknown_refs(package.get("depends_on", []), package_ids, package_id))
        errors.extend(_unknown_refs(package.get("verification_ids", []), verify_ids, package_id))
        if package_id in package.get("depends_on", []):
            errors.append(f"{package_id} cannot depend on itself")
    missing_intent = target_intent - covered_intent
    if missing_intent:
        errors.append(f"target intent IDs without work packages: {sorted(missing_intent)}")
    missing_acceptance = required_acceptance - covered_acceptance
    if missing_acceptance:
        errors.append(f"target acceptance criteria without work packages: {sorted(missing_acceptance)}")
    graph = {p.get("id"): p.get("depends_on", []) for p in packages if p.get("id")}
    errors.extend(_cycle_errors(graph))

    for invariant in invariants:
        errors.extend(
            _unknown_refs(
                invariant.get("verification_ids", []), verify_ids, invariant.get("id", "invariant")
            )
        )

    for contract in contracts:
        contract_id = contract.get("id", "<contract>")
        errors.extend(_unknown_refs(contract.get("invariant_ids", []), invariant_ids, contract_id))
        consumers = contract.get("consumers", [])
        counts = Counter(c.get("layer") for c in consumers if c.get("layer") in STANDARD_CONSUMER_LAYERS)
        missing_layers = STANDARD_CONSUMER_LAYERS - set(counts)
        duplicate_layers = {layer for layer, count in counts.items() if count > 1}
        if missing_layers:
            errors.append(f"{contract_id} omits consumer layers: {sorted(missing_layers)}")
        if duplicate_layers:
            errors.append(f"{contract_id} duplicates consumer layers: {sorted(duplicate_layers)}")
        for consumer in consumers:
            refs = consumer.get("work_package_ids", [])
            errors.extend(_unknown_refs(refs, package_ids, f"{contract_id}:{consumer.get('layer')}") )
            if consumer.get("status") == "affected" and not refs:
                errors.append(f"{contract_id}:{consumer.get('layer')} is affected but has no work package")

    compatibility = data.get("compatibility", {})
    if compatibility.get("required") and not compatibility.get("versions"):
        errors.append("compatibility.required is true but no versions are enumerated")

    for item in verification:
        verify_id = item.get("id", "<verification>")
        errors.extend(_unknown_refs(item.get("covers_intent_ids", []), known_intent, verify_id))
        errors.extend(
            _unknown_refs(
                item.get("covers_acceptance_criteria_ids", []), known_acceptance, verify_id
            )
        )
        errors.extend(_unknown_refs(item.get("covers_invariant_ids", []), invariant_ids, verify_id))
        errors.extend(_unknown_refs(item.get("covers_contract_ids", []), contract_ids, verify_id))

    for case in data.get("adversarial_matrix", []):
        case_name = case.get("case", "<case>")
        refs = case.get("verification_ids", [])
        errors.extend(_unknown_refs(refs, verify_ids, f"adversarial case {case_name}"))
        if case.get("applicability") == "required" and not refs:
            errors.append(f"required adversarial case {case_name} has no verification")
        if case.get("applicability") == "not_applicable" and not case.get("reason"):
            errors.append(f"not-applicable adversarial case {case_name} needs a reason")

    if ready or handoff:
        review = data.get("readiness_review", {})
        if not review.get("reviewer"):
            errors.append("readiness_review.reviewer is required before implementation")
        for field in REVIEW_COVERAGE_FIELDS:
            if review.get(field) != "pass":
                errors.append(f"readiness_review.{field} must be pass")
        if review.get("unresolved_findings"):
            errors.append("readiness_review.unresolved_findings must be empty")

    if handoff:
        for package in packages:
            if package.get("status") != "pass":
                errors.append(f"{package.get('id')} is not passing at handoff")
        for item in verification:
            if item.get("result") != "pass":
                errors.append(f"{item.get('id')} is not passing at handoff")
        for gate in data.get("quality_gates", []):
            if gate.get("required") and gate.get("result") != "pass":
                errors.append(f"required quality gate {gate.get('name')} is not passing")
        if data.get("handoff", {}).get("review_result") != "pass":
            errors.append("handoff.review_result must be pass")

    return errors


def validate_artifact(
    path: Path,
    *,
    kind: str,
    ready: bool = False,
    handoff: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    data = load_yaml(path)
    if kind == "auto":
        if "plan_version" in data:
            kind = "work-plan"
        elif "change_schema_version" in data:
            kind = "change-spec"
        else:
            kind = "spec"
    if kind == "spec":
        version = data.get("meta", {}).get("schema_version")
        if version is None:
            return data, ["legacy implicit-v1 spec: migrate to schema v2 before canonical use"]
        if version != 2:
            return data, [f"unsupported spec schema version {version}; this tool supports 2"]
        errors = schema_errors(data, ROOT / "schemas/spec-v2.schema.json")
        errors.extend(validate_spec_semantics(data, ready=ready))
    elif kind == "work-plan":
        version = data.get("plan_version")
        if version != 1:
            return data, [f"unsupported work-plan version {version}; this tool supports 1"]
        errors = schema_errors(data, ROOT / "schemas/work-plan-v1.schema.json")
        errors.extend(
            validate_work_plan_semantics(
                data, artifact_path=path, ready=ready, handoff=handoff
            )
        )
    elif kind == "change-spec":
        errors = validate_change_spec(data, ready=ready)
    else:
        raise ArtifactError(f"unknown artifact kind: {kind}")
    return data, errors


def _provenance_suffix(item: dict[str, Any]) -> str:
    provenance = item.get("provenance") or {}
    kind = provenance.get("kind")
    note = provenance.get("note")
    if not kind:
        return ""
    return f" _(source: {kind}{' — ' + note if note else ''})_"


def _bullets(values: Iterable[str], empty: str = "None recorded.") -> list[str]:
    values = [str(value) for value in values if value not in (None, "")]
    return [f"- {value}" for value in values] or [empty]


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["None recorded."]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = [str(cell if cell not in (None, "") else "—").replace("\n", " ").replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def render_spec(data: dict[str, Any]) -> str:
    meta = data["meta"]
    fingerprint = canonical_fingerprint(data)
    lines = [
        "<!-- Generated from canonical spec.yaml. Do not edit directly. -->",
        f"<!-- canonical-fingerprint: {fingerprint} -->",
        "",
        f"# Specification: {meta['name']}",
        "",
        f"**Spec ID:** {meta['spec_id']}",
        f"**Revision:** {meta['revision']}",
        f"**Schema version:** {meta['schema_version']}",
        f"**Spec level:** {meta['spec_level']}",
        f"**Desired level:** {meta['desired_level']}",
        f"**Date:** {meta['date']}",
        f"**Extensions active:** {', '.join(meta.get('extensions', [])) or 'None'}",
        "",
        "## 1. Problem Statement",
        "",
        f"**Problem:** {data['problem']['statement']}",
        "",
        f"**User/Operator:** {data['problem']['user_operator']}",
        "",
        f"**Success condition:** {data['problem']['success_condition']}",
        "",
        "## 2. Glossary",
        "",
    ]
    lines += _table(["Term", "Definition"], [[x.get("term"), x.get("definition")] for x in data.get("glossary", [])])
    lines += ["", "## 3. Scope", "", "**In scope:**", ""] + _bullets(data["scope"].get("in_scope", []))
    lines += ["", "**Out of scope:**", ""] + _bullets(data["scope"].get("out_of_scope", []))
    mvp = data["mvp"]
    lines += [
        "",
        "## 4. MVP Definition",
        "",
        f"**MVP is:** {mvp['description']}",
        "",
        f"**MVP functional requirements:** {', '.join(mvp['fr_ids'])}",
        "",
        f"**Rationale:** {mvp.get('rationale') or 'Not recorded.'}",
        "",
        "**Architectural prerequisites identified during elicitation:**",
        "",
    ]
    prereqs = [f"{x.get('fr_id')}: {x.get('requires')} ({x.get('resolution')})" for x in mvp.get("architectural_prerequisites", [])]
    lines += _bullets(prereqs)
    lines += ["", "## 5. Functional Requirements", ""]
    for fr in data.get("functional_requirements", []):
        marker = " **[MVP]**" if fr.get("mvp") else ""
        lines.append(f"- {fr.get('id')}{marker}: {fr.get('text')}{_provenance_suffix(fr)}")

    lines += ["", "## 6. Data", ""]
    data_section = data.get("data", {})
    for label, key in (("Inputs", "inputs"), ("Outputs", "outputs"), ("Persisted state", "persisted_state")):
        lines += [f"**{label}:**", ""]
        rendered = [", ".join(f"{k}: {v}" for k, v in item.items() if v not in (None, "")) for item in data_section.get(key, [])]
        lines += _bullets(rendered)
        lines.append("")

    lines += ["## 7. Business Rules", ""]
    lines += [f"- {x.get('id')}: {x.get('text')}{_provenance_suffix(x)}" for x in data.get("business_rules", [])] or ["None recorded."]
    lines += ["", "## 8. Error and Failure Handling", ""]
    lines += _table(
        ["Failure", "Trigger", "Response", "Notification"],
        [[x.get("failure"), x.get("trigger"), x.get("response"), x.get("notification")] for x in data.get("failure_modes", [])],
    )
    lines += ["", "## 9. Non-Functional Requirements", ""]
    lines += _bullets([f"**{key.replace('_', ' ').title()}:** {value}" for key, value in data.get("nfr", {}).items() if value])
    lines += ["", "## 10. High-Coupling Decisions", ""]
    lines += _table(
        ["Decision", "Status", "Notes", "Provenance"],
        [[x.get("decision"), x.get("status"), x.get("notes"), (x.get("provenance") or {}).get("kind")] for x in data.get("high_coupling_decisions", [])],
    )
    lines += ["", "## 10A. Risk Register", ""]
    lines += _table(
        ["ID", "Risk", "Impact", "Mitigation", "Owner", "Reversibility", "Human decision?"],
        [[x.get("id"), x.get("risk"), x.get("impact"), x.get("mitigation"), x.get("owner"), x.get("reversibility"), x.get("requires_human_decision")] for x in data.get("risks", [])],
    )
    lines += ["", "## 11. Acceptance Criteria and Test Plan", ""]
    for ac in data.get("acceptance_criteria", []):
        lines.append(f"- {ac.get('id')} [{', '.join(ac.get('fr_ids', []))}]: {ac.get('condition')}{_provenance_suffix(ac)}")
    lines += ["", "**Untestable items:**", ""]
    lines += _table(["Item", "Reason"], [[x.get("item"), x.get("reason")] for x in data.get("untestable_items", [])])

    wd = data["work_decomposition"]
    lines += ["", "## 12. Work Decomposition", "", "### Value Phases", ""]
    for phase in wd.get("value_phases", []):
        lines.append(f"- **Phase {phase.get('phase')} ({phase.get('label')}):** {', '.join(phase.get('fr_ids', []))} — {phase.get('rationale')}")
    lines += ["", "### Dependency Hints", ""]
    hints = []
    for hint in wd.get("dependency_hints", []):
        hints.append(f"{hint.get('fr_id')} requires [{', '.join(hint.get('requires', [])) or 'none'}]; parallel with [{', '.join(hint.get('parallel_with', [])) or 'none'}]")
    lines += _bullets(hints)

    lines += ["", "## 13. Open Questions", ""]
    lines += _table(["Question", "Category", "Owner"], [[x.get("question"), x.get("category"), x.get("owner")] for x in data.get("open_questions", [])])
    lines += ["", "## 14. Assumptions", ""]
    lines += [f"- {x.get('assumption')}: {x.get('rationale')}{_provenance_suffix(x)}" for x in data.get("assumptions", [])] or ["None recorded."]

    handoff = data["handoff"]
    lines += ["", "## 15. Handoff State", "", "**Decisions made:**", ""]
    lines += _bullets([f"{x.get('decision')}: {x.get('rationale')}" for x in handoff.get("decisions_made", [])])
    lines += ["", "**Pending / deferred:**", ""]
    lines += _bullets([f"{x.get('item')}: {x.get('why_deferred')} (impact if wrong: {x.get('impact_if_wrong')})" for x in handoff.get("pending", [])])
    lines += ["", "**Intent signals:**", ""]
    lines += _bullets([f"{x.get('signal')}: {x.get('relevance')}" for x in handoff.get("intent_signals", [])])
    lines += ["", "## 16. Delta to Next Level", ""]
    lines += _bullets([f"{x.get('gap')}: {x.get('what_would_close_it')}" for x in data.get("delta_to_next_level", [])])

    if "mobile" in data and "mobile" in meta.get("extensions", []):
        mobile = data["mobile"]
        lines += ["", "## [MOBILE] Platform & Distribution", ""]
        lines += _table(
            ["Platform", "Build approach", "Framework", "Distribution", "Minimum OS"],
            [[mobile.get("platform"), mobile.get("build_approach"), mobile.get("cross_platform_framework"), mobile.get("distribution"), mobile.get("min_os_version")]],
        )
        lines += ["", "## [MOBILE] Screens", ""]
        lines += _table(["Screen", "Purpose"], [[x.get("name"), x.get("purpose")] for x in mobile.get("screens", [])])
    return "\n".join(lines).rstrip() + "\n"


def render_decision_brief(data: dict[str, Any]) -> str:
    meta = data["meta"]
    fingerprint = canonical_fingerprint(data)
    risks = data.get("risks", [])
    decision_risks = [risk for risk in risks if risk.get("requires_human_decision")]
    open_questions = data.get("open_questions", [])
    deferred = [d for d in data.get("high_coupling_decisions", []) if d.get("status") != "decided"]
    lines = [
        "<!-- Generated from canonical spec.yaml. Non-authoritative review view. -->",
        f"<!-- canonical-fingerprint: {fingerprint} -->",
        "",
        f"# Decision Brief: {meta['name']}",
        "",
        f"**Spec:** {meta['spec_id']} revision {meta['revision']}",
        "",
        "## What will be delivered",
        "",
        data["mvp"]["description"],
        "",
        "## Deliberately outside this delivery",
        "",
    ]
    lines += _bullets(data["scope"].get("out_of_scope", []))
    lines += ["", "## Decisions already made", ""]
    lines += _table(
        ["Decision", "Status", "Why", "Source"],
        [[d.get("decision"), d.get("status"), d.get("notes"), (d.get("provenance") or {}).get("kind")] for d in data.get("high_coupling_decisions", []) if d.get("status") == "decided"],
    )
    lines += ["", "## Decisions or answers still needed", ""]
    pending_rows = [[q.get("question"), q.get("category"), q.get("owner"), "Not recorded"] for q in open_questions]
    pending_rows += [[d.get("decision"), d.get("status"), "Human/implementer", d.get("notes")] for d in deferred]
    lines += _table(["Decision", "Why pending", "Owner", "Recommendation or impact"], pending_rows)
    lines += ["", "## Largest risks and hard-to-reverse choices", ""]
    selected_risks = decision_risks + [r for r in risks if r not in decision_risks]
    lines += _table(
        ["Risk", "Impact", "Mitigation", "Reversibility", "Needs your decision?"],
        [[r.get("risk"), r.get("impact"), r.get("mitigation"), r.get("reversibility"), r.get("requires_human_decision")] for r in selected_risks[:3]],
    )
    lines += [
        "",
        "## Confirmation",
        "",
        "Confirm that the delivery, exclusions, pending decisions, and risks above match your intent. Corrections update the canonical YAML and regenerate this brief.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_change_spec(data: dict[str, Any]) -> str:
    meta = data["meta"]
    baseline = data["baseline"]
    change = data["change"]
    fingerprint = canonical_fingerprint(data)
    lines = [
        "<!-- Generated from canonical change-spec.yaml. Do not edit directly. -->",
        f"<!-- canonical-fingerprint: {fingerprint} -->",
        "",
        f"# Change Specification: {meta['title']}",
        "",
        f"**Change ID:** {meta['change_id']}",
        f"**Revision:** {data['change_revision']}",
        f"**Date:** {meta['date']}",
        f"**Baseline repository:** {baseline['repository']}",
        f"**Baseline commit:** {baseline.get('commit') or 'Not yet pinned'}",
        f"**Source spec:** {meta.get('source_spec_id') or 'No prior Socratic spec located'}",
        "",
        "## Change Restatement",
        "",
        f"**Current behavior:** {baseline['current_behavior']}",
        "",
        f"**Change:** {change['statement']}",
        "",
        f"**User/operator outcome:** {change['user_outcome']}",
        "",
        "**In scope:**",
        "",
    ]
    lines += _bullets(change.get("in_scope", []))
    lines += ["", "**Out of scope:**", ""]
    lines += _bullets(change.get("out_of_scope", []))
    lines += ["", "## Preserved Behavior", ""]
    lines += _table(
        ["ID", "Behavior", "Existing evidence", "Regression ACs"],
        [[p.get("id"), p.get("behavior"), p.get("evidence"), ", ".join(p.get("regression_acceptance_ids", []))] for p in data.get("preserved_behaviors", [])],
    )
    lines += ["", "## Touched Couplings", ""]
    lines += _table(
        ["Decision", "Existing constraint", "Impact", "Disposition"],
        [[c.get("decision"), c.get("existing_constraint"), c.get("impact"), c.get("preserve_or_revisit")] for c in data.get("touched_couplings", [])],
    )
    lines += ["", "## Changed Contracts and Consumers", ""]
    for contract in data.get("changed_contracts", []):
        lines += [
            f"### {contract.get('id')}: {contract.get('name')}",
            "",
            contract.get("change", ""),
            "",
            f"**Preserved invariant:** {contract.get('preserved_invariant') or 'Not yet resolved'}",
            "",
        ]
        lines += _table(
            ["Layer", "Location", "Impact", "Verification ACs"],
            [[c.get("layer"), c.get("location"), c.get("impact"), ", ".join(c.get("verification_acceptance_ids", []))] for c in contract.get("consumers", [])],
        )
        lines.append("")
    compatibility = data["compatibility"]
    lines += [
        "## Compatibility and Migration",
        "",
        f"**Classification:** {compatibility['classification']}",
        "",
        f"**Supported read versions:** {', '.join(map(str, compatibility.get('supported_read_versions', []))) or 'None recorded'}",
        "",
        f"**Emitted write version:** {compatibility.get('emitted_write_version') or 'None recorded'}",
        "",
        f"**Migration:** {compatibility.get('migration') or 'Not required'}",
        "",
        f"**Rollback/recovery:** {compatibility.get('rollback') or 'Not required'}",
        "",
        f"**Deprecation/communication:** {compatibility.get('deprecation_or_communication') or 'Not required'}",
        "",
        "## Acceptance Criteria",
        "",
    ]
    lines += [f"- {a.get('id')} [{a.get('kind')}]: {a.get('condition')}" for a in data.get("acceptance_criteria", [])]
    lines += ["", "## Risks", ""]
    lines += _table(
        ["ID", "Risk", "Impact", "Mitigation", "Reversibility", "Human decision?"],
        [[r.get("id"), r.get("risk"), r.get("impact"), r.get("mitigation"), r.get("reversibility"), r.get("requires_human_decision")] for r in data.get("risks", [])],
    )
    return "\n".join(lines).rstrip() + "\n"


def validate_change_spec(data: dict[str, Any], *, ready: bool = False) -> list[str]:
    schema_path = ROOT / "schemas/change-spec-v1.schema.json"
    if not schema_path.exists():
        return ["change-spec schema is not installed"]
    errors = schema_errors(data, schema_path)
    if data.get("change_schema_version") != 1:
        errors.append("unsupported change-spec schema version")
    contracts = data.get("changed_contracts", [])
    criteria = data.get("acceptance_criteria", [])
    preserved = data.get("preserved_behaviors", [])
    contract_ids = {c.get("id") for c in contracts if c.get("id")}
    criterion_ids = {a.get("id") for a in criteria if a.get("id")}
    preserved_ids = {p.get("id") for p in preserved if p.get("id")}
    errors.extend(_duplicate_errors(data.get("changed_contracts", []), "id", "changed-contract ID"))
    errors.extend(_duplicate_errors(criteria, "id", "change acceptance ID"))
    errors.extend(_duplicate_errors(preserved, "id", "preserved-behavior ID"))
    for item in criteria:
        errors.extend(_unknown_refs(item.get("changed_contract_ids", []), contract_ids, item.get("id", "change AC")))
        errors.extend(_unknown_refs(item.get("preserved_behavior_ids", []), preserved_ids, item.get("id", "change AC")))
    for item in preserved:
        errors.extend(_unknown_refs(item.get("regression_acceptance_ids", []), criterion_ids, item.get("id", "preserved behavior")))
    if data.get("compatibility", {}).get("classification") == "breaking":
        if not data.get("compatibility", {}).get("migration"):
            errors.append("breaking change requires a migration plan")
        if not data.get("compatibility", {}).get("rollback"):
            errors.append("breaking change requires rollback or recovery")
    if ready:
        if not data.get("baseline", {}).get("commit"):
            errors.append("baseline.commit is required before implementation")
        if any(not c.get("preserved_invariant") for c in data.get("changed_contracts", [])):
            errors.append("every changed contract needs a preserved invariant")
    _ = contract_ids
    return errors


def print_errors(path: Path, errors: list[str]) -> int:
    if not errors:
        print(f"{path}: valid")
        return 0
    print(f"{path}: {len(errors)} validation error(s)", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a canonical artifact")
    validate_parser.add_argument("path", type=Path)
    validate_parser.add_argument("--kind", choices=["auto", "spec", "work-plan", "change-spec"], default="auto")
    validate_parser.add_argument("--ready", action="store_true", help="Apply the pre-implementation gate")
    validate_parser.add_argument("--handoff", action="store_true", help="Apply the completed-work handoff gate")

    render_parser = sub.add_parser("render", help="Render canonical spec YAML to Markdown")
    render_parser.add_argument("path", type=Path)
    render_parser.add_argument("--output", type=Path, default=Path("spec.md"))

    change_render_parser = sub.add_parser("render-change", help="Render canonical change-spec YAML to Markdown")
    change_render_parser.add_argument("path", type=Path)
    change_render_parser.add_argument("--output", type=Path, default=Path("change-spec.md"))

    brief_parser = sub.add_parser("brief", help="Render the non-authoritative human decision brief")
    brief_parser.add_argument("path", type=Path)
    brief_parser.add_argument("--output", type=Path, default=Path("decision-brief.md"))

    sync_parser = sub.add_parser("check-sync", help="Fail if generated Markdown differs from canonical YAML")
    sync_parser.add_argument("path", type=Path)
    sync_parser.add_argument("markdown", type=Path)
    sync_parser.add_argument("--kind", choices=["spec", "change-spec"], default="spec")

    fingerprint_parser = sub.add_parser("fingerprint", help="Print the canonical structured fingerprint")
    fingerprint_parser.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            _, errors = validate_artifact(
                args.path,
                kind=args.kind,
                ready=args.ready or args.handoff,
                handoff=args.handoff,
            )
            return print_errors(args.path, errors)
        render_kind = (
            "change-spec"
            if args.command == "render-change"
            or (args.command == "check-sync" and args.kind == "change-spec")
            else "spec"
        )
        data, errors = validate_artifact(args.path, kind=render_kind)
        if errors:
            return print_errors(args.path, errors)
        if args.command == "render":
            args.output.write_text(render_spec(data), encoding="utf-8")
            print(f"wrote {args.output}")
        elif args.command == "render-change":
            args.output.write_text(render_change_spec(data), encoding="utf-8")
            print(f"wrote {args.output}")
        elif args.command == "brief":
            args.output.write_text(render_decision_brief(data), encoding="utf-8")
            print(f"wrote {args.output}")
        elif args.command == "check-sync":
            expected = render_change_spec(data) if args.kind == "change-spec" else render_spec(data)
            try:
                actual = args.markdown.read_text(encoding="utf-8")
            except OSError as exc:
                raise ArtifactError(str(exc)) from exc
            if actual != expected:
                print(
                    f"{args.markdown}: generated view is stale; run "
                    f"scripts/spec_tools.py render {args.path} --output {args.markdown}",
                    file=sys.stderr,
                )
                return 1
            print(f"{args.markdown}: synchronized")
        elif args.command == "fingerprint":
            print(canonical_fingerprint(data))
        return 0
    except ArtifactError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
