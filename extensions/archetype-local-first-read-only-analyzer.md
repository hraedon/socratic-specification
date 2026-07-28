# Archetype: Local-First Read-Only Analyzer

**Status: PROPOSED — pending adversarial review.**
**Last validated against:** gpo-lens, adcs-lens, ad-steward, cert-watch (posture),
as of 2026-07-03.

This is the reference archetype — the template every other archetype copies. It
demonstrates the composition rule: an archetype is `guardrail primitives + a small
archetype-specific delta`, never a standalone fork. Nothing here re-implements a
guardrail; it *pulls them in* and adds only what this project type uniquely needs.

---

## What this archetype is

A tool that **reads an existing system, evaluates its posture, and produces
findings — without changing anything.** It is the most-repeated project type in the
library. The corpus instances: gpo-lens (GPO posture), adcs-lens (AD CS / PKI
posture), ad-steward (AD identity posture), and cert-watch's read-only observation
half.

**Detection signals (Step 0):** verbs like *analyze, audit, assess, review, report
on, check the posture/config/health of* an existing system; output is *findings /
evidence / a report*; explicitly *no changes made*.

**Declaration:**
> *"This sounds like a read-only analyzer of an existing system. I'll bring in the
> questions this project type always needs — how it handles the data it reads, what
> runs where, and confirming it never changes anything. Correct me if that's wrong."*

---

## Guardrails this archetype composes

| Guardrail | How it's used here |
|---|---|
| **G1 Data hygiene** | Full. Analyzers read sensitive estate data; findings and fixtures must use synthetic stand-ins for regulated classes, and the real estate must not leak into agent context. |
| **G2 Blast-radius** | **Pinned, not elicited.** The archetype *asserts* posture = read-only observer. The G2 probes become a confirmation ("this only looks, never changes — right?"), and any answer implying a mutation is treated as a mis-detected archetype. |
| **G3 Environment matrix** | Full, and central — see the collector/ingest delta below. The read half almost always runs somewhere different from where it's built. |
| **G4 Operations** | Usually N/A (not a long-running service). The one exception it *does* pull in: distributing and running the collector on the target. |

---

## Archetype delta (what only this project type needs)

### D1 — Collector / ingest split (near-mandatory high-coupling decision)

Every mature instance in the library converged on the same shape: a **collector**
that runs *on or near the target* with the privilege to read it, emitting an inert
export; and an **ingest/analysis** stage that runs *anywhere, offline* over that
export. gpo-lens, adcs-lens, and ad-steward all landed here independently.

Add to Step 4:
- **Collection boundary** — does reading the target require running privileged code
  on the target (a collector), separate from analysis? If yes, the export format
  between them is itself a high-coupling decision (it is the durable contract).

Probe (domain language):
- *"To look at this system, does something have to run right on it with special
  access — or can it all be read from your own machine?"*
- *"If something has to run on it, is what it collects just a file you carry back and
  analyze somewhere else?"*

### D2 — Flag-don't-probe (business rule, mandatory)

The library's hard rule for this archetype: the analyzer **reports exposure; it
never exploits or mutates to confirm one.** This is what makes the read-only
posture real rather than aspirational.

Add to Section 7 (Business Rules), automatically:
- BR: *The system flags a potential exposure from observed configuration; it never
  performs the action that would prove the exposure.* (adcs-lens' "flag don't probe".)

### D3 — Positive-vs-negative validation (acceptance requirement)

The archetype's signature bug class: **fixture and negative validation
structurally hide decode and attribute-name errors.** adcs-lens shipped two real
collector bugs (a Schannel `[ordered]`-index decode; reading `msPKI-OIDToGroupLink`
under the wrong attribute name) that every negative/fixture test passed cleanly —
only a *positive run against a genuinely-exposed target* caught them.

Add to Step 5 / Section 11, automatically (this specializes G3's real-target rule):
- At least one finding class must have an acceptance criterion validated against a
  **real positive** — a target that genuinely exhibits the condition — not only
  against a clean/negative target or a fixture. Where a live positive is
  unavailable, this is recorded as a named delta-to-next-level, not waved away.

### D4 — Findings as durable, diffable evidence (output contract)

Findings across the library are deterministic and comparable run-to-run (drift /
diff detection — new / resolved / changed), and signed where provenance matters.

Add to Section 6 (Data — Outputs), as a default to confirm:
- Findings are deterministic for a given input export and diffable across runs
  (supports "what changed since last time"). Provenance signing is offered as a
  high-coupling decision when the findings are evidence others will rely on.

### D5 — Synthetic fixture-estate discipline (composes G1)

Because testing an analyzer means feeding it an "estate," the fixtures *are* the
test surface — and the recurring pitfall (gpo-lens) is fixtures drifting from the
real system's shape, or embedding real regulated data. G1 already forbids real
regulated data in fixtures; the archetype adds the positive obligation:

- A synthetic estate fixture that matches the *structural shape* of the real target
  (not its data) is a first-class deliverable, because the analyzer's correctness is
  only as good as the shapes it was tested against.

---

## What the driver experiences

The colleague answers, in their own words: what the tool looks at, whether they can
read it from their own machine or something has to run on the system, what in the
data would be sensitive, and where the tool will actually run. From those answers
the agent has already pulled in: read-only posture (confirmed), the collector/ingest
split, flag-don't-probe as a rule, the positive-validation requirement, synthetic
fixtures, and the dev≠deploy risk note — the accumulated playbook of four prior
projects, none of which the driver had to know existed.

---

## Copy-this-to-make-a-new-archetype checklist

1. State what the archetype *is* and its detection signals.
2. List which guardrails it composes, and whether any are **pinned** (asserted) vs.
   elicited.
3. Add only the delta — the high-coupling decisions, business rules, and
   acceptance requirements unique to this project type, each traced to ≥2 corpus
   instances.
4. If the delta can't be kept small, it isn't an archetype — it's a new base-process
   concern and belongs in a `debate/` entry instead.
