# Changelog

All notable changes to Phionyx Core SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] — Pipeline contract v3.8.0

### Added

- **Pipeline contract v3.8.0** — 46 canonical blocks (was 45). New block `response_revision_gate` inserted immediately before `response_build`. Closes the in-turn state→response feedback loop required by Echoism Axiom 1 and patent claims SF1 C1/C4/C15, SF2 C1/C11.
- **`response_revision_gate` block** — Consumes final-turn phi, entropy, coherence, confidence, arbitration, drift, ethics, and CEP signals; emits a deterministic `revision_directive` (`pass` / `damp` / `rewrite` / `regenerate` / `reject`). Pure decision function, does not rewrite narrative.
- **Orchestrator bounded regenerate retry** (founder-approved per Plan v3) — On `regenerate` directive, orchestrator performs a single state-informed retry of `narrative_layer` → `response_revision_gate` (allowlist bounded; state-mutating blocks NOT re-run). Deterministic retry seed (SHA-256 of turn+state), hard cap = 1, Axiom-6 compliant.
- **`AuditRecord.claim_refs` / `revision_directive` fields** — Optional, additive; patent-claim traceability and revision decision capture. `compute_hash()` unchanged → legacy hash chains remain valid.
- **`PipelineBlock.claim_refs`** — Optional tuple on base class for claim→code traceability (e.g. `("SF1:C4", "SF1:C15")`).
- **`response_build` directive consumer** — Applies `pass` / `damp` (amplitude×factor) / `rewrite` (prefix) / `regenerate` (clarification fallback if retry already consumed) / `reject` (safety message + HITL) to the final response.
- **`narrative_layer` constraint consumer** — Prepends deterministic regeneration constraint block (reasons + target phi/confidence + prior narrative hash) to enhanced context when invoked on retry pass.

### Changed

- **Canonical block order:** `phi_computation`, `entropy_computation`, `confidence_fusion`, `arbitration_resolve` moved to execute **before** `response_build` (positions 37–40). Their outputs now drive `response_revision_gate` in-turn instead of informing only the next turn.
- **Current default contract version:** `3.8.0` (v3.7.0 remains loadable via `get_canonical_blocks(version="3.7.0")` for runtime coexistence).
- **`PipelineBlock` docstring** — Corrected stale "31 canonical blocks" reference to v3.8.0 / 46.

### Fixed

- **`test_sf1_claim1_deterministic_kernel`** — Pre-existing pre-v3.5.0 assertion updated to reflect safety-first invariant: position 0 is `kill_switch_gate` since v3.5.0; `time_update_sot` is position 1.

### Tests

- 126+ new tests across `tests/contract/`, `tests/patent_claims/` — state-driven response behaviour, v3.8.0 contract invariants, audit-schema hash-chain continuity, regenerate retry semantics, end-to-end directive application.

### Documentation

- New patent-adjacent docs: `docs/publications/patents/ukipo/BLOCK_CLAIM_ALIGNMENT_ANALYSIS.md`, `BLOCK_CLAIM_IMPROVEMENT_PLAN{,_V2,_V3}.md`.

---

## [0.1.0b1] - 2026-04-04

### Changed (from internal 1.0.0)

- **License:** Changed from MIT to Proprietary (All Rights Reserved)
- **Pipeline:** Expanded from 24 to **45 canonical blocks** (v3.7.0)
- **Tests:** Expanded from ~1,370 to **2,468 tests** (0 failures)
- **Package version:** Reset to 0.1.0b1 (beta) for public release

### Added

- **CEP Engine:** Conscious Echo Proof — synthetic psychopathology prevention (4 detection mechanisms, 46 unit tests)
- **AGI World Model Blocks:** Causal graph update, self-model assessment, goal persistence, confidence fusion, outcome feedback
- **Karpathy Feature Blocks:** Scenario frame, coherence QA, time update
- **Kill Switch:** 4 triggers, fail-closed state machine (335 LOC)
- **Deliberative Ethics:** 4-framework ethical reasoning (379 LOC)
- **Benchmark Suite:** 10 tests verifying all paper performance claims
- **arXiv Paper:** Echoism architecture (22 pages, benchmark-verified)
- **Patent Portfolio:** 49 UKIPO claims across 3 Super Families
- **Research Engine v3.3.0:** 291 experiments, 66 parameters, CQS 0.862

### Performance (Benchmark-Verified)

- Determinism: 100 runs, zero variance (SHA-256 hash-proof)
- CPU overhead: ~31% reduction vs post-hoc filtering (at 30% unsafe ratio)
- Storage: +24% vs LRU, +72% vs FIFO (high-value retention)
- Pipeline overhead: Sub-millisecond per block (mean 0.008ms)

---

## [1.0.0] - 2026-01-29 (Internal)

### Added

- **Initial Release:** Phionyx Core SDK v1.0.0 (internal)
- **EchoOrchestrator:** Main orchestrator for pipeline execution
- **EchoState2:** Canonical state model with thermodynamic state metrics
- **24-Block Canonical Pipeline:** Deterministic cognitive evaluation blocks
- **Hybrid Resonance Model:** Phi calculation (cognitive + physical resonance)
- **Dynamic Entropy:** Kolmogorov Complexity-based entropy calculation
- **Semantic Time-Based Memory:** Physics-based cache eviction
- **Safety & Governance Layer:** Pre-response control, cognitive envelopes, participant isolation
- **Profile Management:** Configurable profiles (edu, game, clinical)
- **Physics Calculations:** Pure mathematical functions for state metrics

---

**Last Updated:** April 4, 2026
