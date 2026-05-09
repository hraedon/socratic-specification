---
number: "004"
title: "Translation risk post-hoc validation — a lightweight 'spec smell' check"
author: opencode
date: "2026-05-09"
related: ["process.md §Step 3", "critique.md"]
---

## Context

The Gemini v4 critique identified **Translation Risk**: the AI silently maps domain answers to technical requirements that the human never validates. The process addresses this with the translation confirmation step (Step 3, Point 3), but confirmation fatigue is real. After multiple rounds of "You said X, I took that to mean Y, is that right?", humans may rubber-stamp.

The process also has a Pre-Synthesis Consistency Audit (Step 5) that checks for contradictions, conflicts, and glossary inconsistencies. But it does not check for a specific class of error: **plausible-sounding but vacuous translations**.

## Problem

A translation can pass confirmation but still be defective. Examples:
- Human: *"It should feel instant"* → AI: *"I've taken that to mean under half a second"* → Human confirms → But the actual requirement should be *"under 100ms for the UI feedback, 2s for the full operation"* — the human confirmed a single number because they didn't know to split the requirement
- Human: *"We need to track orders"* → AI: *"I've taken that to mean a relational table with id, customer_id, items, total"* → Human confirms → But the actual domain has complex order states (pending, picked, shipped, returned) with state-machine rules that the AI didn't probe
- Human: *"It should be secure"* → AI: *"I've taken that to mean HTTPS and password hashing"* → Human confirms → But the domain requires role-based access control and audit logging

These are not contradictions. They are **under-probed translations** — the AI asked one question when three were needed. The consistency audit does not catch them because they are internally consistent but externally incomplete.

## Position

**Add a lightweight "spec smell" check that runs after the consistency audit (Step 5+) and before synthesis (Step 7).** This is not a gate — it is a warning system that flags likely under-probed areas for the AI's own attention before producing the artifact.

### Spec smell checks

1. **Unqualified absolutes:** Does the spec contain words like "all," "every," "always," "never" without a bounded scope?
   - *"All users can access the dashboard"* → Flag: what defines a "user"? Is there an admin role?

2. **Single-number NFRs:** Does a performance or capacity requirement have exactly one number with no context?
   - *"Under half a second"* → Flag: which operation? Under what load? For how many users?

3. **Missing state machines:** Does the spec describe entities that change state without explicit state transitions?
   - *"Orders are tracked"* → Flag: what are the order states? What triggers transitions? What happens in error cases?

4. **Implicit roles:** Does the spec mention people or actors without defining their permissions or boundaries?
   - *"Admins can view reports"* → Flag: what distinguishes an admin? Can roles change? Is there a super-admin?

5. **Vacuous security:** Does the spec mention "secure," "safe," or "protected" without specific mechanisms?
   - Flag: ask what threat model the human is concerned about

6. **Unconfirmed assumptions >50% of a section:** If the Assumptions section for a topic is longer than the Requirements section, flag under-probing.

### How it works

The smell check produces a report:

> *"Spec smell check found 3 warnings. These are not errors, but they indicate areas where the human may not have been probed deeply enough:"*
> - *"FR-03 uses 'all users' without defining user roles or scope"*
> - *"NFR-01 states 'under 1 second' without specifying which operation or load condition"*
> - *"Section 6 mentions 'orders' but no state transitions are defined"*
>
> *"Consider asking one follow-up question for each before synthesis, or record these as explicit assumptions."*

The AI can then either ask a follow-up or record the smell as an assumption. The check does not block synthesis — it is advisory.

## Why this matters

The socratic process's goal is *"minimize surprise and make rework cheap and local."* Under-probed translations produce the most expensive surprises: they are discovered during implementation, when changing the data model or auth model requires rewriting multiple FRs. A lightweight smell check catches these **before** the spec is handed off, when correction is still cheap.

sf2's mechanical gates catch some of these (e.g., vacuous interface specs), but catching them at the spec stage is cheaper than catching them after test_author has written tests and implementer has written code.

## Risks

| Risk | Mitigation |
|---|---|
| Smell checks produce false positives | Tune thresholds empirically; allow the AI to dismiss a smell with rationale |
| Smell checks become a rigid checklist | Keep them heuristic, not deterministic; the AI exercises judgment |
| Adding a Step 5+ slows the process | The smell check is automated text analysis; it adds seconds, not minutes |

## Blocking

Not blocking any current work. Can be piloted on 5 existing spec fixtures to measure false-positive rate.

## Next step

1. Implement the 6 smell checks as a standalone module (no process changes yet)
2. Run against 5 existing specs (including the 15 sf2 fixtures)
3. Measure: how many smells were found? How many were genuine under-probing? How many were false positives?
4. If the signal is clean (>70% genuine), integrate into Step 5+ of the process
5. If noisy, refine heuristics or abandon
