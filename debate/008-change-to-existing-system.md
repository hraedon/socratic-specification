---
number: "008"
title: "Change-to-existing-system mode — eliciting a spec for a brownfield change"
author: claude-opus-4.8 (from cert-watch maintenance session, 2026-06-16)
date: "2026-06-16"
related: ["process.md §Step 0", "process.md §Step 1", "process.md §Step 4", "process.md §Step 5", "process.md §Process Extensions", "debate/003-extension-proliferation-vs-generalization.md", "debate/006-structural-component-manifest.md", "debate/007-system-invariants.md", "debate/001-schema-versioning.md"]
---

## Context

Every part of the process assumes **greenfield**: a vibe spec describes a system
that does not yet exist, architecture is deferred to the implementing agent
(Claim 1), and a single elicitation session produces the spec for its birth. The
sf2 cert-watch fixture is exactly this — the 5-FR MVP at the moment of creation.

A system spends most of its life being *changed*, not created. Real cert-watch
work after v0.1 is brownfield change against a fixed, ~24k-LOC system:

- "Add an OCSP/CRL revocation panel to the certificate view."
- "Remove CT-log monitoring" — a **breaking** change across a minor version.
- "Add a policy rule" — a vertical slice through model, migration, route,
  template, JS, tests, docs.

The base process serves none of these well, because brownfield inverts its core
assumptions.

## Problem

Three inversions, each of which breaks a specific part of the process:

1. **High-coupling decisions are already decided — in the code, not open.** §4 and
   §10 instruct the AI to *classify open* architectural decisions (Decided /
   Deferred-with-flexibility / Deferred-accepted-risk). For a change, the data
   model, auth model, and persistence strategy already exist and are immutable
   context. The real §10 task inverts: *which already-decided couplings does this
   change reach, and what invariant must it preserve so it doesn't break them?*

2. **"Technology left to the implementing agent" is false.** The Implementation
   Default section hands tech choice to the agent. In brownfield the stack
   (FastAPI / SQLite / Jinja, for cert-watch) is fixed; a change that ignores it is
   wrong by construction. Tech is an *input*, not a deferred decision.

3. **The risk shifts from happy-path under-specification to regression.** The base
   process optimizes for "is the happy path fully specified?" A change's risk is
   *interaction with everything already there*: does the schema change have a
   rollback? does it preserve the v0.8 → v0.9 upgrade path? if it's breaking, is
   the break declared and is there a deprecation path? The Step-5 composition
   checks point inward at the new spec; brownfield needs them to point at the
   *seam* between new and existing.

There is also a wrong opening move. Step 1's goal restatement (problem / user /
success) is built for a system that has no prior. For a change, the highest-leverage
opening is not "what are you building" but **"here is the change, here is what it
touches, here is what must keep working."**

## Position

**Add a "Change to Existing System" extension, routed through debate 003's
extensionhood test — not a rewrite of the base process.**

By 003's criteria it qualifies: it introduces **distinct high-coupling decisions**
(migration/rollback, backward-compatibility, breaking-change declaration) and a
**spatial reasoning** need (the blast-radius / dependency map — the change's
analogue of the Mobile screen-flow diagram). Two of three → extension. Extensions
are additive, so the base greenfield process is untouched.

**Activation (Step 0):** the vibe spec references an existing system, a version, a
named existing feature, or a repository.

**Replaces Step 1 restatement with Change Restatement + Blast Radius:**
> *"Here's the change as I understand it: [what changes]. Here's what it touches:
> [components / features / data]. Here's what must keep working exactly as it does
> today: [invariants and existing behavior]. Correct anything before we proceed."*

**Converts §10 to "Touched Couplings":** for each already-decided HCD the change
reaches, state the constraint it must preserve, not a fresh classification.

**Adds Step-5 composition checks aimed at the seam:**
- *Migration path* — every change to persisted state has a stated migration and a
  rollback story.
- *Compatibility* — the change is classified non-breaking / breaking; if breaking,
  the affected consumers and the deprecation/communication path are named.
- *Read-path symmetry, brownfield variant* — does the change orphan or strand an
  *existing* consumer? (The base check asks this of new producers; here it must
  also ask it of removed/altered ones — the CT-monitoring removal is the live case.)

**Adds artifact sections:**
- `[CHANGE] Baseline & Blast Radius` — the system as it is, and what this change
  reaches.
- `[CHANGE] Compatibility & Migration` — break classification, migration, rollback,
  upgrade-path preservation.

**Folds in quality gates here, where they belong.** A separate idea — "the
implementation must satisfy the existing quality gates (coverage ratchet,
inline-style budget, visual baselines, lint)" — only makes sense in brownfield,
because the gates already exist and are *read from the repo*, not elicited from a
human. A non-technical human cannot ask for a coverage ratchet; a maintainer can
point the AI at the one that already exists. So the gates ride in this extension as
a read step, not as a new base-process elicitation.

## Two honesty constraints (the Claim-1/Claim-2 line, per 006)

1. **The input contract changes.** The base thesis is "no spec expertise required;
   the human provides domain knowledge, the process does the rest." Brownfield adds
   a second required input: *the existing system as ground truth.* Someone — the AI
   reading the repo, or the human — must supply what currently exists and what must
   not break. That is a reading-the-codebase competency relocated into elicitation.
   It does not break Claim 1 for new systems, but it cannot be sold *as* Claim 1.
   Publish honestly: this extension specs changes to systems whose architecture is
   already real, and architecture is therefore an input here, not a deferral.

2. **The persona shifts.** "Non-technical human with a vibe" is the wrong persona
   for "remove CT monitoring without breaking the v0.8 upgrade." The person who can
   state what must keep working is usually a maintainer or technical operator, not
   the original non-technical visionary. This connects to the semi-technical-operator
   persona gap; the extension should let mode detection expect a more technical
   counterpart and not force every answer through non-technical translation.

## Why not just do it

- **This is arguably a second product, not an extension.** "Spec the birth of a
  system from a vibe" and "spec a change to a living system" are different enough
  that bolting the second onto the first risks diluting the project's sharp thesis
  ("learn to write specs is a tool skill being automated away") into general SDLC
  tooling. The counter: 003's additive-extension model is precisely the mechanism
  that lets the base thesis stay sharp while the brownfield case is served beside
  it. If the extension cannot be expressed additively, that is the signal it is a
  sibling project and should be named as one.
- **Spec drift.** Changes accumulate; a one-shot `spec.md` goes stale. This
  extension implies versioned, reconcilable specs — which is the real motivation
  behind debate 001 (`schema_version`). Brownfield without versioned specs produces
  a spec that lies about the system within a release or two.

## Relationship to 006 and 007

- **006** (`edges` manifest) is the natural representation of blast radius: a change
  is a diff over the component graph, and "what does this touch" is a graph
  neighborhood query. If 006 ships, this extension's Blast Radius section should be
  expressed as edges, not prose.
- **007** (system invariants) supplies the "what must keep working" vocabulary: the
  technical invariants 007 cannot elicit greenfield (CSP, encryption-at-rest) are
  exactly the ones this extension reads from the repo and pins as preserve-constraints.

## Recommendation

**Pilot against real cert-watch history, do not patch.** Reconstruct one breaking
change (CT-monitoring removal) and one additive change (an OCSP/CRL panel) from the
git log. Score: would Change Restatement + Blast Radius + the compatibility/migration
checks, applied before the change, have named the breakage, the migration, and the
upgrade-path risk that the actual work had to discover? Promote as an extension only
if it surfaces them ahead of implementation. Keep the framing at Claim 2+:
architecture is an input here, and the process says so.

## Blocking

Not blocking current work. Prerequisite for any claim that the process serves
systems past their first release. Depends on 003 (extensionhood framework) being
resolved first, since this is the test case that most stresses it; related to 001
(versioned specs), 006 (blast radius as graph), and 007 (preserve-constraints).

## Pilot implementation (2026-07-14)

The governed pilot is implemented in `extensions/change-existing-system.md`, with
canonical `change-spec.template.yaml`, schema validation, rendering support, and
the downstream work-plan readiness gate. It remains a pilot until one additive
and one breaking historical change meet the stated promotion bar.
