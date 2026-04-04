# Socratic Specification

A process for converting an informal software description ("vibe spec") into a production-grade specification suitable for agentic implementation — without requiring any specification expertise from the human.

## The Thesis

A well-designed elicitation process can produce a production-grade spec from a vague human prompt. The process does the work; the human provides domain knowledge, intent, and decisions.

## What's Here

- **[process.md](process.md)** — The full specification process: roles, spec levels, elicitation steps, the spec artifact template, and process extensions (starting with Mobile)

## How It Works

1. A human writes a description of what they want to build — at whatever quality level they can manage
2. An AI partner reads it, detects the project type, and confirms its understanding
3. The AI iterates with the human using targeted domain-language questions, translating answers into technical requirements
4. The AI synthesizes a structured spec artifact ready for an implementing agent

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

## Process Extensions

The base process handles all project types. Extensions activate for specific project types detected from the vibe spec:

- **Mobile (iOS / Android)** — platform declaration, offline behavior, permissions, screen flow diagram

Additional extensions (web, data pipeline, etc.) follow the same pattern.

## Status

Active development. Critiques and iterations tracked in [critique.md](critique.md).
