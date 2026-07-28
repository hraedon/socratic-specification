# Taxonomy Reconciliation — Wave 1 Calibration

**Date:** 2026-07-14
**Reviewers:** Reviewer A (GLM), Reviewer B (Kimi)
**Projects:** regista (direct-spec), cert-watch lineage (repeated factory)

## Purpose

Two reviewers independently classified findings for the same two projects.
This document records where they disagreed, resolves each disagreement, and
updates classification guidance for Wave 2 reviewers.

## Regista — Disagreements

### D1: Partitioning reversal (RFC-001)

| Reviewer | Primary class | Contributing |
|---|---|---|
| A | `translation_gap` | — |
| B | `decomposition_gap` | `spec_inconsistency` |

**A's reasoning:** The spec assumed partitioning was needed without evidence of volume. A question about expected event volume would have surfaced this. The gap is in translation of "homelab scale" into "needs partitioning."

**B's reasoning:** The partitioned table broke global event_id uniqueness and the hook_queue FK constraint. This is a schema design issue that should have been caught at work decomposition time, before the first migration was written.

**Resolution:** Both are partially right, but B's classification is more precise. The root cause is a decomposition gap: the schema design did not account for Postgres partitioning constraints (FK to partitioned table requires partition key). The translation gap (assuming partitioning was needed) is a contributing factor, not the primary class. The FK constraint issue is a repository-discoverable fact, not a domain-language question.

**Reconciled classification:** `decomposition_gap` / contributing: `translation_gap`

**Guidance:** When a spec assumption leads to an implementation that breaks technical constraints, the primary class is decomposition_gap (the constraint should have been checked during decomposition), not translation_gap (the assumption was reasonable given the stated context). Translation_gap applies when the human's intent was mistranslated; here the intent ("homelab scale") was correctly understood but the technical consequence was not checked.

---

### D2: Adversarial review rounds as finding vs. effective control

| Reviewer | Treatment |
|---|---|
| A | FINDING-06: `decomposition_gap` — verification layer not planned |
| B | Effective control — "breadcrumb discipline and adversarial review cycles" |

**A's reasoning:** Adversarial review was applied post-implementation reactively, not built into the plan. 8+ rounds finding critical/high bugs means the planned verification was insufficient. The pattern is a gap.

**B's reasoning:** Adversarial review is an effective control that caught critical/high issues before merge. It is a demonstrated defect-detection mechanism, not a gap.

**Resolution:** Both are right — this is both a finding and a control. The finding is that adversarial review was not planned in the work decomposition (it was applied reactively). The control is that once applied, it was highly effective. The classification depends on what question is being asked: "was the verification layer sufficient in the plan?" (yes, it's a gap) vs. "did the control work when applied?" (yes, it's effective).

**Reconciled classification:** Keep as both a finding (`decomposition_gap`) and an effective control. The finding's resolution notes that Plan 027 later formalized review as a built-in gate.

**Guidance:** A control can be both a finding and an effective control. The finding records that the control was missing from the plan; the effective control records that the control worked when applied. Reviewers should record both perspectives when a control was applied reactively rather than proactively.

---

### D3: Scope differences — findings only one reviewer recorded

| Finding | A only | B only |
|---|---|---|
| Spec drift (BC-211/212/213) | Yes | — |
| content_hash validation (BC-301) | Yes | — |
| WI-072 halt/revert | Yes | — |
| Actor role enforcement deferred | — | Yes |
| Replay isolation level (BC-310) | — | Yes |
| Cross-work-item ordering (global_seq) | — | Yes |
| Heartbeat coalescing | — | Yes |
| Schema-per-project model change | — | Yes |

**Resolution:** These are not taxonomy disagreements — they are scope differences. Both reviewers found valid findings the other missed. This is expected in independent review and does not require reconciliation. Wave 2 reviewers should be given both sets of findings as input.

**Guidance:** Scope differences between reviewers are normal and valuable. Do not treat a finding only one reviewer recorded as a disagreement — it may simply be that the other reviewer didn't reach that depth. The reconciliation focuses on classification disagreements where both reviewers found the same issue but classified it differently.

---

## Cert-watch — Disagreements

### D4: Handoff/lineage false positives

| Reviewer | Primary class | Contributing |
|---|---|---|
| A | `implementation_error` | `decomposition_gap` |
| B | `environment_gap` | `implementation_error` |

**A's reasoning:** The integration review's static analysis did not follow FastAPI's Depends() injection pattern. This is a tooling implementation error in the integration reviewer.

**B's reasoning:** The integration-review tool either scanned an incomplete worktree, ignored web/routes/, or produced a stale handoff. This is an environment/tooling gap.

**Resolution:** The distinction between implementation_error and environment_gap is subtle here. The root cause is that the integration review tool did not correctly analyze the code (it missed dependency injection patterns). This is an implementation_error in the review tool itself, not an environment gap (the code was present in the scanned environment). B's `environment_gap` classification would apply if the tool couldn't access the code; but the code was accessible and the tool simply didn't follow DI patterns.

**Reconciled classification:** `implementation_error` / contributing: `decomposition_gap`

**Guidance:** `environment_gap` applies when dev/CI/target environments differ in ways that hide defects (e.g., tests pass locally but fail in prod because a dependency is missing). When a review tool produces incorrect analysis because its implementation doesn't handle a code pattern (DI, decorators, metaprogramming), that's an `implementation_error` in the tool, not an environment gap.

---

### D5: Lineage tracking failure (0 work units recorded)

| Reviewer | Primary class | Contributing |
|---|---|---|
| A | `decomposition_gap` | — |
| B | `spec_inconsistency` | `environment_gap` |

**A's reasoning:** The factory's lineage tracking mechanism failed to record the association between work units and FRs. This is a factory instrumentation design gap — lineage should be tied to agent dispatch events, not bridge.yaml status.

**B's reasoning:** Factory state artifacts contradict each other (test-results show passing tests, lineage shows 0 implementations). This is a spec_inconsistency in the artifacts, caused by an environment/tooling gap.

**Resolution:** A's classification is more precise. The root cause is a decomposition_gap: the factory's work decomposition did not include a reliable lineage tracking mechanism. The artifact contradiction (B's observation) is a symptom, not the root cause. `spec_inconsistency` applies when requirements or artifact references contradict each other within the spec; here the contradiction is between factory artifacts, not within the spec.

**Reconciled classification:** `decomposition_gap` / contributing: `environment_gap`

**Guidance:** `spec_inconsistency` is for contradictions within the specification artifact (spec.yaml, spec.md, ACs, etc.). Contradictions between factory-generated artifacts (lineage.json, test-results.json, handoff.md) are not spec inconsistencies — they are decomposition or environment gaps in the factory's instrumentation. When factory artifacts contradict each other, classify by the root cause (why did the instrumentation fail?) not by the symptom (artifacts disagree).

---

### D6: Scheduler wiring bug — different aspects found

| Reviewer | Finding | Primary class |
|---|---|---|
| A | app.state.scheduler never set in production → HTTP 503 | `decomposition_gap` / `environment_gap` |
| B | Dashboard template lacks visible "Scan Now" button | `decomposition_gap` |

**Resolution:** These are two different findings about the same feature (FR-09 manual scan). A found that the production code path is broken (scheduler not wired in app_factory). B found that the UI doesn't expose the button. Both are `decomposition_gap` — the consumer chain (UI → route → service → scheduler) was not fully traced. No taxonomy disagreement; both classified correctly.

**Guidance:** When two reviewers find different aspects of the same feature gap, record both findings. The consumer-map concept applies to all layers: UI affordance → HTTP route → service → infrastructure.

---

### D7: Phantom coverage — scope disagreement

| Reviewer | Investigation depth |
|---|---|
| A | Investigated actual wiring: confirmed 13/15 FRs have no routes; confirmed handoff's FR-02 claim is a false positive |
| B | Focused on handoff's reliability: noted the contradiction but did not independently verify which FRs are actually wired |

**Resolution:** This is a scope difference, not a taxonomy disagreement. A's deeper investigation produced more precise findings. B's approach was valid but less thorough. For Wave 2, reviewers should be instructed to independently verify factory claims against actual source code, not just record the claims.

**Guidance:** Reviewers must verify factory-generated claims (handoff.md, lineage.json) against actual source code. "The handoff says X" is a finding about the handoff's reliability; "I verified X by reading the code" is a finding about the implementation. Both are valid, but the latter is more useful for lesson extraction.

---

## Summary of reconciled classifications

| # | Finding | Reviewer A | Reviewer B | Reconciled |
|---|---|---|---|---|
| D1 | Partitioning reversal | translation_gap | decomposition_gap/spec_inconsistency | **decomposition_gap** / translation_gap |
| D2 | Adversarial review rounds | decomposition_gap (finding) | effective_control | **Both** — finding + control |
| D4 | Handoff false positives | implementation_error/decomposition_gap | environment_gap/implementation_error | **implementation_error** / decomposition_gap |
| D5 | Lineage tracking failure | decomposition_gap | spec_inconsistency/environment_gap | **decomposition_gap** / environment_gap |
| D6 | Scheduler wiring (different aspects) | decomposition_gap/environment_gap | decomposition_gap | **decomposition_gap** (both correct, different scope) |

## Updated classification guidance for Wave 2

1. **decomposition_gap vs. translation_gap:** When a spec assumption leads to a technical constraint violation, the primary class is decomposition_gap. Translation_gap is for mistranslation of human intent; decomposition_gap is for missing technical verification of a translation that was reasonable at the time.

2. **implementation_error vs. environment_gap:** When a review/analysis tool produces incorrect output because it doesn't handle a code pattern, that's implementation_error. Environment_gap is for environmental differences (dev vs. prod, missing dependencies, different OS).

3. **spec_inconsistency scope:** spec_inconsistency is for contradictions within the specification artifact itself. Contradictions between factory-generated artifacts (handoff, lineage, test-results) are decomposition_gap or environment_gap, not spec_inconsistency.

4. **Findings vs. controls:** A control that was applied reactively (not planned) is both a finding (the plan was insufficient) and an effective control (the control worked when applied). Record both perspectives.

5. **Verification requirement:** Reviewers must verify factory-generated claims against actual source code. Do not classify a factory artifact's claim without independent verification.

## Inter-rater agreement

- **Regista:** 3 shared findings (InMemory divergence, signing envelope, partitioning). 2 had classification disagreements (D1, D2). 1 agreed (InMemory divergence).
- **Cert-watch:** 3 shared findings (alert test failures, handoff false positives, scheduler/FR-09). 2 had classification disagreements (D4, D5). 1 agreed (alert test failures).
- **Agreement rate on shared findings:** 2/6 fully agreed, 4/6 had classification disagreements requiring reconciliation.
- **Scope overlap:** ~60% of findings were found by only one reviewer.

This agreement level is sufficient for Wave 2. The reconciled classifications and guidance above should reduce ambiguity for subsequent reviewers.
