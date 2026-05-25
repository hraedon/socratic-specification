# Re-Evaluation: Socratic Specification Process (v4)

The v4 revisions represent a major leap from a "conversation guide" to a full "Product Management Framework." It addresses the complexities of multi-phase delivery and platform-specific nuances (starting with Mobile).

## 1. Resolved: The "Semantic Drift" Risk
The addition of a **Glossary** (Step 3, Point 6 and Section 2) directly addresses the risk of terms shifting meaning over time. By formalizing definitions early and auditing them for consistency, the process ensures that "user," "customer," and "admin" remain distinct and stable concepts throughout the elicitation.

## 2. Resolved: The "Implementation Handoff" Gap
The **MVP Definition** (Step 3, Point 7) and **Work Decomposition** (Section 12) bridge the gap between "what we want" and "how we build it." By forcing a discussion on the "minimum useful version," the process helps the human prioritize value and provides the implementing agent with a logical starting point that isn't just "everything at once."

## 3. Improved: Transparency in the Audit
The **Pre-Synthesis Consistency Audit** (Step 5) is no longer a "black box." By explicitly stating what was checked (N requirements, M assumptions, etc.), it gives the human a "confidence score" and makes the limits of the AI's attention span visible. This is a sophisticated way to manage the inherent limitations of LLM context windows.

## 4. Major Addition: Process Extensions & Mobile
The **Mobile Extension** is a masterclass in platform-specific elicitation. It correctly identifies that mobile isn't just "a small website" but involves distinct high-coupling decisions (Offline behavior, Permissions, Sync strategy).
- **Mermaid Screen Flow:** This is a high-leverage addition. Visualizing navigation as a flow chart is the best way to catch "dead ends" or missing logic that a text-only spec might hide.
- **Intent Signals in Handoff:** Linking Section 15 (Intent Signals) back to Section 10 (High-Coupling Decisions) creates a "Hard Link" that forces the implementing agent to consider the "spirit" of the vibe when making architectural choices.

---

## Remaining / New Adversarial Observations

### 1. The "MVP vs. Architecture" Conflict
Step 3, Point 7 (MVP) and Section 12 (Work Decomposition) acknowledge that MVP is about value, not implementation order.
- **Risk:** A non-technical human might insist on an MVP that is architecturally impossible to build in isolation without first building "Phase 2" infrastructure.
- **New Critique:** The AI must be more aggressive in flagging "Architectural Prerequisites" during the MVP definition. If the MVP requires a complex sync engine, the "simple" version isn't actually simple.

### 2. The "Mobile Default" Bias
The Mobile Extension asks about "Native or Cross-platform."
- **Risk:** Most non-technical users have no idea which one they need. The AI's "Option Generation" (Step 3, Point 4) will heavily influence this choice.
- **Critique:** The choice between Native and Cross-platform is often a business/budget decision disguised as a technical one. The AI needs a probe for "Team size" or "Budget for maintenance" to give a better recommendation.

### 3. The "Diagram Feedback" Loop
The Mermaid flowchart is confirmed via a "walkthrough prompt."
- **Risk:** Mermaid diagrams can become unreadable quickly as complexity grows.
- **Critique:** If the diagram becomes a "spaghetti mess," the human will just say "it looks fine" to move on. There should be a "Complexity Cap" or a requirement to break large flows into sub-diagrams.

### 4. The "Implicit Phase 1" Assumption
Section 12 (Work Decomposition) assumes that "Phase 1" is synonymous with "MVP."
- **Risk:** Sometimes "Phase 1" is "Set up the database and auth," which provides zero user value (not MVP) but is a prerequisite for everything else.
- **Critique:** The process should distinguish more clearly between **"Value Phasing"** (what the user sees) and **"Implementation Phasing"** (what the agent builds).

---

# Independent Validation: Perplexity Review (v5)

A separate adversarial review by Perplexity independently raised three concerns after the v4→v5 iteration. All three map directly to issues Gemini had already identified in the v4 critique and that were addressed in v5.

## Concerns Raised

### 1. MVP vs. Architecture Conflict
> "A human-declared MVP can be architecturally impossible to build in isolation. The process needs stronger Architectural Prerequisite flagging before finalizing MVP scope."

**Status: Already resolved in v5.** Step 3 item 7 now requires the AI to check MVP FRs against high-coupling decisions immediately after MVP declaration, surfacing any architectural prerequisites as a forced choice before recording the MVP definition.

### 2. Value Phasing vs. Implementation Phasing
> "The current Work Decomposition conflates 'what the user sees first' with 'what the agent builds first,' which breaks down when Phase 1 is purely infrastructure with zero user-visible value."

**Status: Already resolved in v5.** Section 12 was restructured into two explicitly separated and labeled parts: Value Phases (human-owned, user-visible delivery) and Implementation Phasing (agent-owned, including invisible infrastructure). The agent is required to surface conflicts between declared value phases and build constraints before writing code.

### 3. Diagram Complexity Cap
> "As screen flows grow, Mermaid diagrams become unreadable and humans start rubber-stamping them. There's no mechanism to enforce sub-diagram decomposition."

**Status: Already resolved in v5.** The mobile extension now includes an explicit 8-screen complexity cap. Above that threshold, the AI must break the flow into named sub-diagrams by logical section, each confirmed separately. The rationale is stated in the process: a diagram that cannot be read comfortably will be rubber-stamped, not audited.

## Significance

Independent convergence on the same issues by two different reviewers (Gemini and Perplexity) validates that these were genuine gaps worth addressing — not reviewer-specific concerns. The v5 fixes are confirmed as load-bearing.

---

# Adversarial Review: Debate 005 (DeepSeek v4-pro)

*Originally planned via Gemini 3 Flash; substituted due to a persistent opencode↔Gemini tool-call error (`Function call is missing a thought_signature`). DeepSeek v4-pro chosen as a third distinct lineage from Kimi (author) and Claude (caller).*

## 1. Location: Fold into Step 5, don't create Step 5.5

The proposal positions this as a new half-step, but the process already has fragmentation risk — debate 004 is at Step 5+, and now 005 wants 5.5. Step 5 is described as "a full pass over all accumulated answers, assumptions, and requirements." Expanding that checklist to include composition checks is cleaner than adding a sibling step. The proposal's argument that "Step 5 does not catch these" is true of the *current* Step 5 description, but the fix is broadening Step 5's scope, not layering on new steps. If every new check gets its own half-step the process becomes unteachable.

**The decomposition-tool alternative** has more merit than the proposal concedes. sf2 already has mechanical gates; a structural "call-graph coverage" check in the decomposer would be more reliable than an LLM self-review. But adding it at spec time is still defensible — just not as a separate headline step.

## 2. Five checks: keep 1 and 4, weaken 2, drop 5

**Check 1 (lifecycle wiring) and check 4 (read-path symmetry) are the high-signal, genuinely novel additions.** Nothing in the current process asks "who reads this table" or "when does this start running." These should be kept.

**Check 2 (configuration provenance)** is on the right track but over-specified. The spec should ask "is config declared as deployment-time configurable?" — not prescribe *how* (env vars vs. config file vs. DB). The proposal's examples demand mechanism-level answers at a stage where deployment choices aren't made. This risks premature architectural coupling.

**Check 3 (data-to-UI coverage)** overlaps substantially with Step 5's existing surface area. If a repository has `delete()` and no FR or AC exercises it, that's a semantic inconsistency, not a novel composition gap. It would be caught by a properly-scoped Step 5.

**Check 5 (validation call-site coverage) is the weakest and should be dropped.** "Every validation or business-rule function must have an AC calling it" would fire on every utility validator (`is_valid_email`, `sanitize_input`) used internally by multiple FRs. The false-positive rate on generic utility functions will be high, and the proposal's AI-judgment mitigation is circular — the same model that missed the composition gap during generation is asked to distinguish utility functions from domain validators at audit time.

## 3. Domain-language tension is unaddressed

The five checks are framed in implementation terms (lifecycle hook, repository method, config dataclass). A non-technical human cannot answer "where does `AlertConfig` come from at runtime." The proposal says the AI should "ask one follow-up question in domain language" but provides zero guidance on that translation. This is the same translation-risk problem that debate 004 addresses, now at the composition layer. Example: "When would you set the email address for alerts — is there a settings page in the app, or would someone provide it when setting the system up?" — that's the domain-language version. The proposal needs a concrete translation table, not a hand-wave.

## 4. Same-AI self-review is insufficient; cross-model audit is needed

The proposal, debate 004, and Step 5 all rely on the same AI that produced the spec also auditing it. For 004's pattern-matching on absolutes and missing state machines, this is tolerable. For 005's requirement to detect "this function has no caller anywhere in the spec," it is not. The model that omitted the call site during generation will not notice the omission during review — self-review is systematically worse at detecting its own errors than at detecting errors in other output. If this check stays, it should be run by a different model instance, or better, as a structural parse (symbol table → list of unreferenced export symbols). The proposal omits this requirement entirely.

## 5. Decomposition vs. Socratic ownership: both are right for different layers

The proposal asserts "the spec should own the system narrative." This is right for *connectivity* questions: "does anything read scan_history?" is a spec-level concern and should be answered at Socratic time. But the proposal overreaches on *mechanism* questions: "does the scheduler start at FastAPI boot or on first request?" depends on the framework and deployment model, neither of which is known at Socratic time. The spec should say "certificate checking runs continuously" without deciding whether that's a lifespan hook, a cron job, or a sidecar. The five checks mix these two layers; they need to be separated.

## 6. Does it catch cert-watch? Mostly yes, with one weak link

- **scheduler never wired** → Check 1 catches this cleanly.
- **AlertConfig no runtime source** → Check 2 catches it, but demands mechanism-level answers the spec shouldn't prescribe.
- **no delete UI** → Check 3 catches this, but it's redundant with an expanded Step 5 consistency check.
- **scan_history never displayed** → Check 4 catches this cleanly.
- **validate_chain_order never called** → Check 5 claims to catch this, but the model that failed to notice the missing call site during generation must now notice it during review. Unreliable. A mechanical "count references" check on the spec text would be more dependable.

Net: four of five real gaps are caught by checks 1-4 alone. Check 5 adds risk without adding coverage.

## 7. What the proposal got right

The "system narrative" framing is correct and worth keeping. Local completeness + global disconnection is a real failure class that the current process does not address. Read-path symmetry and lifecycle wiring are genuinely novel probes. The MVP-scope gating (only flag items in MVP scope to avoid false positives on future-phase modules) is sensible and shows the author thought about over-flagging. The empirical trigger — two independent implementations producing identical gaps — is exactly the right standard for proposing a process change.

## Recommendation: **Accept with modifications**

1. **Fold into Step 5**, not a separate Step 5.5.
2. **Keep checks 1 (lifecycle wiring) and 4 (read-path symmetry)** as-is. These are high-signal and novel.
3. **Weaken check 2** to "is config declared as deployment-configurable?" without prescribing mechanism.
4. **Drop check 3** — it's redundant with an expanded Step 5.
5. **Drop check 5** — false-positive risk on utility functions is too high.
6. **Add cross-model requirement**: the composition audit must be run by a different model instance, or replaced with a structural symbol-reference parse.
7. **Add domain-language translation guidance** for each retained check — a two-column table mapping the implementation question to the domain-language question the human actually hears.
