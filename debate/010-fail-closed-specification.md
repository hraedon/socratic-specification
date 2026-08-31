---
number: "010"
title: "Fail-direction specification for security and provenance decisions"
author: glm-5.2 (from portfolio insight mining, Wave 2 partial execution)
date: "2026-08-10"
related: ["process.md §8 Error and Failure Handling", "process.md §10 High-Coupling Decisions", "process.md §Step 5", "extensions/guardrails.md (G2)", "debate/007-system-invariants.md", "research/project-insight-mining-plan.md"]
---

## Context

A pattern recurs across security-critical and provenance-instrumented projects
in the portfolio: a decision point that affects a security or provenance
property has a logic inversion or silent fallback that *looks* correct in
isolation. The system continues operating — "nothing looked broken" — but
silently weakens its guarantee. The failure is discoverable only by a verifier
or an explicit probe, not by normal operation.

### Corpus evidence

**dossier** — WI-014 (HIGH, security): `assurance.py:56` failed open when
reviewer lineage was undeclared. A one-line logic inversion
(`reviewer_lineage in author_lineages` → should be `not in`). A reviewer with
no declared lineage was reported as `independently_reviewed` — exactly the
over-claim a provenance UI must never make. A related type-coercion bug:
author lineages were `str()`-coerced but the reviewer side wasn't, leaving a
genuine over-claim avenue. (Source: `reflections/2026-07-13-glm-5-2.md`)

**dossier** — WI-035 (HIGH, provenance): human signing identity was broken.
Dossier signed human events under the auth backend's `stable_id` (a minted
uuid / `objectGUID`) but no key was registered against those ids, so
regista's `resolve_signing_key` fell back to the **shared store-level HMAC
key**. The event still sealed into the chain — "nothing looked broken" — but
anyone holding the store key could produce it, and `regista verify` reported
`1 unverifiable (symmetric scheme)`. Found during Plan 020 Lane C Linux
qualification on a human `accept` of a work item whose three agent legs all
signed correctly. Violation of agent-suite bootstrap-contract §5. (Source:
`docs/provenance-model.md`, commit `61eecdc`)

**regista** — WI-239 (HIGH, security): `same_lineage()` returned `False` for
both confirmed-cross-lineage AND undeclared reviewers. The human-gate
escalation read unknown independence as proven independence — the opposite of
conservative. Fixed by introducing `LineageRelation` (SAME/DISTINCT/UNKNOWN)
and treating UNKNOWN like SAME. (Source: git log, WI-239)

**cert-watch** — the 2026-07-01 reflection recorded a rate-limiter fallback to
in-memory state on SQLite errors. Changing that behavior to refuse traffic was
deferred because it could worsen an SQLite-pressure event. This pinned decision
is a declared-direction control, not an assertion about current code and not an
instance of an undeclared-direction failure. (Source:
`reflections/2026-07-01`)

**sluice** — the `retry-after: 0` truthy-string fail-open: `response.headers.get("retry-after")`
returns `"0"` (truthy string), so the 429 was NOT recorded as a concurrency 429
— silent fail-open. Initial fix used exact-match `_ra == "0"`, which
adversarial review (Kimi K2.7) flagged as too narrow — `"00"`, `" 0 "`, `""`,
`"abc"` would all fail-open. Second pass: strip + int-parse, treat unparseable
as concurrency 429 (fail-safe). (Source: `reflections/2026-07-01`)

### Convergence

The corpus supplies candidate failure cases from dossier, regista, and sluice,
plus cert-watch as a declared-direction control. These are project corpora, not
four controlled independent trials; the pilot must verify specification-lineage
independence before counting them toward the mining-plan bar. The dossier
`provenance-model.md` §1 states the corrective rule *reactively* — "rendering
**less** than the engine claims is always safe; rendering **more** never is" —
added after WI-014. The regista WI-239 fix states its rule reactively —
"undeclared lineage is UNKNOWN, never independent." The pattern is plausible:
projects that touch security or provenance often state the conservative rule
only after an incident. The controlled pilot must test whether a spec-time
declaration changes that outcome.

## Problem

The base process has no construct for **fail direction** — the behavior the
system exhibits when a security or provenance decision encounters uncertainty,
missing data, or an unrecognized input.

- **Error and Failure Handling (§8)** describes what triggers a failure and
  what the system does in response. But it assumes the failure is *recognized*.
  The fail-open class is about the system *not recognizing* that it is in a
  failure state — the logic inversion makes the uncertain case look like the
  safe case.
- **High-Coupling Decisions (§10)** may record a security decision (e.g., "auth
  model: LDAP"), but it does not require the decision to declare what happens
  when the auth check is uncertain.
- **NFRs (§9)** state measurable qualities, not behavioral guarantees under
  uncertainty.
- **Business Rules (§7)** state domain rules the system must not violate, but
  the fail-open class is about the system *silently* violating a rule it
  appears to enforce.

The result: an implementer building a security or provenance decision has no
spec-level signal that the decision must declare its fail direction. The
implementer's default — when the spec is silent — is to handle the expected
case and let the unexpected case fall through. The fall-through is the bug.

The **empirical tell**: the candidate failure cases acquired a *reactive* rule
after an incident — dossier's provenance-model §1, regista's
`LineageRelation` enum, and sluice's fail-safe int-parse. The pilot tests
whether those rules were knowable and useful at specification time.

## Position

**Pilot a Step 3 elicitation probe, a Step 5 audit check, uncertainty-case ACs,
and a Section 8 annotation for security/provenance decisions. Keep it inside
Claim 1: the human can answer "what should happen if the system isn't sure?"
Do not promote until the canonical artifact and validator can enforce the
result.**

### Step 3 probe (domain language)

When the spec involves security, auth, identity, provenance, audit, or
access control, add to the iteration loop:

> *"If the system isn't sure whether someone is allowed to do something — say,
> it can't reach the permission system, or the record is incomplete — should
> it let them in and figure it out later, or hold off until it's certain?
> What's the worst that happens each way?"*

This is domain language. The human answers in terms of consequences and risk
tolerance, not fail-open vs. fail-closed. The AI neutrally records the selected
direction, the harm avoided, the harm introduced, and why that tradeoff is
acceptable. Neither direction is labelled inherently safe: refusing may cause
an outage or lockout, while proceeding may weaken a security or provenance
guarantee.

### Step 5 audit check (addition to the manual composition audit)

For every decision point that affects a security or provenance property
(auth, identity, access control, audit, signing, verification, lineage):

- Does the spec state the **fail direction** — what the system does when the
  decision is uncertain (missing data, unrecognized input, dependency
  unreachable)?
- If fail-open: is the rationale recorded and the risk accepted by the human?
- If fail-closed: is the degradation behavior specified (refuse, retry,
  degrade to a safe subset)?

If neither: the decision has a **fail-direction gap**. For MVP-scope
decisions, this blocks synthesis.

For every in-scope decision, acceptance criteria must exercise at least the
applicable uncertainty classes: missing data, malformed or unrecognized input,
dependency unreachable or timed out, and contradictory evidence. Each AC states
the externally observable result and links it to the declared direction. A
declaration without uncertainty-case ACs does not close the gap; these ACs are
the downstream check against implementation logic inversions.

### Section 8 annotation

The failure-mode table (§8) gains a column or annotation for
security/provenance rows: **Fail direction** (fail-closed / fail-open with
rationale / unknown — flagged as a gap). This is a specialization of the
existing failure table, not a new section.

The pilot uses a structured decision record with a stable id, affected FRs and
failure rows, protected property, uncertainty classes, selected behavior,
tradeoff rationale, human confirmation, and linked AC ids. Free-form failure
rows are insufficient. Promotion requires corresponding schema and template
fields, deterministic rendering, referential checks for AC ids, and future
`validate --ready` failures for missing direction or uncertainty coverage. The
current validator does not perform those checks. Until the schema, renderer,
semantic checks, and tests exist, this audit is manual and must not be described
as mechanically enforced.

### Domain-language translation

| Composition concern | Implementation-layer phrasing (do not ask) | Domain-language phrasing (ask) |
|---|---|---|
| Fail direction | "Does `check_access()` fail open or closed on LDAP unreachable?" | "If the system that checks permissions is down, do people get in by default, or get locked out? Which is worse for you?" |
| Verification fail direction | "Does `verify()` return True on unparseable or False?" | "If the system can't tell whether a record is authentic, does it treat it as safe or as suspicious? What does 'suspicious' mean for your users?" |
| Lineage/audit fail direction | "Is undeclared lineage treated as independent or unknown?" | "If someone didn't say whether they reviewed independently, do we assume they did, or assume we don't know?" |

### Relationship to existing constructs

- **Guardrail G2 (blast-radius / mutation posture):** G2 makes failure-mode
  coverage *blocking* for in-path/issuance posture. This debate generalizes
  explicit fail-direction tradeoffs beyond in-path systems to *any* security
  or provenance decision. G2 is the mandatory version for the highest-risk
  posture; this is the general declaration rule for the broader class.
- **Debate 007 (system invariants):** Invariants are properties that must
  hold for every FR. Fail direction is a property of *decision points*, not
  of FRs. An invariant says "every action is audited"; fail direction says
  "when the audit log is unreachable, the action is blocked (fail-closed) or
  proceeds (fail-open with rationale)." They compose: an invariant with an
  unspecified fail direction is half-stated.
- **Provenance taxonomy:** The spec already has `assumed` as a provenance
  kind. A fail-open decision is one where the system *acts* on an assumption
  without flagging it. The new rule makes the assumption explicit at spec
  time, where the provenance taxonomy already has vocabulary for it.

## Constraints and risks

1. **Not every decision has a security/provenance dimension.** A UI
   rendering choice that fails open (shows stale data) is not a security
   failure. The check should scope to decisions where the property at stake
   is auth, identity, access, audit, signing, verification, or lineage —
   the same scope where G2 applies, generalized beyond mutation posture. Generic
   CLI exit-code and exception-mapping behavior is out of scope unless it is
   explicitly tied to one of these protected properties.

2. **Fail-closed can be operationally dangerous.** A fail-closed auth system
   locks everyone out when LDAP is down. The spec should not mandate
   fail-closed universally; it should mandate *that the direction is declared
   and the tradeoff is the human's*. The domain-language probe makes this a
   human decision, not an agent default.

3. **The "uncertain" case is hard to enumerate at spec time.** The
   implementer knows the expected case; the spec can name the obvious
   uncertainty (dependency unreachable, input unrecognized) but cannot
   foresee every edge. The check is a floor — it forces the question for the
   known-uncertain cases, not a guarantee of coverage for all cases. Do not
   overclaim it as exhaustive.

4. **Self-review inherits blind spots (debate 005/006).** A fail-direction
   declaration authored by the same agent that wrote the decision inherits
   the agent's assumptions about what "uncertain" means. The Step 5 check
   raises the floor (the question gets asked); it does not guarantee the
   answer is correct. Step 5 requires an independent mechanism, but the current
   `spec_tools.py validate --ready` implementation checks schema/references,
   MVP-AC coverage, blocking questions, and decision classification; it does
   not mechanically check lifecycle wiring, read-path symmetry, or fail
   direction. Those composition checks remain manual unless a distinct reviewer
   performs them. Mechanical composition and fail-direction checks are proposed
   promotion prerequisites, with an additional independent architecture review
   for factory-bound work.

## Why not just do it

- **Scope ambiguity (debate 003).** "Security or provenance decision" is a
  fuzzy boundary. The pilot should calibrate: does the check fire on every
  auth-adjacent FR, or only on the high-coupling decisions in §10? The
  minimum viable scope: §10 decisions involving auth, identity, access,
  audit, signing, or verification, plus §8 failure rows that touch those
  properties. Broader application can follow if the pilot shows value.

- **The prose check may already be good enough.** The existing §8 failure
  table, if filled honestly, already names what the system does when things
  go wrong. The gap is that §8 does not *require* the fail-direction column
  for security rows, and the implementer's default when the column is empty
  is to handle the expected case. The evidence shows that "naming the
  failure mode" is not "declaring the fail direction" — WI-014's code
  handled the expected case (declared lineage) and let the unexpected case
  (undeclared lineage) fall through to the wrong answer.

- **Template bloat.** This adds a Step 3 probe (conditional on
  security/provenance presence), a Step 5 check, a Section 8 annotation, and
  a translation table row. The additions are small and conditional. The
  Section 8 annotation is a column, not a new section. The Step 3 probe
  joins the existing security-domain flag (Step 3, item 8).

## Recommendation

**Pilot, do not patch.** Build a blinded fixture set before reviewers see known
outcomes. Include:

- dossier (assurance computation, human signing fallback, access control
  mode) — WI-014 and WI-035 are the canonical cases.
- regista (lineage classification, key validity window, replay fail-open) —
  WI-239 is the canonical case.
- sluice retry-after parsing as a candidate failure case with malformed and
  unrecognized-input uncertainty variants.
- cert-watch's pinned 2026-07-01 rate-limiter decision as a declared-direction
  control expected not to be flagged; do not infer current implementation
  behavior from the historical reflection.

Add at least six negative controls from ordinary validation, UI, availability,
and generic CLI failures, plus synthetic uncertainty cases not derived from the
known incidents. Remove project names and outcomes from reviewer packets. Two
reviewers independently identify in-scope decisions, missing declarations, and
missing uncertainty ACs; a separate adjudicator scores against pre-recorded
expected classifications. Run at least one prospective security/provenance
change before implementation if available.

Record decision-level recall, false-positive rate, reviewer agreement, number
of human questions, elapsed time, and model token usage. Promote only if:

- at least 80% of adjudicated in-scope gaps and every adjudicated high-severity
  gap are detected;
- no more than 15% of negative controls are incorrectly pulled into scope;
- reviewers agree on at least 80% of classifications before adjudication;
- the probe adds a median of no more than two human questions and 1,000 model
  tokens per spec containing in-scope decisions; and
- at least one prospective case produces a declared direction plus executable
  uncertainty-case ACs before implementation.

Promotion also requires the schema, renderer, template, and validator work
described above, with tests proving missing, malformed, unreachable, and
contradictory uncertainty cases are represented and linked. Missing the recall
bar means revise the probe; excessive scope or attention cost means narrow it;
no prospective behavior change means park it.

## Blocking

Not blocking. Complementary to 005 (resolved — composition), 007 (cross-cutting
invariants — this specializes the fail-direction dimension of invariants),
and G2 (blast-radius — this generalizes explicit fail-direction handling beyond
in-path posture).
Prerequisite for any claim that the spec process — not just reactive
post-incident rules — closes the fail-open failure class in security and
provenance code.
