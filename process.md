# Vibe-to-Spec Process v1

## Purpose

This process converts an informal description of desired software ("vibe spec") into a production-grade specification suitable for agentic implementation. It requires no specification expertise from the human. The process does the work; the human provides domain knowledge, intent, and decisions.

The underlying thesis: a well-designed elicitation process can produce a production-grade spec from a vague human prompt. "Learn to write specs" is a tool skill being automated away, not a durable competency.

Even a complete spec will encounter conditions that weren't anticipated. The goal of this process is to minimize surprise and make rework cheap and local — not to eliminate it. Some amount of refactoring in any project is unavoidable.

**A note on AI competence:** The AI's assessment reflects general software engineering knowledge. For domains with specialized risk — regulatory compliance, distributed systems, security-critical infrastructure — the output of this process should be reviewed by a domain expert before implementation begins. When the AI detects signals of a specialized domain during elicitation, it surfaces this in the conversation rather than leaving it only as a note in the artifact.

---

## Roles

**Human**
- Writes the initial vibe spec at whatever quality level they can manage
- States delivery or assurance needs in ordinary language; choosing a numbered spec level is optional
- Confirms or corrects the opening restatement
- Answers questions in their own domain language — no technical knowledge required
- Makes decisions when presented with options and trade-offs
- Confirms termination

**AI Partner**
- Recommends the appropriate target level from delivery risk and assurance needs, including pushing back when a requested level is unachievable
- Produces the opening restatement
- Drives the iteration loop: asks questions in domain language, translates answers into technical requirements, states assumptions, flags conflicts, identifies high-coupling decisions
- Declares diminishing returns with explicit reasoning
- Synthesizes the final spec artifact

---

## A Core Principle: Domain Language First

**Elicitation questions must be asked in the human's language. The AI translates answers into technical requirements — not the other way around.**

A non-technical user cannot be expected to know whether they need "sub-second latency" or a "normalized schema." They can answer: *"If this takes 30 seconds to run, does that block someone from doing their job, or is it a background task they'd walk away from?"*

The AI derives the technical requirement from the domain-language answer and records both. This applies to all elicitation: NFRs, data models, integration points, error handling. The human describes their world; the AI maps it to software requirements.

---

## Spec Levels

Testing is not a Level 2 concern — it begins at Level 1. Every spec must identify what is testable and produce acceptance criteria for those items. Items that cannot be tested must be explicitly labeled with a reason.

Level definitions are principle-based, not gate-based. The goal is a spec that serves a non-technical human well, not one that satisfies a rigid checklist. A schema or API contract at Level 2 should be expressed at the level of detail the human can provide — even if that means "a table of customer records with name, email, and order history" rather than a full DDL.

| Level | Name | Requirements |
|---|---|---|
| **1** | Implementable | Full happy path specified. Explicit assumptions recorded. Testable behaviors have acceptance criteria. Untestable items labeled with rationale. Major failure modes identified. High-coupling decisions classified. |
| **2** | Verifiable | All of Level 1. Edge cases enumerated with test criteria. NFRs derived from domain-language answers and stated as concrete, measurable values. Integration points described at the level of detail available. Full failure mode coverage. |
| **3** | Complete | All of Level 2. No unresolved intent or high-coupling product decisions; any remaining open questions are classified as unknowable / needs research / indifferent / cheap-to-change. Scope explicitly bounded. Implementation mechanisms may remain within agent discretion unless they affect a stated constraint. |

### Desired Level vs. Target Level

- **Desired level** — optional; derived from an explicit human request or ordinary-language delivery and assurance needs
- **Target level** — recommended by the AI based on risk and what is achievable from current knowns

Do not make a user learn this level system before describing their problem. If they do not request a level, recommend one and proceed after the opening restatement. When desired and target levels differ, state the gap directly and specifically before elicitation begins:

> *"You've asked for Level 3. This is currently a Level 1 because the authorization model is undefined and the data source is ambiguous. Level 2 is achievable if you can answer two questions. Level 3 requires a decision you may not be able to make before implementation."*

The AI does not soften this assessment. The human may accept a lower target, provide the missing information, or defer decisions with explicit acknowledgment of the cost.

When Level 1 is the target, record the concrete delta to Level 2 in the artifact. Do not add a separate conversation round unless the human asks to explore it.

---

## The Process

### Step 0: Minimum Viable Input Check and Mode Detection

Before restatement, the AI performs two checks.

**Input check:** Does the vibe spec contain enough signal to identify the core goal?

If yes: proceed to mode detection.

If no (e.g., a single aspirational sentence with no grounding): ask up to three orientation questions before proceeding. These are not elicitation questions — they are the minimum needed to attempt a restatement:

1. What does this replace or make easier?
2. Who uses it, and in what context?
3. What does a successful outcome look like?

Once orientation answers exist, proceed to mode detection.

**Mode detection:** The AI reads the vibe spec for signals that indicate one or more process extensions should be activated. It includes the detected mode in the opening restatement rather than requiring a separate confirmation round:

> *"This sounds like a [mobile app / data pipeline / etc.], so I will include [mobile-specific / etc.] concerns. If that or the goal summary below is wrong, correct me."*

A corrected mode is treated like a restatement correction because it signals ambiguity that may recur. See **Process Extensions** for activation signals. Proceed to Step 1 and confirm mode and intent together.

---

### Step 1: Opening Move — Goal Restatement

The AI's first substantive output is a restatement of the human's goals, not an assessment or questions. This is the highest-leverage step in the process. Everything downstream depends on shared understanding of intent.

The restatement covers exactly three things:

1. **The problem being solved** — what situation currently exists that this software addresses
2. **The user and context** — who operates this, in what environment, under what conditions
3. **The definition of success** — what a working system produces or enables, in concrete terms

Format:

> *"Before we go further, here is my understanding of what you're trying to build:*
>
> *[Problem]: ...*
> *[User/Context]: ...*
> *[Success looks like]: ...*
>
> *Is this accurate? Correct anything that's wrong before we proceed."*

The human confirms or corrects. If a correction is needed, the AI notes the nature of the misread — because a restatement failure indicates genuine ambiguity in the vibe spec that will recur during elicitation.

Do not proceed to Step 2 until the restatement is confirmed.

---

### Step 2: Level Assessment

With confirmed intent, the AI:

1. Assigns the current spec level (1, 2, or 3) with specific justification
2. Identifies the target level (highest achievable given current knowns)
3. If the human requested a level, compares it with the target
4. If requested > target: states blockers explicitly and offers a path to close the gap
5. Identifies all high-coupling decisions present in the spec (see Step 4 below)

Keep the full assessment in working state. Show the human a concise version only when it changes what must be answered, reveals a requested-level gap, or exposes a high-coupling decision. A routine internal level label does not justify another confirmation round.

---

### Step 3: Iteration Loop

Repeat until target level is reached or diminishing returns are declared.

**Each round:**

1. **Prioritize gaps** by implementation risk. Address what would block or break implementation before addressing what would merely improve it.

2. **Resolve from evidence before asking.** Check the vibe spec, prior answers, supplied documents, and accessible repository or environment evidence first. Record facts with the appropriate provenance. Never ask the human to repeat a fact that is already available. If sources conflict, ask about the conflict rather than asking the original question again.

3. **Ask, propose, or assume.** For each unresolved gap:
   - If it is a high-stakes intent or trade-off decision only the human can make, ask one targeted question in domain language. Prefer questions that resolve several linked gaps at once. Generic technical questions ("what are your performance requirements?") are not acceptable.
   - If evidence supports a likely answer but a high-stakes decision still needs consent, propose the answer and ask for correction instead of asking an open-ended question.
   - If low-stakes, state an explicit assumption and move on. Use the Assumption Thresholds below; implementation size alone does not make a question human-owned.
   - If it is an implementation mechanism the implementing agent can decide later, do not ask or turn it into an intent requirement.

4. **Confirm translations proportionally.** Confirm translations immediately when they create a measurable user-visible threshold, scope boundary, irreversible commitment, or high-coupling decision:
   > *"You said it should feel instant — I've taken that to mean under half a second. Does that match what you meant, or would a few seconds be acceptable?"*
   Group low-risk derived details into the next summary or decision brief for correction. Do not require a separate yes/no exchange for every derived field, and do not silently record a consequential derivation.

5. **Handle "I don't know."** When a human doesn't know how to answer a forced choice, the AI presents 2-3 concrete options with plain-language trade-offs expressed as outcomes the human will experience, not technology choices. The AI also explicitly invites domain input:
   > *"There may be options I haven't listed — if you have a preference or constraint from your industry or context, say so and we'll work from there."*
   The human may choose an option, provide their own, or defer with explicit classification.

6. **Batch questions.** Ask no more than 3 questions per round and default to 1-2. Order by decision impact and expected information gain, not template order. Do not fill the batch merely because capacity remains.

7. **Build the glossary.** The first time a domain-specific term is introduced — by either party — record it with its agreed definition. If a term appears to shift meaning across rounds, surface the discrepancy and agree on a canonical definition before proceeding:
   > *"You've used 'customer' and 'user' — are these the same person or different roles?"*

8. **Elicit MVP definition.** Once functional requirements are substantially sketched (typically after round 1 or 2), use any priority already stated in the vibe spec or answers to propose an MVP for correction. If no priority is available, ask once:
   > *"If you could only ship the most essential part of this first — the version that would already be genuinely useful — what would that be?"*
   Record the confirmed MVP FRs and rationale. If the human is unsure, ask what problem they most urgently need solved. Do not invent priorities, but do not ask the human to repeat a priority they already supplied.

   After the human declares MVP FRs, check them against the current high-coupling decisions. If any MVP FR has a significant architectural prerequisite — an auth system, a sync engine, a data model — that isn't itself in the MVP, surface it as a forced choice before recording:
   > *"[FR-X] needs [prerequisite] to exist first — that's not in your MVP as described. We can include it as invisible infrastructure (the user never sees it, but it has to be built), or we scope down to a version that doesn't need it yet. Which makes more sense?"*

   **Prerequisites gate (blocking):** Before recording MVP FRs in the artifact, evaluate each against this checklist and populate `mvp.architectural_prerequisites` explicitly — even if the answer is "none":
   - Does this FR read from or write to persistent storage?
   - Does this FR depend on a parsing, transformation, or cryptographic module?
   - Does this FR call an external service, network endpoint, or OS resource?
   - Does this FR require an auth or identity system to exist?

   If any check is yes, that infrastructure is a prerequisite. Record it with a resolution (`invisible_infrastructure`, `scope_reduction`, or `deferred`). If all checks are no, record `architectural_prerequisites: []` explicitly. A silently empty prerequisites section is a spec defect — the check must be performed and the result recorded either way.

9. **Flag specialized domains.** If the spec shows signals of a domain with compliance, regulatory, or safety requirements (healthcare, finance, legal, critical infrastructure), surface this in the conversation:
   > *"This sounds like it may touch [domain]. There are likely requirements in that space I'm not equipped to identify on my own. You may want a domain expert to review the spec before implementation."*
   Record this flag in the Open Questions section of the artifact.

10. **Flag conflicts.** If a human's answer contradicts a prior answer or the original spec, surface the conflict explicitly before proceeding:
   > *"This conflicts with [X] you said earlier. Which is correct, or do both need to be true?"*
   Unresolved conflicts are not papered over — they are recorded as open questions.

11. **Check outcome boundaries.** Split an FR during elicitation only when it combines independently valuable user outcomes, contains conflicting scope choices, or cannot be confirmed as one coherent behavior. Do not estimate files or lines of code and do not ask the human to perform implementation decomposition. Codebase-grounded package size and agent context limits belong to the downstream work-plan gate.

12. **Re-assess level** internally after each round. Tell the human only when the level changes, a blocker appears, a requested-level gap remains, or termination is being proposed. The artifact records the delta to the next level without requiring repeated status exchanges.

---

### Step 4: High-Coupling Decisions

At each iteration, the AI identifies decisions where being wrong scales in cost with implementation depth. These are flagged regardless of whether the human raised them.

Common examples to check in every spec:
- Data model / schema
- Identity and authorization model — if the spec involves auth or identity in any form, this is automatically a high-coupling decision, not an NFR
- State persistence strategy (where state lives, consistency model)
- Integration contracts (if anything external depends on outputs)
- Deployment and runtime assumptions (job, service, CLI, etc.)

Each high-coupling decision is classified:

| Status | Meaning |
|---|---|
| **Decided** | Explicitly answered; rationale recorded |
| **Deferred with flexibility** | Not answered; implementation instructed to build in abstraction or configurability |
| **Deferred, accepted risk** | Not answered; no flexibility built in; human has acknowledged the rework cost |

A decision cannot remain unclassified in the final spec.

---

### Step 5: Pre-Synthesis Consistency and Composition Audit

Before synthesis, the AI performs a full pass over all accumulated answers, assumptions, and requirements to check for:

**Consistency checks:**

- Contradictions between early assumptions and later answers
- Requirements that conflict with each other
- High-coupling decisions whose classification is inconsistent with stated requirements
- Glossary terms used inconsistently across sections

**Composition checks** *(added per debate 005 resolution; only applied to items in MVP scope to avoid false positives on deferred work):*

- **Lifecycle wiring** — for every recurring, scheduled, background, or cleanup behavior the spec describes, is there an AC that places it in the runtime lifecycle? *Symptom this catches: a "daily scan" requirement with no AC saying when the scan loop starts running.*
- **Read-path symmetry** — for every data producer or event log the spec describes (scan history, alert log, audit trail), is there a stated consumer? *Symptom this catches: a `scan_history` table written by an automated job that no FR ever reads.*
- **Configuration surface** — for every configurable behavior, is the spec explicit that it is deployment-configurable (without prescribing the mechanism)? *Symptom this catches: an `alert_email` field defined with no statement that the operator must be able to set it. The spec must say "the operator can set this"; it must not say "via env var SMTP_HOST".*

**Independent audit boundary.** `spec_tools.py validate --ready` independently checks the structure it can know: schema conformance, identifier references, MVP/acceptance-criterion coverage, and readiness fields. It does **not** prove that prose describes every lifecycle edge or real read path. The elicitation AI performs those semantic composition checks, and factory-bound work receives a separate codebase-grounded architecture and coverage review. Until a machine-readable lifecycle or producer/consumer model exists, do not claim mechanical verification of those meanings.

**Blocking requirement.** Composition gaps in MVP scope block synthesis. Resolve facts from supplied context or inspectable evidence first. Ask the human in domain language only when the gap is an intent or trade-off decision, then record the answer as an AC. Non-MVP gaps may be recorded as assumptions.

**Domain-language translation.** All composition-check questions must be translated into the human's terms before being asked, per the Step 3 domain-language principle. Reference table:

| Composition concern | Implementation-layer phrasing (do not ask the human this) | Domain-language phrasing (ask the human this) |
|---|---|---|
| Lifecycle wiring | "Where does `start_scheduler()` get called?" | "When should the system start doing this on its own — as soon as it's running, only when someone triggers it, or on a schedule someone sets?" |
| Read-path symmetry | "What consumer reads the `scan_history` table?" | "When something goes wrong with a scan, how does someone find out what happened? Do they see it on a screen, get notified, or only check if they go looking?" |
| Configuration surface | "Where does `AlertConfig` come from at runtime?" | "When would someone first set the email address for alerts — is there a place for that in the app, or does someone configure it once when setting the system up?" |

The audit records its checked counts and findings in working state so coverage is attributable rather than silent. Show the human only unresolved intent choices or conflicts. A clean internal audit does not need a permission-only conversation turn. After synthesis, run structural validation on the canonical YAML; automatically repair and revalidate machine-detectable defects unless they expose a human-owned decision.

---

### Step 6: Termination

Stop eliciting when no unanswered question is expected to change MVP scope, externally visible behavior or contracts, safety or compliance obligations, or a high-coupling decision beyond the accepted risk. A question may remain resolvable when its expected value is lower than the cost of another human turn.

Classify every remaining open question as:

- **Unknowable** — cannot be resolved without implementation data or decisions outside the scope of this session
- **Needs research** — can be resolved, but requires information not available in this session
- **Indifferent** — valid either way, low consequence
- **Cheap to change** — low coupling, easily revised after the fact

Default transition:

> *"I have enough to draft the decision brief and spec. The remaining items are [brief classified list]; none changes the current MVP beyond the recorded risk. I will synthesize now unless I have misunderstood a priority."*

Do not require a separate permission-only turn. The decision brief remains the normal final confirmation gate. Ask before synthesis only when the human has requested checkpoints or a remaining ambiguity could change what is built.

---

### Step 7: Synthesis

Before generating the artifact, the AI makes one final pass over the original vibe spec to capture informal signals — growth expectations, scale hints, future intentions — that were not elevated to formal requirements. These populate Section 15 (Handoff State — Intent Signals), clearly distinguished from requirements and explicitly linked to Section 10 (High-Coupling Decisions) so the implementing agent must address them when resolving architectural choices.

Before writing the canonical artifact, the AI attaches categorical provenance to functional requirements, business rules, high-coupling decisions, acceptance criteria, assumptions, and risks: `human_stated`, `translated_confirmed`, `repo_observed`, `agent_inferred`, `assumed`, or `externally_verified`. These categories route review; they are not model confidence scores. Notes identify the source or confirmation briefly without embedding sensitive content.

The AI produces one canonical artifact and two generated views:

1. **`spec.yaml`** — the canonical, versioned specification. See **`spec.template.yaml`** and `schemas/spec-v2.schema.json`.
2. **`spec.md`** — a deterministic human-readable rendering of `spec.yaml`.
3. **`decision-brief.md`** — a concise, non-authoritative confirmation view containing delivery, exclusions, pending decisions, and the largest risks.

Validate `spec.yaml`, then generate both views with `scripts/spec_tools.py`. The human confirms the decision brief and may inspect the full Markdown. Corrections are applied to the canonical YAML by the elicitation tool, validated, and rendered again. Generated views are never edited independently. Any divergence fails `check-sync`; there is no precedence rule for contradictory artifacts.

Every confirmed intent change increments `meta.revision` and records the previous canonical fingerprint in `meta.parent_fingerprint`. Schema version changes only when the machine contract changes.

---

## Implementation Default

Technology choices are left to the implementing agent and are not part of the spec unless the human states explicit constraints. When options are equivalent, prefer:

1. Tools with broad adoption and active ecosystems over niche alternatives
2. Inherently safer tools over those requiring greater care to use correctly

These are defaults, not rules. The implementing agent exercises judgment within them.

When NFRs or requirements materially constrain the technology options (e.g., a stated performance requirement that most default stacks cannot meet), the spec notes this so the implementing agent evaluates fit before writing code rather than after.

---

## Assumption Thresholds

A gap is **low-stakes** (assume, don't ask) when all of the following are true:
- It does not change MVP scope or an externally visible behavior or contract
- It does not affect safety, compliance, privacy, or another material harm boundary
- It does not touch a high-coupling decision
- Available evidence or a conventional default makes the assumption reasonable and cheap to revise

A gap is **high-stakes** only when a wrong answer can materially change one of those outcomes. Even then, ask the human only if evidence cannot resolve it and it is an intent or trade-off decision they own. Otherwise record a research task, accepted risk, or implementing-agent decision.

Every assumption made during elicitation is recorded explicitly in the spec artifact's Assumptions section.

---

## Spec Artifact Template

```markdown
# Specification: [Name]

**Spec ID:** [stable ID]
**Revision:** [1..N]
**Schema Version:** [2]
**Spec Level:** [1 / 2 / 3]
**Desired Level:** [what the human requested, or "not requested"]
**Date:** [date of synthesis]
**Extensions active:** [None / Mobile / ...]

---

## 1. Problem Statement

**Problem:** [What situation currently exists that this software addresses]
**User/Operator:** [Who runs this, in what environment, with what permissions or context]
**Success condition:** [What a working system produces or enables, in concrete terms]

---

## 2. Glossary

Terms defined during elicitation. All sections of this spec use these definitions consistently.

| Term | Definition |
|---|---|
| [Domain term] | [Agreed definition, including any distinctions from related terms] |

---

## 3. Scope

**In scope:**
- [Explicit list of what this system does]

**Out of scope:**
- [Explicit list of what this system does not do]

---

## 4. MVP Definition

The minimum version of this system that would be genuinely useful. Declared by the human during elicitation.

**MVP is:** [One sentence describing the minimum useful version]

**MVP functional requirements:** [FR-xx, FR-xx, ...]

**Rationale:** [Why these and not others — what problem they solve first]

**Note to implementing agent:** This reflects value priority as declared by the human, not implementation order. Some non-MVP requirements may be architecturally load-bearing and must be built before MVP features can function. Surface any such conflicts before writing code.

---

## 5. Functional Requirements

Numbered list. Each requirement is a complete, testable behavior.
Format: Given [precondition], when [event/input], the system [does X].

MVP items are marked **[MVP]**.

- FR-01 **[MVP]**: ...
- FR-02: ...

Each FR carries categorical provenance in canonical YAML. The generated Markdown may show this as a compact source annotation; the human is never asked to edit provenance syntax.

---

## 6. Data

**Inputs:**
- [Name, format, source, validation rules — expressed at the level of detail available]

**Outputs:**
- [Name, format, destination]

**Persisted state:**
- [What the system owns, where it lives, retention/consistency requirements]

---

## 7. Business Rules

Rules the system must not violate, distinct from implementation choices.

- BR-01: ...

---

## 8. Error and Failure Handling

For each failure mode: what triggers it, what the system does, who is notified (if anyone).

| Failure | Trigger | Response | Notification |
|---|---|---|---|
| ... | ... | ... | ... |

---

## 9. Non-Functional Requirements

Values are derived from domain-language answers and stated as concrete, measurable criteria.
Adjectives alone (fast, secure, reliable) are not acceptable — each must have a measurable condition.
Auth and identity, if present, belong in Section 10, not here.

Each value must include an inline derivation note citing the domain-language answer it came from. If you cannot cite the derivation, the value is a guess and belongs in Open Questions instead.

- **Performance:** [value — derived from: "quoted or paraphrased domain-language answer"]
  - e.g., "report generation under 10 seconds — derived from: 'users expect it before their next action'"
- **Reliability:** [value — derived from: ...]
- **Operability:** [value — derived from: ...]

*(Omit subcategories not applicable at this spec level.)*

---

## 10. High-Coupling Decisions

Decisions where being wrong scales in cost with implementation depth. When resolving any of these during implementation, the implementing agent must explicitly note how the intent signals in Section 15 influenced the resolution.

| Decision | Status | Notes |
|---|---|---|
| [e.g., Data model] | Decided / Deferred with flexibility / Deferred, accepted risk | [Rationale or flexibility approach] |

---

## 10A. Risk Register

The largest delivery or hard-to-reverse risks. Risks are categorical and evidence-routed; do not invent numerical confidence or probability.

| ID | Risk | Impact | Mitigation | Owner | Reversibility | Human decision? |
|---|---|---|---|---|---|---|
| RISK-01 | ... | ... | ... | ... | Easy / Costly / Irreversible / Unknown | Yes / No |

---

## 11. Acceptance Criteria and Test Plan

**Testable items** — each maps to one or more functional requirements:

- AC-01 [FR-01]: [Given/when/then test condition]
- AC-02 [FR-02]: ...

**Untestable items:**

| Item | Reason untestable |
|---|---|
| ... | [External dependency / non-deterministic / requires human judgment / etc.] |

---

## 12. Work Decomposition

This section has two distinct parts with different owners. Do not conflate them.

### Value Phases — owned by the human

What user-visible capability is delivered in each phase. Declared during elicitation. Reflects priority and usefulness, not build order.

- **Phase 1 (MVP):** [FR list] — [what the user can do; why this is the minimum useful version]
- **Phase 2:** [FR list] — [what additional capability this adds for the user]

### Implementation Phasing — owned by the implementing agent

The agent is responsible for determining build sequence based on architectural dependencies. This includes invisible infrastructure (auth, data model, sync engine) that must exist before user-facing features can function. The agent must:

1. Map value phases to an implementation sequence
2. Identify any architectural prerequisites not captured in value phases
3. Surface conflicts between declared value phases and build constraints before writing code — do not silently reorder
4. Inspect the target codebase and produce `.factory/work-plan.yaml` using `work-plan.template.yaml`
5. Pass the work-decomposition readiness gate before implementation begins

**Known prerequisites identified during spec:**
- [FR-xx likely requires [prerequisite] — flagged during elicitation, not yet validated]

**Dependency hints** *(intent-level only — not a build plan):*
- [FR-xx likely requires FR-xx to be complete first — reason: ...]
- [FR-xx and FR-xx are likely independent]

**Limitation:** Dependency hints reflect intent and logical inference from the spec, not verified implementation constraints. Implementing agents must derive actual build order from the codebase. Do not treat these as authoritative.

### Implementation Readiness Gate — factory-bound work

The spec or change-spec establishes intent; it cannot establish facts about a codebase it has not inspected. Before writing code, the implementing agent converts the confirmed target intent and dependency information into a codebase-grounded work plan. This is a separate downstream artifact, not a rewrite of the intent artifact.

The gate passes only when the work plan:

1. States the invariant each changed contract must preserve, including its authoritative owner and any identity, ordering, round-trip, or compatibility guarantees that apply
2. Maps every changed shared contract across its actual consumers — for example parser, domain model, persistence, API, browser, validation, comparison or hashing, export, and documentation — marking a consumer not applicable only with a reason
3. Includes an explicit read/write compatibility matrix and real historical fixtures whenever persisted or externally exchanged formats may change
4. Assigns every target intent item and acceptance criterion, plus every changed contract and affected consumer, to a bounded work package with prerequisites and a verifiable completion condition
5. Defines verification at the layer where behavior is real: browser runtime tests for browser behavior, serialize/reparse and unchanged-round-trip tests for persisted data, and real-environment tests for integrations that can be run
6. Includes adversarial cases appropriate to the change, including zero/one/many, boundary positions, missing or conflicting metadata, duplicate or missing identity, and old/current representations where applicable
7. Receives an independent architecture and coverage review for factory-bound work; unresolved coverage gaps block implementation

An implementation task is not complete merely because its local tests pass. It is complete when its assigned acceptance criteria and consumer obligations pass at the declared verification layers.

**Defect-class recurrence rule:** The first defect in a class triggers a consumer-wide fix and a regression test at the violated boundary. A second occurrence of the same defect class pauses implementation. The agent must revisit the invariant, consumer map, and task boundaries before continuing; reproducing and patching only the latest symptom is insufficient.

**Ownership boundary:** The implementing agent may reorder implementation work but must not silently change the human's value phases, scope, or acceptance criteria. Any genuine conflict returns to the human as a plain-language decision with impact, not as an undocumented planning assumption.

These are implementation-planning controls. They do not add technical invariants to greenfield elicitation. Change-to-existing-system mode uses the pilot extension in `extensions/change-existing-system.md` and the same downstream readiness gate.

---

## 13. Open Questions

| Question | Category | Owner |
|---|---|---|
| ... | Unknowable / Needs research / Indifferent / Cheap-to-change / Blocked on [X] | ... |

---

## 14. Assumptions

Explicit list of every assumption made during elicitation where the human did not provide an answer.

- [Assumption]: [Rationale for why this was assumed rather than asked]

---

## 15. Handoff State

Structured context for the implementing agent. Divided into three parts.

**Decisions made:**
- [Decision]: [Rationale — why this was chosen over alternatives]

**Pending / deferred:**
- [Item]: [Why deferred, what would resolve it, estimated impact if wrong]

**Intent signals:**
Informal signals from the original vibe spec that did not become formal requirements but reflect the human's broader goals or expectations. These are not requirements. When resolving high-coupling decisions (Section 10), the implementing agent must explicitly address each signal and note how it was weighed.

- [Signal]: [Quoted or paraphrased from vibe spec — brief note on relevance]

---

## 16. Delta to Next Level

What would be required to reach Level [N+1]:

- [Specific gap and what information or decision would close it]
```

---

## What This Process Does Not Do

- Prescribe technology choices (those belong to the implementing agent)
- Replace domain expertise (the human must know their domain; the process extracts it)
- Guarantee a complete spec when the problem itself is genuinely underspecified — it surfaces that condition and names it honestly
- Eliminate refactoring — it reduces the cost of being wrong, not the possibility of it

---

## Process Extensions

The base process handles all project types. Extensions add mode-specific probes, high-coupling decisions, and artifact sections for project types with requirements the base process doesn't fully address.

**How extensions work:**
- Activated during Step 0 mode detection and included in the combined opening restatement
- Add candidate concerns to the Step 4 high-coupling decision review
- Add candidate probes to the Step 3 iteration loop
- Add sections to the Step 7 synthesis artifact
- A project may activate more than one extension simultaneously

Extensions are additive in obligations, not necessarily in human questions. Before elicitation, compile all active probes into one decision graph, deduplicate overlaps, satisfy nodes from evidence or safe defaults, and ask the smallest remaining set of human-owned decisions. Per-round width is not a substitute for a total attention budget; if extension composition would create a long interview, state the blocking decisions and defer lower-value probes.

Extension governance and status live in `extensions/index.yaml`. New extensions use `extensions/extension.template.md`, meet the extensionhood/composition rules, and declare an empirical promotion bar. Pilot and proposed entries do not silently alter the stable process.

### Extension: Change to an Existing System

When a request changes a living repository or deployed system, activate the pilot described in `extensions/change-existing-system.md`. It produces canonical `change-spec.yaml` from `change-spec.template.yaml`, pins the inspected baseline, records preserved behavior and touched couplings, and makes compatibility, migration, rollback, and existing quality gates explicit. It is a delta to the baseline spec, not a regenerated claim to describe the entire system.

---

### Extension: Mobile (iOS / Android)

**Activated when:** the vibe spec describes an app distributed via app stores, a touch-first interface, or use of device capabilities (camera, location, notifications, biometrics, etc.).

**Declaration format:**
> *"This sounds like a mobile app. I'll include mobile-specific questions about platform, offline behavior, device permissions, and navigation alongside the standard ones. If this is a web or desktop tool, correct me now."*

#### Additional platform declaration

Platform reach and distribution are product constraints and belong in the combined opening restatement when already stated. Ask only for missing constraints that materially affect delivery:

- Which users or managed devices must be supported: iOS, Android, or both?
- Is distribution public through an app store, private/internal, or undecided?
- Are there explicit schedule, maintenance-capacity, device-integration, or existing-team constraints?

Native versus cross-platform is normally an implementing-agent decision informed by those constraints. Present it to the human only when the choice changes a user-visible capability, delivery commitment, or accepted maintenance trade-off.

#### Additional high-coupling decisions

Add these to the Step 4 checklist when the Mobile extension is active:

| Decision | Why it's high-coupling |
|---|---|
| Platform reach and distribution (iOS / Android / both; public / private) | Determines supported users, device capabilities, and delivery constraints |
| Offline and connectivity model | Determines state architecture and sync strategy |
| Authentication pattern | Biometric, social login, Apple/Google sign-in, email — each has distinct UX and implementation implications |
| Backend sync strategy | If there is a server: how data moves, how conflicts are resolved |
| Permissions model | Which device capabilities are required vs. optional; affects first-run UX and store compliance |

#### Additional elicitation probes

Ask these in domain language during the iteration loop:

- *"If someone opens this app and has no signal, what should happen — does it still work, show what it last had, or ask them to reconnect?"*
- *"Does the app need access to anything on the device — camera, location, contacts, notifications?"*
- *"Will users need to sign in? What happens if they get a new phone or log out?"*
- *"Is there information the app stores that would be a problem if someone else picked up the phone and opened it?"*

#### Screen flow diagram

After functional requirements are established and before the pre-synthesis audit, the AI generates a Mermaid flowchart representing the navigation model: screens as nodes, user actions or transitions as labeled edges.

**Complexity cap:** If the app has more than 8 screens, do not generate a single diagram. Break the flow into named sub-diagrams by logical section (e.g., Onboarding, Core Flow, Settings). Review them together in the decision brief unless one subflow contains a blocking ambiguity. A diagram that cannot be read comfortably will be rubber-stamped, not audited.

Each diagram is presented with a specific walkthrough prompt — not "does this look right?" but:

> *"Here's what I think [section] looks like to navigate. Walk through it as if you're a new user — start at the beginning and tell me if anything is missing, doesn't make sense, or goes somewhere unexpected."*

Corrections are incorporated before final decision-brief confirmation. The resulting sub-diagrams are included in the spec artifact as the confirmed navigation model; do not create a separate confirmation loop for every diagram.

Example structure (not content):

```mermaid
flowchart TD
    A([Launch]) --> B[Onboarding]
    B --> C[Sign In]
    C --> D[Home]
    D --> E[Detail View]
    D --> F[Settings]
    E --> D
    F --> G[Edit Profile]
    G --> F
```

#### Additional artifact sections

Insert these into the spec artifact when the Mobile extension is active:

---

**[MOBILE] Platform & Distribution**

*(Insert after Section 1 — Problem Statement, before Section 2 — Glossary)*

| | |
|---|---|
| **Platform** | iOS / Android / Both |
| **Build approach** | Native / Cross-platform [framework] |
| **Distribution** | App Store / Play Store / Enterprise / TestFlight |
| **Minimum OS version** | [if known or constrained] |

---

**[MOBILE] Screen Flow**

*(Insert after Section 5 — Functional Requirements)*

Navigation model confirmed with human during elicitation. Screens are nodes; labeled edges are user actions or system transitions.

```mermaid
[diagram]
```

**Screens:**
- [Screen name]: [primary purpose, one line]

---
