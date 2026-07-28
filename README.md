# Socratic Specification

A process for converting an informal software description ("vibe spec") into a production-grade specification suitable for agentic implementation — without requiring any specification expertise from the human.

## The Thesis

A well-designed elicitation process can produce a production-grade spec from a vague human prompt. The process does the work; the human provides domain knowledge, intent, and decisions.

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
2. An AI partner reads it, detects the project type, and confirms its understanding
3. The AI iterates with the human using targeted domain-language questions, translating answers into technical requirements
4. The AI synthesizes a structured spec artifact ready for an implementing agent
5. The canonical YAML is validated and rendered into a full human view plus a concise decision brief
6. For factory-bound work, the implementing agent inspects the target codebase and produces a verified work plan before writing code

## Spec Levels

| Level | Name | What it means |
|---|---|---|
| 1 | Implementable | Agent can build something matching intent |
| 2 | Verifiable | Agent can build and write tests against the spec |
| 3 | Complete | Agent can implement without asking any clarifying question |

The human declares a desired level. The AI assesses what's actually achievable and pushes back if the gap can't be closed.

## Key Principles

- **Domain language first** — questions are asked in the human's language; the AI translates answers into technical requirements
- **Translation confirmation** — derived technical values are shown to the human in plain language before being recorded
- **Desired vs. target level** — the AI is empowered to say a desired level is unachievable and explain why
- **Testing at the baseline** — every spec identifies testable behaviors and acceptance criteria from Level 1
- **High-coupling decisions** — load-bearing architectural choices are classified explicitly rather than left implicit
- **MVP definition** — human-declared value priority, separate from implementation sequencing
- **One canonical contract** — YAML is authoritative; human-readable artifacts are generated and fingerprinted
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
python scripts/spec_tools.py validate .factory/work-plan.yaml --ready
python scripts/spec_tools.py validate .factory/work-plan.yaml --handoff
python scripts/spec_tools.py validate change-spec.yaml --kind change-spec --ready
python scripts/spec_tools.py render-change change-spec.yaml --output change-spec.md
python scripts/spec_tools.py check-sync change-spec.yaml change-spec.md --kind change-spec
```

Install development dependencies with `python -m pip install -r requirements-dev.txt`; run contract tests with `python -m pytest -q`.

Legacy specifications used the implicit sidecar format. Preserve their history and follow [the v1-to-v2 migration guide](docs/schema-migration-v1-to-v2.md) when a project needs a canonical revision.

## Status

Active development. Critiques and iterations tracked in [critique.md](critique.md). Open architectural debate tracked in [debate/](debate/).
