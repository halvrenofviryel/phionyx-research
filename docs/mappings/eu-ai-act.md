# Phionyx ↔ EU AI Act, Articles 9–15 (High-Risk AI Systems)

> **Mapping target:** Regulation (EU) 2024/1689 (AI Act), Articles 9–15
> Authoritative source: <https://eur-lex.europa.eu/eli/reg/2024/1689/oj>
>
> **Phionyx version mapped:** v0.3.0 · DOI [10.5281/zenodo.20027535](https://doi.org/10.5281/zenodo.20027535)
> **Pipeline contract:** v3.8.0 (46 canonical blocks)
> **Mapping last verified:** 2026-05-04

This document maps each of the seven high-risk AI obligations in Articles 9–15 of the EU AI Act to the Phionyx Core component(s) that produce relevant evidence, the coverage level, and the artifact(s) that let an external reviewer verify the claim. Where Phionyx does **not** address an obligation, this is stated explicitly.

> **Scope statement.** This is an **evidence mapping**, not legal compliance. The EU AI Act's high-risk obligations apply to a *deployed AI system* placed on the EU market — not to a software library. Phionyx is a runtime layer that *produces* evidence that a deployer can use to discharge specific obligations; whether their final deployment is compliant is a determination only the deployer (and ultimately, the supervisory authority) can make. Adopting Phionyx does not by itself satisfy any AI Act obligation.

---

## Coverage summary

| Article | Topic | Coverage | Primary Phionyx contribution |
|---------|-------|----------|------------------------------|
| 9 | Risk management system | Partial | `kill_switch`, `behavioral_drift_detection`, `ethics_pre_response`, audit-recorded risk decisions |
| 10 | Data and data governance | **Gap** | Phionyx is a runtime layer, not training-time data governance |
| 11 | Technical documentation | Partial | Architecture paper (arXiv), README, CITATION.cff, CHANGELOG, Evidence Matrix |
| 12 | Record-keeping | **Full** | `audit_layer` (Ed25519 hash chain), `AuditRecord` v4 schema |
| 13 | Transparency / deployer information | Partial | README "Scope of Claims" + "Known Limitations" + Evidence Matrix at `/evidence` |
| 14 | Human oversight | Partial | `human_in_the_loop` queue, `kill_switch` (operator trigger), `deliberative_ethics` |
| 15 | Accuracy, robustness, cybersecurity | Partial | Determinism, mypy/ruff strict, pip-audit clean, security-hardened workflows |

**Score:** 1 Full · 5 Partial · 1 Gap.

The single Full row is **Article 12 (Record-keeping)** — the regulatory text and the `AuditRecord` v4 contract align almost line-by-line. The single Gap is **Article 10 (Data governance)** — that obligation lives at training time, upstream of any runtime; Phionyx does not change it. Every Partial row identifies the specific deployer responsibility that must complement Phionyx's contribution.

---

## How to read each entry

Every article entry below follows the same structure:
- **Article text (relevant excerpt)** — paraphrased, with the obligation flag (e.g., "shall ensure", "shall document").
- **Phionyx mechanism** — specific block, contract, or governance feature.
- **Coverage** — *Full* / *Partial* / *Gap*.
- **Evidence** — file paths, test names, reproducibility commands.
- **Deployer responsibility (gap)** — what the deployer must add. This is where most of the AI Act obligation lives even when Phionyx is in use.

---

## Article 9 · Risk management system

**Article text (paraphrase).** *Providers of high-risk AI systems shall establish, implement, document and maintain a risk management system, understood as a continuous iterative process, planned and run throughout the entire lifecycle of the system. The system shall identify and analyse the known and reasonably foreseeable risks, estimate and evaluate risks that may emerge in use, and adopt suitable risk-management measures.*

**Phionyx mechanism.**
- `phionyx_core/governance/kill_switch.py` — fail-closed shutdown on four named triggers (ethics_max_risk, t_meta_below_threshold, consecutive_drift, manual). Every evaluation produces a `KillSwitchEvent` recorded in the audit log.
- `phionyx_core/governance/deliberative_ethics.py` — four-framework ethics scoring (utilitarian, deontological, virtue, care) per turn; `EthicsVector` carries `harm_risk`, `manipulation_risk`, `attachment_risk`, `boundary_violation_risk` as explicit risk axes.
- `pipeline/blocks/behavioral_drift_detection.py` (block 23) — continuous, automatic drift monitoring across turns; sustained drift escalates to HITL or kill_switch.
- `pipeline/blocks/ethics_pre_response.py` (block 18) and `ethics_post_response.py` — pre- and post-generation risk gates; both must pass.

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/governance/kill_switch.py` — KillSwitchConfig with documented thresholds.
- `phionyx_core/contracts/v4/ethics_decision.py` — typed risk-decision contract.
- `tests/core/test_behavioral_drift*.py`, `tests/core/test_kill_switch*.py`.
- Reproducibility pack: `audit_chain_example.json` shows an ETHICS_CRITICAL trigger fire at risk 0.99.

**Deployer responsibility (gap).** Article 9 demands a *documented* risk management system as an organisational deliverable. Phionyx provides the *runtime instruments* and the audit trail; the deployer must wrap them in a risk-management policy document, a risk register, periodic review records, and named accountability — none of which a software library can produce.

---

## Article 10 · Data and data governance

**Article text (paraphrase).** *High-risk AI systems shall be developed on the basis of training, validation and testing data sets that meet quality criteria… Training, validation and testing data sets shall be subject to data-governance and management practices appropriate for the intended purpose: relevance, representativeness, examination for biases, completeness…*

**Phionyx mechanism.** **None.** Phionyx is a runtime layer. It is invoked *after* training is complete and consumes whatever LLM the deployer has installed.

**Coverage.** **Gap (out of scope by architecture).**

**What Phionyx does instead.**
- Treats the LLM as a noisy sensor — explicitly *not* trusting the model as a source of truth (architecture paper Section 4.2). This is a *containment* posture, not a data-governance posture.
- The Non-Persistence Doctrine prevents derived metrics (Φ, R) from feeding back into any future training corpus, which a deployer could use as evidence under GDPR data-minimisation, but is **not** a substitute for Article 10 obligations on the upstream training set.

**Deployer responsibility (gap).** Article 10 obligations apply to whoever trains, fine-tunes, or curates the model. If the deployer uses a third-party LLM (GPT-4, Claude, Llama, etc.), the Article 10 evidence chain follows that vendor's data-governance practices, not Phionyx's. This boundary is intentional and correct.

---

## Article 11 · Technical documentation

**Article text (paraphrase).** *The technical documentation of a high-risk AI system shall be drawn up before that system is placed on the market and shall be kept up-to-date. The technical documentation shall be drawn up in such a way to demonstrate that the high-risk AI system complies with the requirements set out in this Section… (general description, detailed system description, monitoring, performance metrics, etc.)*

**Phionyx mechanism.**
- The architecture paper (arXiv preprint, 27 pages, 4 figures, 5 tables) describes design choices, the 46-block pipeline, state-evolution equations, safety/governance layer, memory model, and known limitations.
- README, CITATION.cff, CHANGELOG document the public surface, version history, and citation chain.
- The Evidence Matrix at [`/evidence`](https://phionyx.ai/evidence) lists every load-bearing claim with its evidence status.
- The reproducibility pack (`reproducibility_pack_v0.3.0.zip`) attaches to every release with JUnit XML, coverage, determinism hashes, audit-chain example, governed-response envelope, and OTel sample trace.
- This mappings directory (`docs/mappings/`) provides framework-by-framework coverage analysis.

**Coverage.** Partial.

**Evidence.**
- `https://github.com/halvrenofviryel/phionyx-research`
- arXiv preprint (in moderation at submission time of this mapping)
- `https://doi.org/10.5281/zenodo.20027534` (concept DOI, latest archived version)

**Deployer responsibility (gap).** Article 11 documentation is *deployment-specific*: it must describe the system "as placed on the market". The deployer combines Phionyx's substrate documentation with their own deployment configuration, prompt design, tool inventory, and intended-purpose statement. Phionyx documents the runtime; the deployer documents the system.

---

## Article 12 · Record-keeping

**Article text (paraphrase).** *High-risk AI systems shall technically allow for the automatic recording of events ('logs') over the lifetime of the system. The logging capabilities shall enable the recording of events relevant for: identifying situations that may result in the AI system presenting a risk… for any subsequent monitoring of the operation of the high-risk AI system… The logs shall be kept for a period appropriate to the intended purpose of the high-risk AI system…*

**Phionyx mechanism.**
- `pipeline/blocks/audit_layer.py` (block 44 of the canonical pipeline) — every turn produces an `AuditRecord` with Ed25519 signature and prev/link hash chain.
- `phionyx_core/contracts/v4/audit_record.py` — Pydantic-frozen, append-only schema. Required fields: `turn_id`, `participant_id`, `timestamp_utc`, `pipeline_contract_version`, `gate_decisions`, `risk_decision`, `kill_switch_state`, `prev_hash`, `link_hash`, `signature`.
- The contract test `tests/contract/test_audit_chain_integrity.py` enforces append-only semantics and hash-chain continuity.
- Retention is a deployment-configuration parameter; the architecture imposes no upper bound on chain length.

**Coverage.** **Full** (within the documented threat model).

**Evidence.**
- `phionyx_core/contracts/v4/audit_record.py` — schema reads almost exactly like the Article 12 obligation list.
- `tests/contract/test_audit_chain_integrity.py` — proves hash-chain integrity over a real KillSwitch event sequence.
- Reproducibility pack: `audit_chain_example.json` — verifiable hash chain over 4 evaluations including an ETHICS_CRITICAL trigger.

**Deployer responsibility (gap).** "Full" here means "the technical record-keeping requirement is structurally satisfied". The deployer must still: (a) define the *retention period* "appropriate to the intended purpose" — Phionyx does not auto-decide this, (b) provide secure storage and access control for the chain, (c) ensure operational logging covers both the substrate AND deployer-specific events not seen by Phionyx (e.g., admin user actions on the bridge layer).

---

## Article 13 · Transparency and provision of information to deployers

**Article text (paraphrase).** *High-risk AI systems shall be designed and developed in such a way to ensure that their operation is sufficiently transparent to enable deployers to interpret the system's output and use it appropriately. An appropriate type and degree of transparency shall be ensured, with a view to achieving compliance with the relevant obligations of the deployer. Instructions for use shall accompany the system… (characteristics, capabilities, limitations, intended purpose, training data, expected lifetime, performance metrics under conditions of use…)*

**Phionyx mechanism.**
- README "Scope: what Phionyx is, and is not" — six explicit non-claims (LLM determinism, certification authority, NIST/ISO/EU replacement, third-party audit, production-readiness, clinical framings).
- README "Known limitations" — six implementation-grounded limitation rows (controlled benchmarks, no third-party audit, no production deployment claims, LLM quality not guaranteed, compliance is evidence not legal cert, Φ/entropy experimental).
- Evidence Matrix at `/evidence` — 19+ load-bearing claims with explicit Public/Beta/Planned/Pending status per row, plus per-public-row Expected runtime / Expected result / Tested on / Last verified.
- `governed_response.schema.json` (Draft 2020-12 JSON Schema) — every field of the runtime envelope is documented with its constraints and meaning.
- Architecture paper provides the formal technical description.

**Coverage.** Partial.

**Evidence.**
- README, `/evidence`, schema in `examples/envelopes/`.
- `tests/contract/test_envelope_validation*.py` — proves the schema is enforced.

**Deployer responsibility (gap).** Article 13 instructions for use must describe the system "in conditions of use" — meaning the deployment-specific instance, including the LLM choice, prompts, guardrails, intended user population, and the deployer's expected performance metrics. Phionyx supplies the substrate documentation; the deployer authors instruction sheets for their final product.

---

## Article 14 · Human oversight

**Article text (paraphrase).** *High-risk AI systems shall be designed and developed in such a way, including with appropriate human-machine interface tools, that they can be effectively overseen by natural persons during the period in which they are in use. Oversight measures shall enable the natural persons to: fully understand the capacities and limitations of the system, remain aware of automation bias, correctly interpret the output, decide not to use the system or otherwise disregard, override or reverse the output, and intervene on the operation of the system or interrupt the system through a 'stop' button or similar procedure.*

**Phionyx mechanism.**
- `phionyx_core/governance/human_in_the_loop.py` — explicit HITL queue with priority (critical / high / normal) and `expires_at`. Expired entries promote to kill_switch rather than silently approve.
- `phionyx_core/governance/kill_switch.py::manual_trigger` — operator-callable interrupt. Fail-closed semantics: triggered state must be explicitly reset by an authorised operator.
- `pipeline/blocks/response_revision_gate.py` — directives `pass | damp | rewrite | regenerate | reject` give the deployer a structured override surface, not just a binary block.
- `phionyx_core/governance/deliberative_ethics.py` — four-framework reasoning makes the *grounds* for a risk decision visible, not just the verdict; this supports Article 14's "fully understand the capacities" requirement.
- The Evidence Matrix at `/evidence` and the Scope/Known Limitations sections are designed exactly to satisfy "remain aware of automation bias".

**Coverage.** Partial.

**Evidence.**
- `phionyx_core/governance/human_in_the_loop.py`, `kill_switch.py`, `rbac.py`.
- `tests/core/test_human_in_the_loop*.py`, `tests/core/test_kill_switch*.py`.
- Reproducibility pack: `audit_chain_example.json` shows the kill-switch trigger and reset path.

**Deployer responsibility (gap).** Article 14 ultimately demands a *human-machine interface*. Phionyx exposes the governance primitives (queue, kill switch, ethics decision contract) through a Python API; the deployer must build the actual operator UI, train the operators, schedule shifts, and document override procedures. The risk of automation bias is socio-technical, not purely architectural — Phionyx mitigates it but does not eliminate it.

---

## Article 15 · Accuracy, robustness and cybersecurity

**Article text (paraphrase).** *High-risk AI systems shall be designed and developed in such a way that they achieve, in light of their intended purpose, an appropriate level of accuracy, robustness and cybersecurity, and that they perform consistently in those respects throughout their lifecycle. The levels of accuracy and the relevant accuracy metrics shall be declared in the accompanying instructions of use. The systems shall be resilient against errors, faults or inconsistencies that may occur within the system or the environment in which the system operates… resilient as regards attempts by unauthorised third parties to alter their use, behaviour or performance by exploiting the AI system vulnerabilities.*

**Phionyx mechanism.**
- **Accuracy:** Determinism — same input + same state → same governance path (verified across 100 runs, hash-equivalent, see `01_determinism_and_physics.ipynb`). Note: Phionyx does **not** make the LLM accurate; it makes the *governance path* deterministic and the audit trail accurate.
- **Robustness:**
  - mypy strict-clean across the full SDK (327 source files, 0 errors) — eliminates a large class of type-induced runtime failures.
  - ruff strict-clean — eliminates a class of stylistic and idiomatic errors that correlate with bugs.
  - 1,137 passing tests on the public CI subset, Python 3.10–3.13 matrix.
  - `pipeline/blocks/entropy_amplitude_pre_gate.py` rejects out-of-bound inputs before computation.
- **Cybersecurity:**
  - `pip-audit` clean — 0 known CVEs across all listed dependencies (verified in v0.3.0 hardening sweep).
  - No `eval` / `exec` / `pickle.loads` / `os.system` / `shell=True` anywhere in `phionyx_core/`.
  - GitHub workflows have top-level `permissions: contents: read` and elevate per-job; the only third-party Action in the release path is SHA-pinned (`softprops/action-gh-release@3bb12739…`).
  - Private vulnerability reporting via `SECURITY.md` (3-business-day acknowledgement, 30-day fix-or-disclosure-timeline target).

**Coverage.** Partial.

**Evidence.**
- Determinism: `examples/notebooks/01_determinism_and_physics.ipynb`.
- Type safety + lint: `.github/workflows/ci.yml` mypy + ruff steps.
- Tests: `pytest tests/core tests/contract tests/benchmarks` → 1,137 collected.
- Workflow hardening: PR #54 (merged) — `.github/workflows/release.yml` permissions block.
- Reproducibility pack: `pytest_report.xml`, `coverage.xml`, `determinism_hashes.json`.

**Deployer responsibility (gap).** Article 15 demands *declared accuracy metrics in instructions of use*. Phionyx publishes its *governance-path* metrics (determinism, audit chain integrity, gate-decision throughput); the deployer must declare *deployment-level* metrics (response quality, factual accuracy, downstream task accuracy) measured under their conditions. Adversarial robustness against prompt-injection and other AI-specific attacks is **partially** mitigated by `input_safety_gate` and `cep_evaluation`, but a full red-team programme is the deployer's responsibility (see also OWASP mapping T1, T6, T15).

---

## Gap analysis

The single Gap row:

| Article | Topic | Why gap | Where the obligation lives |
|---------|-------|---------|----------------------------|
| 10 | Data and data governance | Phionyx is a runtime layer, not a training pipeline | LLM provider's data governance + deployer's fine-tuning data process |

The Partial entries each carry a **"Deployer responsibility (gap)"** line; that line is the AI Act obligation perimeter that Phionyx does *not* close on its own. Most of the regulatory work is structured this way: Phionyx supplies a *technical evidence channel*, the deployer supplies the *organisational evidence* (policies, SOPs, accountability roles, retention decisions, operator UIs, instructions for use).

---

## Companion mappings

This document is one of three Phase 3 mappings:
- [`owasp-agentic-ai-2025.md`](owasp-agentic-ai-2025.md) — OWASP Agentic AI Threats v1.0 (15 threat categories)
- `nist-ai-rmf.md` — NIST AI Risk Management Framework 1.0 (Govern / Map / Measure / Manage) — *planned, in progress*
- `iso-42001.md` — ISO/IEC 42001 AI management system controls — *P2-deferred per the master plan*

The OWASP and NIST mappings give a deployer **threat-model** and **risk-management-framework** views of the same Phionyx evidence; the EU AI Act mapping gives the **regulatory** view. Together they cross-reference: an Article 12 record-keeping obligation maps to OWASP T8 (Repudiation & Untraceability) maps to NIST MEASURE-2 (Tracked metrics).

---

## How to use this mapping

For an EU AI Act conformity-assessment exercise:
1. Pick an article (9 through 15).
2. Read the Phionyx mechanism — it tells you what evidence the runtime produces.
3. Click the evidence file paths to read the implementation; run the reproducibility command to confirm.
4. Read the **"Deployer responsibility (gap)"** line — that is the work *you* must still do (policy docs, retention decisions, operator UIs, intended-purpose statement, declared accuracy metrics).
5. Cross-check against your conformity-assessment working paper.

For a deployment-architecture review:
1. Each Partial row's deployer-responsibility line is a checklist item for your deployment.
2. The single Gap row (Article 10) tells you where you must engage your model provider, not Phionyx.

---

## Versioning

Mappings are dated. Future versions will be cut on:
- Phionyx feature changes that move a row's coverage level (e.g., when adversarial-robustness demos ship in Phase 3, Article 15 may move).
- AI Act amendments or guidance updates from the European AI Office.
- Independent third-party validation that re-classifies a row.

**License.** This mapping inherits the repo licence (AGPL-3.0). The AI Act text excerpts and paraphrases are © European Union, used under the OJ-text reuse policy.
