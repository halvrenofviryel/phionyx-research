# Changelog

All notable changes to Phionyx Core SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_(no changes yet)_

---

## [0.2.0] — 2026-05-01

PyPI-readiness release. Public surface is unchanged from v0.2.0-dev;
the work in this version is packaging hygiene, dependency correctness,
and CI / release infrastructure so that `pip install phionyx-core`
behaves as advertised on a clean machine.

### Added

- **CI matrix** — GitHub Actions running `ruff check phionyx_core`, smoke
  imports, and `pytest tests/core tests/contract tests/benchmarks` on
  Python 3.10 / 3.11 / 3.12 / 3.13 plus a build job that produces sdist
  + wheel and verifies them with `twine check` and a fresh-venv install.
- **Release workflow** — `.github/workflows/release.yml` triggers on
  tags matching `v*`, builds the wheel, and publishes to PyPI via
  OIDC trusted publisher (no API token in repo or secrets). The
  workflow also cross-checks that the tag matches `pyproject.toml`
  `project.version` before uploading.
- **Demo notebooks** — `examples/notebooks/01_determinism_and_physics.ipynb`,
  `02_kill_switch_in_action.ipynb`, `03_pipeline_blocks_and_audit.ipynb`
  with a Try-It-In-30-Seconds entry in the README.

### Changed

- **Required dependencies** — `PyYAML >= 6.0` and `numpy >= 1.24` moved
  from optional extras into base `dependencies`. They were imported at
  module top level by `phionyx_core.physics.profiles`,
  `phionyx_core.cep.cep_config`, and `phionyx_core.state.ukf_*`, so a
  vanilla install previously raised `ModuleNotFoundError` on
  `import phionyx_core`. `networkx` remains optional under `[graph]`.
- **Single packaging metadata source** — removed legacy `setup.py` (it
  duplicated and disagreed with `pyproject.toml`).
- **Pydantic V2 idioms across the codebase** — 26 nested `class Config:`
  blocks migrated to `model_config = ConfigDict(...)`, 5 `@validator`
  to `@field_validator` + `@classmethod`, 3 `.dict()` to
  `.model_dump()`. Clears all `PydanticDeprecatedSince20` warnings.
- **PEP 585 typing across the codebase** — `typing.List/Dict/Optional`
  rewritten to `list/dict/X | None`, import order normalized,
  comprehension shape simplified. 293 files mechanically updated;
  every change is type-annotation or formatting only — no behavioural
  diff.
- **`datetime.utcnow()` removed from tests** — 4 occurrences in
  `tests/core/test_human_in_the_loop.py` replaced with
  `datetime.now(timezone.utc)` to match the source layer and clear
  the deprecation warning.
- **README** — new "Try It In 30 Seconds" section above Quick Start
  with a Φ heatmap from notebook 01; CI badge added; static test count
  corrected from 2,571 (monorepo number) to 1,230 (this repo:
  1,013 core + 107 contract + 10 benchmarks).

### Fixed

- **`tests/contract/test_product_registry.py`** — was failing on a clean
  clone because it imported from `phionyx_products`, a monorepo-only
  package. Now uses `pytest.importorskip` so the file skips cleanly
  on the public release.
- **`tests/contract/test_block_determinism.py::test_matrix_doc_in_sync`**
  — invoked `scripts/active/generate_determinism_matrix.py`, which is
  monorepo-only. Now skips with a clear reason if the script is
  absent.
- **`tests/core/test_mind_loop_validator.py`** — imported
  `tests.behavioral_eval.conftest.CANONICAL_V3_5_0` which is
  monorepo-only. Now loads the current canonical block list directly
  from `phionyx_core.contracts.telemetry.get_canonical_blocks()`,
  fixing 12 collection failures.
- **`B904` (raise from)** — 4 `raise ValueError(...)` calls inside
  `except` blocks now chain via `from err` or `from None` so the
  triggering exception is preserved in tracebacks.

### Tests

- Clean-clone test count rose from 998 (pre-hardening, with one
  failing test in `tests/core` and a collection error in
  `tests/contract`) to **1,230 passed, 7 skipped, 0 failed**.

---

## [0.2.0-dev] — Pipeline contract v3.8.0

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
