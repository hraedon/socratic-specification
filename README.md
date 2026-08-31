# Socratic Specification

A process for converting an informal software description ("vibe spec") into a production-grade specification suitable for agentic implementation — without requiring any specification expertise from the human.

## The Thesis

A well-designed elicitation process can produce a production-grade spec from a vague human prompt. The process does the work; the human provides domain knowledge, intent, and decisions.

**What the spec is:** a birth certificate, not a living contract. The spec's value is front-loaded — it aligns intent at project inception, gives the implementing agent a complete picture, and then steps aside. Consumer evidence (usage-dashboard, regista, openbia) shows that artifact fidelity is inversely correlated with project maturity: the newest consumer is the most spec-faithful. The canonical machinery exists to make birth rigorous, not to impose lifelong maintenance. Post-delivery drift is expected and addressed through lightweight re-specification (change-spec) when a system needs a new phase of intentional change — not through continuous synchronization.

**What the spec is not:** a substitute for architecture. Elicitation is democratized; architecture is relocated upstream (into the work-plan gate, invariants, and component manifests), not eliminated. The honest claim is Claim 2: the process makes architectural competence explicit and auditable, rather than claiming to remove the need for it.

## What's Here

- **[process.md](process.md)** — The full specification process: roles, spec levels, elicitation steps, the spec artifact template, and process extensions (starting with Mobile)
- **[spec.template.yaml](spec.template.yaml)** — Canonical schema-v2 specification template. Generated Markdown is a view of this artifact.
- **[work-plan.template.yaml](work-plan.template.yaml)** — Machine-readable contract for the factory's work-decomposition phase. Produced from the confirmed spec or change-spec plus inspection of the target codebase before implementation begins.
- **[change-spec.template.yaml](change-spec.template.yaml)** — Canonical delta contract for changes to existing systems.
- **[scripts/spec_tools.py](scripts/spec_tools.py)** — Structural and semantic validation, deterministic rendering, synchronization checks, and readiness/handoff gates.
- **[evals/](evals/)** — Regression cases for evaluating the process without prescribing exact wording.
- **[research/project-insight-mining-plan.md](research/project-insight-mining-plan.md)** — Evidence protocol for extracting lessons from projects produced from Socratic specs.
- **[scripts/inventory_projects.py](scripts/inventory_projects.py)** — Read-only metadata census that seeds the mining manifest without copying project content.

## How It Works

1. A human writes a description of what they want to build — at whatever quality level they can manage
2. An AI partner reads the prompt and available evidence, detects the project type, and confirms one combined understanding
3. The AI resolves discoverable facts first, then asks the smallest useful set of domain-language questions and translates consequential answers into technical requirements
4. The AI synthesizes a structured spec artifact ready for an implementing agent
5. The canonical YAML is validated and rendered into a full human view plus a concise decision brief
6. For factory-bound work, the implementing agent inspects the target codebase and produces a verified work plan before writing code

## Spec Levels

| Level | Name | What it means |
|---|---|---|
| 1 | Implementable | Agent can build something matching intent |
| 2 | Verifiable | Agent can build and write tests against the spec |
| 3 | Complete | Agent can implement without asking any clarifying question |

The human may request a level, but does not need to learn the level system. The AI recommends a target from the intended use and risk, then pushes back if a requested level is not achievable.

## Key Principles

- **Domain language first** — questions are asked in the human's language; the AI translates answers into technical requirements
- **Translation confirmation** — derived technical values are shown to the human in plain language before being recorded
- **Desired vs. target level** — the AI is empowered to say a desired level is unachievable and explain why
- **Testing at the baseline** — every spec identifies testable behaviors and acceptance criteria from Level 1
- **High-coupling decisions** — load-bearing architectural choices are classified explicitly rather than left implicit
- **MVP definition** — human-declared value priority, separate from implementation sequencing
- **One canonical artifact at synthesis** — YAML is authoritative at birth; human-readable artifacts are generated and fingerprinted. Post-delivery, the spec is a record of intent, not a continuously enforced contract.
- **Categorical provenance** — important claims say whether they were stated, confirmed, observed, inferred, assumed, or externally verified
- **Evidence before promotion** — process additions graduate through evaluation cases and independent project evidence

## Process Extensions

The base process handles all project types. Extensions activate for specific project types detected from the vibe spec:

- **Mobile (iOS / Android)** — platform declaration, offline behavior, permissions, screen flow diagram
- **Change to an existing system (pilot)** — baseline, preserved behavior, blast radius, compatibility, migration, rollback, and existing gates

The machine-readable registry and governance rules are in [extensions/index.yaml](extensions/index.yaml).

## Output Artifacts

Each completed spec produces one canonical file and two generated human views:

| File | Purpose |
|---|---|
| `spec.yaml` | Canonical, versioned specification. Source of truth. |
| `spec.md` | Generated full human-readable specification. |
| `decision-brief.md` | Generated concise confirmation surface for the human. |

Generated files carry the canonical fingerprint. If they differ, validation fails and they must be regenerated; neither silently wins.

## Spec Lifecycle

Specs are front-loaded. Their primary value is at synthesis: aligning intent, giving the implementing agent a complete picture, and making architectural decisions explicit and auditable. After delivery, the spec is a record of what was intended and why — not a continuously synchronized contract.

When a system needs a new phase of intentional change, the [change-to-existing-system extension](extensions/change-existing-system.md) produces a `change-spec.yaml` that pins the current baseline and specifies the delta. This is re-specification, not maintenance. Systems that have moved beyond their spec need not regenerate views or pass sync checks — the spec's job was already done.

Factory-bound implementation then produces an additional downstream artifact:

| File | Purpose |
|---|---|
| `.factory/work-plan.yaml` | Codebase-grounded implementation sequence, invariants, affected consumers, compatibility work, and verification gates. |

This file is not part of elicitation and does not amend the human's spec. It records how an implementing agent will satisfy that spec in the codebase it actually inspected.

## Tooling

```bash
python scripts/spec_tools.py validate spec.yaml --ready
python scripts/spec_tools.py render spec.yaml --output spec.md
python scripts/spec_tools.py brief spec.yaml --output decision-brief.md
python scripts/spec_tools.py check-sync spec.yaml spec.md
python scripts/spec_tools.py check-sync spec.yaml decision-brief.md --kind brief
python scripts/spec_tools.py validate .factory/work-plan.yaml --ready
python scripts/spec_tools.py validate .factory/work-plan.yaml --handoff
python scripts/spec_tools.py validate change-spec.yaml --kind change-spec --ready
python scripts/spec_tools.py render-change change-spec.yaml --output change-spec.md
python scripts/spec_tools.py check-sync change-spec.yaml change-spec.md --kind change-spec
```

Install development dependencies with `python -m pip install -r requirements-dev.txt`; run contract tests with `python -m pytest -q`.

Legacy specifications used the implicit sidecar format. Preserve their history and follow [the v1-to-v2 migration guide](docs/schema-migration-v1-to-v2.md) when a project needs a canonical revision.

Ready work plans verify every declared compatibility fixture by its byte-level
`sha256:` fingerprint, require `immutable_on_read: true`, and require it to remain
below the plan or target-project tree. A missing, moved, or rewritten fixture is a
validation error, not a path comparison. Resolve value/build conflicts
(`status: resolved`) and retain one unique entry for each canonical adversarial
case: `zero_one_many`, `first_middle_last`, `missing_conflicting_metadata`,
`duplicate_missing_identity`, and `old_current_representations`. A required case
needs verification; a not-applicable case needs a nonblank reason.

Readiness reviewers must use a nonblank identity label and an RFC 3339 timestamp;
handoff reviewers use the same rules. Every brownfield changed contract must name
at least one structured, nonblank consumer.

Work-plan v1 does not record an implementer's identity or model lineage. Its
reviewer strings therefore cannot support a reliable reviewer/implementer
distinctness check; the readiness gate intentionally does not fake one. Add
structured identity and lineage for both roles before enforcing that separation.

This is a readiness-gate hardening, not an artifact schema-version change. To
migrate an existing plan, copy each historical snapshot into its plan/project
tree, set `fixture_fingerprint` to the fixture bytes' SHA-256, resolve every
recorded value/build conflict, and attach verification to at least one required
adversarial case.

Evaluation cases and runs have an explicit compatibility split. The unversioned
`evals/case.schema.json` and `evals/run.schema.json` remain the frozen v1 contracts;
`case-v2.schema.json` and `run-v2.schema.json` are the current v2 contracts. The
checker selects the schema from the artifact version and rejects case/run version
mismatches. v2 rejects whitespace-only evidence; v1 remains accepted unchanged.

## Status

Active development. Critiques and iterations tracked in [critique.md](critique.md). Open architectural debate tracked in [debate/](debate/).
