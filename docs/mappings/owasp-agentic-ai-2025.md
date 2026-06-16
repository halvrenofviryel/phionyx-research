# Phionyx ↔ OWASP Agentic AI Threats v1.0 (2025)

> **Mapping target:** OWASP Agentic AI — Threats and Mitigations v1.0 (Feb 2025)
> Authoritative source: <https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/>
>
> **Phionyx version mapped:** v0.3.0 · DOI [10.5281/zenodo.20027535](https://doi.org/10.5281/zenodo.20027535)
> **Pipeline contract:** v3.8.0 (46 canonical blocks)
> **Mapping last verified:** 2026-05-04

This document maps each of the 15 OWASP Agentic AI threat categories to the Phionyx Core component(s) that address it, the coverage level, and the artifact(s) that let an external reviewer verify the claim. Where Phionyx does **not** cover a threat, this is stated explicitly — the document is a coverage map *and* a gap analysis.

> **Scope statement.** This is an **evidence mapping**, not legal compliance certification. Phionyx is not an accredited security or AI-safety authority. Adopting Phionyx does not by itself satisfy any regulatory or contractual security obligation; it produces artifacts that an auditor or compliance officer can use as inputs to such an assessment. See [`/evidence`](https://phionyx.ai/evidence) for the broader claims framework.

---

## Coverage summary

| ID | Threat | Coverage | Primary Phionyx component |
|----|--------|----------|----------------------------|
| T1 | Memory Poisoning | Partial | `memory/`, `meta/knowledge_boundary`, `audit_layer` |
| T2 | Tool Misuse | Partial | `pipeline/blocks/action_intent_gate`, `RBAC`, `kill_switch` |
| T3 | Privilege Compromise | Partial | `governance/rbac`, `CapabilityProfile`, `audit_layer` |
| T4 | Resource Overload | Partial | `pipeline/blocks/entropy_amplitude_pre_gate`, ExecutionGuard, `kill_switch` |
| T5 | Cascading Hallucination Attacks | Partial | `cep_evaluation` (CEP), `confidence_fusion`, `response_revision_gate` |
| T6 | Intent Breaking & Goal Manipulation | Partial | `intent_classification`, `goal_decomposition`, `goal_evaluation` |
| T7 | Misaligned & Deceptive Behaviours | Partial | `deliberative_ethics`, `ethics_pre_response`, `behavioral_drift_detection` |
| T8 | Repudiation & Untraceability | **Full** | `audit_layer` (Ed25519 hash chain), `AuditRecord` v4 contract |
| T9 | Identity Spoofing & Impersonation | Partial | Participant-scoped state, `cognitive_envelope` |
| T10 | Overwhelming Human-in-the-Loop | Partial | `governance/human_in_the_loop` (priority + expiry) |
| T11 | Unexpected RCE & Code Attacks | **Gap** | Out of scope — addressed by deployment infrastructure |
| T12 | Agent Communication Poisoning | Partial | `contracts/envelopes/AgentMessageEnvelope` (typed, validated) |
| T13 | Rogue Agents in Multi-Agent Systems | **Gap** | Single-instance scope only in v0.3.0 |
| T14 | Human Attacks on Multi-Agent Systems | **Gap** | Single-instance scope only |
| T15 | Human Manipulation | Partial | `cep_evaluation`, `ethics_post_response` |

**Score:** 1 Full · 10 Partial · 4 Gap. The four gaps are honest: three of them require multi-agent or distributed-deployment work that v0.3.0 has not done, and the fourth (T11) is intentionally outside the runtime's scope.

---

## How to read each entry

Every threat below follows the same structure:

- **OWASP description** — one-line paraphrase of the OWASP threat statement.
- **Phionyx mechanism** — the specific block, contract, or governance feature that addresses the threat.
- **Coverage** — *Full* (the threat surface is closed in v0.3.0), *Partial* (mitigation present but not exhaustive), or *Gap* (out of scope or future work).
- **Evidence** — the artifact a reviewer can read or run to confirm.
- **What's still missing** — explicit residual risk, even on Partial / Full rows. This is on purpose; "Full" never means "no residual risk", only "Phionyx covers the named OWASP threat surface".

---

## T1 · Memory Poisoning

**OWASP description.** Adversarial inputs cause persistent contamination of an agent's memory, biasing future retrievals and decisions.

**Phionyx mechanism.**
- `phionyx_core/memory/consolidation.py` — impact-weighted eviction; a poisoned high-novelty item still has to clear a coherence and Φ check before it enters durable memory.
- `phionyx_core/meta/knowledge_boundary.py` — block 16 in the canonical pipeline; rejects retrieval requests for content outside the participant's declared knowledge boundary.
- `phionyx_core/pipeline/blocks/audit_layer.py` — every memory write is hash-chained, so post-incident replay can identify the poisoning event.
- Non-Persistence Doctrine — derived metrics (Φ, R, trust) are *never* written. Poisoning attacks aimed at these channels have no persistence surface.

**Coverage.** Partial.

**Evidence.**
- Tests: `tests/core/test_consolidation*.py`, `tests/core/test_knowledge_boundary*.py`
- Schema: `phionyx_core/contracts/v4/audit_record.py`
- Reproducibility: `python scripts/make_reproducibility_pack.py` produces `audit_chain_example.json`.

**What's still missing.** No active anomaly detection on the *content* of memory writes; the system trusts the upstream input gate to catch malicious content. A poisoned item that passes `input_safety_gate` and looks coherent will be stored. This is an explicit gap; an upstream content-classification adapter is recommended for hostile environments.

---

## T2 · Tool Misuse

**OWASP description.** An agent invokes a tool with arguments that violate scope, intent, or organisational policy.

**Phionyx mechanism.**
- `phionyx_core/pipeline/blocks/action_intent_gate.py` — every action-intent must include `source_goal_id` and `ethics_decision_id`; unsignalled actions are rejected at the contract level (Pydantic `call-arg` enforcement).
- `phionyx_core/governance/rbac.py` — capability-based access checks; tools are bound to RBAC roles.
- `phionyx_core/governance/kill_switch.py` — fail-closed shutdown when ethics_max_risk > threshold or behavioural drift exceeds bound.
- `CapabilityProfile` (per-deployment) declares which tools each block can invoke; enforced architecturally, not by convention.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/contracts/v4/action_intent.py`
- `tests/core/test_action_intent*.py`, `tests/core/test_rbac*.py`
- Reproducibility pack: `audit_chain_example.json` (showing a kill-switch trigger blocking an unsafe action).

**What's still missing.** Tool registries themselves are not validated by Phionyx Core — that is the bridge layer's responsibility. Phionyx enforces *whether* an action can fire; it does not validate that the named tool *is* what it claims to be (supply-chain concern; see T11).

---

## T3 · Privilege Compromise

**OWASP description.** An agent acquires permissions beyond its assigned scope through prompt injection, role spoofing, or capability inheritance.

**Phionyx mechanism.**
- `phionyx_core/governance/rbac.py` — capability tokens, not free-text role labels. Tokens are issued by a trusted authority and validated each gate decision.
- `audit_layer` records the capability set in effect at every gate decision; privilege escalation produces a hash-chain entry.
- `participant-scoped state` — per-participant cognitive isolation prevents one participant's elevated state from affecting another's gate decisions.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/governance/rbac.py`
- `tests/core/test_rbac*.py`
- Audit chain example demonstrates a `policy_bypass` audit entry when a capability check fails.

**What's still missing.** Phionyx assumes the authority that *issues* capability tokens is honest. If the issuer itself is compromised (e.g., a bridge-layer auth service), Phionyx cannot detect it. This is consistent with how every capability system (UNIX users, IAM roles, JWT) works — but it is a gap to disclose explicitly.

---

## T4 · Resource Overload

**OWASP description.** An adversary forces an agent to consume disproportionate compute, memory, or external API budget — denial of service via the agent itself.

**Phionyx mechanism.**
- `phionyx_core/pipeline/blocks/entropy_amplitude_pre_gate.py` — block 14; rejects inputs whose computed entropy or amplitude fall outside operational bounds before any downstream LLM call is made.
- ExecutionGuard / circuit breaker pattern in `pipeline/blocks/behavioral_drift_detection.py` — opens when drift signal exceeds threshold; subsequent calls short-circuit.
- `kill_switch.py` consecutive_drift_count trigger fires after sustained anomaly (default 5 turns).

**Coverage.** Partial.

**Evidence.**
- `tests/core/test_entropy_amplitude_pre_gate*.py`
- `tests/core/test_execution_guard*.py`
- Reproducibility pack: `benchmark_results.json` shows per-call cost (~µs) so deployments can size budgets.

**What's still missing.** Phionyx does not provide a global rate limiter or quota system — it provides per-turn safety gates and per-deployment budgets via configuration. A truly distributed budget enforcer (across many participants in real time) is bridge-layer territory. Distributed scenarios are explicitly out of scope for v0.3.0.

---

## T5 · Cascading Hallucination Attacks

**OWASP description.** Hallucinations from one step propagate as inputs into subsequent steps, compounding error rate non-linearly.

**Phionyx mechanism.**
- `pipeline/blocks/cep_evaluation.py` — the Conscious Echo Proof engine runs four pattern detectors (identity confabulation, distress-language mimicry, repetitive echo loops, self-diagnostic assertions) on every generated narrative *before* it is returned or fed back into state.
- `pipeline/blocks/confidence_fusion.py` — block 39; produces a `w_final` calibrated confidence score and `t_meta` meta-cognitive trust value. Outputs flagged at low `t_meta` get routed to `response_revision_gate` for damp/rewrite/regenerate/reject.
- `pipeline/blocks/response_revision_gate.py` — closes the in-turn loop. A hallucination caught here never makes it into the audit-recorded final response.

**Coverage.** Partial.

**Evidence.**
- `tests/core/test_cep_evaluation*.py` (46 unit tests covering all four detectors)
- `tests/core/test_response_revision_gate*.py`
- Reproducibility pack: `governed_response_example.json` includes `t_meta`, `confidence_score`, and revision_directive fields.

**What's still missing.** CEP detects pattern-level distortion in the *output text*; it does not score factual accuracy of claims. A coherent, well-structured falsehood passes CEP unless the LLM also produces one of the four distortion patterns. This is documented in the README "Known limitations" and the Evidence Matrix (Φ-as-experimental row).

---

## T6 · Intent Breaking & Goal Manipulation

**OWASP description.** An adversary causes the agent to silently substitute its declared goal for an attacker-supplied one (goal hijack, sub-goal injection).

**Phionyx mechanism.**
- `pipeline/blocks/intent_classification.py` (block 17) — explicit intent extraction; all downstream blocks read `selected_intent` from context, not raw user text.
- `pipeline/blocks/goal_decomposition.py` + `goal_evaluation.py` — every action_intent carries a `source_goal_id` (Pydantic-required field). An action without a registered source goal is rejected at contract validation time.
- `phionyx_core/planning/goal_persistence.py` — goals are first-class records with conflict detection (`get_active_goals`, conflict pair detection). A new attacker-supplied goal that conflicts with an existing active goal fires a conflict alert.

**Coverage.** Partial.

**Evidence.**
- `tests/core/test_goal_persistence*.py`
- `tests/core/test_intent_classification*.py`
- Schema: `phionyx_core/contracts/v4/action_intent.py` (source_goal_id is non-optional)

**What's still missing.** Goal conflict detection is structural — it catches contradictions between registered goals. A *novel* goal that doesn't contradict anything still passes. Detecting "this is a hijacked goal that no human ever requested" requires an external attestation channel not currently in scope.

---

## T7 · Misaligned & Deceptive Behaviours

**OWASP description.** The agent produces outputs that satisfy a narrow optimisation target while violating broader operator intent (deceptive alignment, sycophancy, gaming).

**Phionyx mechanism.**
- `phionyx_core/governance/deliberative_ethics.py` — four-framework ethical reasoning (utilitarian, deontological, virtue, care). Each output is scored against all four; sustained imbalance triggers `behavioral_drift_detection`.
- `pipeline/blocks/ethics_pre_response.py` (block 18) and `ethics_post_response.py` — pre- and post-generation ethical checks both required to pass. EthicsVector (harm_risk, manipulation_risk, attachment_risk, boundary_violation_risk) is recorded per-turn.
- `pipeline/blocks/behavioral_drift_detection.py` (block 23) — tracks deviation from baseline behavioural metrics across turns. Triggers HITL queue or kill_switch when consecutive_drift_count exceeds threshold.
- Φ (cognitive coherence) is never stored — denying any optimisation pressure to game the metric.

**Coverage.** Partial.

**Evidence.**
- `tests/core/test_deliberative_ethics*.py`
- `tests/core/test_behavioral_drift*.py`
- Audit chain example shows an ETHICS_CRITICAL kill-switch trigger from `ethics_max_risk = 0.99`.

**What's still missing.** Deceptive alignment in the LLM's *internal* representation cannot be detected from outputs alone. Phionyx detects *behavioural* misalignment (what the agent does over time) — not latent intent. This is the same fundamental limitation every output-monitoring system has; it is documented in the README "Known limitations".

---

## T8 · Repudiation & Untraceability

**OWASP description.** After-the-fact, neither the agent nor any observer can prove which inputs led to which actions, or detect tampering.

**Phionyx mechanism.**
- `pipeline/blocks/audit_layer.py` (block 44) — every turn produces an `AuditRecord` with prev/link hash chain. Records are append-only by design.
- `phionyx_core/contracts/v4/audit_record.py` — Ed25519 signature on each record; any post-hoc edit invalidates the chain.
- Append-only contract: no API path mutates a recorded `AuditRecord`. This is enforced by both the schema (`model_config = ConfigDict(frozen=True)`) and the policy doc.

**Coverage.** **Full** for in-scope claims (single-instance, append-only chain over the deterministic pipeline).

**Evidence.**
- `tests/core/test_audit_record*.py`, `tests/core/test_audit_layer*.py`
- `tests/contract/test_audit_chain_integrity.py`
- Reproducibility pack: `audit_chain_example.json` — verifiable hash chain over a real KillSwitch event sequence.

**What's still missing.** "Full" here means "the named OWASP threat surface is closed under the documented threat model". If an attacker has root on the host running Phionyx, they can replace the binary that produces the chain — Phionyx assumes a trusted process. Distributed, multi-host audit consensus is future work.

---

## T9 · Identity Spoofing & Impersonation

**OWASP description.** A second party pretends to be a participant the agent has previously trusted; or one participant influences another's session.

**Phionyx mechanism.**
- Participant-scoped state — per `participant_id` cognitive isolation. State vectors, memory traces, and goal records are never shared across participants at the runtime level.
- `phionyx_core/contracts/envelopes/agent_envelope.py` — `AgentMessageEnvelope` carries `sender_participant_ref` and `receiver_participant_ref` with type tags (HUMAN, AI_AGENT, SYSTEM). Messages without a valid pair are rejected at envelope validation.
- Cognitive envelopes are typed and signed, preventing replay across sessions.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/contracts/participants.py`
- `tests/core/test_participant_isolation*.py`
- `tests/contract/test_envelope_validation*.py`

**What's still missing.** Phionyx does not authenticate participants — it consumes whatever `participant_id` the bridge layer asserts. Participant authentication, credential rotation, and multi-factor flows are the bridge layer's responsibility (and outside the runtime's scope).

---

## T10 · Overwhelming Human-in-the-Loop

**OWASP description.** The HITL queue is flooded faster than humans can review, causing rubber-stamping or abandonment of the safety mechanism.

**Phionyx mechanism.**
- `phionyx_core/governance/human_in_the_loop.py` — every queue entry has `priority` (critical/high/normal) and `expires_at`. Expired entries auto-promote to `kill_switch.evaluate()` rather than silently approve.
- Queue depth is a tracked metric; drift detection treats sustained queue growth as a behavioural anomaly (T7-style alert).
- HITL is fail-closed: an unreviewed expired action does **not** execute by default. The deployment must explicitly opt into "auto-approve on timeout" to invert this default.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/governance/human_in_the_loop.py`
- `tests/core/test_human_in_the_loop*.py`
- `phionyx_core/monitoring/human_approval.py`

**What's still missing.** Human cognitive load is not measured by Phionyx — only the queue is. A reviewer who gets 5 high-priority items and approves them all in 2 seconds will pass Phionyx's checks. Reviewer-side workload management is operational, not architectural.

---

## T11 · Unexpected RCE & Code Attacks

**OWASP description.** The agent or its hosting infrastructure executes attacker-controlled code (deserialisation attacks, sandbox escape, dependency confusion).

**Phionyx mechanism.** **None at runtime layer.**

**Coverage.** **Gap (out of scope).** RCE is a deployment-infrastructure concern. Phionyx does not eval, exec, pickle, or shell out on user input; this was explicitly verified in the v0.3.0 security audit (PR #54). But Phionyx itself running inside a vulnerable container, or imported into a process that is, cannot be defended by Phionyx.

**What it does provide:**
- `pip-audit`-clean dependencies (verified in v0.3.0 hardening).
- No `shell=True` subprocess calls anywhere in `phionyx_core/`.
- Workflow permissions hardened (top-level read-only, SHA-pinned third-party action) so the supply chain into PyPI/Zenodo is tighter than industry default.

**Recommended companion controls.**
- Run Phionyx inside a hardened container image with a SBOM.
- Pin Phionyx by hash, not by version label, in production.
- Use the published `[reproducibility_pack_v0.3.0.zip]` SHA-256 as the install-time integrity check.

---

## T12 · Agent Communication Poisoning

**OWASP description.** Inter-agent messages are forged, tampered with, or injected with hostile content.

**Phionyx mechanism.**
- `phionyx_core/contracts/envelopes/agent_envelope.py` — `AgentMessageEnvelope` is a Pydantic-validated typed envelope with required fields: `protocol`, `sender_participant_ref`, `receiver_participant_ref`, `trace_id`, `turn_id`, `message_id`, `nonce`, `ttl_seconds`. Every field is strictly typed.
- `cognitive_metrics` field on the envelope carries Φ, entropy, etc. signed alongside the payload.
- `envelope_validator.py` and `causal_chain_tracker.py` check envelope integrity and trace continuity.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/contracts/envelopes/agent_envelope.py`
- `phionyx_core/contracts/envelopes/envelope_validator.py`
- `phionyx_core/contracts/envelopes/causal_chain_tracker.py`
- `tests/contract/test_envelope_validation*.py`

**What's still missing.** Envelope schemas guarantee *structural* validity; cryptographic integrity (Ed25519 over the envelope hash) is wired but the bridge layer must propagate signatures across hops. Multi-agent end-to-end auth is in scope for v0.4+, not v0.3.0.

---

## T13 · Rogue Agents in Multi-Agent Systems

**OWASP description.** A compromised agent in a swarm acts maliciously while passing identity / health checks at the swarm level.

**Phionyx mechanism.** **None for v0.3.0.**

**Coverage.** **Gap (single-instance scope).** Phionyx v0.3.0 is documented and tested only in single-instance deployments. The architecture has been designed with multi-agent containment in mind (participant-scoped state, typed envelopes, audit chains), but multi-agent reputation, peer-attestation, and quarantine flows are future work.

**What we do say honestly:**
- The in-repo documentation explicitly scopes claims to single-instance.
- The Evidence Matrix marks all multi-agent integration claims as **planned**.
- The internal roadmap lists "Multi-tenant production deployment" as out-of-scope for v0.3.x.

---

## T14 · Human Attacks on Multi-Agent Systems

**OWASP description.** A malicious human exploits the multi-agent framework itself — e.g., by submitting attacker-crafted "agent identity" claims into the swarm.

**Phionyx mechanism.** **None for v0.3.0.** Same scope as T13.

**Coverage.** **Gap.**

---

## T15 · Human Manipulation

**OWASP description.** The agent influences its human user(s) in ways that shift their behaviour against their own interests (sycophancy, flattery, dependency creation, dark-pattern dialogue).

**Phionyx mechanism.**
- `pipeline/blocks/cep_evaluation.py` — distress-language and self-diagnostic detectors specifically catch dependency-creating dialogue patterns ("I'm always here for you", excessive sycophancy, identity confabulation).
- `phionyx_core/governance/deliberative_ethics.py` — `EthicsVector.attachment_risk` and `manipulation_risk` are explicit risk axes scored every turn.
- `pipeline/blocks/ethics_post_response.py` — second pass after generation; high attachment/manipulation risk triggers revision or block.

**Coverage.** Partial.

**Evidence.**
- `tests/core/test_cep_evaluation*.py` (mirror-self, distress-language tests)
- `tests/core/test_deliberative_ethics*.py` (4-framework ethics)
- `phionyx_core/contracts/v4/ethics_decision.py`

**What's still missing.** Long-horizon manipulation (where each individual turn looks innocent but the cumulative pattern is harmful) is harder than per-turn detection. `behavioral_drift_detection` mitigates *some* of this by tracking trajectories, but adversarial long-horizon influence is an open research problem, not a closed one.

---

## Gap analysis

The four explicit gaps:

| ID | Threat | Why gap | When closed |
|----|--------|---------|-------------|
| T11 | Unexpected RCE | Out of scope — deployment infrastructure layer | Never (correct boundary) |
| T13 | Rogue Agents (multi-agent) | v0.3.0 is single-instance | v0.4+ on roadmap |
| T14 | Human Attacks on Multi-Agent | v0.3.0 is single-instance | v0.4+ on roadmap |
| T6 (deep) | Latent goal hijack | Output-monitoring fundamental limit | Open research problem |

The Partial entries each carry a "What's still missing" line; that line is the residual-risk register for an auditor.

---

## How to use this mapping

For an auditor:
1. Pick a threat row.
2. Click the evidence file paths to read the implementation.
3. Run the reproducibility command (most are `pytest tests/core -k <area>`).
4. Cross-check against the [Evidence Matrix at /evidence](https://phionyx.ai/evidence) for the same artifacts.
5. The "What's still missing" line is the *intentional* residual risk — record it in the audit working paper.

For a deployment team:
1. The Coverage column tells you where you must add controls *outside* Phionyx (Gap rows = bridge-layer / deployment work).
2. The Phionyx mechanism column tells you which `CapabilityProfile` settings affect that threat.
3. None of the "Partial" rows can be promoted to "Full" by configuration alone — they require external companion controls (auth, network, content classifiers).

---

## Versioning

This mapping is dated. Future versions will be cut on:
- Phionyx feature changes that move a row's coverage level.
- Updates to the OWASP Agentic AI threat list.
- Independent third-party validation that re-classifies a coverage column.

**Companion mappings:** NIST AI RMF and EU AI Act mappings ship in this same `docs/mappings/` directory.

**License.** This mapping inherits the repo licence (AGPL-3.0). The OWASP threat names and descriptions are © OWASP Foundation, used under their content licence.
