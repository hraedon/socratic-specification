---
number: "001"
title: "Schema versioning for spec.template.yaml"
author: opencode
date: "2026-05-09"
related: ["spec.template.yaml", "process.md"]
---

## Context

The `spec.template.yaml` schema is currently implicit version 1. It has no `schema_version` field. Downstream consumers (software-factory-2, and potentially other agentic pipelines) parse this schema to extract functional requirements, acceptance criteria, MVP tags, and dependency hints.

As the process adds new sections (e.g., `implementation_notes` was added post-v1, Mobile extension adds `mobile.*` fields), the schema evolves. Consumers that expect certain fields may break silently when a newer or older spec is fed to them.

## Problem

Without explicit versioning:
- A consumer built against the current schema may fail when encountering a spec produced by a newer or older version of the process
- Adding new fields (e.g., a `security` extension with `compliance_frameworks`) becomes a breaking change for all consumers
- There is no way for a consumer to say "I require schema version >= 2" or "I only understand versions 1–3"

This is the same failure mode as API drift: producer and consumer evolve independently, and breakage is discovered at runtime.

## Position

**Add a required `schema_version: int` field to `spec.template.yaml` under `meta.schema_version`, starting at `1`.**

Rules:
- The process increments the version when a new **required** field is added or an existing field's semantics change
- Adding optional fields does not increment the version
- Removing a field increments the version (breaking change)
- The process writes the version it produced
- Consumers declare `min_schema_version` and `max_schema_version` they understand
- A consumer encountering an out-of-range version fails fast with a clear message: "Spec schema version 4 not supported; consumer supports 1–3"

## Why now

Currently there is one known consumer (software-factory-2). Adding versioning when there is one consumer is cheap. Adding it after three consumers exist requires updating all three.

## Minimal change

```yaml
meta:
  name: ""
  schema_version: 1              # [REQUIRED] Integer. Incremented on breaking changes.
  spec_level: 1
  desired_level: 1
  date: ""
  extensions: []
```

This is one line in the template and one line in any consumer's validation.

## Risks

| Risk | Mitigation |
|---|---|
| Consumers forget to check the version | The reference validator (`validate_yaml`) can include a version check helper |
| Version increments too frequently | Only breaking changes (required new fields, semantic changes, removals) increment |
| Version increments too rarely | Optional fields accumulate; consumers start depending on them; then making them required breaks things | Set a policy: a field must be optional for at least one minor version before becoming required |

## Blocking

Not blocking any current work. Should be completed before a second downstream consumer is built.

## Next step

1. Add `schema_version: 1` to `spec.template.yaml`
2. Update `process.md` Step 7 synthesis to include the field
3. Update `README.md` to mention versioning
4. File a note in sf2's `debate/009-event-schema-evolution.md` that the upstream schema now has versioning
