# Project Insight Mining Plan

## Purpose

Mine completed and ongoing projects that began from a Socratic specification to
learn which questions, translations, decomposition controls, and verification
obligations reliably predict successful delivery—and which omissions repeatedly
surface later as rework.

This is retrospective evidence collection, not a search for anecdotes that justify
the current process. The output is a ranked set of lesson candidates with explicit
support, counterevidence, human-attention cost, and a proposed home: base process,
extension, work decomposition, executable tooling, or nowhere.

## Core questions

1. Which implementation defects were already visible in the original spec?
2. Which defects required repository inspection and therefore belong in work
   decomposition or brownfield mode rather than human elicitation?
3. Which questions produced decisions that materially prevented rework?
4. Which questions or artifact sections were ignored, misunderstood, or answered
   without affecting implementation?
5. Which implementation-time human questions should have been resolved earlier?
6. Which requirements changed because intent changed, versus because the original
   translation was incomplete?
7. Which patterns recur across genuinely independent projects and archetypes?

## Safety and evidence boundaries

- Do not copy regulated data, secrets, live identifiers, proprietary source, or
  sensitive logs into this repository.
- Store pointers, commit IDs, structural summaries, and synthetic reproductions.
- Review each source repository's instructions before reading project artifacts.
- Treat missing evidence as missing. Do not infer that a behavior worked because
  no defect was recorded.
- Do not grade individual humans or agents. The unit of analysis is the process
  boundary and failure class.
- Keep portfolio-level results separate from confidential project narratives.

## Corpus discovery

Begin with a census, not a hand-picked success/failure sample. Populate
`corpus-manifest.yaml` from `corpus-manifest.template.yaml`.

### Known first-pass candidates

Direct paired `spec.md`/`spec.yaml` artifacts currently exist in:

- `/projects/openbia/docs/`
- `/projects/regista/`
- `/projects/usage-dashboard/docs/`
- `/projects/software-factory/projects/` (multiple cert-watch runs,
  port-observer-receiver, rds-manager, and golden fixtures)
- `/projects/software-factory-2/tests/fixtures/` and its golden-run evidence

Additional likely lineage signals exist in the histories of `agent-notes`,
`cert-watch`, `oh-my-pi`, `sysadmin_competence_evaluation`, and the factory repos.
Most portfolio repositories may have begun from a Socratic conversation without
retaining a file named `spec.*`; their origin must be established from history,
handoffs, factory state, or human confirmation rather than guessed.

Do not treat `provider-bench/SPEC.md` files as Socratic projects solely because of
their filenames; classify provenance first.

### Discovery procedure

For every repository under `/projects`:

1. Locate `spec.md`, `spec.yaml`, change specs, `.factory/` state, handoffs,
   breadcrumbs, RFCs, postmortems, and run summaries.
2. Search git history for the introduction and revision of specification artifacts.
3. Identify the implementation baseline and the first useful-delivery commit.
4. Determine whether the project was greenfield, a change to an existing system,
   a factory fixture, or unrelated to this process.
5. Record evidence strength: direct artifact, history inference, human-confirmed,
   or unknown.
6. Include eligible failures, partial projects, and abandoned efforts—not only
   polished repositories.

## Sampling and independence

Run a census inventory first. For deep review, stratify by:

- Greenfield versus existing-system change.
- Small local tool, deployed service, analyzer, UI application, infrastructure
  component, and factory fixture.
- Successful, partial, abandoned, and substantially reworked outcomes.
- Single-agent and multi-agent implementation.

Repeated runs of the same cert-watch specification are valuable for measuring
implementation variance but count as **one specification lineage** when deciding
whether a lesson recurs across independent projects. A pattern needs at least two
independent lineages before promotion beyond a project-specific note.

## Review method per project

Use `project-review.template.yaml`. Pin every claim to immutable evidence.

### 1. Reconstruct the starting contract

- Original vibe spec or earliest retained intent statement.
- Confirmed canonical spec revision.
- Desired and achieved spec level.
- Active extensions and assumptions.
- Human-owned MVP/value phases.
- Known architectural prerequisites and risks.

Do not evaluate the original spec using facts learned only later without marking
that hindsight explicitly.

### 2. Reconstruct the delivery timeline

Identify:

- First implementation commit and first useful-delivery commit.
- Work decomposition or factory task graph.
- Human clarification points.
- Spec, AC, and plan revisions.
- Test failures, review findings, and architecture resets.
- Final state: accepted, partial, abandoned, superseded, or still active.

### 3. Classify every material finding

Use exactly one primary class and optional contributing classes:

| Class | Earliest responsible boundary |
|---|---|
| `elicitation_gap` | Intent-relevant question was never asked or resolved |
| `translation_gap` | Human intent was translated into an incomplete/wrong technical requirement |
| `spec_inconsistency` | Requirements or artifact references contradicted one another |
| `decomposition_gap` | Codebase consumer, invariant, dependency, or verification layer was missed |
| `implementation_error` | The contract and plan were sufficient; implementation violated them |
| `environment_gap` | Dev/CI/target differences were not represented or exercised |
| `compatibility_gap` | Existing/persisted/external behavior lacked migration or preservation coverage |

Also record the earliest stage that could reasonably have caught it. Do not push
repository-discoverable facts onto a non-technical human merely because earlier
would have been convenient.

### 4. Identify effective controls

Record not only failures, but controls that demonstrably helped:

- A question that changed scope or prevented an invalid assumption.
- An AC that caught a defect before handoff.
- A fixture or target-runtime test that exposed a hidden class.
- A glossary or intent signal that resolved implementation ambiguity.
- A decomposition invariant or consumer map that prevented local-only fixes.

Evidence must show a causal or strongly plausible connection. "The section was
present" is not evidence that it helped.

### 5. Seek counterevidence

For each proposed lesson, ask:

- Did another project succeed without this control?
- Would the control have been knowable at that stage?
- Would it create false positives or extra human questions in unrelated projects?
- Is the failure already caught more reliably by downstream tooling?
- Is this a recurring class or a single implementation mistake?

## Synthesis and promotion

Create one `lesson-candidate.yaml` per proposed lesson.

A lesson may be promoted only when:

1. It has evidence from at least two independent project lineages, or one lineage
   plus a deliberately constructed evaluation case and strong causal evidence.
2. Counterexamples and alternative explanations have been recorded.
3. The earliest correct process boundary is identified.
4. Human-attention cost is estimated.
5. A falsifiable pilot bar is defined.

Routing rules:

| Evidence points to… | Put the control in… |
|---|---|
| Domain intent a human can answer | Base elicitation or a domain-language extension probe |
| Recurring project-type risk | Guardrail or archetype extension |
| Existing codebase facts | Brownfield inspection or work decomposition |
| Referential/coverage correctness | Executable validator or factory gate |
| One-off implementation mistake | Regression test in that project, not this process |

## Deliverables

1. `corpus-manifest.yaml` — census and eligibility/provenance record.
2. One immutable-evidence `project-review.yaml` per deeply reviewed lineage.
3. A defect/control matrix across projects.
4. Ranked `lesson-candidate.yaml` records with counterevidence.
5. Synthetic evaluation cases for promoted failure classes.
6. Proposed process patches only after the evidence review is complete.
7. A short human report: what repeatedly helped, what repeatedly failed, and what
   should remain project-specific.

## Suggested execution plan

### Wave 1 — inventory and calibration

- Census all repositories.
- Deep-review one direct-spec project and one repeated factory lineage.
- Have two reviewers classify the same findings independently.
- Reconcile taxonomy disagreements before scaling.

### Wave 2 — stratified review

- Review 6–10 independent lineages across the strata above.
- Batch evidence extraction separately from lesson synthesis to reduce confirmation
  bias: extractors record facts; synthesizers compare across projects.

### Wave 3 — adversarial synthesis

- Challenge each lesson with the strongest counterexample.
- Route lessons to the earliest correct boundary.
- Add synthetic evaluation cases before changing the process.

### Wave 4 — controlled promotion

- Pilot proposed changes against the corpus and evaluation suite.
- Compare critical-obligation recall, false positives, human questions, plan
  revisions, and downstream defect classes.
- Promote, refine, or reject with a dated resolution.

## Completion criteria

The mining effort is complete when every eligible repository has a disposition,
deep-reviewed findings are evidence-pinned, classification agreement is measured,
every promoted lesson has counterevidence and a regression case, and no process
change relies only on a compelling story from one project.
