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
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
_TOOL_DIR = Path(__file__).resolve().parent
SCHEMA_ROOT = _TOOL_DIR / "schemas" if (_TOOL_DIR / "schemas").is_dir() else ROOT / "schemas"
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
    package_by_id = {item.get("id"): item for item in packages if item.get("id")}
    verification_by_id = {item.get("id"): item for item in verification if item.get("id")}
    target_intent = set(data.get("phase_plan", {}).get("intent_ids", []))
    known_intent: set[str] = set()
    known_acceptance: set[str] = set()
    required_acceptance: set[str] = set()
    source_data: dict[str, Any] = {}
    source_prerequisite_descriptions: set[str] = set()
    source_change_contracts: dict[str, dict[str, Any]] = {}
    source_preserved_behavior_ids: set[str] = set()
    source_historical_fixtures: set[str] = set()
    source_quality_gates: set[tuple[str, str]] = set()

    source = data.get("source", {})
    source_kind = source.get("artifact_kind")
    declared_source = source.get("artifact_path")
    source_path: Path | None = None
    if declared_source:
        candidate = Path(declared_source)
        if candidate.is_absolute():
            candidates = [candidate]
        else:
            candidates = []
            repository_path = Path(source.get("repository", ""))
            if repository_path.is_absolute():
                candidates.append(repository_path / candidate)
            if artifact_path is not None:
                candidates.append(artifact_path.parent / candidate)
                if artifact_path.parent.name == ".factory":
                    candidates.append(artifact_path.parent.parent / candidate)
            candidates.append(Path.cwd() / candidate)
        source_path = next((item for item in candidates if item.exists()), None)
    if source_path is None:
        errors.append(f"source artifact does not exist: {declared_source}")
    else:
        try:
            source_data = load_yaml(source_path)
            detected_kind = (
                "change_spec" if "change_schema_version" in source_data
                else "spec" if "schema_version" in source_data.get("meta", {})
                else None
            )
            if detected_kind != source_kind:
                errors.append(
                    f"source.artifact_kind is {source_kind!r}, but the artifact is {detected_kind!r}"
                )
            if source_kind == "spec":
                source_errors = schema_errors(source_data, SCHEMA_ROOT / "spec-v2.schema.json")
                source_errors.extend(validate_spec_semantics(source_data, ready=True))
            elif source_kind == "change_spec":
                source_errors = schema_errors(
                    source_data, SCHEMA_ROOT / "change-spec-v1.schema.json"
                )
                source_errors.extend(validate_change_spec(source_data, ready=True))
            else:
                source_errors = [f"unsupported source artifact kind: {source_kind!r}"]
            errors.extend(f"source artifact: {error}" for error in source_errors)

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
                source_prerequisite_descriptions = {
                    item.get("requires")
                    for item in source_data.get("mvp", {}).get(
                        "architectural_prerequisites", []
                    )
                    if item.get("resolution") == "invisible_infrastructure"
                    and item.get("fr_id") in target_intent
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
                if source.get("change_mode") != "existing_system":
                    errors.append("change-spec work plans use source.change_mode: existing_system")
                baseline = source_data.get("baseline", {})
                if source.get("repository") != baseline.get("repository"):
                    errors.append("source.repository must match change-spec baseline.repository")
                if source.get("base_commit") != baseline.get("commit"):
                    errors.append("source.base_commit must match change-spec baseline.commit")
                source_change_contracts = {
                    item.get("id"): item
                    for item in source_data.get("changed_contracts", [])
                    if item.get("id")
                }
                source_preserved_behavior_ids = {
                    item.get("id")
                    for item in source_data.get("preserved_behaviors", [])
                    if item.get("id")
                }
                source_historical_fixtures = set(
                    source_data.get("compatibility", {}).get("historical_fixtures", [])
                )
                source_quality_gates = {
                    (item.get("name", ""), item.get("command", ""))
                    for item in source_data.get("baseline", {}).get("quality_gates", [])
                }
        except ArtifactError as exc:
            errors.append(str(exc))

    errors.extend(_unknown_refs(target_intent, known_intent, "phase_plan.intent_ids"))

    planned_prerequisite_descriptions: set[str] = set()
    for prerequisite in data.get("phase_plan", {}).get("architectural_prerequisites", []):
        prerequisite_packages = prerequisite.get("work_package_ids", [])
        if prerequisite.get("description"):
            planned_prerequisite_descriptions.add(prerequisite["description"])
        errors.extend(
            _unknown_refs(prerequisite_packages, package_ids, "architectural prerequisite")
        )
    missing_prerequisites = (
        source_prerequisite_descriptions - planned_prerequisite_descriptions
    )
    if missing_prerequisites:
        errors.append(
            "source architectural prerequisites without work-plan mapping: "
            f"{sorted(missing_prerequisites)}"
        )

    covered_intent: set[str] = set()
    covered_acceptance: set[str] = set()
    covered_invariants: set[str] = set()
    covered_contracts: set[str] = set()
    contract_owners: dict[str, list[str]] = {contract_id: [] for contract_id in contract_ids}
    for package in packages:
        package_id = package.get("id", "<package>")
        package_intent = package.get("intent_ids", [])
        package_acceptance = package.get("acceptance_criteria_ids", [])
        package_invariants = package.get("invariant_ids", [])
        package_contracts = package.get("contract_ids", [])
        package_verification_ids = package.get("verification_ids", [])
        covered_intent.update(package_intent)
        covered_acceptance.update(package_acceptance)
        covered_invariants.update(package_invariants)
        covered_contracts.update(package_contracts)
        errors.extend(_unknown_refs(package_intent, known_intent, package_id))
        errors.extend(_unknown_refs(package_acceptance, known_acceptance, package_id))
        errors.extend(_unknown_refs(package_invariants, invariant_ids, package_id))
        errors.extend(_unknown_refs(package_contracts, contract_ids, package_id))
        errors.extend(_unknown_refs(package.get("owns_contracts", []), contract_ids, package_id))
        errors.extend(_unknown_refs(package.get("depends_on", []), package_ids, package_id))
        errors.extend(_unknown_refs(package_verification_ids, verify_ids, package_id))

        for contract_id in package.get("owns_contracts", []):
            if contract_id in contract_owners:
                contract_owners[contract_id].append(package_id)
            if contract_id not in package_contracts:
                errors.append(f"{package_id} owns {contract_id} but does not include it in contract_ids")

        package_phase = package.get("value_phase")
        target_phase = data.get("phase_plan", {}).get("target_value_phase")
        if package_phase != target_phase:
            errors.append(
                f"{package_id}.value_phase must equal phase_plan.target_value_phase "
                f"({package_phase} != {target_phase})"
            )

        package_verifications = [
            verification_by_id[verification_id]
            for verification_id in package_verification_ids
            if verification_id in verification_by_id
        ]
        for values, coverage_field, label in (
            (set(package_intent), "covers_intent_ids", "intent IDs"),
            (set(package_acceptance), "covers_acceptance_criteria_ids", "acceptance criteria"),
            (set(package_invariants), "covers_invariant_ids", "invariants"),
            (set(package_contracts), "covers_contract_ids", "contracts"),
        ):
            verification_coverage = {
                ref
                for item in package_verifications
                for ref in item.get(coverage_field, [])
            }
            missing = values - verification_coverage
            if missing:
                errors.append(
                    f"{package_id} {label} without package verification coverage: {sorted(missing)}"
                )

        for dependency_id in package.get("depends_on", []):
            dependency = package_by_id.get(dependency_id)
            if dependency is not None and dependency.get("sequence", 0) >= package.get("sequence", 0):
                errors.append(
                    f"{package_id} dependency {dependency_id} must have an earlier sequence"
                )
        if package_id in package.get("depends_on", []):
            errors.append(f"{package_id} cannot depend on itself")

    missing_intent = target_intent - covered_intent
    if missing_intent:
        errors.append(f"target intent IDs without work packages: {sorted(missing_intent)}")
    missing_acceptance = required_acceptance - covered_acceptance
    if missing_acceptance:
        errors.append(f"target acceptance criteria without work packages: {sorted(missing_acceptance)}")
    missing_invariants = invariant_ids - covered_invariants
    if missing_invariants:
        errors.append(f"invariants without work packages: {sorted(missing_invariants)}")
    missing_contracts = contract_ids - covered_contracts
    if missing_contracts:
        errors.append(f"changed contracts without work packages: {sorted(missing_contracts)}")
    for contract_id, owners in contract_owners.items():
        if len(owners) != 1:
            errors.append(
                f"{contract_id} must have exactly one owning work package (owners={sorted(owners)})"
            )

    graph = {p.get("id"): p.get("depends_on", []) for p in packages if p.get("id")}
    errors.extend(_cycle_errors(graph))

    for invariant in invariants:
        invariant_id = invariant.get("id", "<invariant>")
        invariant_verification_ids = invariant.get("verification_ids", [])
        errors.extend(
            _unknown_refs(invariant_verification_ids, verify_ids, invariant_id)
        )
        for verification_id in invariant_verification_ids:
            verification_item = verification_by_id.get(verification_id)
            if (
                verification_item is not None
                and invariant_id not in verification_item.get("covers_invariant_ids", [])
            ):
                errors.append(
                    f"{invariant_id} names {verification_id}, but that verification does not cover it"
                )

    planned_preserved_behavior_ids = {
        preserved_id
        for invariant in invariants
        for preserved_id in invariant.get("source_preserved_behavior_ids", [])
    }
    missing_preserved_behaviors = (
        source_preserved_behavior_ids - planned_preserved_behavior_ids
    )
    if missing_preserved_behaviors:
        errors.append(
            "source preserved behaviors without invariant mapping: "
            f"{sorted(missing_preserved_behaviors)}"
        )

    affected_consumer_packages: dict[str, set[str]] = {}
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
            layer = consumer.get("layer")
            consumer_ref = f"{contract_id}:{layer}:{consumer.get('location', '')}"
            refs = consumer.get("work_package_ids", [])
            errors.extend(_unknown_refs(refs, package_ids, f"{contract_id}:{layer}"))
            if consumer.get("status") == "affected":
                affected_consumer_packages[consumer_ref] = set(refs)
                if not refs:
                    errors.append(f"{contract_id}:{layer} is affected but has no work package")
                contract_invariants = set(contract.get("invariant_ids", []))
                for package_id in refs:
                    package = package_by_id.get(package_id)
                    if package is None:
                        continue
                    if consumer_ref not in package.get("affected_consumers", []):
                        errors.append(
                            f"{consumer_ref} names {package_id}, but that package does not name the consumer"
                        )
                    if contract_id not in package.get("contract_ids", []):
                        errors.append(
                            f"{consumer_ref} assigns {package_id}, but that package does not include {contract_id}"
                        )
                    missing_package_invariants = contract_invariants - set(
                        package.get("invariant_ids", [])
                    )
                    if missing_package_invariants:
                        errors.append(
                            f"{consumer_ref} assigns {package_id} without contract invariants: "
                            f"{sorted(missing_package_invariants)}"
                        )

    for package in packages:
        package_id = package.get("id", "<package>")
        for consumer_ref in package.get("affected_consumers", []):
            assigned_packages = affected_consumer_packages.get(consumer_ref)
            if assigned_packages is None:
                errors.append(f"{package_id}.affected_consumers references unknown affected consumer {consumer_ref}")
            elif package_id not in assigned_packages:
                errors.append(
                    f"{package_id} names {consumer_ref}, but the consumer does not name that package"
                )

    plan_contracts_by_id = {
        item.get("id"): item for item in contracts if item.get("id")
    }
    missing_source_contracts = set(source_change_contracts) - set(plan_contracts_by_id)
    if missing_source_contracts:
        errors.append(
            f"source changed contracts omitted from work plan: {sorted(missing_source_contracts)}"
        )
    for contract_id, source_contract in source_change_contracts.items():
        planned_contract = plan_contracts_by_id.get(contract_id)
        if planned_contract is None:
            continue
        planned_consumers = {
            (item.get("layer"), item.get("location")): item
            for item in planned_contract.get("consumers", [])
        }
        for source_consumer in source_contract.get("consumers", []):
            key = (source_consumer.get("layer"), source_consumer.get("location"))
            planned_consumer = planned_consumers.get(key)
            if planned_consumer is None or planned_consumer.get("status") != "affected":
                errors.append(
                    f"source consumer {contract_id}:{key[0]}:{key[1]} is not mapped as affected"
                )

    planned_quality_gates = {
        (item.get("name", ""), item.get("command", ""))
        for item in data.get("quality_gates", [])
    }
    missing_quality_gates = source_quality_gates - planned_quality_gates
    if missing_quality_gates:
        errors.append(
            f"source quality gates omitted from work plan: {sorted(missing_quality_gates)}"
        )

    compatibility = data.get("compatibility", {})
    if compatibility.get("required") and not compatibility.get("versions"):
        errors.append("compatibility.required is true but no versions are enumerated")
    if source_historical_fixtures and not compatibility.get("required"):
        errors.append("source compatibility fixtures require compatibility.required: true")
    planned_fixtures = {
        item.get("fixture") for item in compatibility.get("versions", []) if item.get("fixture")
    }
    missing_source_fixtures = source_historical_fixtures - planned_fixtures
    if missing_source_fixtures:
        errors.append(
            f"source historical fixtures omitted from compatibility matrix: "
            f"{sorted(missing_source_fixtures)}"
        )
    for migration in compatibility.get("migration_steps", []):
        errors.extend(
            _unknown_refs(
                [migration.get("work_package_id")],
                package_ids,
                "compatibility migration step",
            )
        )

    verified_intent: set[str] = set()
    verified_acceptance: set[str] = set()
    verified_invariants: set[str] = set()
    verified_contracts: set[str] = set()
    for item in verification:
        verify_id = item.get("id", "<verification>")
        item_intent = item.get("covers_intent_ids", [])
        item_acceptance = item.get("covers_acceptance_criteria_ids", [])
        item_invariants = item.get("covers_invariant_ids", [])
        item_contracts = item.get("covers_contract_ids", [])
        verified_intent.update(item_intent)
        verified_acceptance.update(item_acceptance)
        verified_invariants.update(item_invariants)
        verified_contracts.update(item_contracts)
        errors.extend(_unknown_refs(item_intent, known_intent, verify_id))
        errors.extend(_unknown_refs(item_acceptance, known_acceptance, verify_id))
        errors.extend(_unknown_refs(item_invariants, invariant_ids, verify_id))
        errors.extend(_unknown_refs(item_contracts, contract_ids, verify_id))

    for required, covered, label in (
        (target_intent, verified_intent, "target intent IDs"),
        (required_acceptance, verified_acceptance, "target acceptance criteria"),
        (invariant_ids, verified_invariants, "invariants"),
        (contract_ids, verified_contracts, "changed contracts"),
    ):
        missing = required - covered
        if missing:
            errors.append(f"{label} without verification coverage: {sorted(missing)}")

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
        if not review.get("reviewed_at"):
            errors.append("readiness_review.reviewed_at is required before implementation")
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
            if not item.get("evidence"):
                errors.append(f"{item.get('id')} has no evidence at handoff")
        for gate in data.get("quality_gates", []):
            if gate.get("required") and gate.get("result") != "pass":
                errors.append(f"required quality gate {gate.get('name')} is not passing")
            if gate.get("required") and not gate.get("result_evidence"):
                errors.append(
                    f"required quality gate {gate.get('name')} has no result evidence"
                )

        handoff_data = data.get("handoff", {})
        if handoff_data.get("review_result") != "pass":
            errors.append("handoff.review_result must be pass")
        if not handoff_data.get("independent_reviewer"):
            errors.append("handoff.independent_reviewer is required")
        if not handoff_data.get("reviewed_at"):
            errors.append("handoff.reviewed_at is required")
        for field in ("base_commit", "head_commit"):
            if not handoff_data.get(field):
                errors.append(f"handoff.{field} is required")
            elif handoff_data.get(field) != source.get(field):
                errors.append(f"handoff.{field} must match source.{field}")
        if set(handoff_data.get("invariant_ids", [])) != invariant_ids:
            errors.append("handoff.invariant_ids must exactly match planned invariants")
        if set(handoff_data.get("changed_contract_ids", [])) != contract_ids:
            errors.append(
                "handoff.changed_contract_ids must exactly match planned changed contracts"
            )
        expected_consumers = set(affected_consumer_packages)
        missing_inspected = expected_consumers - set(
            handoff_data.get("consumers_inspected", [])
        )
        if missing_inspected:
            errors.append(
                f"handoff.consumers_inspected omits affected consumers: "
                f"{sorted(missing_inspected)}"
            )
        expected_commands = {
            item.get("command") for item in verification if item.get("command")
        }
        expected_commands.update(
            gate.get("command")
            for gate in data.get("quality_gates", [])
            if gate.get("required") and gate.get("command")
        )
        missing_commands = expected_commands - set(handoff_data.get("commands_run", []))
        if missing_commands:
            errors.append(f"handoff.commands_run omits commands: {sorted(missing_commands)}")
        if compatibility.get("required"):
            if not handoff_data.get("persisted_formats_affected"):
                errors.append(
                    "handoff.persisted_formats_affected is required for compatibility work"
                )
            missing_handoff_fixtures = planned_fixtures - set(
                handoff_data.get("migration_versions_and_fixtures", [])
            )
            if missing_handoff_fixtures:
                errors.append(
                    "handoff.migration_versions_and_fixtures omits fixtures: "
                    f"{sorted(missing_handoff_fixtures)}"
                )

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
        errors = schema_errors(data, SCHEMA_ROOT / "spec-v2.schema.json")
        errors.extend(validate_spec_semantics(data, ready=ready))
    elif kind == "work-plan":
        version = data.get("plan_version")
        if version != 1:
            return data, [f"unsupported work-plan version {version}; this tool supports 1"]
        errors = schema_errors(data, SCHEMA_ROOT / "work-plan-v1.schema.json")
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
    desired_level = meta.get("desired_level") or "not requested"
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
        f"**Desired level:** {desired_level}",
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
    lines += ["", "## Material risks and hard-to-reverse choices", ""]
    hard_risks = [
        risk
        for risk in risks
        if risk.get("reversibility") in {"costly", "irreversible"}
    ]
    selected_risks = decision_risks + [
        risk for risk in hard_risks if risk not in decision_risks
    ]
    if not selected_risks:
        selected_risks = risks[:3]
    lines += _table(
        ["Risk", "Impact", "Mitigation", "Reversibility", "Needs your decision?"],
        [[r.get("risk"), r.get("impact"), r.get("mitigation"), r.get("reversibility"), r.get("requires_human_decision")] for r in selected_risks],
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
    schema_path = SCHEMA_ROOT / "change-spec-v1.schema.json"
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
    sync_parser.add_argument(
        "--kind", choices=["spec", "change-spec", "brief"], default="spec"
    )

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
            if args.kind == "change-spec":
                expected = render_change_spec(data)
                render_command = "render-change"
            elif args.kind == "brief":
                expected = render_decision_brief(data)
                render_command = "brief"
            else:
                expected = render_spec(data)
                render_command = "render"
            try:
                actual = args.markdown.read_text(encoding="utf-8")
            except OSError as exc:
                raise ArtifactError(str(exc)) from exc
            if actual != expected:
                print(
                    f"{args.markdown}: generated view is stale; run "
                    f"scripts/spec_tools.py {render_command} {args.path} "
                    f"--output {args.markdown}",
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
