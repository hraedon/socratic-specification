from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMA_PATH = Path(__file__).parent.parent / "schemas/session-metrics-v1.schema.json"
REQUIRED_FIELDS = {
    "metrics_version",
    "session_key",
    "project_key",
    "mode",
    "started_at",
    "highest_step",
    "rounds_completed",
    "human_questions",
    "human_corrections",
    "desired_level",
    "achieved_level",
    "reached_synthesis",
    "work_plan_revisions",
    "implementation_human_decisions",
    "defects",
    "acceptance_criteria_revisions",
    "value_phase_accepted",
}
CONTENT_FIELDS = {
    "prompt",
    "prompts",
    "answer",
    "answers",
    "content",
    "requirement_text",
    "repository_contents",
    "project_name",
    "personal_identifier",
}


def _load_fixture(name: str) -> dict:
    return yaml.safe_load((FIXTURES / name).read_text())


def _errors(data: dict) -> list:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))


def test_valid_session_metrics_fixture_conforms_to_schema() -> None:
    assert _errors(_load_fixture("valid-session-metrics-v1.yaml")) == []


@pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
def test_session_metrics_requires_each_required_field(field: str) -> None:
    metrics = _load_fixture("valid-session-metrics-v1.yaml")
    metrics.pop(field)

    assert any(error.validator == "required" and field in error.message for error in _errors(metrics))


def test_session_metrics_required_fields_are_regression_locked() -> None:
    schema = json.loads(SCHEMA_PATH.read_text())

    assert set(schema["required"]) == REQUIRED_FIELDS


def test_session_metrics_rejects_invalid_enum_and_range_values() -> None:
    errors = _errors(_load_fixture("invalid-session-metrics-v1-enum-ranges.yaml"))
    invalid_paths = {tuple(error.absolute_path) for error in errors}

    assert {
        ("metrics_version",),
        ("mode",),
        ("highest_step",),
        ("rounds_completed",),
        ("human_questions",),
        ("human_corrections",),
        ("desired_level",),
        ("achieved_level",),
        ("time_to_synthesis_seconds",),
        ("spec_word_count",),
        ("work_plan_revisions",),
        ("post_implementation_plan_revisions",),
        ("implementation_human_decisions",),
        ("defects", 0, "class"),
        ("defects", 0, "count"),
        ("acceptance_criteria_revisions",),
        ("time_to_first_useful_delivery_seconds",),
    } <= invalid_paths


def test_session_metrics_rejects_unknown_and_content_properties() -> None:
    errors = _errors(_load_fixture("invalid-session-metrics-v1-additional-properties.yaml"))

    assert sum(error.validator == "additionalProperties" for error in errors) == 2
    assert any("'prompt' was unexpected" in error.message for error in errors)
    assert any("'detail' was unexpected" in error.message for error in errors)


def test_valid_session_metrics_fixture_contains_no_content_fields() -> None:
    metrics = _load_fixture("valid-session-metrics-v1.yaml")
    defect_keys = {key for defect in metrics["defects"] for key in defect}

    assert not (set(metrics) | defect_keys) & CONTENT_FIELDS


@pytest.mark.parametrize("field", sorted(CONTENT_FIELDS))
def test_session_metrics_rejects_sensitive_content_fields(field: str) -> None:
    metrics = _load_fixture("valid-session-metrics-v1.yaml")
    metrics[field] = "sensitive content"

    assert any(error.validator == "additionalProperties" for error in _errors(metrics))
