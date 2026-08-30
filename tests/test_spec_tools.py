from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from scripts.spec_tools import (
    canonical_fingerprint,
    render_change_spec,
    render_decision_brief,
    render_spec,
    validate_artifact,
    validate_spec_semantics,
    validate_work_plan_semantics,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_spec_passes_ready_gate() -> None:
    _, errors = validate_artifact(FIXTURES / "valid-spec-v2.yaml", kind="spec", ready=True)
    assert errors == []


def test_unknown_fr_is_rejected_semantically() -> None:
    _, errors = validate_artifact(FIXTURES / "invalid-spec-unknown-fr.yaml", kind="spec")
    assert any("unknown ID FR-99" in error for error in errors)
    assert any("must exactly match" in error for error in errors)


def test_rendered_views_are_deterministic_and_fingerprinted() -> None:
    data = yaml.safe_load((FIXTURES / "valid-spec-v2.yaml").read_text())
    fingerprint = canonical_fingerprint(data)
    rendered = render_spec(data)
    brief = render_decision_brief(data)
    assert fingerprint in rendered
    assert fingerprint in brief
    assert rendered == render_spec(data)
    assert "# Decision Brief: Plant Reminder" in brief


def test_value_phases_map_requirements_and_business_rules_mechanically() -> None:
    data = yaml.safe_load((FIXTURES / "valid-spec-v2.yaml").read_text())
    legacy_partial = deepcopy(data)
    legacy_partial["work_decomposition"]["value_phases"][0]["fr_ids"].remove("FR-02")
    legacy_errors = validate_spec_semantics(legacy_partial, ready=True)
    assert not any("functional requirements missing from value phases" in error for error in legacy_errors)

    data["work_decomposition"]["value_phases"][0]["br_ids"] = ["BR-01"]
    assert validate_spec_semantics(data, ready=True) == []
    assert "BRs: BR-01" in render_spec(data)

    missing_fr = deepcopy(data)
    missing_fr["work_decomposition"]["value_phases"][0]["fr_ids"].remove("FR-02")
    errors = validate_spec_semantics(missing_fr, ready=True)
    assert any("functional requirements missing from value phases" in error for error in errors)

    data["work_decomposition"]["value_phases"][0]["br_ids"] = []
    errors = validate_spec_semantics(data, ready=True)
    assert any("business rules missing from value phases" in error for error in errors)


def test_decision_brief_includes_all_hard_to_reverse_risks() -> None:
    data = yaml.safe_load((FIXTURES / "valid-spec-v2.yaml").read_text())
    data["risks"] = [
        {
            "id": f"RISK-{index}",
            "risk": f"hard risk {index}",
            "impact": "material",
            "mitigation": "mitigate",
            "owner": "owner",
            "reversibility": "costly",
            "requires_human_decision": False,
            "provenance": {"kind": "agent_inferred", "note": "test"},
        }
        for index in range(1, 5)
    ]
    brief = render_decision_brief(data)
    for index in range(1, 5):
        assert f"hard risk {index}" in brief
    assert "## Material risks and hard-to-reverse choices" in brief


def test_valid_work_plan_passes_readiness_gate() -> None:
    _, errors = validate_artifact(
        FIXTURES / "valid-work-plan.yaml", kind="work-plan", ready=True
    )
    assert errors == []


def test_valid_change_spec_passes_ready_gate_and_renders() -> None:
    data, errors = validate_artifact(
        FIXTURES / "valid-change-spec.yaml", kind="change-spec", ready=True
    )
    assert errors == []
    rendered = render_change_spec(data)
    assert "# Change Specification: Add stable identity to policy entries" in rendered
    assert "Historical snapshots remain readable" in rendered


def _valid_change_work_plan() -> dict:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    change = yaml.safe_load((FIXTURES / "valid-change-spec.yaml").read_text())
    plan["source"].update(
        {
            "artifact_path": str((FIXTURES / "valid-change-spec.yaml").resolve()),
            "artifact_kind": "change_spec",
            "artifact_fingerprint": canonical_fingerprint(change),
            "change_mode": "existing_system",
            "repository": change["baseline"]["repository"],
            "base_commit": change["baseline"]["commit"],
        }
    )
    plan["phase_plan"].update(
        {"target_value_phase": 0, "intent_ids": ["CAC-01", "CAC-02"]}
    )
    package = plan["work_packages"][0]
    package["value_phase"] = 0
    package["intent_ids"] = ["CAC-01", "CAC-02"]
    package["acceptance_criteria_ids"] = ["CAC-01", "CAC-02"]

    contract = plan["changed_contracts"][0]
    contract["id"] = "CHANGE-CONTRACT-01"
    for consumer in contract["consumers"]:
        if consumer["layer"] == "parser":
            consumer.update(
                {
                    "location": "policy_parser",
                    "status": "affected",
                    "evidence": "Source change-spec consumer.",
                    "work_package_ids": ["WP-01"],
                }
            )
        if consumer["layer"] == "browser":
            consumer.update(
                {
                    "location": "policy_editor",
                    "status": "affected",
                    "evidence": "Source change-spec consumer.",
                    "work_package_ids": ["WP-01"],
                }
            )
    package["contract_ids"] = ["CHANGE-CONTRACT-01"]
    package["owns_contracts"] = ["CHANGE-CONTRACT-01"]
    package["affected_consumers"].extend(
        [
            "CHANGE-CONTRACT-01:parser:policy_parser",
            "CHANGE-CONTRACT-01:browser:policy_editor",
        ]
    )
    package["affected_consumers"] = [
        "CHANGE-" + value if value.startswith("CONTRACT-01:") else value
        for value in package["affected_consumers"]
    ]
    plan["invariants"][0]["source_preserved_behavior_ids"] = ["PRESERVE-01"]
    for verification in plan["verification"]:
        verification["covers_contract_ids"] = ["CHANGE-CONTRACT-01"]
    plan["verification"][0]["covers_intent_ids"] = ["CAC-01"]
    plan["verification"][0]["covers_acceptance_criteria_ids"] = ["CAC-01"]
    plan["verification"][1]["covers_intent_ids"] = ["CAC-02"]
    plan["verification"][1]["covers_acceptance_criteria_ids"] = ["CAC-02"]
    plan["compatibility"] = {
        "required": True,
        "rationale": "The source change-spec supports historical snapshots.",
        "versions": [
            {
                "version": version,
                "read_behavior": "Read and preserve semantics.",
                "write_behavior": "Write only on explicit save.",
                "fixture": fixture,
                "fixture_fingerprint": "sha256:" + "0" * 64,
                "immutable_on_read": True,
            }
            for version, fixture in (
                (1, "tests/fixtures/snapshot-v1.yaml"),
                (2, "tests/fixtures/snapshot-v2.yaml"),
            )
        ],
        "migration_steps": [
            {
                "from": 1,
                "to": 2,
                "work_package_id": "WP-01",
                "rollback_or_recovery": "Restore the immutable v1 fixture.",
            }
        ],
    }
    plan["quality_gates"] = [
        {
            "name": "Test suite",
            "command": "pytest -q",
            "evidence": "Repository test configuration",
            "required": True,
            "result": "pending",
            "result_evidence": "",
        }
    ]
    plan["handoff"]["changed_contract_ids"] = ["CHANGE-CONTRACT-01"]
    return plan


def test_work_plan_can_reference_change_spec_without_fake_frs(tmp_path: Path) -> None:
    plan_path = tmp_path / "change-work-plan.yaml"
    plan_path.write_text(yaml.safe_dump(_valid_change_work_plan(), sort_keys=False))

    _, errors = validate_artifact(plan_path, kind="work-plan", ready=True)

    assert errors == []


def test_ready_work_plan_requires_verification_coverage() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    for verification in plan["verification"]:
        verification["covers_intent_ids"] = []
        verification["covers_acceptance_criteria_ids"] = []
        verification["covers_invariant_ids"] = []
        verification["covers_contract_ids"] = []

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("target intent IDs without verification coverage" in error for error in errors)
    assert any("target acceptance criteria without verification coverage" in error for error in errors)
    assert any("invariants without verification coverage" in error for error in errors)
    assert any("changed contracts without verification coverage" in error for error in errors)


def test_work_plan_consumer_mapping_is_bidirectional() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["work_packages"][0]["affected_consumers"] = []

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("package does not name the consumer" in error for error in errors)


def test_changed_contract_has_exactly_one_owner() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    second_package = deepcopy(plan["work_packages"][0])
    second_package.update(
        {
            "id": "WP-02",
            "sequence": 2,
            "intent_ids": [],
            "acceptance_criteria_ids": [],
            "invariant_ids": [],
            "affected_consumers": [],
        }
    )
    plan["work_packages"].append(second_package)

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("must have exactly one owning work package" in error for error in errors)


def test_work_package_dependency_must_precede_dependent_package() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    prerequisite = deepcopy(plan["work_packages"][0])
    prerequisite.update(
        {
            "id": "WP-02",
            "sequence": 2,
            "intent_ids": [],
            "acceptance_criteria_ids": [],
            "invariant_ids": [],
            "contract_ids": [],
            "owns_contracts": [],
            "affected_consumers": [],
        }
    )
    plan["work_packages"].append(prerequisite)
    plan["work_packages"][0]["depends_on"] = ["WP-02"]

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("dependency WP-02 must have an earlier sequence" in error for error in errors)


def test_spec_work_plan_rejects_change_spec_value_phase_zero() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["work_packages"][0]["value_phase"] = 0

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("must equal phase_plan.target_value_phase" in error for error in errors)


def test_work_plan_rejects_invalid_or_misdeclared_source(tmp_path: Path) -> None:
    source_path = tmp_path / "not-a-spec.yaml"
    invalid_source = {"functional_requirements": [], "acceptance_criteria": []}
    source_path.write_text(yaml.safe_dump(invalid_source))
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["source"]["artifact_path"] = str(source_path)
    plan["source"]["artifact_fingerprint"] = canonical_fingerprint(invalid_source)
    plan_path = tmp_path / "work-plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))

    _, errors = validate_artifact(plan_path, kind="work-plan", ready=True)

    assert any("source.artifact_kind" in error for error in errors)
    assert any("source artifact:" in error for error in errors)


def test_source_architectural_prerequisite_requires_package_mapping(
    tmp_path: Path,
) -> None:
    source = yaml.safe_load((FIXTURES / "valid-spec-v2.yaml").read_text())
    source["mvp"]["architectural_prerequisites"] = [
        {
            "fr_id": "FR-01",
            "requires": "A persistence adapter",
            "resolution": "invisible_infrastructure",
        }
    ]
    source_path = tmp_path / "spec.yaml"
    source_path.write_text(yaml.safe_dump(source, sort_keys=False))
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["source"]["artifact_path"] = str(source_path)
    plan["source"]["artifact_fingerprint"] = canonical_fingerprint(source)
    plan_path = tmp_path / "work-plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))

    _, errors = validate_artifact(plan_path, kind="work-plan", ready=True)

    assert any("source architectural prerequisites without work-plan mapping" in error for error in errors)


def test_change_spec_contracts_fixtures_and_quality_gates_cannot_disappear() -> None:
    plan = _valid_change_work_plan()
    plan["changed_contracts"] = []
    plan["quality_gates"] = []
    plan["compatibility"] = {
        "required": False,
        "rationale": "Omitted",
        "versions": [],
        "migration_steps": [],
    }

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("source changed contracts omitted" in error for error in errors)
    assert any("source quality gates omitted" in error for error in errors)
    assert any("source historical fixtures omitted" in error for error in errors)


def test_affected_consumer_package_must_preserve_contract_invariants() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    second_package = deepcopy(plan["work_packages"][0])
    second_package.update(
        {
            "id": "WP-02",
            "sequence": 2,
            "intent_ids": [],
            "acceptance_criteria_ids": [],
            "invariant_ids": [],
            "owns_contracts": [],
            "affected_consumers": ["CONTRACT-01:domain_model:plant"],
            "verification_ids": ["VERIFY-01"],
        }
    )
    plan["work_packages"].append(second_package)
    domain_consumer = next(
        item
        for item in plan["changed_contracts"][0]["consumers"]
        if item["layer"] == "domain_model"
    )
    domain_consumer["work_package_ids"].append("WP-02")

    errors = validate_work_plan_semantics(plan, ready=True)

    assert any("without contract invariants" in error for error in errors)


def _completed_work_plan() -> dict:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["source"]["head_commit"] = "def456"
    for package in plan["work_packages"]:
        package["status"] = "pass"
    for verification in plan["verification"]:
        verification["result"] = "pass"
        verification["evidence"] = f"evidence for {verification['id']}"
    plan["handoff"] = {
        "base_commit": "abc123",
        "head_commit": "def456",
        "invariant_ids": ["INV-01"],
        "changed_contract_ids": ["CONTRACT-01"],
        "persisted_formats_affected": [],
        "migration_versions_and_fixtures": [],
        "consumers_inspected": list(plan["work_packages"][0]["affected_consumers"]),
        "prior_findings_and_regressions": [],
        "commands_run": [item["command"] for item in plan["verification"]],
        "known_limitations": [],
        "independent_reviewer": "independent-reviewer",
        "reviewed_at": "2026-07-14T01:00:00Z",
        "review_result": "pass",
    }
    return plan


def test_complete_handoff_requires_and_accepts_evidence(tmp_path: Path) -> None:
    plan_path = tmp_path / "completed-work-plan.yaml"
    plan_path.write_text(yaml.safe_dump(_completed_work_plan(), sort_keys=False))

    _, errors = validate_artifact(plan_path, kind="work-plan", handoff=True)

    assert errors == []


def test_handoff_rejects_missing_record_and_verification_evidence() -> None:
    plan = _completed_work_plan()
    plan["verification"][0]["evidence"] = ""
    plan["handoff"] = {"review_result": "pass"}

    errors = validate_work_plan_semantics(plan, ready=True, handoff=True)

    assert any("has no evidence at handoff" in error for error in errors)
    assert any("handoff.independent_reviewer is required" in error for error in errors)
    assert any("handoff.commands_run omits commands" in error for error in errors)


def test_compatibility_matrix_rejects_unshaped_version_entries(tmp_path: Path) -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    plan["compatibility"]["required"] = True
    plan["compatibility"]["versions"] = [{}]
    plan_path = tmp_path / "invalid-compatibility-work-plan.yaml"
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))

    _, errors = validate_artifact(plan_path, kind="work-plan", ready=True)

    assert any("read_behavior" in error for error in errors)
    assert any("fixture_fingerprint" in error for error in errors)


def test_spec_can_record_that_no_level_was_requested(tmp_path: Path) -> None:
    spec = yaml.safe_load((FIXTURES / "valid-spec-v2.yaml").read_text())
    spec["meta"]["desired_level"] = None
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))

    data, errors = validate_artifact(spec_path, kind="spec", ready=True)

    assert errors == []
    assert "**Desired level:** not requested" in render_spec(data)
