---
number: "009"
title: "External contract validation — the theater-test failure class"
author: glm-5.2 (from portfolio insight mining, Wave 2 partial execution)
date: "2026-08-10"
related: ["process.md §5 Functional Requirements", "process.md §11 Acceptance Criteria", "process.md §Step 5", "debate/006-structural-component-manifest.md", "extensions/archetype-local-first-read-only-analyzer.md (D3)", "research/project-insight-mining-plan.md"]
---

## Context

A pattern recurs across the project portfolio that the base process does not
address: a test encodes a contract with something outside the repository — an
external API, a real dependency, a cross-system protocol — and the test is
self-consistent but built from a hand-written assumption, not a recorded real
payload. It passes, ships, and fails silently in production.

This is not the same as debate 006's composition gap (locally complete, globally
disconnected). It is not the same as resolved debate 005's manual
lifecycle/read-path checks.
Those are internal referent problems — wiring among declared components. This is
an **external referent problem** — the spec and its tests assume a contract that
the external system does not honor.

### Corpus evidence

**cert-watch** — the dated 2026-06-05 LDAP handoff records three integration
bugs that had shipped with a green mocked suite and were then corrected:
- `_resolve_ca_cert()` passed inline PEM contents to `Path().is_file()`,
  raising `OSError(ENAMETOOLONG)`.
- `authenticate()` passed `use_ssl=` to `ldap3.Connection(...)` — it is a
  `Server` argument.
- `LDAP_REQUIRED_GROUPS` was split on `,` — but group DNs *contain* commas, so
  each DN was shredded into RDN fragments and every login failed.

  The `MagicMock` Connection swallowed bad kwargs; comma-split never hit a real
  DN. The mocked unit suite passed. (Source: `docs/archive/2026-06-05-ldap-e2e-handoff.md`)

**usage-dashboard** — the spec's own reconciliation note names the pattern
explicitly:

> "Three separate bugs found on 2026-08-03 shared this shape: a test that is
> self-consistent but never touches reality."

  - At the 2026-08-03 incident baseline, Switchboard read
    `target.get("timestamp")` while usage-dashboard emitted `fetched_at` →
    `ts_epoch` was `None` → `stale` stayed `True` → `CachedReading.ok` was
    `False` on successful fetches → usage-aware failover did not fire. The
    fixture encoded the wrong contract. This is a historical reconstruction,
    not a claim about the current implementations.
  - z.ai window bug with an aged fixture — the fixture's values no longer
    matched the live API's ranges.
  - At the Plan 003/spec baseline, the open questions (§13) listed the Ollama
    login method, z.ai field mappings, and Claude OAuth schema as "needs
    research," while implementation initially proceeded from assumptions. The
    then-assumed Ollama email/password flow did not match the subsequently
    observed WorkOS AuthKit flow; the Claude endpoint was established by CLI
    binary analysis. These are pinned historical findings, not assertions about
    current provider behavior. (Source: `docs/spec.md` §0, §13, §16; Plan 003)

**adcs-lens** — ESC13 was a *permanent false negative*: the detector read the
OID→group link from `msPKI-OIDToGroupLink` instead of `msDS-OIDToGroupLink`.
Every fixture test passed. Only live validation against the lab CA caught it.
The archetype for local-first analyzers already encodes this as D3
(positive-vs-negative validation). (Source: `docs/review-findings.md`, git log)

**agent-notes** — the native op-log degrade path (Tier A — the *default* safe
mode) was untested for `model_lineage`; the regista-attached path was
well-covered. `model_lineage` was stored on create/update/close but never read
back or surfaced in `diagnose` output on the native path. A different contract
than the regista path, undocumented. (Source: `reflections/2026-07-20`)

**sluice** — the `retry-after` classifier used `retry-after` presence/value to
classify 429s as concurrency vs rate-limit vs gateway. This was empirically
wrong: genuine umans concurrency 429s arrive with `retry_after: 1` (a positive
value), so the heuristic never fired on the real thing. The breaker stayed
`closed` through the event it was meant to prevent. A 5-hour self-inflicted
outage resulted from treating `rate_limited` (deprioritization, account still
serving) as a hard box. (Source: `docs/wi-024-429-capture-2026-07-03.md`,
`docs/wi-033-canonical-429-bodies.md`)

### Convergence

Five project corpora exhibit the candidate failure class; they are not yet five
verified independent specification lineages. Independence must be established
from their source-spec and implementation histories before the mining-plan bar
is counted. The usage-dashboard reflection names the pattern with unusual
directness — "a test that is self-consistent but never touches reality" — and
the cert-watch LDAP handoff and adcs-lens ESC13 bug are structural twins. The
recurrence is sufficient to justify a pilot, not promotion.

## Problem

The base process has no slot for *external contract validation*. The spec:

- Records open questions (§13) that may include "needs research" items about
  external systems — but implementation proceeds against assumptions anyway.
- Defines acceptance criteria (§11) that may depend on external contracts — but
  does not require evidence that the contract was validated.
- Classifies spec levels (§2) where Level 2 requires "integration points
  described at the level of detail available" — but "available" can be zero
  real evidence, and the spec does not flag the gap as blocking.

The result: an FR that depends on an external API enters the spec with an
assumed contract, gets an AC that encodes the assumption, passes a test that
asserts the assumption, and ships. The assumption was never validated against
the real system. The failure is invisible until production.

The **empirical tell** mirrors debate 007's ratchet observation: when a project
grows a "recorded fixture" discipline (adcs-lens's live-validation status per
ESC class, cert-watch's `ldap-e2e` CI job, usage-dashboard's Plan 003 named
pattern), that discipline is the fossil of a spec-level gap. The projects
that survive this class are the ones that built the discipline reactively after
a production incident. The spec should make it proactive.

## Position

**Pilot a manual Step 5 audit check and a Level 2 readiness rule for external-contract
FRs. Keep it inside Claim 1: the human can answer "did you test it against the
real thing?" Do not promote the rule until the canonical artifact and validator
can represent and enforce it.**

### Step 5 audit check (addition to the consistency and composition audit)

For every FR that calls, reads from, or depends on an external system:

- Is there a **recorded real payload, contract excerpt, or live-validation
  result** in the spec's evidence? Or
- Is the external contract explicitly classified as **unvalidated**, with a
  named risk, owner, delta-to-next-level, and explicit human acceptance of
  proceeding at Level 1?

If neither condition is complete, the FR has an **external-contract gap**. For
MVP-scope FRs, an `unvalidated` classification without explicit human acceptance
still blocks synthesis. Qualifying evidence closes the gap; explicit acceptance
instead permits synthesis and implementation at Level 1 while leaving the gap
open in the delta-to-next-level. It never makes the integration Level
2-verifiable. For non-MVP FRs, the unvalidated contract is recorded as an
assumption with the specific risk named; acceptance is required only before the
FR enters MVP scope.

### Step 2/Level 2 rule

An FR that depends on an external contract with no recorded evidence cannot
contribute to a Level 2 ("Verifiable") assessment. The spec may still be Level
1 ("Implementable") — but the "integration points described at the level of
detail available" clause is honest about what "available" means: zero real
evidence means the integration point is described at Level 1, not Level 2.

This does not permanently block implementation: the human may accept the risk,
but the achieved level and delta-to-next-level must remain honest.

### Canonical evidence record (pilot prerequisite)

The pilot must use a structured record, even before it is added to the stable
schema. Each externally controlled contract records:

- stable contract id and affected FR ids;
- evidence kind (`official_contract`, `sanitized_observation`,
  `live_validation`, or `unvalidated`);
- source reference, observation date, and immutable fingerprint where a local
  artifact is retained;
- validation scope and known limitations;
- for `unvalidated`, the named risk, owner, and human risk-acceptance decision.

The evidence kind is the contract-evidence layer; categorical provenance remains
the existing artifact-wide source layer. `official_contract`,
`sanitized_observation`, and `live_validation` map to `externally_verified` only
when the source reference and validation scope support the affected claim.
`unvalidated` maps to `assumed`, even when the human accepts its risk. Risk
acceptance authorizes proceeding; it does not upgrade provenance.

Free-text provenance notes alone are not sufficient. Promotion requires a
versioned schema field, deterministic rendering, and `validate --ready`
semantics that reject an MVP external-contract FR with neither qualifying
evidence nor explicit risk acceptance, and reject a Level 2 claim for any MVP
contract that remains `unvalidated` even when its risk was accepted. Until
those mechanics exist, this is a manual pilot and must not be described as
mechanically enforced.

The current `validate --ready` implementation does not inspect external
contracts, lifecycle wiring, or read-path symmetry; it checks the installed
schema plus existing reference, MVP-AC, blocking-question, and classified-
decision conditions. External-contract validation and the broader composition
checks therefore remain manual. Their mechanical checks are proposed promotion
prerequisites, not current validator capabilities.

### Domain-language translation (per the Step 5 principle)

| Composition concern | Implementation-layer phrasing (do not ask) | Domain-language phrasing (ask) |
|---|---|---|
| External-contract validation | "Does AC-03 have a recorded payload from the real API?" | "When we build this connection to [external system], have we seen what it actually sends back — or are we guessing? If we're guessing, is that a risk you want to take now, or should we check before building?" |

### Relationship to existing constructs

- **Open questions (§13):** An external-contract unknown already lands here as
  "needs research." The new rule makes it **blocking for MVP scope** rather than
  merely recorded. The human can proceed only by explicitly accepting the
  unvalidated-contract risk at Level 1; merely deferring or recording the
  question does not unblock synthesis.
- **Assumptions (§14):** An unvalidated external contract that proceeds anyway
  is an assumption. The new rule requires the assumption to name the specific
  risk ("if the API field mapping is wrong, the integration silently produces
  no data") rather than a generic rationale.
- **Archetype D3:** The local-first read-only analyzer archetype already
  requires positive validation for finding classes. This debate generalizes
  the principle beyond analyzers to *any* FR with an external dependency.

## Constraints and risks

1. **Not every external dependency needs a recorded payload.** A well-known
   API with stable, documented behavior (e.g., a standard OAuth flow) may not
   need the same rigor as an undocumented vendor API. The check should allow
   `official_contract` as an evidence kind, mapped to `externally_verified`
   provenance for the supported claim. The gap is specifically *assumed*
   contracts presented as if *known*.

2. **False-positive risk on trivial integrations.** An FR that reads a JSON
   file from disk has an "external" dependency in a literal sense. The check
   should scope to integrations where the contract is not under the author's
   control — APIs, protocols, file formats defined by others.

3. **The human may not know the answer.** "Did you test it against the real
   thing?" is a question a non-technical human cannot always answer — they may
   not have access to the external system during the spec conversation. The
   domain-language probe handles this: "are we guessing, and is that a risk?"
   The human can say "yes, we're guessing, and I accept the risk" — that is a
   valid deferral, now explicit.

4. **This is not a demand for integration tests at spec time.** The check is
   about *evidence in the spec*, not *test execution during elicitation*. A
   sanitized payload extract, redacted transcript, official contract excerpt,
   or access-controlled observation can prove the contract was observed rather
   than invented. The test comes later; the safe evidence reference comes now.

5. **Observed evidence must be safe to retain.** Raw curl transcripts,
   screenshots, headers, directory records, and vendor payloads may contain
   credentials, identifiers, PII, or regulated data. The canonical record must
   point to a minimized, redacted extract or an access-controlled evidence
   location; secrets and regulated records must not be copied into the spec,
   fixtures, review output, or agent context. Redaction must preserve the fields
   and shapes relevant to the claimed contract, and the record must say what was
   removed.

## Why not just do it

- **Template bloat (debate 003).** This adds a Step 5 check, a Level 2 rule,
  and a domain-language translation. The check is a natural extension of the
  existing manual composition checks, not a new section. The Level 2 rule is a
  clarification of "level of detail available," not a new field. The
  translation table grows by one row. Net addition is small.

- **The prose check may already be good enough.** The existing Step 5
  "integration points described at the level of detail available" *names* the
  gap but does not *flag* it. The cert-watch, usage-dashboard, and adcs-lens
  evidence shows that "naming" is not "flagging" — the specs had open questions
  about external contracts, and implementation proceeded anyway. The check
  needs to be **blocking for MVP scope** to have teeth, not just advisory.

- **The evidence bar is fuzzy.** What counts as a "recorded real payload"? A
  full API transcript? A single curl output? A link to docs? The pilot should
  calibrate. The minimum bar: the contract claim is externally sourced or
  observed, not invented. Qualifying official docs produce `official_contract`
  evidence and `externally_verified` provenance; a hand-written expectation
  produces `unvalidated` evidence and `assumed` provenance. The structured
  evidence record carries details that categorical provenance alone cannot.

## Recommendation

**Pilot, do not patch.** Build a scored fixture set before reviewers see the
historical outcomes:

- usage-dashboard's pinned Plan 003 baseline (Claude OAuth, z.ai, Ollama) — use
  only the pre-fix spec-time evidence and exclude current implementation state.
- cert-watch's pinned 2026-06-05 LDAP handoff — use the pre-fix contract evidence
  that preceded the three documented and subsequently corrected bugs.
- adcs-lens (ESC13 detector) — fixture passed; live validation caught the bug;
- at least six negative controls: documented standard integrations and
  repository-owned formats that should not trigger a gap;
- at least three ambiguous controls whose classification is adjudicated before
  scoring.

Remove project names and known outcomes from the review packet. Two reviewers
independently classify each FR using only the spec-time evidence. A separate
adjudicator resolves disagreements against the canonical evidence records.
Where possible, add one prospective integration before implementation; do not
count a retrospective known failure as prospective evidence.

Record recall on known assumed-contract gaps, false-positive rate on negative
controls, reviewer agreement, number of new human questions, elapsed review
time, and model token usage. Promote only if the pilot:

- detects at least 80% of adjudicated gaps and all gaps judged capable of
  causing silent security or data-loss failure;
- produces no more than 20% false positives on negative controls;
- reaches at least 80% reviewer agreement before adjudication;
- adds a median of no more than one human question and 800 model tokens per
  externally integrated MVP FR; and
- demonstrates in at least one prospective case that the check produces either
  qualifying evidence or explicit risk acceptance before implementation.

Promotion also requires the schema, renderer, template, and validator changes
described above, with tests for evidence, risk-acceptance, Level-2, and redaction
failure cases. Failing the detection bar means revise the classifier; exceeding
the false-positive or attention-cost bar means narrow the scope; failure to
produce a prospective behavior change means park the proposal.

## Blocking

Not blocking. Complementary to 005 (resolved — internal composition), 006
(structural verification of internal referents), and 007 (cross-cutting
properties). Prerequisite for any claim that the spec process — not just
downstream production incidents — closes the external-contract failure class.
