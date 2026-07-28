# Extension: Change to an Existing System

**Status: IMPLEMENTED — pilot against historical changes before declaring stable.**

This extension produces a delta specification for changing a living system. It
does not regenerate or pretend to replace the system's complete baseline spec.
The existing repository is an explicit input and remains ground truth for current
architecture and behavior.

## Activation

Activate when the request names an existing repository, release, deployed system,
or behavior to add, remove, repair, or alter. Confirm in domain language:

> This is a change to an existing system. I will inspect what exists, identify
> what the change touches, and make preservation, compatibility, and rollback
> explicit. Correct me if this is actually a new standalone system.

## Replaces the greenfield opening

Restate four things before detailed questions:

1. What changes.
2. What user or operator outcome changes.
3. What the initial repository inspection suggests it touches.
4. What must continue working exactly as it does now.

The human confirms intent and preserved outcomes. The agent—not the human—owns
repository inspection and technical blast-radius discovery.

## Additional high-coupling decisions

- Compatibility classification: non-breaking or breaking.
- Persisted/exchanged representation migration and supported read versions.
- Rollback or recovery when rollback is impossible.
- Whether an existing coupling is preserved or deliberately revisited.

## Additional probes

- "What works today that would be unacceptable to lose while making this change?"
- "Do older saved records, exported files, or clients still need to work afterward?"
- "If the change behaves badly after release, what is the safe way back?"
- "Does anyone outside this repository rely on the thing being changed?"

## Repository-derived inputs

Before synthesis, inspect and record:

- Baseline commit and release/state.
- Existing tests, linters, budgets, and deployment checks.
- Actual consumers of every changed contract.
- Persisted/exchanged versions and real historical fixtures.
- Existing behavior evidence for every preservation claim.

Absence must be explicit. "No existing quality gates found after inspecting X"
is valid; an omitted quality-gate section is not.

## Seam audit

The pre-synthesis audit checks:

- Every preserved behavior has repository/test evidence and a regression AC.
- Every changed contract names consumers and a preserved invariant.
- Breaking changes have migration, rollback/recovery, and communication paths.
- Read-path changes do not strand an existing producer or consumer.
- The proposed change does not silently revise the baseline spec's human-owned
  scope or value priorities.

## Output

Produce canonical `change-spec.yaml` from `change-spec.template.yaml`, validate it,
and render a human-readable `change-spec.md`. Work decomposition then produces the
usual `.factory/work-plan.yaml`, with `change_mode: existing_system`.

## Pilot bar

Evaluate at least one additive and one breaking historical change. Promote this
extension to stable only if it surfaces known migration, consumer, or regression
risks before implementation without forcing the human to answer codebase questions.
