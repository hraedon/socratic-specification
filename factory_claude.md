# factory_claude.md

*Briefing for a new Claude instance starting the software factory project.*

---

## What you're building

A software factory: a pipeline that takes a vague human description of desired software ("vibe spec") and produces working, tested code. The pipeline has a defined intake format (the socratic spec process), a defined intermediate format (the YAML schema), and a defined output (deployable software with passing tests).

This is not a research project. The goal is working software from a vague prompt.

---

## What already exists

The foundation is complete and lives at **https://github.com/hraedon/socratic-specification**.

Read `process.md`, `spec.template.yaml`, and `work-plan.template.yaml` before writing a line of code. The pipeline stages, artifact formats, and interface contracts between spec, planning, and implementation are defined there. You are building the implementation layer, not redesigning the spec layer.

Key things the spec process gives you:

- `functional_requirements[]` with `mvp: true/false` flags — what to build and in what priority order
- `work_decomposition.value_phases` — human-declared delivery phases
- `work_decomposition.dependency_hints` — intent-level prerequisite relationships between FRs
- `mvp.architectural_prerequisites` — non-MVP FRs that must exist before MVP features can function
- `high_coupling_decisions[]` — load-bearing architectural choices, each with a status
- `handoff.intent_signals` — informal goals from the original vibe spec; must be weighed when resolving high-coupling decisions
- `acceptance_criteria[]` — testable conditions mapped to FRs
- `glossary[]` — canonical term definitions for the domain
- `risks[]` — hard-to-reverse delivery risks and whether human decisions remain
- `provenance` — categorical source routing for important requirements and decisions

The YAML is the canonical contract. Parse `spec.yaml`, not generated `spec.md`. Reject unsupported `meta.schema_version` values and fail if a checked-in Markdown view does not match its canonical fingerprint.

Stage 3 produces a second machine-readable contract: `.factory/work-plan.yaml`, following `work-plan.template.yaml`. The spec says what must be true; the work plan records how the inspected codebase will make and prove it true. Never use the work plan to silently weaken or rewrite the spec.

---

## The pipeline

```
Stage 1: Spec intake
  Human provides vibe spec
  /spec skill runs the socratic elicitation process
  Output: canonical spec.yaml
  Validate, then generate spec.md + decision-brief.md
  Human confirms the decision brief; corrections update YAML and regenerate views

Stage 2: Validation gate
  Run: scripts/spec_tools.py validate spec.yaml --ready
  Read canonical spec.yaml
  Confirm supported schema_version and revision lineage
  Confirm spec_level >= 1
  Confirm mvp.fr_ids is non-empty
  Confirm all high_coupling_decisions have a status
  Flag any blocking open questions
  Do not proceed if spec is not at Level 1
  For existing-system work, also validate change-spec.yaml --ready and pin its baseline

Stage 3: Work decomposition
  Record the repository base/head and existing quality gates
  Map target intent (MVP FRs or change ACs) and resolve architectural prerequisites
  State invariants for every contract the phase will change
  Trace each changed contract through all actual consumers
  Define compatibility matrices and historical fixtures where formats persist
  Produce bounded work packages with dependencies and verification obligations
  Run an independent architecture and coverage review
  Output: .factory/work-plan.yaml
  Gate: do not implement while any required coverage is unresolved

Stage 4: Agentic implementation
  Spawn worktree agent per work package (use isolation: "worktree")
  Inject into each agent: the full spec.yaml; the full work-plan header; its package;
    referenced invariants, contracts, consumers, acceptance criteria, and verification;
    the glossary; and relevant intent signals
  Agent implements, writes tests, runs tests
  Agent does not proceed past its package boundary without passing its declared tests

Stage 5: Test execution
  Run each work package's declared tests at the real behavior boundary
  Exercise historical fixtures, round trips, and browser runtime when applicable
  Run the adversarial matrix and existing repository quality gates
  Collect evidence per work package, acceptance criterion, and invariant

Stage 6: Failure loop
  Failed tests return to the implementing agent with:
    - The original FR and acceptance criteria
    - The test failure output
    - The spec.yaml context (not just the error)
  Agent diagnoses and retries
  Escalate to human after N failed attempts on the same work package
  First defect in a class → inspect every mapped consumer and add a boundary regression
  Second occurrence of the class → pause; revisit invariant, consumer map, and task boundaries

Stage 7: Phase completion
  Independent reviewer runs the pre-handoff adversarial review
  All work packages, invariants, ACs, and repository gates passing → human checkpoint
  Record base/head, changed contracts, affected formats, fixtures, consumers,
    regression tests, commands run, and known limitations
  Update handoff state with what was built and what decisions were made
  Proceed or stop based on human input
```

---

## Key decisions already made

**Technology choices belong to the implementing agent.** The spec does not prescribe a stack. When options are equivalent, prefer tools with broad adoption and active ecosystems over niche alternatives, and inherently safer tools over those requiring greater care. These are defaults, not rules.

**MVP definition is human-declared, build order is agent-determined.** The spec tells you what the human wants to see first. You determine what has to be built first. These often differ. Architectural prerequisites (auth, data model, sync engine) may need to exist before any user-visible MVP feature can function. Surface this before writing code, not after.

**Value phases ≠ implementation phases.** Phase 1 to the human means "first thing they can use." Phase 1 to you might mean "invisible infrastructure that nothing else can run without." Make this distinction explicit in your planning; do not silently reorder the human's declared phases.

**Tests run in real environments.** The feedback loop only closes if tests run against something real. Mocked tests that pass and prod environments that fail is a documented failure mode (it happened before this project existed). Do not mock what can be run.

**The spec is a starting point for dependency mapping, not a finalized build plan.** `work_decomposition.dependency_hints` reflects logical inference from the spec process, not validated implementation constraints. You own the actual dependency graph. Surface conflicts before building, not while building.

**Invariants come before tasks.** For every shared contract the phase changes, state what remains true and who owns the authoritative representation. Make identity, meaningful ordering, unchanged round trips, and backward compatibility explicit when they apply. If the invariant cannot be stated clearly, the change is not ready to decompose.

**Trace contracts through consumers.** A model or schema change is not local just because it begins in one file. Inspect the actual path through parser, domain model, persistence, API, browser, validation, comparison or hashing, export, and documentation. The repository may use different names or omit layers; record evidence for what exists and a reason for what does not apply.

**Prefer coherent vertical work packages.** A package owns one bounded behavior or prerequisite and its verification across affected layers. If a shared contract requires multiple packages, designate one owner and make every downstream consumer an explicit dependent obligation. A local unit test does not close an integration obligation.

**Compatibility is executable.** When stored or exchanged formats change, enumerate supported versions and read/write behavior. Keep one real fixture for every supported historical form and verify load → validate → unchanged edit → serialize → reparse, plus diff/hash/export behavior where present. Normalize reads when useful, but do not mutate historical records merely by reading them.

**Review adversarially before handoff.** A reviewer other than the implementing agent checks zero/one/many values, first/middle/last positions, missing or conflicting metadata, duplicate or missing identity, old/current representations, and unchanged browser round trips where applicable. The reviewer checks the defect class and its consumer surface, not only the reported reproduction.

---

## Practical starting points

**The `/spec` skill** — loads the socratic specification process and runs the elicitation conversation. Writes canonical `spec.yaml`, validates it, and generates `spec.md` plus `decision-brief.md`. This is Stage 1 of the factory. The process is fully documented in the spec repo; the skill is a thin wrapper that invokes it and manages file output.

**The `/factory` skill** — reads `spec.yaml`, runs Stages 2-7. The human invokes this after `/spec` completes. Takes an optional `--phase` flag to run a specific phase only.

**State persistence** — write the Stage 3 plan to `.factory/work-plan.yaml` and session progress to `.factory/state.yaml`. The state file tracks: current stage, completed work packages, test results, decisions made during implementation, defect classes observed, and deferred items. A new session picks up from these files, not from memory.

**Worktree agents** — use `isolation: "worktree"` when spawning implementing agents. Each agent gets its own branch. Merge back to main only when tests pass.

---

## Known hard parts

**Consistency across a growing codebase.** Individual agents handle their assigned FR well. Maintaining architectural consistency across many agents across many sessions is harder. Mitigations: inject the full spec.yaml into every agent (not just its assigned FR), enforce the glossary definitions, require agents to read existing code before writing new code.

**Graceful error recovery.** Agents get stuck. The failure loop (Stage 6) handles test failures but not all failures are test failures — sometimes an agent reaches a decision point it can't resolve from the spec alone. Design explicit escalation paths: the agent states what it can't determine, what information would unblock it, and what it has tried. Do not let agents silently make consequential decisions outside the spec.

**Context window limits on long sessions.** Worktree isolation helps because each agent has a fresh context. The `.factory/state.yaml` file is how state survives across sessions. Keep it current.

**The MVP-architecture conflict.** This is the most common planning failure: the human declares an MVP that is architecturally impossible to build without first building Phase 2 infrastructure. The spec process flags architectural prerequisites, but you should validate these before committing to a build plan. If the declared MVP requires invisible infrastructure, say so explicitly before starting Stage 4.

**Repeated patches are an architecture signal.** One failure may be local. A second failure in the same class means the current invariant, consumer map, or task boundary is incomplete. Pause implementation, update the work plan, and have its coverage reviewed again before continuing.

---

## What success looks like

A human writes: *"I want an app that lets me track which of my houseplants need watering and reminds me when to water them."*

The factory:
1. Runs the socratic spec process, produces `spec.md` and `spec.yaml`
2. Identifies MVP: plant list + watering schedule + reminder notification
3. Identifies architectural prerequisite: local notification permission model
4. Builds in declared phase order, tests in real environment
5. Delivers working software the human can use

At the scale this factory targets — scripting, self-contained LOB apps, simple mobile apps — this is achievable. Non-trivial apps with complex state, novel architecture, or extensive third-party integration will need human checkpoints at phase boundaries. The spec process already structures those boundaries; use them.

---

## Contact with the spec process

If the spec process needs to change to better serve the factory — a missing field in the YAML schema, an elicitation gap that shows up repeatedly in implementation, a section that doesn't map cleanly to a build task — raise it as an issue or PR against https://github.com/hraedon/socratic-specification. The spec repo is a dependency, not a fork. Keep the interface clean.
