---
number: "005"
title: "Composition and lifecycle audit — catching orphaned modules and unstated wiring"
author: opencode-kimi-k2.6
date: "2026-05-25"
resolved: "2026-05-25"
resolution: accepted-with-modifications
related: ["process.md §Step 5", "debate/004-translation-risk-spec-smells.md", "critique.md §Adversarial Review: Debate 005"]
---

> **Resolution (2026-05-25): Accepted with modifications per [DeepSeek v4-pro adversarial review](../../critique.md).** Folded into Step 5 (no separate Step 5.5). Retained: lifecycle wiring (check 1) and read-path symmetry (check 4). Weakened: configuration check now asks "is this deployment-configurable?" without prescribing mechanism. Dropped: data-to-UI coverage (check 3, redundant with expanded Step 5) and validation call-site coverage (check 5, false-positive risk on utility functions). Added: cross-model audit requirement and domain-language translation table. See `process.md` §Step 5 for the merged version. Original proposal preserved below for traceability.

---

## Context

Two independent implementations of the same MVP (cert-watch) from the same per-module work-item files produced identical gaps. Both built `start_scheduler()`, `AlertConfig`, and `validate_chain_order()` correctly — and neither ever called them. Both included `delete()` in the repository base class but built no delete UI. Both ran the scheduler but never displayed `scan_history`. The spec was faithful module-by-module; the product was still broken.

This is not translation risk in the sense of debate 004. The requirements are not vacuous or under-probed. They are *locally complete and globally disconnected*. The Socratic process probes happy-path functional requirements well; it probes how those FRs compose into a running system weakly.

The cert-watch input was post-decomposition work items, so decomposition may have stripped composition context. But the same gaps appear in full Socratic specs: interfaces are defined, but call graphs, lifecycle hooks, and configuration provenance are left to the implementing agent's inference. The limitation is upstream.

## Problem

The process has no explicit check for three structural composition failures:

1. **Orphaned modules:** Interfaces are defined but no caller or lifecycle hook is specified.
2. **Unstated provenance:** Configuration objects exist with no stated runtime source.
3. **Negative-space gaps:** Operations exist in the data layer but no FR drives the corresponding UI or API.

These are not contradictions (Step 5 does not catch them). They are not oversized FRs (Step 3 item 10 does not catch them). They are not translation-quality smells (debate 004 does not catch them). They are omissions in the *system narrative* — the story of how the pieces actually run together.

## Position

Add a **Composition and Lifecycle Audit** as Step 5.5, running after the Pre-Synthesis Consistency Audit (Step 5) and before synthesis (Step 7). It is a checklist, not a gate — the AI runs it against the accumulated spec and either asks the human a closing question or records an explicit assumption.

### Composition checks

1. **Lifecycle wiring:** For every function or module flagged as startup, background, scheduler, or cleanup, is there an AC that places it in the runtime lifecycle?
   - *`start_scheduler()` is defined but no AC says "Given the app has booted, the scheduler is running."* → Flag: where does this start? At boot, on first request, or manually?

2. **Configuration provenance:** For every configuration dataclass or object, is there a stated runtime source (env vars, config file, DB, UI form)?
   - *`AlertConfig` has fields but no AC says "Given SMTP_HOST is set, alerts send."* → Flag: where does this config come from in production?

3. **Data-to-UI coverage:** For every abstract repository method (create, read, update, delete, list), is there a corresponding UI or API FR that exposes it to a user or system?
   - *`delete()` is in the repository base class but no FR says "the user can remove a host."* → Flag: is delete for users, for tests, or for future use?

4. **Read-path symmetry:** For every data producer, is there a stated consumer?
   - *`scan_history` is written by the scheduler but no FR says "the user views scan history."* → Flag: who reads this table, and under what condition?

5. **Validation call-site coverage:** For every validation or business-rule function, is there an AC that calls it in the context of a user-visible workflow?
   - *`validate_chain_order()` is implemented but no AC says "when a chain is uploaded, order is validated."* → Flag: when is this validation triggered?

If a gap touches a high-coupling decision (e.g., where configuration lives), the AI asks the human. If it is low-stakes (e.g., whether delete is MVP), the AI assumes, records the default, and moves on. The audit does not block synthesis — it is advisory.

## How it works

The AI runs the five checks against the accumulated spec, focusing on Section 11 (Acceptance Criteria), Section 12 (Work Decomposition), and module interface definitions. It produces a report:

> *"Composition audit complete. I reviewed [N] lifecycle items, [N] config objects, [N] repository methods, [N] data producers, and [N] validation functions. [No orphaned items found. / I found the following wiring gaps: [list].]"*

For each gap, the AI chooses:
- **Ask:** one follow-up question in domain language, or
- **Assume:** record an explicit assumption with a default (e.g., "Assumption: `delete()` is for future use, not MVP").

The check is deterministic and fast. A clean audit is a single sentence; only gaps expand the conversation.

## Why this matters

The Socratic process optimizes for local completeness: each FR is testable, each module is well-defined. Agentic implementation optimizes for local faithfulness: each work item is implemented as specified. The result is a system where every piece is correct and the whole still doesn't work. This is the most expensive class of surprise because it is discovered at integration time, when rewiring requires touching multiple modules. Catching it before synthesis keeps rework cheap — often a single missing AC.

The alternative — catching this at decomposition time — means the decomposer must reconstruct composition context that the spec never captured. That is backwards: the spec should own the system narrative; decomposition should only slice it.

## Risks

| Risk | Mitigation |
|---|---|
| False positives on intentionally deferred features | Check MVP tags: if a method belongs to a non-MVP module, the gap is expected. Only flag items in MVP scope. |
| Global context may exceed context window | Run the check as a structured review of Sections 11 and 12, not a free-text pass over the entire spec. |
| Adds another step to an already long process | The check is deterministic; it adds seconds, not minutes. |
| Overlap with Step 3 item 7 (prerequisites gate) | The prerequisites gate checks architectural dependencies; this checks wiring and call-graph coverage. Different surface area. |
| Decomposition tools (sf2) could own this instead | True, but decomposition happens after spec synthesis. Catching the gap at spec time avoids emitting work items that bake in the omission. |

## Blocking

Not blocking current work. Complementary to debate 004 — they are checks at different layers. Can be piloted on the cert-watch fixture and 3 existing Socratic specs.

## Next step

1. Implement the 5 composition checks as a standalone module (no process changes yet)
2. Run against the cert-watch spec and 3 existing Socratic specs
3. Measure: how many genuine omissions vs. false positives?
4. If signal is clean (>70% genuine), integrate into Step 5.5 of the process
5. If noisy, refine heuristics or merge into debate 004 as a "system-structure" sub-category
