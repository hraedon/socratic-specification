---
title: "Debate 004 pilot: spec smell checker results"
date: "2026-07-28"
debate: "004"
status: "pilot-complete"
---

## Setup

Implemented `scripts/spec_smells.py` with the 6 heuristic checks from debate 004.
Ran against all 3 in-tree spec-like fixtures:
- `tests/fixtures/valid-spec-v2.yaml` (Plant Reminder, Level 2)
- `tests/fixtures/valid-change-spec.yaml` (policy reorder change-spec)
- `tests/fixtures/valid-work-plan.yaml` (work plan)

## Results

| Fixture | Smells | Genuine | Borderline | False positive |
|---|---|---|---|---|
| valid-spec-v2 | 4 | 1 | 1 | 2 |
| valid-change-spec | 2 | 0 | 0 | 2 |
| valid-work-plan | 3 | 0 | 0 | 3 |
| **Total** | **9** | **1 (11%)** | **1 (11%)** | **7 (78%)** |

## Analysis

**Genuine signal:** The `single_number_nfr` check caught a real under-probing:
"Due list renders within 2 seconds" without specifying device, load, or data
volume. This is exactly the class of error debate 004 targets.

**False-positive sources:**
1. `unqualified_absolute` fires on "no" as a negative-existence quantifier
   ("No external parser exists", "no stable ID", "no longer causes"). This is
   the dominant noise source — 5 of 7 false positives. "No" in technical
   writing is almost always a factual claim, not an unqualified absolute.
2. `missing_state_machine` matches "application" (the software) as a stateful
   entity. The entity list needs to exclude software/system nouns.
3. `implicit_roles` fires on single-user tools where permission boundaries
   are irrelevant.

## Verdict

**Below the 70% genuine bar.** The mechanism works; the heuristics need tuning.

Recommended next steps (not blocking):
- Remove "no" from the absolute-word list, or require it to modify a plural
  noun ("no users" but not "no parser exists")
- Add negative-existence patterns to the scope-qualifier allowlist
- Exclude software/system nouns from the state-entity list
- Add a "single-user declared" suppression for the role check
- Re-pilot against real consumer specs (regista, cert-watch) once tuning is done

The pilot validates that the *approach* is viable (the genuine catch was
exactly the right class of error) but the *implementation* is not ready for
process integration.
