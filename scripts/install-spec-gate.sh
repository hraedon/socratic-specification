#!/usr/bin/env bash
set -euo pipefail

# Install a lightweight spec-validity gate into a consumer project's CI.
#
# The gate validates spec.yaml (if present) against the socratic-specification
# schema and checks that generated views are in sync. It does NOT enforce
# ongoing maintenance — specs are scaffolding, not living contracts. The gate
# catches broken YAML at commit time (the regista failure) and stale generated
# views, then gets out of the way.
#
# Usage:
#   /path/to/socratic-specification/scripts/install-spec-gate.sh [target-repo]
#
# If target-repo is omitted, installs into the current directory.

SPEC_REPO="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

if [ ! -d "$TARGET/.git" ]; then
  echo "error: $TARGET is not a git repository" >&2
  exit 1
fi

GATE_DIR="$TARGET/.spec-gate"
mkdir -p "$GATE_DIR"

cp "$SPEC_REPO/scripts/spec_tools.py" "$GATE_DIR/spec_tools.py"
cp -r "$SPEC_REPO/schemas" "$GATE_DIR/schemas"

cat > "$GATE_DIR/spec-gate.sh" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Spec-validity gate. Validates spec.yaml and checks generated view sync.
# Exit 0 if no spec.yaml exists (not all projects have one).

GATE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

SPEC="$REPO_ROOT/spec.yaml"
if [ ! -f "$SPEC" ]; then
  exit 0
fi

python_bin="$(command -v python3 || command -v python)"

"$python_bin" "$GATE_DIR/spec_tools.py" validate "$SPEC"

if [ -f "$REPO_ROOT/spec.md" ]; then
  "$python_bin" "$GATE_DIR/spec_tools.py" check-sync "$SPEC" "$REPO_ROOT/spec.md"
fi

if [ -f "$REPO_ROOT/decision-brief.md" ]; then
  "$python_bin" "$GATE_DIR/spec_tools.py" check-sync "$SPEC" \
    "$REPO_ROOT/decision-brief.md" --kind brief
fi

echo "spec-gate: passed" >&2
EOF
chmod +x "$GATE_DIR/spec-gate.sh"

WORKFLOW_DIR="$TARGET/.github/workflows"
mkdir -p "$WORKFLOW_DIR"

cat > "$WORKFLOW_DIR/spec-gate.yml" << 'EOF'
name: spec-gate
on:
  push:
    paths: ['spec.yaml', 'spec.md', 'decision-brief.md', '.spec-gate/**', '.github/workflows/spec-gate.yml']
  pull_request:
    paths: ['spec.yaml', 'spec.md', 'decision-brief.md', '.spec-gate/**', '.github/workflows/spec-gate.yml']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install 'PyYAML>=6.0,<7' 'jsonschema>=4.20,<5'
      - run: .spec-gate/spec-gate.sh
EOF

echo "Installed spec gate into $TARGET"
echo "  Gate script: .spec-gate/spec-gate.sh"
echo "  CI workflow: .github/workflows/spec-gate.yml"
echo ""
echo "The gate validates spec.yaml against the schema and checks generated"
echo "view sync. It is a no-op if no spec.yaml exists."
