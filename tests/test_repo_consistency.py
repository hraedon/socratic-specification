from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _workflow_files() -> list[Path]:
    if not WORKFLOWS.is_dir():
        return []
    return sorted(WORKFLOWS.glob("*.yml"))


def test_ci_dependency_paths_exist() -> None:
    for wf in _workflow_files():
        content = wf.read_text()
        for match in re.finditer(r"cache-dependency-path:\s*(.+)", content):
            dep_path = match.group(1).strip().strip("'\"")
            assert (REPO_ROOT / dep_path).exists(), (
                f"{wf.name}: cache-dependency-path references '{dep_path}' "
                f"which does not exist"
            )

    for wf in _workflow_files():
        content = wf.read_text()
        for match in re.finditer(r"pip install -r\s+(\S+)", content):
            req_path = match.group(1).strip().strip("'\"")
            assert (REPO_ROOT / req_path).exists(), (
                f"{wf.name}: pip install -r references '{req_path}' "
                f"which does not exist"
            )


def test_ci_scripts_exist() -> None:
    for wf in _workflow_files():
        content = wf.read_text()
        for match in re.finditer(r"python\s+(scripts/\S+)", content):
            script_path = match.group(1)
            assert (REPO_ROOT / script_path).exists(), (
                f"{wf.name}: references script '{script_path}' "
                f"which does not exist"
            )


def test_ci_fixture_paths_exist() -> None:
    for wf in _workflow_files():
        content = wf.read_text()
        for match in re.finditer(r"(tests/\S+\.ya?ml)", content):
            fixture_path = match.group(1)
            assert (REPO_ROOT / fixture_path).exists(), (
                f"{wf.name}: references fixture '{fixture_path}' "
                f"which does not exist"
            )


def test_workflows_are_valid_yaml() -> None:
    for wf in _workflow_files():
        with wf.open() as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), f"{wf.name}: not a valid YAML mapping"
        assert "jobs" in data, f"{wf.name}: missing 'jobs' key"
