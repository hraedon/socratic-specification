# Optional Local Process Metrics

The process should be improved from outcomes, not completion anecdotes. Runners
may write a local metrics record conforming to `schemas/session-metrics-v1.schema.json`.
Collection is opt-in, disclosed, content-free, and local by default.

## Privacy boundary

Never record prompts, answers, requirement text, repository contents, personal
identifiers, or project names. `project_key` is a locally generated opaque value.
Publishing or aggregating records is a separate human decision.

## Elicitation measures

- Highest process step reached.
- Question rounds and total human questions.
- Human corrections per round.
- Desired and achieved spec levels.
- Time to synthesis and generated artifact size.
- Whether a decision brief was confirmed or corrected.

## Downstream outcome measures

- Work-plan revisions before implementation and after implementation began.
- Human decisions requested during implementation.
- Defects classified as elicitation, translation, specification consistency,
  decomposition/consumer coverage, implementation, environment, or compatibility.
- Repeated defect classes and architecture pauses.
- Acceptance criteria revised after code began.
- Time to first useful delivery and whether the value phase was accepted.

Completion and downstream quality must be reported together. A shorter process
that shifts questions into implementation is not an improvement.

## Interpretation rules

- Do not draw conclusions from fewer than ten comparable sessions.
- Report counts and distributions; do not assign individuals a quality score.
- Compare like project modes and complexity bands.
- Investigate outliers qualitatively without copying sensitive content into the
  metrics store.
- A process change graduates only when it improves its intended outcome without
  increasing critical misses or human-attention cost elsewhere.
