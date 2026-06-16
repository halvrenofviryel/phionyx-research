# Phionyx ↔ NIST AI Risk Management Framework 1.0

> **Mapping target:** NIST AI 100-1, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (January 2023)
> Authoritative source: <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf>
>
> **Phionyx version mapped:** v0.3.0 · DOI [10.5281/zenodo.20027535](https://doi.org/10.5281/zenodo.20027535)
> **Pipeline contract:** v3.8.0 (46 canonical blocks)
> **Mapping last verified:** 2026-05-04

This document maps the four core functions of the NIST AI RMF — **GOVERN, MAP, MEASURE, MANAGE** — and their primary categories to the Phionyx Core component(s) that produce relevant evidence, the coverage level, and the artifact(s) that let an external reviewer verify the claim. Where Phionyx does **not** address a category, this is stated explicitly.

> **Scope statement.** This is an **evidence mapping**, not an organisational risk-management programme. The AI RMF is voluntary guidance directed at *organisations that develop, deploy, or use AI systems* — not at software libraries. Phionyx is a runtime layer that produces *technical evidence* a deployer can fold into their RMF programme; whether the organisation's overall AI risk management is appropriate is a determination only the deployer (and their stakeholders) can make. Adopting Phionyx does not by itself satisfy any AI RMF outcome.

---

## Coverage summary

| Function | Topic | Coverage | Primary Phionyx contribution |
|----------|-------|----------|------------------------------|
| **GOVERN** | Policies, accountability, risk-management culture | Partial | `RBAC`, `CapabilityProfile`, audit-recorded decisions, ADR documents |
| **MAP** | Context, categorisation, impact assessment | Partial | `CapabilityProfile` declares allowed actions; epistemic-boundary block flags out-of-context inputs |
| **MEASURE** | Identifying, tracking, and analysing risks | Partial | Φ/R/coherence telemetry, drift detection, behavioural-eval suite, confidence fusion |
| **MANAGE** | Prioritising, responding to, recovering from risks | **Full (runtime layer)** | `kill_switch`, `HITL`, `ethics_pre_response`, `ethics_post_response`, audit trail |

**Score:** 1 Full · 3 Partial · 0 Gap (within the runtime perimeter).

The MANAGE function is the closest fit: Phionyx is in essence a runtime risk-management substrate — its job is to detect, contain, and audit cognitive-risk events on a per-turn basis. The Partial rows reflect the fact that GOVERN, MAP, and MEASURE are *organisational* functions whose AI RMF outcomes can only be partially discharged by any single technical artifact.

---

## How to read each entry

Every function entry below follows the same structure:
- **Function statement (paraphrase)** — the AI RMF outcome the function is meant to produce.
- **Phionyx mechanism** — specific block, contract, or governance feature.
- **Coverage** — *Full* / *Partial* / *Gap*, **scoped to the runtime perimeter**.
- **Evidence** — file paths, test names, reproducibility commands.
- **Deployer responsibility (gap)** — what the deploying organisation must add. The AI RMF is fundamentally an *organisational* framework; most of each function lives outside any runtime.

---

## GOVERN · A culture of risk management is cultivated and present

**Function statement (paraphrase).** *Policies, processes, procedures, and practices across the organisation related to the mapping, measuring, and managing of AI risks are in place, transparent, and implemented effectively. Roles and responsibilities are clearly defined; a risk-management culture is fostered.*

**Phionyx mechanism.**
- `phionyx_core/governance/rbac.py` — typed Role/Permission model; every governance decision is RBAC-checked.
- `phionyx_core/contracts/v4/capability_profile.py` — `CapabilityProfile` declares the allowed action surface for a deployed instance (which tools, which data sources, which reach). Bypassing a capability is a *policy* operation that produces an audit record, not a code change.
- `phionyx_core/contracts/v4/audit_record.py` — every governance decision (kill switch, HITL, ethics gate, RBAC denial) writes a signed AuditRecord. The chain itself is the documented evidence trail.
- `docs/adr/` — Architecture Decision Records (ADR-0001…ADR-0005) document non-obvious governance decisions, including the two-layer governance split (ADR-0005).

**Coverage.** Partial — *within the runtime perimeter*.

**Evidence.**
- `phionyx_core/governance/rbac.py`, `phionyx_core/contracts/v4/capability_profile.py`.
- `tests/contract/test_governance_layering.py` — enforces ADR-0005 dependency rules.
- `docs/adr/0005-governance-layering.md` — documented decision on per-turn vs. cross-turn governance.
- Audit chain example in the reproducibility pack (`audit_chain_example.json`).

**Deployer responsibility (gap).** GOVERN is overwhelmingly an *organisational* function: AI RMF expects documented policies, named accountable roles, risk-management strategy approved by leadership, training programmes, and stakeholder engagement. Phionyx provides the *technical anchors* for those policies (RBAC, capability profiles, signed audit) but cannot author the organisational policy that points at them. The deployer must produce: an AI risk policy, a roles-and-responsibilities matrix, a documented escalation path, and periodic governance reviews.

---

## MAP · Context is established and understood

**Function statement (paraphrase).** *Context is understood, AI system categorisation is performed, AI capabilities and limitations are documented, third-party risks are mapped, and impacts to individuals, groups, communities, organisations, and society are characterised.*

**Phionyx mechanism.**
- `phionyx_core/contracts/v4/capability_profile.py` — declares the *intended use* envelope of the deployed system (allowed tools, allowed data sources, allowed reach). Any action outside the profile triggers a policy denial.
- `pipeline/blocks/knowledge_boundary.py` (block 15) — epistemic-boundary check; flags requests that fall outside what the system can be expected to answer reliably. This operationalises "AI capabilities and limitations are documented" at runtime.
- `pipeline/blocks/input_safety_gate.py` (block 3) — input categorisation against unsafe-input taxonomy.
- README "Scope of Claims" and "Known Limitations" — the public-facing documentation of what Phionyx can and cannot do, mirrored in the Evidence Matrix at `/evidence`.

**Coverage.** Partial — *within the runtime perimeter*.

**Evidence.**
- `phionyx_core/contracts/v4/capability_profile.py` — typed contract.
- `pipeline/blocks/knowledge_boundary.py`, `pipeline/blocks/input_safety_gate.py` — code.
- `tests/core/test_knowledge_boundary*.py`, `tests/core/test_input_safety*.py`.
- In-repo architecture documentation (README, `ARCHITECTURE.md`) — narrative context.

**Deployer responsibility (gap).** MAP outcomes such as *third-party impact assessment*, *stakeholder mapping*, *socio-technical context analysis*, and *intended-use vs. foreseeable-misuse documentation* are deployment-context-specific. Phionyx provides the technical surface (capability profile, epistemic boundary) but cannot describe the deployer's domain, user population, or societal context. The deployer must produce an intended-use statement, a stakeholder map, and a documented impact assessment for the specific deployment.

---

## MEASURE · Methods and metrics are identified and applied

**Function statement (paraphrase).** *Appropriate methods, metrics, and tools are identified and applied. AI systems are evaluated for trustworthy characteristics — including safety, security and resilience, transparency and accountability, explainability and interpretability, privacy, fairness, and validity. Mechanisms for tracking risks over time are in place, and feedback is integrated.*

**Phionyx mechanism.**
- `pipeline/blocks/phi_calculation.py` (block 37) — Φ (cognitive coherence) per turn.
- `pipeline/blocks/entropy_calculation.py` (block 38) — entropy per turn.
- `pipeline/blocks/confidence_fusion.py` (block 39) — `w_final` confidence fusion per turn.
- `pipeline/blocks/behavioral_drift_detection.py` (block 23) — sustained drift over turns; escalates to HITL or kill_switch.
- `tests/behavioral_eval/` (730 tests) — adversarial / red-team / fuzz harnesses over canonical scenarios.
- `tests/research_engine/` (231 tests) — Tier A reproducibility tests (291 experiments, 66/66 parameters).
- `data/mcp_telemetry/session_*.json` — per-call telemetry log including w_final, trust, integrity.

**Coverage.** Partial — *within the runtime perimeter*.

**Evidence.**
- Pipeline blocks above (canonical block IDs 23, 37, 38, 39).
- `tests/behavioral_eval/`, `tests/research_engine/` — pass/fail counts in CI badge.
- Research Engine tier-A documentation (in `phionyx_core/research_engine/`).
- `CITATION.cff` and `CHANGELOG.md` document the v0.3.0 measurement surface.

**Deployer responsibility (gap).** AI RMF expects MEASURE outcomes for the *deployed* system in its *deployment context* — for example, measuring fairness against a specific user population, measuring privacy against a specific data flow, or measuring validity against a specific task definition. Phionyx supplies *generic* trustworthy-AI measurements (Φ, drift, audit integrity, behavioural evals); the deployer must define which task-specific measurements apply, gather the necessary baseline data, and integrate user feedback. Fairness metrics in particular are deployment-specific and not produced by the runtime.

---

## MANAGE · Risks are prioritised, responded to, recovered from

**Function statement (paraphrase).** *AI risks based on assessments and other analytical output from the MAP and MEASURE functions are prioritised, responded to, and managed. Strategies to maximise AI benefits and minimise negative impacts are planned, prepared, implemented, documented, and informed by input from relevant AI actors.*

**Phionyx mechanism.**
- `phionyx_core/governance/kill_switch.py` — fail-closed runtime kill switch with four documented triggers (ethics_max_risk, t_meta_below_threshold, consecutive_drift, manual). This *is* the runtime risk-response mechanism.
- `phionyx_core/governance/human_in_the_loop.py` — priority-ordered HITL queue with expiry and reviewer-handoff records; sustained-risk turns can be escalated to a human reviewer rather than refused outright.
- `pipeline/blocks/ethics_pre_response.py` (block 18), `pipeline/blocks/ethics_post_response.py` — pre- and post-generation ethical risk gates; both must pass before a response is released.
- `pipeline/blocks/revision_gate.py` (block 41) — final response-eligibility gate; a turn that fails any prior gate is revised or refused.
- `pipeline/blocks/audit_layer.py` (block 44) — every risk decision is recorded with Ed25519 signature in the AuditRecord chain. This is the recovery / forensic record.

**Coverage.** **Full** — *within the runtime perimeter*. The four AI RMF MANAGE outcomes (prioritise, respond, document, monitor) all map cleanly to native Phionyx mechanisms at the per-turn level.

**Evidence.**
- `phionyx_core/governance/kill_switch.py`, `phionyx_core/governance/human_in_the_loop.py`.
- `pipeline/blocks/ethics_pre_response.py`, `pipeline/blocks/ethics_post_response.py`, `pipeline/blocks/revision_gate.py`, `pipeline/blocks/audit_layer.py`.
- `tests/core/test_kill_switch*.py`, `tests/core/test_hitl*.py`, `tests/core/test_ethics*.py`.
- Reproducibility pack `audit_chain_example.json` shows a real risk-response sequence (ETHICS_CRITICAL → kill_switch → audit record).

**Deployer responsibility (gap).** AI RMF MANAGE also has *organisational* outcomes that no runtime can produce: incident-response procedures, stakeholder-communication plans, periodic risk-treatment reviews, and post-incident learning loops. Phionyx produces the per-turn risk-response evidence that feeds those organisational processes; the deployer must define the human-side response chain (who is paged when kill_switch fires, what the disclosure threshold is, how lessons are captured).

---

## What this mapping is *not*

1. **Not certification.** NIST AI RMF is voluntary guidance and does not have a certification regime. This document does not assert that an organisation using Phionyx is "AI RMF compliant" — that phrase has no formal meaning under AI RMF 1.0.
2. **Not coverage of the AI RMF Profile companion documents.** The Profile companion documents (e.g., for generative AI, NIST AI 600-1) define context-specific tailoring; we map only the four core functions of NIST AI 100-1 here.
3. **Not a substitute for organisational risk management.** Every Partial row above identifies *organisational* deliverables that Phionyx cannot produce. The runtime supplies technical evidence; the organisation supplies the policy, accountability, and governance scaffolding.

---

## Reproducibility

Every claim above can be verified by an external reviewer with two operations:

```bash
git clone https://github.com/halvrenofviryel/phionyx-research.git
cd phionyx-research
pip install -e .
pytest tests/core/ tests/contract/ -q
```

The audit-chain example is in the reproducibility pack:

```bash
python scripts/make_reproducibility_pack.py
unzip -l phionyx_reproducibility_pack_v0.3.0.zip
# → audit_chain_example.json shows kill_switch + audit_layer interaction
```

---

## Cross-references

- OWASP Agentic AI Threats v1.0 mapping — `docs/mappings/owasp-agentic-ai-2025.md`
- EU AI Act Articles 9–15 mapping — `docs/mappings/eu-ai-act.md`
- In-repo architecture documentation (README, `ARCHITECTURE.md`)
- Evidence Matrix — <https://phionyx.ai/evidence>
