---
number: "007"
title: "System invariants — requirements quantified over all functional requirements"
author: claude-opus-4.8 (from cert-watch maintenance session, 2026-06-16)
date: "2026-06-16"
related: ["process.md §5 Functional Requirements", "process.md §7 Business Rules", "process.md §9 Non-Functional Requirements", "process.md §Step 5", "debate/006-structural-component-manifest.md", "debate/008-change-to-existing-system.md"]
---

## Context

The spec artifact has four constructs for "what the system must do or be":

- **Functional Requirements** (§5) — one testable behavior each, vertical.
- **Business Rules** (§7) — a domain rule the system must not violate.
- **Non-Functional Requirements** (§9) — a measurable runtime quality (latency, reliability).
- **High-Coupling Decisions** (§10) — a point architectural choice.

None of these expresses a requirement **quantified over every functional
requirement** — a property that must hold each time the system does anything,
regardless of which FR is executing. The sf2 cert-watch fixture
(`tests/fixtures/cert-watch/`, 5 FRs + 3 infra work-items) does not surface this
gap, because at five FRs there is nothing to quantify over. The real cert-watch
(~24k LOC, production) is dominated by it.

Examples from the deployed system, none of which is an FR, NFR, or BR as the
template defines them:

- *Every state-changing action is written to the audit log, fail-open (the log
  never blocks the action it records).*
- *Every HTTP response carries a CSP nonce; no inline styles or scripts.*
- *Every endpoint enforces the calling identity's RBAC scope.*
- *Every stored secret is encrypted at rest and never written to a log.*

## Problem

An invariant is not any of the existing constructs:

| Construct | Why it doesn't fit |
|---|---|
| FR | An FR is *one* behavior. "Every action is audited" is not a behavior; it is a constraint on all behaviors. |
| NFR | An NFR is a measurable runtime quality with a derived numeric threshold. "No inline styles" has no threshold; it is a boolean that must hold everywhere. |
| Business Rule | A BR is a single domain rule ("an order total cannot be negative"). The template treats BRs as a flat list, with no obligation that *each FR demonstrate conformance*. An invariant's whole content is the universal quantifier. |
| HCD | An HCD is decided once. An invariant must be *re-satisfied by every FR that is added later* — including FRs that do not exist when the spec is written. |

Because the process has no slot for these, every new FR silently re-opens each
invariant, and conformance is left to the implementing agent's memory. At scale
this is the largest single source of regressions: an agent implementing "add a
policy rule" has no spec-level signal that the new route must enforce RBAC scope,
emit an audit record, and carry the CSP nonce.

**The empirical tell.** When a codebase grows a *mechanical gate* to enforce a
property across all surfaces, that property was an unspecified invariant. cert-watch
has a committed `INLINE_STYLE_BUDGET` ratchet test whose only job is to enforce
"no inline styles" across every template, a coverage ratchet, and CSP-nonce
plumbing threaded through the base template. Each is a lint compensating for a
requirement the spec never stated. The ratchet is the fossil of a missing
invariant. (Observed directly: a one-line UI change in this session tripped the
inline-style ratchet on CI — the gate caught what no FR had ever declared.)

## Position

**Add a fifth construct — System Invariants — with a Step-3 elicitation probe, a
synthesis section, and a per-FR conformance obligation. Keep it inside Claim 1:
invariants are behavioral, not architectural.**

**Elicitation (Step 3 probe), domain language:**
> *"Is there anything that has to be true every single time the system does
> something — a record of who did it, a check that they were allowed to, a limit
> that always applies? Not for one feature — for all of them."*

**Synthesis (new section, between §7 Business Rules and §9 NFRs):**

> ## System Invariants
> Properties that must hold for every functional requirement, including ones added
> later. Each invariant names the FRs it does *not* apply to, with a reason.
>
> - INV-01: [property] — applies to: all FRs except [FR-xx: reason]

**Conformance obligation (the load-bearing part).** §11 (Acceptance Criteria)
gains a rule: each FR carries a one-line **invariant checklist** — for each
INV, `conforms` / `N/A (reason)`. This is a checklist, not duplicated ACs; the
goal is to force the *question* per FR, not to multiply test rows. An FR that
silently omits the checklist is a spec defect, in the same spirit as the §Step-5
"silently empty prerequisites section" rule.

## Constraints and risks

1. **Over-flagging.** Not every shared utility is an invariant. The bar: a property
   is an invariant only if violating it on *any single* FR is a defect of the
   whole system, not of that FR. "Validate email format" is a utility (debate 005
   dropped check 5 for exactly this reason); "every action is audited" is an
   invariant. Invariants should be few and human-confirmed — the 80/20, not an
   exhaustive aspect catalogue.

2. **Scope to MVP**, mirroring the resolved 005 decision: only enforce the per-FR
   checklist on MVP-scope FRs to avoid noise on deferred work.

3. **The non-technical-human boundary is real and partial.** A non-technical human
   can name "there must be a record every time" (audit) but will never name "CSP
   nonce on every response." The behavioral, domain-expressible invariants are
   in-thesis and elicitable now. The purely technical ones (CSP, encryption-at-rest)
   are not elicitable from a vibe spec — they become spec-able only in the
   brownfield mode (debate 008), where they already exist in the repo and are
   *read*, not asked. This debate claims only the elicitable subset for the base
   process; it forward-references 008 for the rest.

## Relationship to 006

006's `components`/`edges` block is the natural structural home for *checking*
invariant conformance mechanically once it exists — e.g., every component with a
state-changing `writes` edge must carry an `audited` marker; the graph pass flags
those that don't. That is complementary and should be piloted on its own bar
(006's <30% false-positive threshold), not bundled here. This debate is about
*declaring* invariants at elicitation time; 006 is about *verifying* topology.
Declaration is useful even with no graph pass.

## Why not just do it

- **Template bloat (debate 003).** A fifth construct plus a per-FR checklist is a
  real addition to the base template for a benefit that only materializes past a
  handful of FRs. It may warrant the same extensionhood test 003 proposes rather
  than unconditional base inclusion — though unlike Mobile, invariants are
  project-type-agnostic, which argues for the base.
- **It can be gamed.** A checklist of `conforms` lines authored by the same model
  that wrote the FRs inherits that model's blind spots — the same self-review
  weakness 005/006 name. The checklist raises the floor (the question gets asked
  per FR); it does not guarantee the answer is true. Do not overclaim it as a
  conformance *proof*.

## Recommendation

**Pilot, do not patch.** Reconstruct the invariant set cert-watch actually enforces
(audit fail-open, CSP/no-inline-style, RBAC scope, secret-at-rest) and one or two
other Socratic specs' implicit invariants. Score: would a System Invariants section
+ per-FR checklist, applied at spec time, have named the property each ratchet now
mechanically enforces? Promote into the base template only if it names the
invariant class without ballooning AC counts (target: per-FR checklist adds one
line per FR, not new test rows).

## Blocking

Not blocking. Complementary to 005 (resolved), 006 (structural verification), and
008 (the brownfield subset). Prerequisite for any claim that the spec process
addresses cross-cutting properties rather than only per-FR behavior.
