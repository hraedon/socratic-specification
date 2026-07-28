from __future__ import annotations

from pathlib import Path

import yaml

from scripts.spec_tools import (
    canonical_fingerprint,
    render_decision_brief,
    render_change_spec,
    render_spec,
    validate_artifact,
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


def test_work_plan_can_reference_change_spec_without_fake_frs() -> None:
    plan = yaml.safe_load((FIXTURES / "valid-work-plan.yaml").read_text())
    change = yaml.safe_load((FIXTURES / "valid-change-spec.yaml").read_text())
    plan["source"].update(
        {
            "artifact_path": str((FIXTURES / "valid-change-spec.yaml").resolve()),
            "artifact_kind": "change_spec",
            "artifact_fingerprint": canonical_fingerprint(change),
            "change_mode": "existing_system",
        }
    )
    plan["phase_plan"].update(
        {"target_value_phase": 0, "intent_ids": ["CAC-01", "CAC-02"]}
    )
    package = plan["work_packages"][0]
    package["value_phase"] = 0
    package["intent_ids"] = ["CAC-01", "CAC-02"]
    package["acceptance_criteria_ids"] = ["CAC-01", "CAC-02"]
    plan["verification"][0]["covers_intent_ids"] = ["CAC-01"]
    plan["verification"][0]["covers_acceptance_criteria_ids"] = ["CAC-01"]
    plan["verification"][1]["covers_intent_ids"] = ["CAC-02"]
    plan["verification"][1]["covers_acceptance_criteria_ids"] = ["CAC-02"]
    assert validate_work_plan_semantics(plan, ready=True) == []
