# Active Debate

Structured positions on architectural and design questions that are not yet resolved. One file per topic. These are arguments and recommendations, not defects.

When a debate item is resolved (accepted or rejected), it should be:
- Accepted → move to a process amendment with resolution note
- Rejected → move to `debate/resolved/` with rejection rationale
- Stale → close if no activity for 90 days

## Index

| # | Title | Position | Blocking |
|---|---|---|---|
| 001 | Schema versioning for spec.template.yaml | Add `schema_version` to spec.template.yaml before downstream consumers proliferate | Next consumer beyond sf2 |
| 002 | Completion rate instrumentation | Add lightweight session telemetry to measure where humans drop off | Before adding new extensions |
| 003 | Extension proliferation vs. generalization | Define when an extension belongs in the base process vs. as an extension | Next extension (web, data pipeline, etc.) |
| 004 | Translation risk post-hoc validation | Add a lightweight "spec smell" check that runs after synthesis, before handoff | Before spec is consumed by multi-agent pipelines |
