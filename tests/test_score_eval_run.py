from __future__ import annotations

import yaml

from scripts.score_eval_run import score_eval_run


def _case() -> dict:
    return yaml.safe_load(
        """
id: scoring-case
attention_budget:
  maximum_human_questions: 0
  rationale: No questions are needed.
expected_obligations:
  - id: OB-01
    severity: critical
    deadline: pre_synthesis
    obligation: Find the critical issue.
    rationale: Test.
  - id: OB-02
    severity: important
    deadline: work_decomposition
    obligation: Find the important issue.
    rationale: Test.
anti_obligations:
  - id: ANTI-01
    anti_obligation: Do not invent a framework choice.
    rationale: Test.
"""
    )


def _run() -> dict:
    return {
        "case_id": "scoring-case",
        "process_revision": "abc123",
        "obligations": [
            {
                "id": "OB-01",
                "status": "surfaced",
                "stage": "elicitation",
                "evidence": "Question 1",
            },
            {
                "id": "OB-02",
                "status": "surfaced",
                "stage": "pre_handoff",
                "evidence": "Plan review",
            },
        ],
        "anti_obligations": [
            {"id": "ANTI-01", "status": "committed", "evidence": "Draft spec"}
        ],
        "human_questions": [
            {
                "question": "Which database is already configured?",
                "necessity": "discoverable_from_context",
                "evidence": "Repository manifest",
            }
        ],
        "corrections": 2,
        "artifact_validation": {
            "schema": "pass",
            "readiness": "fail",
            "generated_views_sync": "not_run",
        },
    }


def test_score_keeps_recall_attention_and_artifact_results_separate() -> None:
    report, errors = score_eval_run(_case(), _run())

    assert errors == []
    assert report is not None
    assert report["obligation_recall"] == {
        "critical_on_time": 1,
        "critical_total": 1,
        "important_on_time": 0,
        "important_total": 1,
        "late": ["OB-02"],
        "missed": [],
    }
    assert report["anti_obligations"]["committed_count"] == 1
    assert report["human_attention"]["unnecessary_question_count"] == 1
    assert report["human_attention"]["over_budget_by"] == 1
    assert report["artifact_validation"]["readiness"] == "fail"
    assert report["weighted_signal"] == -1


def test_score_rejects_missing_or_duplicate_judgments() -> None:
    run = _run()
    run["obligations"] = [run["obligations"][0], run["obligations"][0]]

    report, errors = score_eval_run(_case(), run)

    assert report is None
    assert any("duplicate obligation judgments" in error for error in errors)
    assert any("missing obligation judgments" in error for error in errors)
