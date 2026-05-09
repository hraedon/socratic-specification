---
number: "003"
title: "Extension proliferation vs. generalization — when does a project type belong in the base process?"
author: opencode
date: "2026-05-09"
related: ["process.md §Process Extensions", "spec.template.yaml"]
---

## Context

The base process handles all project types. Extensions add mode-specific probes for project types with requirements the base process doesn't fully address. Currently:
- **Mobile** (iOS / Android) — the only implemented extension
- Mentioned but not implemented: web, data pipeline, CLI, API, etc.

The Mobile extension adds:
- Platform declaration (native vs. cross-platform)
- Additional high-coupling decisions (offline, sync, permissions)
- Additional elicitation probes (5 domain-language questions)
- Screen flow diagrams (Mermaid, with 8-screen complexity cap)
- Additional artifact sections (`[MOBILE] Platform & Distribution`, `[MOBILE] Screen Flow`)

## Problem

If every project type gets its own extension, the process becomes a framework of frameworks. The base process risks becoming a thin wrapper that delegates everything to extensions. Conversely, if too much stays in the base process, it becomes bloated with questions that don't apply to most projects.

There is no documented rule for when something belongs in the base process vs. an extension.

## Position

**Document an explicit decision framework with three criteria for extensionhood:**

1. **Platform-specific capabilities** — Does the project type require access to device or runtime capabilities that other types do not? (camera, GPS, biometrics, offline storage, background jobs)
2. **Distinct high-coupling decisions** — Does the project type introduce load-bearing architectural choices that the base process checklist misses? (sync strategy, permissions model, app store compliance)
3. **Visual or spatial reasoning** — Does the project type require the human to reason about navigation, layout, or flow in a way that text alone cannot capture? (screen flows, data pipeline topology, API dependency graphs)

**If a project type meets 2+ of these criteria, it is an extension. Otherwise, it belongs in the base process or is out of scope.**

### Applying the framework

| Project Type | Platform-specific | Distinct HCDs | Visual/spatial | Verdict |
|---|---|---|---|---|
| Mobile | Yes (camera, GPS, biometrics) | Yes (offline, sync, permissions) | Yes (screen flows) | **Extension** |
| Web app | No (runs in browser) | Maybe (auth is not web-specific) | Maybe (page flows, but similar to mobile) | **Base process** |
| Data pipeline | No (runs anywhere) | Yes (batch vs. streaming, backfill, schema evolution) | Yes (topology diagram) | **Extension** |
| CLI tool | No | No (most HCDs are base-process) | No | **Base process** |
| API/service | No | Maybe (rate limiting, versioning) | Maybe (endpoint dependency graph) | **Base process** |
| Desktop app | Yes (file system, notifications) | Maybe (auto-update, platform APIs) | Maybe (window flows) | **Extension** |

### Why a framework matters

Without it, the process author must make ad-hoc decisions for each new project type. This leads to:
- Inconsistency (why does Mobile get screen flows but Web does not?)
- Bloat (every project type gets its own section, even when the base process handles it)
- Gaps (a project type that should be an extension is treated as generic, missing critical probes)

## Risks

| Risk | Mitigation |
|---|---|
| Framework is too rigid | Treat it as guidance, not law; document exceptions with rationale |
| Web and Mobile blur (PWA, React Native) | Extensions are additive; a project can activate multiple extensions (Mobile + Web) |
| Process implementers ignore the framework | Reference the framework in `README.md` and `process.md`; add it as a checklist for new extensions |

## Blocking

Not blocking any current work. Should be completed before the next extension is designed (likely Data Pipeline or Web).

## Next step

1. Add the three-criteria framework to `process.md` under "Process Extensions"
2. Apply the framework retroactively to Mobile; document the justification
3. Create a placeholder extension template (`extension.template.md`) that new extensions must follow
4. Close this debate when the first new extension is accepted under the framework
