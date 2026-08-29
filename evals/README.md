# Process Evaluation Corpus

This directory regression-tests the Socratic process itself. Cases define the
obligations a capable run should surface; they do not prescribe exact questions,
wording, architecture, or implementation.

## What a case measures

Each case contains:

- A synthetic vibe spec and any legitimate context available to the process.
- Expected obligations, each tied to a process stage and severity.
- Anti-obligations: questions or commitments that would be premature or harmful.
- A case-specific human-question budget with rationale.
- A scoring rule that separates important coverage from human-attention cost.

An evaluator runs the current process, records the generated artifacts and
conversation metrics, then scores whether the obligations were surfaced before
their deadlines. Paraphrases count. Confidently inventing an answer does not.

## Recording and scoring a run

Use `run.schema.json` to record one independent judgment for every expected and
anti-obligation. Each judgment cites transcript or artifact evidence. The scorer
does not decide whether a paraphrase counts; a reviewer makes that semantic
judgment and the machine checks completeness, deadlines, and arithmetic.

Stages are ordered as elicitation, pre-synthesis, work decomposition, pre-handoff,
and implementation. An obligation is on time when it is surfaced at or before its
case deadline.

- Critical obligation surfaced on time: **+3**
- Important obligation surfaced on time: **+1**
- Critical obligation late or missed: **-5**
- Important obligation late or missed: **0**
- Anti-obligation committed: **-3**
- Unnecessary human question whose answer was discoverable from supplied context: **-1**

Run:

```bash
python scripts/score_eval_run.py evals/cases/<case>.yaml path/to/run.yaml
```

The output reports obligation recall, anti-obligations, human attention,
corrections, and artifact validation separately. `weighted_signal` is useful for
comparing runs on the same case; it is not a general "spec quality" score and
must not replace the separate measures.

## Promotion rule

A process change must improve its target failure class without regressing a
critical obligation in another case. Heuristic proposals also report false
positives. Stable promotion requires evidence from both synthetic cases and at
least two independent historical projects where available.

## Adding cases

Use `case.schema.json`. Prefer the smallest input that isolates a failure class.
Never copy regulated, confidential, or identifying project data into this corpus;
represent the structural shape synthetically.
