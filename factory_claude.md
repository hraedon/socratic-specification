# factory_claude.md

*Briefing for a new Claude instance starting the software factory project.*

---

## What you're building

A software factory: a pipeline that takes a vague human description of desired software ("vibe spec") and produces working, tested code. The pipeline has a defined intake format (the socratic spec process), a defined intermediate format (the YAML schema), and a defined output (deployable software with passing tests).

This is not a research project. The goal is working software from a vague prompt.

---

## What already exists

The foundation is complete and lives at **https://github.com/hraedon/socratic-specification**.

Read `process.md` and `spec.template.yaml` before writing a line of code. The pipeline stages, the artifact format, and the interface contract between spec and implementation are all defined there. You are building the implementation layer, not redesigning the spec layer.

Key things the spec process gives you:

- `functional_requirements[]` with `mvp: true/false` flags — what to build and in what priority order
- `work_decomposition.value_phases` — human-declared delivery phases
- `work_decomposition.dependencies` — intent-level prerequisite relationships between FRs
- `mvp.architectural_prerequisites` — non-MVP FRs that must exist before MVP features can function
- `high_coupling_decisions[]` — load-bearing architectural choices, each with a status
- `handoff.intent_signals` — informal goals from the original vibe spec; must be weighed when resolving high-coupling decisions
- `acceptance_criteria[]` — testable conditions mapped to FRs
- `glossary[]` — canonical term definitions for the domain

The YAML is the machine-readable contract. Parse `spec.yaml`, not `spec.md`.

---

## The pipeline

```
Stage 1: Spec intake
  Human provides vibe spec
  /spec skill runs the socratic elicitation process
  Outputs: spec.md + spec.yaml
  Human confirms before proceeding

Stage 2: Validation gate
  Read spec.yaml
  Confirm spec_level >= 1
  Confirm mvp.fr_ids is non-empty
  Confirm all high_coupling_decisions have a status
  Flag any blocking open questions
  Do not proceed if spec is not at Level 1

Stage 3: Work decomposition
  Map MVP FRs to Phase 1
  Resolve architectural prerequisites (build order, not user-value order)
  Produce ordered task list with dependencies
  Each task: one FR or prerequisite, acceptance criteria attached

Stage 4: Agentic implementation
  Spawn worktree agent per task (use isolation: "worktree")
  Inject into each agent: the full spec.yaml, the specific FR, its acceptance criteria,
    the glossary, and the intent signals relevant to its high-coupling decisions
  Agent implements, writes tests, runs tests
  Agent does not proceed past its task boundary without passing tests

Stage 5: Test execution
  Run tests in real environment (not mocked)
  Collect results per task

Stage 6: Failure loop
  Failed tests return to the implementing agent with:
    - The original FR and acceptance criteria
    - The test failure output
    - The spec.yaml context (not just the error)
  Agent diagnoses and retries
  Escalate to human after N failed attempts on the same task

Stage 7: Phase completion
  All Phase 1 tasks passing → human checkpoint before Phase 2
  Update handoff state with what was built, what decisions were made
  Proceed or stop based on human input
```

---

## Key decisions already made

**Technology choices belong to the implementing agent.** The spec does not prescribe a stack. When options are equivalent, prefer tools with broad adoption and active ecosystems over niche alternatives, and inherently safer tools over those requiring greater care. These are defaults, not rules.

**MVP definition is human-declared, build order is agent-determined.** The spec tells you what the human wants to see first. You determine what has to be built first. These often differ. Architectural prerequisites (auth, data model, sync engine) may need to exist before any user-visible MVP feature can function. Surface this before writing code, not after.

**Value phases ≠ implementation phases.** Phase 1 to the human means "first thing they can use." Phase 1 to you might mean "invisible infrastructure that nothing else can run without." Make this distinction explicit in your planning; do not silently reorder the human's declared phases.

**Tests run in real environments.** The feedback loop only closes if tests run against something real. Mocked tests that pass and prod environments that fail is a documented failure mode (it happened before this project existed). Do not mock what can be run.

**The spec is a starting point for dependency mapping, not a finalized build plan.** `work_decomposition.dependencies` reflects logical inference from the spec process, not validated implementation constraints. You own the actual dependency graph. Surface conflicts before building, not while building.

---

## Practical starting points

**The `/spec` skill** — loads the socratic specification process and runs the elicitation conversation. Writes `spec.md` and `spec.yaml` when complete. This is Stage 1 of the factory. The process is fully documented in the spec repo; the skill is a thin wrapper that invokes it and manages file output.

**The `/factory` skill** — reads `spec.yaml`, runs Stages 2-7. The human invokes this after `/spec` completes. Takes an optional `--phase` flag to run a specific phase only.

**State persistence** — write session state to `.factory/state.yaml` between stages. This file tracks: current stage, completed tasks, test results, decisions made during implementation, and any deferred items. A new session picks up from this file, not from memory.

**Worktree agents** — use `isolation: "worktree"` when spawning implementing agents. Each agent gets its own branch. Merge back to main only when tests pass.

---

## Known hard parts

**Consistency across a growing codebase.** Individual agents handle their assigned FR well. Maintaining architectural consistency across many agents across many sessions is harder. Mitigations: inject the full spec.yaml into every agent (not just its assigned FR), enforce the glossary definitions, require agents to read existing code before writing new code.

**Graceful error recovery.** Agents get stuck. The failure loop (Stage 6) handles test failures but not all failures are test failures — sometimes an agent reaches a decision point it can't resolve from the spec alone. Design explicit escalation paths: the agent states what it can't determine, what information would unblock it, and what it has tried. Do not let agents silently make consequential decisions outside the spec.

**Context window limits on long sessions.** Worktree isolation helps because each agent has a fresh context. The `.factory/state.yaml` file is how state survives across sessions. Keep it current.

**The MVP-architecture conflict.** This is the most common planning failure: the human declares an MVP that is architecturally impossible to build without first building Phase 2 infrastructure. The spec process flags architectural prerequisites, but you should validate these before committing to a build plan. If the declared MVP requires invisible infrastructure, say so explicitly before starting Stage 4.

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
