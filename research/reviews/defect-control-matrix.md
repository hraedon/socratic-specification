# Defect/Control Matrix — Wave 1

**Date:** 2026-07-14
**Source reviews:** reviewer-a-regista.yaml, reviewer-b-regista.yaml, reviewer-a-cert-watch.yaml, reviewer-b-cert-watch.yaml
**Reconciliation:** taxonomy-reconciliation.md

## Purpose

Factual record of all findings and effective controls across the two reviewed
projects, using reconciled classifications. This is extraction, not synthesis.
Lesson candidates (synthesis) are in separate files.

## Legend

- **R-A:** Reviewer A found
- **R-B:** Reviewer B found
- **Both:** Both reviewers found (classification may have been reconciled)

---

## Regista findings

| ID | Summary | Reconciled class | R-A | R-B | Evidence |
|---|---|---|---|---|---|
| RG-01 | Spec drift: implementation diverged from spec.md (BC-211/212/213) | decomposition_gap / spec_inconsistency | Yes | — | commit 4170912, bb2768d |
| RG-02 | InMemorySubstrate diverged from Postgres (10+ bugs across 6+ sweeps) | decomposition_gap / implementation_error | Yes | Yes | commits 76cf93c, 09f6a5b, c61fc07, 14dd8a9, c20e269, 2ab9116 |
| RG-03 | Signing envelope v1→v5 evolution (trust model underspecified) | translation_gap / elicitation_gap | Yes | Yes | spec.md rev history v6/v7/v8/v9, commits 765e7f2, 7a42657 |
| RG-04 | Month-partitioning reverted as premature (RFC-001) | decomposition_gap / translation_gap | Yes | Yes | commit 9565bcb, spec.md v5 |
| RG-05 | content_hash length validation missing (BC-301) | implementation_error / decomposition_gap | Yes | — | commit b19e6bd |
| RG-06 | Adversarial review rounds repeatedly found critical/high bugs (8+ rounds) | decomposition_gap (finding) + effective control | Yes | — | commits 8d27c5b, 519ea2b, e048ab3, b8e81ec, 1752b2b, 087ecee |
| RG-07 | WI-072 halt/revert — custom transitions incorrectly halted | implementation_error / translation_gap | Yes | — | commit 1ab43ca |
| RG-08 | Actor role enforcement deferred (audit-only until FR-24) | elicitation_gap | — | Yes | spec.md BR-09, commit c8f240a |
| RG-09 | Replay isolation level wrong (READ COMMITTED → REPEATABLE READ, BC-310) | decomposition_gap / implementation_error | — | Yes | CHANGELOG [Unreleased] BC-310, spec.md §17.1 |
| RG-10 | Cross-work-item ordering missing (global_seq added later) | decomposition_gap / translation_gap | — | Yes | Plan 014, CHANGELOG v0.3.0 |
| RG-11 | claim attempt_number dropped by WorkItem dataclass | implementation_error | — | Yes | commit 1424d5f BC-054 |
| RG-12 | Heartbeat coalescing required replay tolerance adjustment | implementation_error / translation_gap | — | Yes | CHANGELOG v0.1.1 BC-194 |
| RG-13 | Schema-per-project replaced DB-per-project isolation model | translation_gap | — | Yes | spec.md §10 v4, BR-13 |

## Regista effective controls

| ID | Control | R-A | R-B | Evidence |
|---|---|---|---|---|
| RG-C01 | Two-reviewer correctness pass (spec v2) | Yes | — | spec.yaml open_questions |
| RG-C02 | Breadcrumb tracking (BC-XXX) for issue lifecycle | Yes | Yes | 94+ commits reference BC- |
| RG-C03 | Cross-model adversarial review (GLM, Kimi, etc.) | Yes | Yes | commits e865445, 1752b2b, 3263c91 |
| RG-C04 | Backend conformance test suite (test_in_memory_conformance.py) | Yes | Yes | commit 2ab9116, tests/test_in_memory_conformance.py |
| RG-C05 | Spec revision discipline with explicit revision history | Yes | — | spec.md v1-v9 changelog |
| RG-C06 | Session worklogs and reflections | Yes | — | commits ccf3304, 6cd5570, ba6102b |
| RG-C07 | Public API surface formalized (§19) | — | Yes | spec.md §19, AC-34 |
| RG-C08 | API-layer idempotency (event_id as idempotency key) | — | Yes | spec.md BR-12, AC-24 |
| RG-C09 | Replay with drift detection (FR-16) | — | Yes | spec.md FR-16, AC-27, AC-29 |
| RG-C10 | Vendored rfc8785 module (Plan 008 WS-3) | — | Yes | CHANGELOG v0.2.0 |
| RG-C11 | Single-source-of-truth backend contract (_contract.py) + property-based conformance | — | Yes | commit 154a56d, tests/test_property_conformance.py |

---

## Cert-watch findings

| ID | Summary | Reconciled class | R-A | R-B | Evidence |
|---|---|---|---|---|---|
| CW-01 | Scheduler wiring bug: app.state.scheduler never set in production → HTTP 503 | decomposition_gap / environment_gap | Yes | — | .review-feedback, fr09_manual_scan.py |
| CW-02 | 7 test failures in BR-01 status derivation boundaries | implementation_error | Yes | Yes | test-results.json, commits 2e8e51d, 7e371ef |
| CW-03 | Stale test-results.json (shows pre-fix failures, not final state) | environment_gap / decomposition_gap | Yes | — | test-results.json vs factory.log |
| CW-04 | Empty handoff.md template — no knowledge transfer | decomposition_gap | Yes | — | .factory/handoff.md |
| CW-05 | Lineage tracking failure: 0 work units recorded despite 19 agents running | decomposition_gap / environment_gap | Yes | Yes | lineage.json vs .events.jsonl |
| CW-06 | Phantom coverage: 13/15 FRs have no HTTP routes | decomposition_gap / implementation_error | Yes | — | src/cert_watch_8/web/routes/ |
| CW-07 | 413 tests pass despite 13/15 FRs unwired (false coverage) | decomposition_gap / environment_gap | Yes | — | test-results.json, tests/integration/test_wiring.py |
| CW-08 | Handoff false positives: claims services never called but fr02_scan.py calls them | implementation_error / decomposition_gap | Yes | Yes | handoff.md vs fr02_scan.py |
| CW-09 | spec.yaml meta.name='cert-watch-2' but directory is cert-watch-3 | spec_inconsistency | Yes | — | spec.yaml line 2 |
| CW-10 | Scheduler starts but no scan jobs registered (FR-10 non-functional) | decomposition_gap | Yes | — | lifespan_hooks.py:91 |
| CW-11 | Factory spec lint warnings (FR testability) | translation_gap / spec_inconsistency | — | Yes | factory.log lines 2-13 |
| CW-12 | MVP FR count mismatch between spec.md and spec.yaml | spec_inconsistency | — | Yes | factory.log lines 16-18 |
| CW-13 | Alert records returned newest-first instead of oldest-first | implementation_error | — | Yes | commit 852b3c8 |
| CW-14 | FR-09 UI missing "Scan Now" button | decomposition_gap | — | Yes | factory.log fr-09 review |
| CW-15 | Duplicate matching semantics changed between runs (subject+hostname → fingerprint) | translation_gap / elicitation_gap | — | Yes | cw3 BR-06 vs cw8 BR-01 |
| CW-16 | SmtpAlertService milestone keying potentially non-deterministic | implementation_error / translation_gap | — | Yes | alert.py lines 79-95 |
| CW-17 | PFX password prompt exposed as API but no UI modal flow | decomposition_gap | — | Yes | spec.yaml FR-05, routes listing |

## Cert-watch effective controls

| ID | Control | R-A | R-B | Evidence |
|---|---|---|---|---|
| CW-C01 | Factory test gate with auto-fix agent | Yes | Yes | factory.log, commits 2e8e51d, 7e371ef |
| CW-C02 | Post-factory .review-feedback correctness review | Yes | — | .review-feedback file |
| CW-C03 | test_wiring.py orphan service detection attempt (insufficient but correct intent) | Yes | — | tests/integration/test_wiring.py |
| CW-C04 | Integration review in handoff (phantom coverage detection) | Yes | — | .factory/handoff.md |
| CW-C05 | Factory work decomposition with prerequisite resolution | Yes | — | spec.yaml mvp.architectural_prerequisites |
| CW-C06 | Factory spec lint (testability and drift warnings) | — | Yes | factory.log lines 2-18 |
| CW-C07 | Adversarial security review (zero findings for cw8) | — | Yes | security-findings.json |
| CW-C08 | Spec level upgrade from 2 to 3 between runs | — | Yes | cw3 spec_level:2, cw8 spec_level:3 |

---

## Cross-project patterns (factual, not synthesis)

These are observed facts that appear in both projects. Lesson synthesis is in separate files.

| Pattern | Regista evidence | Cert-watch evidence |
|---|---|---|
| Test environment differs from production | InMemory backend diverged from Postgres (RG-02) | Fixtures injected scheduler that production never set (CW-01) |
| Verification didn't cover full consumer chain | Spec drift: code diverged from spec (RG-01) | 13/15 FRs unwired, tests pass on isolated services (CW-06, CW-07) |
| Factory/artifact reliability issues | N/A (no factory) | Stale test-results (CW-03), empty handoff (CW-04), lineage failure (CW-05), handoff false positives (CW-08) |
| Adversarial review as highest-yield detection | 8+ rounds finding critical/high bugs (RG-06) | Post-factory review found scheduler bug (CW-C02) |
| Signing/trust model underspecification | v1→v5 envelope evolution (RG-03) | N/A |

---

## Coverage summary

| Metric | Regista | Cert-watch |
|---|---|---|
| Total findings (both reviewers) | 13 | 17 |
| Findings both reviewers found | 3 | 3 |
| Findings only A found | 4 | 5 |
| Findings only B found | 6 | 7 |
| Effective controls (both reviewers) | 11 | 8 |
| Reconciled classification changes | 2 | 2 |
