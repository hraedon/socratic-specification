#!/usr/bin/env python3
"""Create a metadata-only seed manifest for Socratic project mining."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import yaml


SKIP_PARTS = {".git", ".venv", "node_modules", ".pytest_cache", ".worktrees"}
SPEC_NAMES = {"spec.md", "spec.yaml", "change-spec.md", "change-spec.yaml"}
FACTORY_NAMES = {"run-summary.json", "run-history.jsonl", "handoff.md", "test-results.json", "state.yaml", "work-plan.yaml"}


def bounded_files(root: Path, max_depth: int = 4) -> list[Path]:
    files: list[Path] = []
    for directory, dirnames, filenames in os.walk(root):
        current = Path(directory)
        depth = len(current.relative_to(root).parts)
        dirnames[:] = [
            name for name in dirnames if name not in SKIP_PARTS and depth < max_depth
        ]
        files.extend(current / name for name in filenames)
    return files


def history_mentions(repository: Path) -> list[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "log",
                "--all",
                "--format=%H",
                "--regexp-ignore-case",
                "--grep=socratic",
                "--grep=vibe spec",
                "--grep=specification",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [line for line in result.stdout.splitlines() if line]


def build_manifest(root: Path) -> dict:
    projects = []
    repositories = sorted(
        (path for path in root.iterdir() if path.is_dir() and (path / ".git").exists()),
        key=lambda path: path.name.lower(),
    )
    for number, repository in enumerate(repositories, start=1):
        files = bounded_files(repository)
        spec_artifacts = sorted(
            str(path) for path in files if path.name.lower() in SPEC_NAMES
        )
        factory_evidence = sorted(
            str(path)
            for path in files
            if ".factory" in path.parts and path.name.lower() in FACTORY_NAMES
        )
        commits = history_mentions(repository)
        if spec_artifacts:
            strength = "direct_artifact"
            pointers = spec_artifacts[:20]
        elif commits:
            strength = "history_inference"
            pointers = [f"commit:{commit}" for commit in commits[:20]]
        else:
            strength = "unknown"
            pointers = []
        projects.append(
            {
                "project_key": f"project-{number:03d}",
                "repository_path": str(repository),
                "eligibility": "candidate" if strength != "unknown" else "unknown",
                "exclusion_reason": "",
                "lineage_type": "unknown",
                "archetype": "",
                "origin_evidence": {"strength": strength, "pointers": pointers},
                "spec_artifacts": spec_artifacts,
                "factory_evidence": factory_evidence,
                "implementation_baseline": "",
                "first_useful_delivery": "",
                "outcome": "unknown",
                "privacy_classification": "review_required",
                "deep_review_selected": False,
            }
        )
    return {
        "manifest_version": 1,
        "generated_at": "",
        "scope_root": str(root),
        "projects": projects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/projects"))
    parser.add_argument("--output", type=Path, default=Path("research/corpus-manifest.yaml"))
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"root does not exist: {args.root}")
    manifest = build_manifest(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    print(f"wrote {args.output} with {len(manifest['projects'])} repository candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
