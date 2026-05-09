---
number: "002"
title: "Completion rate instrumentation — where do humans drop off?"
author: opencode
date: "2026-05-09"
related: ["process.md", "critique.md"]
---

## Context

The socratic-specification process is substantial: `process.md` is 631 lines, the spec artifact has 16 sections, a full Level 2 spec could be 3,000+ words. The process includes up to 6 rounds of questioning, a consistency audit, synthesis, and confirmation.

There is no data on where humans drop off. The process assumes completion but does not measure it.

## Problem

Without completion data, the process cannot be optimized for the actual constraint: human attention. We do not know:
- What percentage of sessions reach synthesis (Step 7) vs. abandoning in Step 3 (iteration loop)
- Which rounds produce the most corrections (signal of confusion)
- Whether the diminishing-returns declaration is accepted or argued
- Whether Level 2 specs are actually produced when Level 2 is desired
- Whether the spec is used after production (does the human return to it?)

The session reflection notes: *"The perfectionism trap would have produced something brittle."* But we don't know if the current non-perfectionist version is still too long.

## Position

**Add lightweight, privacy-preserving instrumentation to the process — not as a requirement, but as an optional telemetry mode that process implementers can enable.**

### What to measure

Anonymous, aggregated session metrics:
- `session_reached_step` — highest step completed (0–7)
- `rounds_completed` — how many iteration rounds before termination
- `corrections_per_round` — count of human corrections per round
- `level_achieved` vs `level_desired` — gap frequency
- `time_to_synthesis` — wall-clock from start to Step 7
- `spec_words` — final artifact length

No content is captured. No human input is logged. Only counts and durations.

### Why this matters

The process claims to be "without requiring specification expertise." But if 60% of humans abandon after Round 2, that claim is false and the process needs redesign — shorter rounds, fewer questions per round, or earlier synthesis with lower target levels.

Factory's missions (Luke talk) emphasize that human attention is the bottleneck. The spec process is the first gate in that bottleneck. If the spec process loses humans, nothing downstream matters.

## Risks

| Risk | Mitigation |
|---|---|
| Telemetry feels invasive | Make it opt-in; disclose exactly what is measured; no content, no identifiers |
| Data is misleading (small sample) | Run for N sessions before drawing conclusions; report confidence intervals |
| Optimization for completion degrades spec quality | Measure both completion rate *and* downstream success rate (e.g., does the spec produce passing implementations?) |

## Blocking

Not blocking any current work. This is research infrastructure. However, it should be in place before the next major process revision (v6+), so that v6 can be evaluated against v5 completion data.

## Next step

1. Add a `TELEMETRY.md` document describing the optional instrumentation
2. Define the 6 metrics above with exact measurement rules
3. Implement a lightweight `SessionMetrics` dataclass that process runners can optionally instantiate
4. Run 10 sessions with telemetry enabled
5. Report completion rates and identify the largest drop-off point
