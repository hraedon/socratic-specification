# Active Debate

Structured positions on architectural and design questions that are not yet resolved. One file per topic. These are arguments and recommendations, not defects.

When a debate item is resolved (accepted or rejected), it should be:
- Accepted → move to a process amendment with resolution note
- Rejected → move to `debate/resolved/` with rejection rationale
- Stale → close if no activity for 90 days

## Index

| # | Title | Position | Blocking |
|---|---|---|---|
| 002 | Completion rate instrumentation | Metrics contract implemented; collect enough local outcome data before drawing process conclusions | Before the next major process revision |
| 004 | Translation risk post-hoc validation | Add a lightweight "spec smell" check that runs after synthesis, before handoff | Before spec is consumed by multi-agent pipelines |
| 006 | Structural component manifest for Step 5 | Back the composition checks with a mechanical graph pass over a `components`/`edges` block; pilot before patching; keep in Claim 2 | Prerequisite for claiming the spec process closes the composition-gap class |
| 007 | System invariants (requirements over all FRs) | Add a fifth construct for properties that must hold for every FR (audit, RBAC scope, CSP), with a per-FR conformance checklist; pilot against cert-watch's ratchets; keep the elicitable subset in Claim 1 | Prerequisite for claiming the process addresses cross-cutting properties, not just per-FR behavior |
| 008 | Change-to-existing-system mode (brownfield) | Pilot extension and delta schema implemented; validate against additive and breaking historical changes before stable promotion | Prerequisite for claiming the process serves systems past first release |

## Resolved

| # | Title | Resolution |
|---|---|---|
| 001 | Schema versioning | **Accepted** (2026-07-14) — canonical spec schema v2, work-plan v1, change-spec v1, explicit compatibility checks. |
| 003 | Extension governance | **Accepted** (2026-07-14) — registry, composition rules, template, statuses, and empirical promotion bars implemented in `extensions/`. |
| 005 | Composition and lifecycle audit | **Accepted with modifications** (2026-05-25) — folded into process.md §Step 5 per [DeepSeek adversarial review](../critique.md). See [resolved/005-composition-audit.md](resolved/005-composition-audit.md). |
