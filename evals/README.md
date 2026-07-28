# Process Evaluation Corpus

This directory regression-tests the Socratic process itself. Cases define the
obligations a capable run should surface; they do not prescribe exact questions,
wording, architecture, or implementation.

## What a case measures

Each case contains:

- A synthetic vibe spec and any legitimate context available to the process.
- Expected obligations, each tied to a process stage and severity.
- Anti-obligations: questions or commitments that would be premature or harmful.
- A scoring rule that separates important coverage from human-attention cost.

An evaluator runs the current process, records the generated artifacts and
conversation metrics, then scores whether the obligations were surfaced before
their deadlines. Paraphrases count. Confidently inventing an answer does not.

## Scoring

- Critical obligation found before its deadline: **+3**
- Important obligation found: **+1**
- Critical obligation missed or found only during implementation: **-5**
- Anti-obligation committed without evidence: **-3**
- Unnecessary human question whose answer was discoverable from supplied context: **-1**

Report obligation recall, anti-obligation count, human questions, corrections,
and artifact validation results separately. Do not collapse them into a single
"spec quality" score; the tradeoffs are the useful result.

## Promotion rule

A process change must improve its target failure class without regressing a
critical obligation in another case. Heuristic proposals also report false
positives. Stable promotion requires evidence from both synthetic cases and at
least two independent historical projects where available.

## Adding cases

Use `case.schema.json`. Prefer the smallest input that isolates a failure class.
Never copy regulated, confidential, or identifying project data into this corpus;
represent the structural shape synthetically.
