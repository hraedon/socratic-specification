# Guardrail Primitives (Family A)

**Status: PROPOSED — pending adversarial review.**

Four reusable primitives that encode the library's recurring pitfalls. Each is in
the established extension shape (activation → Step 4 → Step 3 → Step 5 → Step 7) so
it drops into the base process the same way the Mobile extension does. Archetypes
compose these; guardrails also fire on their own signals independent of any
archetype.

The governing insight: an expert driver supplies these silently, so the base
process never had to ask. A non-expert driver supplies none of them. These are the
tacit knowledge, made into questions.

---

## G1 — Data hygiene (classification-first)

**Context (from the library):** every project that touches real data or ships to a
shared repo hit this. The costly, recurring failure is *real data or secrets
landing where they shouldn't* — in fixtures, logs, sample output, or the agent's
own context window. For **internal projects in a private repo**, public identifier
leakage (hostnames, domains) is a minor concern — a private ADO repo tolerates
internal names. What stays load-bearing is **keeping regulated data (PHI/PII,
records, live credentials) out of code, fixtures, logs, and agent context** —
which is the same audit/provenance concern that gates agent tools out of regulated
workplaces in the first place.

So this guardrail is **layered, classification-first**:

- **Primary layer — data classification.** What class of real data does this touch,
  and where is each class *allowed to appear*: in the running system, in committed
  artifacts/fixtures, in logs, in the agent's context window?
- **Secondary layer — identifier hygiene (light for private repos).** Live
  credentials never in artifacts; test constants named so they don't read as live
  secrets to a scanner. Internal hostnames/domains are acceptable in a private repo
  and are *not* scrubbed.

**Activation:** always-on whenever the system reads, stores, or emits real data, or
when an agent will be given real data during development. (For a regulated
workplace, effectively always.)

**Step 4 — high-coupling decisions added:**
- **Data-context boundary** — which data classes may enter the agent's context and
  the committed artifacts vs. must be represented only by synthetic/fixture stand-ins.

**Step 3 — probes (domain language):**
- *"What information does this touch that would be a problem if it showed up in a
  screenshot, a log file, or pasted into a code example?"*
- *"When we build and test this, can we use made-up stand-in data, or does testing
  it need to see the real records?"* (Surfaces whether real data must enter the
  agent's context — a blocking concern in a regulated shop.)
- *"Are there live passwords, keys, or tokens involved? Where do they come from?"*
  (Never into artifacts; provisioning belongs to G4.)

**Step 5 — audit checks added:**
- Every data input is classified, and each class has an explicit
  may-enter-artifacts / may-enter-agent-context answer.
- No fixture or example embeds a regulated data class; synthetic stand-ins are used.
- Test constants are named so a secret scanner won't false-positive (a recurring
  merge-blocker across the library).

**Step 7 — artifact section added:** *Data Classification*

| Data class | Example | May enter artifacts/fixtures? | May enter agent context? | Handling |
|---|---|---|---|---|
| … | … | yes / synthetic-only / no | yes / synthetic-only / no | … |

---

## G2 — Blast-radius / mutation posture

**Context (from the library):** the posture axis is flagged on nearly every tool,
almost verbatim — "issuance-path infra — NOT read-only" (acme), "first IN-PATH
tool" (sluice), "local-first read-only" / "flag don't probe" (gpo-lens,
adcs-lens), "read-only LDAP bind" (ad-steward). This single classification
determines the entire test strategy and blast radius, and it is currently implicit.
It is more load-bearing than the data model.

**Activation:** always-on. Every system has a posture.

**Step 4 — high-coupling decisions added (mandatory, cannot be left unclassified):**
- **Mutation posture** ∈ { read-only observer · mutates state it owns · mutates
  state other systems/people rely on · in-path / issuance (sits in a live request
  or issuance flow) }.

**Step 3 — probes (domain language):**
- *"When this runs, does it only look at things, or does it change something?"*
- *"If it changes something — does it change things it owns, or things other people
  or systems are relying on?"*
- *"If it did the wrong thing once, what's the worst that happens — and could you
  undo it?"*

**Step 5 — audit checks added:**
- Test strategy matches posture. Mutating posture ⇒ acceptance criteria exercise a
  reversible path (mutate → verify → roll back), because the library's positive
  live validations were only safe because mutations were reversible and reverted.
- In-path / issuance posture ⇒ failure-mode coverage (Section 8) is **blocking**,
  not optional.

**Step 7 — artifact:** posture stated in the Section 1 restatement, plus a
*Blast-radius* line (worst-case effect + reversibility).

---

## G3 — Environment matrix

**Context (from the library):** "green where I develop, red where it runs" recurs —
cert-watch (dev 3.12 / CI 3.13 / prod Windows + 3.14; first real Windows run caught
a cluster of CI-hidden bugs), agent-notes (an undeclared cross-project import was
green locally forever, failed only in CI), gpo-lens/adcs-lens (collectors run
PowerShell 5.1 on Windows while authored on Linux; **positive validation on the
real target caught two bugs the fixture path structurally hid**). The divergence
between authoring environment and deployment environment is a named bug reservoir,
not an implementation detail.

**Activation:** fires whenever the deployment context can differ from the authoring
context (near-always for anything deployed; skip pure throwaway scripts).

**Step 4 — high-coupling decisions added:**
- **Target runtime matrix** — OS, runtime/version, and privilege identity where the
  system does its real job, vs. where it is built and tested.

**Step 3 — probes (domain language):**
- *"Where does this actually run when it's doing its real job — your laptop, a
  server, someone else's machine, Windows?"*
- *"Is that the same kind of place you (or the agent) build and test it?"*

**Step 5 — audit checks added:**
- If dev-context ≠ deploy-context, emit it as a **named risk** (not silent), and
  require at least one acceptance criterion validated on the real target — because
  fixture/negative validation structurally hides decode and attribute-name bugs
  that only a positive run on the real thing surfaces.

**Step 7 — artifact section added:** *Environment Matrix* (authoring vs. target:
OS, runtime version, run-as identity) + the dev≠deploy risk note where applicable.

---

## G4 — Operations / provisioning

**Context (from the library):** debate 005 gave "is this deployment-configurable?"
The recurring pain is a layer past that — usage-dashboard (three deploy paths; an
`install.sh` self-reset hazard), cert-watch (installer had to learn
`web.config` **no-clobber on upgrade** — upgrades were silently destroying operator
config), acme-adcs-ra (runs as a **gMSA** in an IIS app pool; run-as identity was
load-bearing and ACL-gated), sluice (gitops relink + cache gotchas). Three things
recur and none are elicited today: the install/upgrade path, the run-as identity,
and the secret-provisioning surface.

**Activation:** fires for deployed services, installers, and long-running processes.
Skips libraries and one-shot CLIs.

**Step 4 — high-coupling decisions added:**
- **Upgrade path** — specifically whether an upgrade preserves operator-configured
  state (the no-clobber requirement).
- **Run-as identity** — a person's account vs. a dedicated service identity.
- **Secret/config provisioning surface** — where secrets and config come from at
  startup (as a *requirement*, not a mechanism).

**Step 3 — probes (domain language):**
- *"Once it's running and you ship an update, what happens to the settings someone
  already configured — do they survive, or do they get wiped?"*
- *"Who or what runs this — a person's login, or a dedicated account made just for
  it?"*
- *"When it starts up, where does it get its passwords and settings from?"*

**Step 5 — audit checks added:**
- An upgrade-preserves-configuration acceptance criterion exists (or no-clobber is
  explicitly out of scope with the risk accepted).
- Run-as identity is declared.
- Each secret has a provisioning statement — *that* the operator provides it, not
  *how* (env var vs. vault vs. OS store stays with the implementing agent, per the
  debate-005 layer rule).

**Step 7 — artifact section added:** *Operations* (install & upgrade path with the
no-clobber statement · run-as identity · secret/config provisioning surface).

---

## Layer discipline (carried from debate 005)

Every probe above elicits *intent or a requirement*, never a mechanism. The spec
says "the operator must be able to upgrade without losing configuration" and "this
runs under a dedicated service identity"; it never says "use Vault" or "gMSA." Any
guardrail probe that forces a mechanism at spec time has crossed the line the
composition audit was built to hold.
