# Extension Library — Guardrails and Archetypes

**Governance status: IMPLEMENTED. Content status varies by registry entry.**
`index.yaml` is the machine-readable registry. Stable entries are process inputs;
pilot and proposed entries remain evidence-gathering work and do not silently
alter the base process. `process.md` remains authoritative for stable behavior.

New entries use `extension.template.md` and must satisfy the registry's
extensionhood, composition, empirical-evidence, and promotion-bar rules.

**Motivation.** The base process and the Mobile extension were shaped largely by
one project's pain (cert-watch / sf2 maintenance — see debates 005–008). This
library is shaped by the *portfolio*: patterns and pitfalls that recur across the
whole project corpus (gpo-lens, adcs-lens, ad-steward, cert-watch, acme-adcs-ra,
dossier, agent-notes, sluice, usage-dashboard, …). The empirical bar is the same
one debate 005 set — a pattern must recur across independent implementations
before it earns a place here.

**Audience.** Operationalizing spec-authoring for a team learning agentic
development. The driver is often not a software engineer. That inverts a hidden
assumption in the base process: the expert driver silently supplied blast-radius
awareness, dev≠deploy instinct, and data hygiene, so those never had to be asked.
A non-expert driver supplies none of it. This library externalizes that tacit
knowledge into questions the agent asks on the driver's behalf.

---

## The composition architecture

Width must not land on the human. The base process already solved this: extensions
are mode-detected in Step 0, declared, confirmed, and auto-activated. The driver
answers domain-language questions three at a time and never sees the machinery.

This library keeps that discipline by splitting width into two layers:

### Guardrail primitives (`guardrails.md`) — Family A

Four reusable primitives, each in the established extension shape (activation
signal → Step 4 high-coupling decisions → Step 3 probes → Step 5 audit checks →
Step 7 artifact fields). They encode the recurring *pitfalls* of the library.

| ID | Guardrail | Encodes the library lesson |
|---|---|---|
| **G1** | Data hygiene (classification-first) | Keep real regulated data out of code, fixtures, logs, and agent context. |
| **G2** | Blast-radius / mutation posture | Read-only vs. mutating vs. in-path is more load-bearing than the data model. |
| **G3** | Environment matrix | dev ≠ deploy is where CI-green bugs hide. |
| **G4** | Operations / provisioning | Install/upgrade-without-clobber, run-as identity, secret surface. |

### Archetype starters — Family B

An archetype is **not a new fork**. It is a *composition* of guardrail primitives
plus a small archetype-specific delta (its own high-coupling decisions, business
rules, and known pitfalls). This is the anti-proliferation rule (debate 003): if
an archetype can't be expressed as `guardrails + small delta`, it doesn't belong
here.

For a learning team the archetype is the highest-leverage artifact in the library:
it is simultaneously the guardrail-delivery mechanism *and* the curriculum. A
colleague who picks "I'm building a read-only analyzer" inherits the entire learned
playbook of four prior projects as questions the agent already knows to ask.

| Archetype | Composes | Drawn from | Status |
|---|---|---|---|
| **Local-first read-only analyzer** | G1 + G2(pinned read-only) + G3 | gpo-lens, adcs-lens, ad-steward, cert-watch | **Drafted** (`archetype-local-first-read-only-analyzer.md`) |
| Deployed service | G1 + G2 + G3 + G4 | cert-watch, acme-adcs-ra, sluice | Stub |
| Provenance-instrumented tracker | G1 + G2 + G4 + cross-component seam | dossier, agent-notes | Stub |
| Agent-suite component | G1 + cross-component seam | anything on regista's canonical contract | Stub |
| Internal CLI / skill | G1 + G2 | acb, agent-wake | Stub |

---

## Detection → composition → elicitation (the runtime shape)

1. **Step 0 detection.** The agent reads the vibe spec for archetype signals and
   declares the match: *"This sounds like a read-only analyzer of an existing
   system. I'll bring in the questions that project type always needs — data
   handling, what runs where, and confirming it never changes anything. Correct me
   if that's wrong."* Wrong detection is treated like a restatement failure.
2. **Composition.** The archetype pulls in its guardrail primitives. Guardrails
   also activate independently of any archetype when their own signals fire.
3. **Elicitation.** Guardrail probes and archetype-delta probes join the Step 3
   loop in domain language, three at a time. Guardrail audit checks join Step 5.
   Guardrail and archetype artifact sections join the Step 7 output.

The human's experience is unchanged: domain-language questions, batched, with
translation confirmation. The width lives in what the agent pulls in, never in
what the human faces.

---

## Honest risks (carried from debate 003)

- **Proliferation / drift.** Enforced by the composition rule: archetypes are
  `guardrails + small delta`, never standalone. An archetype that duplicates a
  guardrail instead of composing it is a defect.
- **Starters encode current truth, which moves.** dossier/agent-notes convergence
  reversed a prior plan; an archetype that hard-codes stale architecture lies to
  the driver. Archetypes state *intent and pitfalls*, not mechanism, and carry a
  "last validated against" note.
- **Teachability cliff.** Width the driver *sees* is the enemy; width the agent
  *pulls in* is the goal. Any change that puts more of the machinery in front of a
  first-time driver has regressed.
