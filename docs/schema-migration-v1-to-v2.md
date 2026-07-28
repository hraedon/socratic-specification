# Migrating Legacy Specifications to Canonical Schema v2

Legacy v1 was implicit: `spec.md` was authoritative, `spec.yaml` was a sidecar,
and projects added fields independently. Migration is therefore an intent review,
not a blind field rename.

## Do not rewrite history

Leave the original spec files and implementation baseline available at their
original commits. Create a v2 revision on a new commit and record the old artifact
fingerprint or commit in migration notes. Historical project mining should analyze
the artifacts that actually drove implementation, not backfilled v2 files.

## Required v2 changes

1. Add `meta.schema_version: 2`, stable `spec_id`, `revision: 1`, and
   `parent_fingerprint: null`.
2. Populate the structured `problem` block from the confirmed Markdown Problem
   Statement. Do not infer missing intent without human confirmation.
3. Add categorical provenance to FRs, business rules, high-coupling decisions,
   ACs, assumptions, and risks. Use `repo_observed` only for facts actually read
   from the repository.
4. Populate `risks` or use `[]` after reviewing hard-to-reverse choices.
5. Reconcile MVP flags, `mvp.fr_ids`, value phase 1, AC references, and dependency
   hints. The semantic validator intentionally rejects disagreement.
6. Validate canonical YAML, render new Markdown and the decision brief, and have
   the human confirm the brief.

## Commands

```bash
python scripts/spec_tools.py validate spec.yaml
python scripts/spec_tools.py render spec.yaml --output spec.md
python scripts/spec_tools.py brief spec.yaml --output decision-brief.md
python scripts/spec_tools.py validate spec.yaml --ready
```

The first validation pass may fail. Resolve errors in canonical YAML rather than
editing generated Markdown. Do not mark an inferred statement as human-confirmed
merely to satisfy the schema.

## Existing-system alternative

If the legacy spec is materially stale and the immediate goal is a bounded change,
do not first pretend to reconstruct a complete current-system v2 spec. Preserve
the legacy artifact, create `change-spec.yaml`, pin the repository baseline, and
use the brownfield extension. A reconciled full-system spec can follow when it has
an actual owner and purpose.
