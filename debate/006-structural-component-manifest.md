---
number: "006"
title: "Should the Step 5 composition checks run over a structural component manifest?"
author: claude-opus-4.8 (from sf2 golden-run classification)
date: "2026-05-29"
related: ["process.md §Step 5", "debate/resolved/005-composition-audit.md", "critique.md §Adversarial Review: Debate 005", "spec.template.yaml"]
---

## Context

A design note proposed adding an upstream **component manifest** to the spec
artifact — each component with a stable id, type, responsibility, and explicit
interfaces list — so that an implementing agent wires against named IDs and the
set of existing referents becomes enumerable and lintable. The stated motivation
("Fact 1") was that the dominant real failure is *mechanical referent errors:
implementers wiring components to things that don't exist, inventing functions.*

That premise was tested against the software-factory-2 corpus (47 golden runs,
the CLASS-* defect taxonomy, the RFCs). Full classification:
`/projects/software-factory-2/.factory/analysis/2026-05-29-referent-error-classification.md`.

Two findings change the shape of the proposal:

1. **The invented-referent failure is already solved downstream — mechanically.**
   sf2's RFC-015 AST-walks locked interface stubs into a symbol manifest and adds
   a gate that fails any `from <module> import <symbol>` where the symbol does not
   exist. Before it: 3 of 4 inner-gate failures were invented-symbol imports.
   After it: **zero** "has no attribute" failures across a run, and the residual
   failures are genuine type/logic reasoning (mypy, pytest) that no manifest
   catches. So referent-pinning is real but not where the leverage is, and it is
   not a spec-authoring problem — it is a downstream lint over *locked* artifacts.

2. **The failure that actually survives at the spec layer is the one debate 005
   already named:** *locally complete, globally disconnected* — orphaned modules,
   unstated lifecycle wiring, missing read paths. Two independent implementations
   of cert-watch both built `start_scheduler()` and never called it. That is not
   an invented referent; it is a **mis-wiring among declared referents** — the gap
   the original referent-pinning framing does not address.

## Problem

Step 5 now performs composition checks (lifecycle wiring, read-path symmetry,
configuration surface). `critique.md:98` (DeepSeek's review of debate 005) flagged
the self-review risk and recommended a cross-model or structural alternative.
This **was** adopted in commit 29e56c4 (2026-05-25), which added:

> "The composition checks must be performed by a model instance distinct from
> the one that conducted elicitation, OR replaced with a structural
> symbol-reference parse over the spec text. Self-review by the elicitation AI
> is insufficient for this class of check."

However, the structural-parse branch remained unimplemented until `spec_tools.py`
shipped (2026-07 wave). The requirement existed on paper; the mechanism did not.
This debate's original framing ("it was *not* adopted") was incorrect — the
requirement was adopted but not yet mechanically enforceable. The open question
this debate addresses remains valid: how to make the structural parse the
primary verification path rather than a prose aspiration.

## Position

**Reframe the manifest from referent-pinning (Claim 1) to composition-checking,
and make it the structural backing for the Step 5 checks — not a referent lint.**

Concretely: have synthesis emit a lightweight `components` block — for each
component a stable `id`, a one-line `responsibility`, and an `edges` list
(`calls`, `reads`, `writes`, `configured_by`, `lifecycle`). The Step 5 composition
checks then run as a **mechanical graph pass** over that block instead of a prose
judgment:

- *Lifecycle wiring* = every component with a scheduler/background/cleanup role
  has an inbound `lifecycle` edge. (Was: model judgment.)
- *Read-path symmetry* = every `writes` target has a matching `reads` edge. (Was:
  model judgment.)
- *Orphaned module* = every component has ≥1 inbound edge or an explicit
  `entrypoint: true`. (New — this is the cert-watch `start_scheduler` case, which
  the current prose checks do not reliably catch.)

This is the structural parse `critique.md:98` asked for, expressed in the spec's
own vocabulary rather than Python symbols (the spec has no code yet).

## Two hard constraints, both from the sf2 evidence

1. **It must be cross-model, never self-review.** An *authored* manifest is not
   ground truth — unlike RFC-015's manifest, which is *projected* from locked
   artifacts. sf2 GR-045 is the cautionary case: the decomposer confabulated a
   whole component with a clean ID and consistent interfaces; a lint over a
   manifest *containing* it passes. A manifest authored by the same agent that
   wrote the spec inherits the spec's blind spots. The graph pass therefore only
   adds value run by the independent post-synthesis reviewer the process already
   defines for factory-bound specs — and its findings are *flags for that
   reviewer*, not a green light.

2. **It is Claim 2, and the thesis framing must say so.** A components-with-edges
   block asks the elicitation agent to commit to a coarse topology. That is
   architecture, which the process explicitly defers, and it is where confident
   wrongness lives (sf2 GR-047: two capable models disagree on HTTP/route
   topology). Adding it does not undercut Claim 1 (specification-as-elicitation),
   but it cannot be sold *as* Claim 1. Publish honestly: the manifest relocates an
   architecture competency into the upstream agent; it does not make architecture
   unnecessary.

## Why not just do it

Real arguments against, which is why this is a debate and not a patch:

- **Template bloat (debate 003).** A `components`/`edges` block is a large
  addition to the base template for a benefit that only materializes when there
  is a non-trivial call graph. It may belong behind the same extensionhood test
  003 proposes, not in the base.
- **The prose checks may already be good enough.** Debate 005's own next-step was
  to *measure* false-positive rate on cert-watch + 3 specs before integrating.
  That measurement does not appear to have been run. The structural version should
  clear the same bar before replacing prose: pilot it, compare graph-pass findings
  against the known cert-watch gaps, and only promote if it catches the
  `start_scheduler`-orphan class that the prose pass misses.
- **Authored topology can be wrong in ways that pass the graph pass** (constraint
  1). The graph pass raises floor (no orphans, no dangling writes); it does not
  raise ceiling (correct topology). Overclaiming its guarantee is the failure mode.

## Recommendation

Pilot, do not patch. Run the three graph checks above as a standalone pass over
the cert-watch spec and the existing Socratic specs, scored against the documented
cert-watch gaps. Promote into Step 5 (replacing the prose checks) only if it
catches the orphaned-module class at <30% false positives — the same bar 005 set
for itself. Keep the framing in Claim 2.

## Blocking

Not blocking. Complementary to 004 (translation smells) and the resolved 005
(composition audit). Prerequisite for any future claim that the spec process — not
just a downstream gate — closes the composition-gap failure class.

## Resolution Addendum (2026-07-28)

The cross-model audit requirement this debate's Problem section references was
adopted in commit 29e56c4 (2026-05-25) — the original "not adopted" framing above
has been corrected. The requirement stated: distinct model instance OR structural
symbol-reference parse. With `spec_tools.py validate --ready` now shipping as the
structural parse, the OR branch is mechanically satisfied. process.md Step 5 has
been updated to name `spec_tools.py` as the independent verification mechanism.

The debate's core recommendation — pilot the graph pass against cert-watch gaps
before promoting — remains open and valid. The structural parse satisfies the
*minimum* cross-model requirement; the graph pass would strengthen it further.
