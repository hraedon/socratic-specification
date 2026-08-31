---
number: "011"
title: "Factory review protocol candidate — breadth, depth, and durable verdicts"
author: glm-5.2 (from portfolio insight mining, Wave 2 partial execution)
date: "2026-08-10"
related: ["process.md §12 Implementation Readiness Gate", "process.md §Step 5", "critique.md (DeepSeek review of debate 005, §4)", "debate/resolved/005-composition-audit.md", "debate/006-structural-component-manifest.md", "debate/010-fail-closed-specification.md", "research/project-insight-mining-plan.md"]
---

## Context

The process requires Step 5 composition verification independent of the
elicitation AI: either a distinct model instance or a structural parse. The
current `spec_tools.py validate --ready` implementation validates schema and
referential/readiness conditions, but does not mechanically check lifecycle
wiring or read-path symmetry. Those composition checks are therefore manual
today unless a distinct reviewer performs them; a mechanical graph/read-path
pass remains a proposed prerequisite rather than a current stable capability.
Factory-bound work additionally receives an independent architecture and
coverage review (§12 Implementation Readiness Gate). The corpus shows that
projects that institutionalize
adversarial review runs a recognizable *shape* — and that shape catches
HIGH/CRITICAL bugs that solo authorship and self-review consistently miss.
The shape is not codified by the process; it is re-derived per project. This
debate proposes formalizing the shape so the process can expect it rather
than hope for it.

### Corpus evidence

**cert-watch** — the 2026-07-01 adversarial review (5 Kimi-K2.7 subagents)
recorded findings at that review baseline, including BasicConstraints.ca
enforcement in `_is_signed_by` (a leaf cert could
act as an intermediate to forge a trusted chain), tag-scoped access control
not consistently applied to alerts/events/analytics, `/metrics` auth gate as
a breaking change, rate limiter fail-open, API-key hash migration issues.
(Source: `reflections/2026-07-01-glm-5-2-7.md`). These are historical review
findings, not claims that the defects remain in current code.

**regista** — WI-239 (lineage fail-open) was caught by adversarial review.
WI-267 (row vs. envelope reconciliation) was caught by independent review.
The project runs a hardening cycle dominated by "fail closed" fixes found by
review, not by tests. (Source: git log, PRs #23–#37)

**usage-dashboard** — the 2026-06-11 adversarial review caught: timing-attack
auth vulnerability, credential exposure in Dockerfiles, exception swallowing,
stale-reading race, spurious offline rows. (Source: `reflections/2026-06-11`)

**openbia** — a cross-lineage adversarial review (Kimi) caught the
MSSQL-breaking `String(32)` vs `String(64)` timestamp width bug. A second
review (Nemotron) caught a tag-dropdown information leak across scopes. Both
were invisible to single-agent authorship. (Source: `reflections/2026-07-08-glm-5-2.md`)

**dossier** — WI-014 (assurance fail-open) caught by Kimi + GLM review. WI-035
(human signing fallback) found during Plan 020 Lane C qualification. The
2026-07-05 reflection: "The two rounds were complementary — round 1 was
breadth (did you wire it everywhere?), round 2 was depth (are the failure
paths sound?)." (Source: `reflections/2026-07-05`, `reflections/2026-07-13`)

**agent-notes** — the 2026-07-20 reflection: "Round 1 (Kimi) found 3 MAJOR
bugs I'd shipped … the kind of thing that looks correct in isolation but
fails in production. … This is the process working as designed." The project
ships adversarial-review skills and subagents (glm/kimi/minimax/nemotron)
that drive review-gate transitions. (Source: `reflections/2026-07-20`)

**gpo-lens** — Plan 024 adversarial review (2 rounds) caught: OR-vs-AND in
the active-occurrence query, severity/summary swap, stale triage metadata,
ignored lifecycle filter, non-atomic expiration sweep — and critically, the
v2 lifecycle engine was implemented but **not wired** to CLI/web ingest
paths. Round 2 caught the unwired engine. (Source: git log, Plan 024)

**adcs-lens** — phase 5 review (3 rounds) caught expired-rule-before-active-rule
corruption. The SARIF structure bug shipped in v1.0.0 because no adversarial
review ran before the initial release; the review discipline was added
afterward. (Source: `docs/review-findings.md`, git log)

**Switchboard** — at the reviewed 2026-08-08 baseline, the adversarial pass
recorded a HIGH HMAC route-key rotation defect: a previous-secret match was
re-resolved under the current secret, causing healthy keyed traffic to receive
503 responses during the rotation window. This is a pinned historical finding,
not a claim that the corrected defect remains present. (Source:
`reflections/2026-08-08`)

### Convergence

Nine project corpora report review findings, but they are not nine controlled
independent trials. adcs-lens additionally supplies a retrospective no-review
comparison from v1.0.0; that comparison is a control candidate, not proof that
the proposed shape would have caught its defects. Specification-lineage
independence and causality must be established by the controlled pilot. The
recurring candidate shape is:

1. **Breadth round** — a different model lineage from the author surveys the
   whole change: "did you wire it everywhere? are all entry points covered?
   is there an unwired engine?" The breadth round catches structural gaps
   (gpo-lens unwired engine, openbia MSSQL width, cert-watch RBAC scope).
2. **Depth round** — the breadth reviewer or another reviewer examines failure
   paths and edge cases; every reviewer must be a different lineage from every
   implementation author: "are the failure paths sound? what happens on
   uncertain input? does the security decision fail open?" The depth round
   catches logic inversions (dossier WI-014, regista WI-239, switchboard HMAC
   rotation).
3. **Durable verdict** — the review verdict is not an ephemeral comment. Where
   a workflow engine exists it advances review or returns work with findings;
   elsewhere it is a durable review record. The record is provenance that the
   review happened and what it found. dossier and agent-notes use regista
   workflow transitions; cert-watch tracks the result in reflections.

The current process references "independent architecture and coverage review"
(§12) and independent Step 5 verification by distinct model **or structural
parse** (debate 005) but does not specify
the breadth/depth/durable-verdict shape. The result: projects that run review
well do so because they developed the practice independently; projects that
don't (adcs-lens v1.0.0) ship preventable bugs.

## Problem

The process has three gaps relative to the observed practice:

1. **The review has no tested shape.** §12 requires an independent architecture
   and coverage review but does not prescribe whether breadth and depth are
   separate rounds. The corpus suggests that they may catch different bugs;
   it does not yet establish incremental yield over one well-scoped pass.

2. **The review is for factory-bound work only.** §12's readiness gate
   applies to "factory-bound work." Projects that use the socratic spec but
   not the factory (most of the corpus: cert-watch, regista, usage-dashboard,
   openbia, agent-notes, dossier, gpo-lens, adcs-lens, sluice, switchboard)
   have no process-level expectation of review. They either build the
   practice themselves or don't.

3. **The review verdict is not an artifact.** The process does not specify
   that the review result is recorded as a state transition or a durable
   artifact. In the corpus, the projects that record the verdict (dossier,
   agent-notes via regista gate transitions) can prove the review happened.
   Projects that don't (cert-watch reflections, adcs-lens review findings)
   have the evidence but not the structured transition.

## Position

**Park this as a factory/review-protocol candidate, not a process extension.
It is an implementation-time competency in Claim 2, does not meet the current
extensionhood criteria, and belongs at the executable review gate rather than
Step 0 elicitation.**

### The shape

**Breadth round:**
- Reviewer: a different model lineage from the author.
- Scope: the whole change — all entry points, all wired paths, all
  consumers.
- Question: "is everything connected? are there unwired engines, unread
  fields, missing entry points?"
- Output: a findings list, each with a location and a class (structural /
  wiring / coverage).

**Depth round:**
- Reviewer: the breadth reviewer or another reviewer; every reviewer declares a
  lineage distinct from every implementation author.
- Scope: failure paths, edge cases, security/provenance decisions, uncertain
  inputs.
- Question: "what happens when things go wrong? does any decision fail open?
  are the failure modes as specified?"
- Output: a findings list, each with a location, a class (logic / security /
  fail-direction), and a severity.

**Durable verdict:**
- The review verdict is recorded as a state transition or a durable artifact.
  For factory-bound work, `readiness_review` is the pre-implementation
  architecture/coverage gate; it is not the implementation verdict. The
  post-implementation verdict belongs in `handoff.review_result`, after the
  independent pre-handoff review. For non-factory work, a regista transition
  may enforce a gate; a reflection or plan-status update is only a durable
  review record and must not be described as an enforcing transition.
- The durable record names the reviewers (lineages), the rounds, the findings,
  and the resolution. It is provenance that the review happened.

### Where it lives

This is not a base-process step or governed process extension. If validated,
it belongs in the factory/review protocol and its executable gate. Candidate
activation signals are:

- The work is factory-bound and reaches the independent pre-handoff review.
- The spec involves security, provenance, auth, or access control
  (overlaps with debate 010's scope).
- The implementing agent is a single agent working alone (the highest-risk
  configuration for self-review blindness).
- The human opts in for non-factory work.

The protocol composes G2 (blast-radius — failure-mode coverage is blocking
for in-path posture) and the debate-005 independent-verification requirement.
It does not re-implement either; it names the shape that may make both more
effective at implementation review.

Before adoption, the factory artifact contract must record round kind,
reviewer identity and lineage, reviewed base/head, scope, finding ids and
severity, disposition, resolution evidence, and final verdict. Schema and
validator changes must distinguish `readiness_review` from
`handoff.review_result`, require every post-implementation reviewer to declare
a model lineage distinct from every implementation author's lineage (UNKNOWN or
missing lineage blocks the gate), require reviewer identity to differ from all
implementers, and reject unresolved blocking findings. Until that exists, the
proposal is descriptive only.

### Relationship to existing constructs

- **§12 Implementation Readiness Gate:** `readiness_review` remains the
  independent pre-implementation architecture/coverage review. This candidate
  concerns the later implementation review and `handoff.review_result`; it does
  not replace or rename the readiness gate.
- **Step 5 independent audit (debate 005):** allows either a distinct model
  instance or a structural parse. The current validator does not implement the
  lifecycle/read-path branch, so those checks remain manual and a mechanical
  composition pass remains proposed. This candidate does not alter that rule.
  It separately requires implementation reviewers to be different lineages
  from every implementation author.
- **agent-notes adversarial-review skills:** already ship the mechanism —
  subagents of different lineages (glm, kimi, minimax, nemotron) that drive
  review-gate transitions. This debate proposes a factory-protocol contract for
  the practice those skills implement.
- **debate 010 (fail-closed specification):** the depth round is the
  verification that fail-direction declarations are honored by the
  implementation. The two debates compose: 010 specifies the property at
  spec time; 011 specifies the review that verifies it at implementation
  time.

## Constraints and risks

1. **Cost.** Two review rounds by different lineages is more expensive than
   one pass or self-review. The protocol is opt-in for non-factory work;
   for factory-bound work, §12 already requires review, and this debate does
   not yet show that a second reviewer is worth its marginal cost. The pilot
   below deliberately holds reviewer count constant, so it estimates the effect
   of review shape only; it cannot justify changing a one-reviewer gate into a
   two-reviewer gate.

2. **The reviewer needs context.** A breadth reviewer who sees only the diff
   misses the unwired-engine class (gpo-lens Plan 024). A depth reviewer who
   sees only the spec misses the implementation's logic inversions. The
   protocol should specify that the reviewer receives the spec, the
   work-plan, and the implementation — not just a diff.

3. **Lineage availability.** Not every environment has multiple model
   lineages available. The minimum: one reviewer whose identity and declared
   model lineage are both distinct from every implementation author.
   The recommended: two reviewers, different lineages from the author and
   from each other. The protocol should name the minimum and the
   recommended, not mandate a specific count.

4. **Self-review is not useless; it's insufficient.** The process should
   not discourage self-review — it catches many bugs. The point is that
   self-review + adversarial review catches more than self-review alone,
   and the adversarial round catches bugs self-review *structurally
   cannot* (the "looks correct in isolation" class). The protocol
   complements, not replaces, self-review.

5. **Enforcement is only as good as the state system.** For factory-bound work,
   the post-implementation verdict is `handoff.review_result`; the separate
   `readiness_review` already gates the start of implementation. For
   non-factory work, a regista transition may enforce a gate, while a reflection
   or plan-status update merely records a result. The protocol should require a
   durable, findable record and state explicitly whether it enforces completion.

## Why not just do it

- **This is an implementation-time concern, not a spec-authoring concern.**
  The socratic spec process is about elicitation and synthesis. The
  adversarial review happens *after* implementation, not during elicitation.
  Putting it in the base process or extension registry would blur the boundary
  between specification and implementation. It should remain a factory/review
  protocol candidate.

- **The factory already has a readiness gate.** §12 already requires
  independent review for factory-bound work. The marginal value of this
  debate is the later implementation-review *shape* (breadth/depth/durable
  verdict), not the *existence* or reviewer count of review. The pilot should
  compare shaped and unstructured review at the same reviewer count and budget.

- **The corpus is self-selecting.** The projects that run adversarial
  review well are the ones that chose to. The ones that didn't (adcs-lens
  v1.0.0) may not have had the infrastructure. The evidence supports
  "review catches bugs" but is weaker on "the breadth/depth split catches
  more than equally resourced general review." The pilot should compare those
  shapes without changing reviewer count.

- **Factory and artifact bloat.** A second round, additional lineage metadata,
  structured findings, and an enforcing verdict are non-trivial additions.
  Controlled evidence must justify them before the factory contract changes.

## Recommendation

**Park pending controlled evidence; do not patch.** Create blinded review
packets from at least six completed changes, including changes with no known
severe defect. Strip prior review results and known outcomes, stratify packets
by change size, risk, and known-defect presence, then randomize within strata.
Both arms receive exactly two independent reviewers, two rounds, the same
lineage-separation rules, the same per-round token/time caps, and the same spec,
work plan, base/head, implementation, and test evidence:

- **Control:** both reviewers receive the same general adversarial-review brief.
- **Treatment:** one reviewer receives the breadth brief and one receives the
  depth brief.

Pre-register reviewer assignments and rotate reviewers across arms on different
packets; no reviewer sees the same packet in both arms, and paired reviewers do
not see each other's findings before adjudication. A separate adjudication panel
validates findings against the code and later outcomes. This estimates
review-shape effect while holding reviewer count and budget constant; reviewer-
count effect is explicitly out of scope.

Add at least two prospective factory changes. Pre-register the treatment before
implementation completes and do not reveal one treatment's findings to the
other. Place prospective changes in matched strata; if both arms review the same
prospective change, use different reviewer pairs and keep their findings
isolated until adjudication. Retrospective reconstruction may calibrate the
taxonomy but cannot by itself satisfy the promotion bar.

Measure validated findings by severity and class, unique validated findings per
arm, false-positive findings, reviewer agreement, elapsed time, model tokens,
and human triage minutes. Reconsider the breadth/depth shape for work that
already uses two reviewers only if:

- shaped review produces at least 25% more validated severity-weighted finding
  yield, using severity weights fixed before review, per fixed review budget
  than the two-reviewer general control, and at least one additional validated
  high/critical finding across the prospective stratum;
- breadth and depth each contribute at least one unique validated finding class;
- false-positive findings do not exceed the matched-control rate by more than five
  percentage points;
- median total model tokens and elapsed reviewer time are no more than 10% above
  the matched control despite the equal caps, and added human triage is no more
  than five minutes per change;
  and
- the canonical artifact and validator prerequisites above are implemented and
  tested before any enforcing gate is claimed.

If incremental yield is absent or cost exceeds the bar, retain unstructured
review at the existing reviewer count. Clearing this bar supports role
specialization only where two reviewers are already required; it does not
support mandating a second reviewer. Any reviewer-count change needs separate
controlled evidence. Do not reconsider process-extension status without a
separate governance change.

## Blocking

**Parked pending controlled evidence.** Complementary to 005 (spec-time audit),
006 (structural verification), 010 (fail-direction specification), the
pre-implementation `readiness_review`, and the post-implementation
`handoff.review_result`. It is not a prerequisite for synthesis and must not be
presented as a stable process extension.
