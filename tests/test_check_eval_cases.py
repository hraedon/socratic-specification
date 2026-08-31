from __future__ import annotations

from pathlib import Path

import yaml

from scripts import check_eval_cases


def test_check_eval_cases_reports_bad_yaml_with_path(monkeypatch, tmp_path: Path, capsys) -> None:
    root = tmp_path
    cases = root / "evals" / "cases"
    cases.mkdir(parents=True)
    (cases / "bad.yaml").write_text("id: [unterminated\n")
    for filename in (
        "case.schema.json",
        "case-v2.schema.json",
        "run.schema.json",
        "run-v2.schema.json",
    ):
        (root / "evals" / filename).write_text(
            (Path(__file__).parent.parent / "evals" / filename).read_text()
    )
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text(
        (Path(__file__).parent.parent / "extensions/index.yaml").read_text()
    )
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 1

    captured = capsys.readouterr()
    assert str(cases / "bad.yaml") in captured.err
    assert "cannot read YAML" in captured.err
    assert "Traceback" not in captured.err


def test_check_eval_cases_reports_non_mapping_with_path(monkeypatch, tmp_path: Path, capsys) -> None:
    root = tmp_path
    cases = root / "evals" / "cases"
    cases.mkdir(parents=True)
    (cases / "bad.yaml").write_text("- not\n- a mapping\n")
    for filename in (
        "case.schema.json",
        "case-v2.schema.json",
        "run.schema.json",
        "run-v2.schema.json",
    ):
        (root / "evals" / filename).write_text(
            (Path(__file__).parent.parent / "evals" / filename).read_text()
    )
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text(
        (Path(__file__).parent.parent / "extensions/index.yaml").read_text()
    )
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 1

    captured = capsys.readouterr()
    assert str(cases / "bad.yaml") in captured.err
    assert "top level must be a mapping" in captured.err


def test_check_eval_cases_reports_schema_type_errors_with_path(monkeypatch, tmp_path: Path, capsys) -> None:
    root = tmp_path
    cases = root / "evals" / "cases"
    cases.mkdir(parents=True)
    (cases / "bad.yaml").write_text("id: 1\n")
    for filename in (
        "case.schema.json",
        "case-v2.schema.json",
        "run.schema.json",
        "run-v2.schema.json",
    ):
        (root / "evals" / filename).write_text(
            (Path(__file__).parent.parent / "evals" / filename).read_text()
        )
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text(
        (Path(__file__).parent.parent / "extensions/index.yaml").read_text()
    )
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 1

    captured = capsys.readouterr()
    assert f"{cases / 'bad.yaml'}: $.id:" in captured.err
    assert "is not of type 'string'" in captured.err


def test_check_eval_cases_reports_invalid_utf8_without_traceback(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    root = tmp_path
    cases = root / "evals" / "cases"
    cases.mkdir(parents=True)
    (cases / "bad.yaml").write_bytes(b"id: \xff\n")
    evals = root / "evals"
    for filename in (
        "case.schema.json",
        "case-v2.schema.json",
        "run.schema.json",
        "run-v2.schema.json",
    ):
        (evals / filename).write_bytes(
            (Path(__file__).parent.parent / "evals" / filename).read_bytes()
        )
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text("entries: []\n")
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 1

    captured = capsys.readouterr()
    assert f"{cases / 'bad.yaml'}: cannot read YAML: invalid UTF-8" in captured.err
    assert "Traceback" not in captured.err


def test_check_eval_cases_reports_invalid_schema_json_without_traceback(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    root = tmp_path
    evals = root / "evals"
    evals.mkdir(parents=True)
    (evals / "case.schema.json").write_text("{not-json")
    for filename in ("case-v2.schema.json", "run.schema.json", "run-v2.schema.json"):
        (evals / filename).write_text(
            (Path(__file__).parent.parent / "evals" / filename).read_text()
        )
    cases = evals / "cases"
    cases.mkdir()
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text("entries: []\n")
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 1

    captured = capsys.readouterr()
    assert f"{evals / 'case.schema.json'}: invalid schema:" in captured.err
    assert "Traceback" not in captured.err


def test_check_eval_cases_selects_v1_and_v2_case_schemas(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    root = tmp_path
    evals = root / "evals"
    cases = evals / "cases"
    cases.mkdir(parents=True)
    source_case = yaml.safe_load(
        (Path(__file__).parent.parent / "evals/cases/greenfield-local-tool.yaml").read_text()
    )
    v1_case = dict(source_case)
    v1_case["case_version"] = 1
    (cases / "v1.yaml").write_text(yaml.safe_dump(v1_case, sort_keys=False))
    v2_case = dict(source_case)
    v2_case["case_version"] = 2
    v2_case["id"] = "greenfield-local-tool-v2"
    (cases / "v2.yaml").write_text(yaml.safe_dump(v2_case, sort_keys=False))
    for filename in (
        "case.schema.json",
        "case-v2.schema.json",
        "run.schema.json",
        "run-v2.schema.json",
    ):
        (evals / filename).write_text(
            (Path(__file__).parent.parent / "evals" / filename).read_text()
        )
    extensions = root / "extensions"
    extensions.mkdir()
    (extensions / "index.yaml").write_text(
        (Path(__file__).parent.parent / "extensions/index.yaml").read_text()
    )
    schemas = root / "schemas"
    schemas.mkdir()
    (schemas / "extension-registry-v1.schema.json").write_text(
        (Path(__file__).parent.parent / "schemas" / "extension-registry-v1.schema.json").read_text()
    )
    monkeypatch.setattr(check_eval_cases, "ROOT", root)

    assert check_eval_cases.main() == 0

    assert "validated 2 evaluation cases" in capsys.readouterr().out
