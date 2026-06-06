# Changelog

All notable changes to Phionyx Core SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

(nothing yet)

---

## [0.8.1] — 2026-06-06

**Patch — bug fixes.**

### Fixed

- **`EventReference` construction.** `state/state_migration.py` and
  `state/echo_state_2.py` built `EventReference` with `event_id`/`event_type`/`tags`,
  but the dataclass fields are `id`/`tag`/`intensity` — which would raise `TypeError`
  on the legacy state-migration and `add_event_tag` paths. Now constructs with the
  correct fields.
- **`VectorStore` None / repository-mode guards.** `store()` now returns `None`
  gracefully when `metadata` is `None` (was an `AttributeError`); `search_similar()`
  returns `[]` with a warning when the direct client is unavailable in repository
  mode (was an `AttributeError` on `None.rpc(...)`).

---

## [0.8.0] — 2026-06-06

**Theme: Production Hardening (schema-freeze candidate).**

v0.8.0 hardens the existing runtime rather than adding new product features: real
axiom enforcement in CI, an adversarial regression corpus, a performance gate, a
cryptographically consistent signed chain, and a type-modernized source tree. It is a
schema-freeze **candidate** — not a freeze. The v1.0 freeze is a separate milestone, and
the docs site, companion-package republish, and external audit are independent workstreams
that do not gate this package release.

### Added

- **`contracts/interlink/` — cross-runtime envelope module** (`envelope.py`). Houses the
  interchange envelope schema previously kept outside the package; additive.
- **`contracts/v4/claim.py` — typed `Claim` lifecycle contract.** Ties a `claim_id` from
  creation → gate decision → signed record → observed outcome, with an
  `is_lifecycle_complete()` predicate. Realized through the existing pipeline; no new blocks.
- **8-axiom CI gate.** The Echoism axiom suite now asserts real invariants in CI (replacing
  a previously always-passing aggregator).
- **Adversarial corpus + confusion matrix.** A 30-safe / 30-unsafe input regression set with
  a published baseline recall, run in CI.
- **10K-envelope performance benchmark + latency gate.** Sub-millisecond per-envelope
  verification, wired as a CI regression gate.

### Changed

- **Signed-chain canonicalization → RFC 8785 (JCS).** The signed audit chain now
  canonicalizes via a byte-identical JCS canonicalizer shared with the evidence-export path,
  eliminating float (`5.0` vs `5`) and non-ASCII divergence. **Breaking** for chains
  persisted by earlier versions (they no longer verify); new chains are JCS-consistent. The
  frozen `audit_record.py` hash domain is unchanged.
- **Type-modernization sweep** across `phionyx_core/` (PEP 585/604 builtin generics, `X | None`,
  import ordering). `ruff`- and `mypy`-clean on Python 3.10–3.13. No behavioral change.
- **Privacy rebuild.** Genericized example/keyword data in `context/` and
  `narrative/lore_mapping.py` to remove maintainer-personal and domain-specific literals from
  the published package. No behavioral change.

### Notes

- **Not a schema freeze.** v0.8.0 is a freeze candidate. Version axes (product release, RGE
  wire schema, V4 contract suite, pipeline contract, AIREP protocol) are intentionally
  independent and each follow their own bump rules.

---

## [0.7.0] — 2026-05-27

**Theme: Compliance Evidence Pack.**

v0.7.0 takes the evidence layer from "auditable by reviewers" (v0.6.0 multi-agent) to "framework-readable by compliance officers." Same envelope chain. Different vocabulary.

Six work blocks ship: phionyx-compliance with four framework templates (W1), RGE v0.2 reasoning + retrieval extensions (W2.1 + W2.2), schema portfolio bump (W2.3), phionyx-letta memory mutation audit (W3), and the HearthOS bounded-authority envelope foundation with three reviewer-runnable pinned traces (W4.1 + W4.2.a).

**Two new schemas:** Schema 8 `phionyx.memory_mutation_envelope.v1` (Letta) and Schema 9 `phionyx.bounded_authority_envelope.v1` (HearthOS). Both additive — every v0.6.0 envelope continues to validate; no breaking changes.

### Added

- **F14 — `phionyx-compliance` package** (separate public repo: `halvrenofviryel/phionyx-compliance` — coming when GHA billing resolved). Read-only over the envelope chain. Produces framework-shaped markdown drafts. Four templates ship at v1.0.0: EU AI Act Article 13, NIST AI RMF 1.0, ISO/IEC 42001:2023, OWASP Top 10 for Agentic Applications. Every report carries the canonical "evidence-oriented mapping, not legal compliance guarantee" disclaimer.
- **F4 — RGE v0.2 reasoning surface extension** (W2.1). Three optional fields on `reasoning`: `rationale_summary`, `knowledge_sources_consulted[]`, `constraints_acknowledged[]`. Additive; v0.6.0 envelopes continue to validate.
- **F8 — RGE v0.2 retrieval block activation** (W2.2). `retrieval.status` flips from `reserved-for-v0.4.1-f8` to `active` for Phionyx producers. Block-level additions: `corpus` (name/version/language), `similarity_threshold`, `query_text_hash`. Per-document additions: `chunk_offset`, `source_url`, `retrieved_at`.
- **F15 — `phionyx-letta` memory mutation audit** (W3). New companion package. Schema 8 `phionyx.memory_mutation_envelope.v1`. Per-mutation signed envelope with structured before/after diff. Six mutation kinds: write/append/clear/delete/forget/consolidate. Optional `MemoryConsolidationAudit` subblock cross-references canonical pipeline block #43. Cross-runtime composition via `subject.metadata.memory_audit`.
- **HearthOS bounded-authority envelope** (W4.1 + W4.2.a). Schema 9 `phionyx.bounded_authority_envelope.v1`. Eight event types covering the bounded-authority lifecycle (propose / execute_requested / execute_approved / execute_rejected / execute_completed / safety_gate_blocked / authority_tier_change / proof_recorded). Seven preservation rules formalised in a separate `verifyBoundedAuthority()` verifier. Three pinned demo traces (Diagnostic, Weekly Reset, Boundary Script) under `examples/hearthos_traces/` — reviewer-runnable offline.
- **v0.7.0 schema portfolio document** at `examples/envelopes/v0_7_schema_portfolio.md` — eight schemas catalogued; versioning policy reaffirmed.

### Changed

- `examples/envelopes/rge_v0_2/rge_v0_2.schema.json` extended with W2.1 and W2.2 additive fields.
- `examples/envelopes/rge_v0_2/rge_v0_2.md` (spec doc) §2.2.1 + §2.2.2 updated.
- `examples/envelopes/rge_v0_2/rge_v0_2_mcp_envelope.json` example envelope extended.

### Migration

**Nothing required from v0.6.0.** All schemas backward compatible. New fields optional or null-default. New schemas (8, 9) are additive new identifiers. Mixed-schema chains still rejected — keep one schema id per trace.

### Tests

70/70 across new/extended packages: 20 phionyx-mcp-server (W2.1+W2.2) + 20 phionyx-letta (W3) + 30 phionyx-compliance (W1). Three pinned HearthOS traces self-verify deterministically (14 + 16 + 11 envelopes, chains intact).

### PyPI release

`phionyx-letta` and `phionyx-compliance` PyPI uploads are gated on GitHub Actions billing resolution. Release workflow infrastructure is ready; PyPI publish will trigger when CI is unblocked.

---

## [0.6.0] — 2026-05-25

**Theme: Multi-Agent Evidence.**

v0.6.0 answers the next question after *a model saying fixed is not evidence*: when multiple agents collaborate, what shape lets a reviewer reconstruct the flow from the signed evidence alone, with no insider access and no trust in any single agent's narration?

Four features ship: the multi-agent envelope chain (F5), an LLM-as-judge eval primitive (F9, in the separate `phionyx-eval` companion package), cross-runtime evidence portability for Langfuse / LangSmith (F13, also in `phionyx-eval`), and the F12-plus extension to the Claude Code plugin from v0.5.1. Plus the v0.6 schema portfolio is published as a stabilisation candidate.

### Added

- **F5 — `subagent_chain` v0.1 active spec.** Multi-agent / subagent audit chain block. The block reserved in RGE v0.2 §2.2.3 as `reserved-for-v0.6.0-f5` is now an active specification.
  - `phionyx_core.contracts.envelopes.SubagentChainV0` — Pydantic v2 model.
  - `phionyx_core.contracts.envelopes.SubagentChainProtocol` — Literal type covering `a2a`, `agntcy`, `phionyx_native`, `langgraph_subgraph`, `crewai`, `autogen`.
  - `phionyx_core.contracts.envelopes.SubagentChainRole` — Literal type covering `root`, `child`, `leaf`.
  - `phionyx_core.contracts.envelopes.compute_handoff_signing_body()` — canonical-JSON encoding (sort_keys, no whitespace, ASCII-safe) of the 5-field handoff signing body per RFC §2.4.
  - JSON Schema (Draft 2020-12) at `examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.schema.json`.
  - 6-file RFC bundle in `examples/envelopes/subagent_chain_v0_1/`: RFC (`subagent_chain_v0_1.md`), JSON Schema, 3-agent minimal envelope example, A2A protocol-mapped worked example, extended walkthroughs, migration doc from RGE v0.2 reserved status to v0.1 active.
- **RGE v0.2 RFC bundle backport.** `examples/envelopes/rge_v0_2/` — the 6-file RFC originally shipped with v0.4.0 W1, now published in the open repo alongside the new subagent_chain v0.1 RFC.
- **ADR-0007 — Multi-Agent Envelope Chain.** Decision record in `docs/adr/0007-multi-agent-envelope-chain.md`.
- **v0.6 Schema portfolio.** `examples/envelopes/v0_6_schema_portfolio.md` catalogues the seven schemas Phionyx publishes at v0.6.0 across the Core SDK and four companion packages, plus the additive-only versioning policy.
- **v0.6.0 release notes.** `docs/releases/v0.6.0_RELEASE_NOTES.md` — full release content + effort matrix + what is NOT in release + migration guide.
- **Public surface growth.** `phionyx_core.contracts.envelopes.__all__` grew from 8 to 12 exports (additive only).

### Changed

- **`phionyx_core.__version__`** 0.5.0 → 0.6.0.
- **`pyproject.toml` version** 0.5.0 → 0.6.0.

### Companion package shipping alongside (separate PyPI releases, not phionyx-core code)

- **`phionyx-eval` 0.1.0a1** — LLM-as-judge primitive (F9) + Langfuse / LangSmith import-only cross-runtime portability (F13). New companion package; first release at v0.6.0. Repo: `halvrenofviryel/phionyx-eval`.
- **Claude Code plugin F12-plus extension** — `/phionyx:replay-trace` slash command added to the v0.5.1 plugin for walking multi-agent envelope chains. Two worked walkthroughs (LangGraph + OpenAI Agents). No new MCP tools; the command interprets persisted envelopes.

### What is NOT in v0.6.0

- Cross-runtime export (Phionyx → Langfuse / LangSmith) — v0.7.0 candidate.
- OpenAI Agents `subagent_chain` integration — demand-driven add in v0.7.0+.
- AGNTCY/ACP worked example — v0.6.x patch if adoption signals.
- Full A2A protocol adapter — v1.1 per public roadmap.

### Breaking changes

**None.** v0.6.0 is fully backwards-compatible with v0.5.0. The new optional `subagent_chain` field added to `phionyx.langchain_event_envelope.v1` (in the companion package) is strictly additive — old envelopes verify byte-identically.

---

## [0.5.0] — 2026-05-24

**Theme: Distribution & First-Run Proof — ecosystem milestone release.**

v0.5.0 is an **ecosystem milestone release**. The `phionyx-core` public API surface is unchanged from v0.4.0 except for one new discoverability namespace (`phionyx_core.__companions__`). What changed is the surrounding ecosystem: two new PyPI companion packages, two new website discovery surfaces, and three runnable framework example bundles. The milestone shipped ~2 months ahead of its 2026-07-28 target.

### Added

- **`phionyx_core.__companions__`** — a discoverable `dict` listing the five official Phionyx ecosystem packages on PyPI. Each entry is `(pypi_name, github_repo, what_it_does)`. Surfaced so downstream users can enumerate the ecosystem from inside `phionyx-core` without hardcoding the list. Added to `__all__`; backwards-compatible.

### Ecosystem additions (separate PyPI releases, not phionyx-core code)

- **`phionyx-langchain-langgraph` 0.1.0a1** (PyPI alpha) — native adapters for LangChain `BaseCallbackHandler` and LangGraph supervisor patterns. Every LangChain chain / tool / LLM event and every LangGraph supervisor handoff is recorded as a signed, hash-chained envelope (`AgentMessageEnvelope` inner record + `phionyx.langchain_event_envelope.v1` outer schema). 52 tests. Repo: [halvrenofviryel/phionyx_langchain_langgraph](https://github.com/halvrenofviryel/phionyx_langchain_langgraph).
- **`phionyx-openai-agents` 0.1.0a1** (PyPI alpha) — OpenAI Agents SDK tracing bridge. Implements the SDK's `TracingProcessor` interface (six abstract methods). `AgentMessageEnvelope` inner record + `phionyx.openai_agents_event_envelope.v1` outer schema. SDK-deferred import (loads cleanly without `openai-agents` installed). 37 tests including a 5-thread × 20-callback concurrency test that verifies cross-thread emission lock. Repo: [halvrenofviryel/phionyx_openai_agents](https://github.com/halvrenofviryel/phionyx_openai_agents).
- **`phionyx.ai/standard`** — 3-button discovery hero on the Evaluation Standard page. CTAs: Read the Standard (GitHub spec), See a Sample Report (GitHub example), Bridge via Inspect AI (`phionyx-eval-inspect` companion).
- **`phionyx.ai/examples`** — unified showcase comparing the three framework bundles side-by-side. Each card: framework name, package + PyPI link, what the example shows, expected envelope output, install command, run command, GitHub source link.

### Unchanged

- 46-block pipeline contract v3.8.0 — no block additions, removals, or reordering.
- All v0.4.0 public API exports (87 functions/classes/types) — preserved.
- All v0.4.0 evidence guarantees — preserved.
- `phionyx-mcp-server`, `phionyx-pipeline-mcp`, `phionyx-eval-inspect` — unchanged from v0.4.0.

### Release notes

Full milestone release notes (with plan-vs-actual variance breakdown and v0.6.0 preview) live in the Viryel monorepo at `docs/releases/v0.5.0_RELEASE_NOTES.md`.

---

## [0.4.0] — 2026-05-19

**Theme: signed runtime evidence over agentic AI — MCP + OpenTelemetry + Inspect AI + RGE v0.2.**

v0.4.0 extends Phionyx Core from a deterministic governance runtime into a full evidence stack that emits signed records both *outward* (third-party MCP tool calls) and *inward* (the agent's own self-reports), exports those records into vendor-portable OpenTelemetry GenAI spans, and bridges them into Inspect AI's evaluation logs for the eval frameworks several government safety institutes already use.

The hot lane is four feature releases plus one schema RFC, shipped in five sequential weeks (W1 → W4 + W2.1 integration):

### Added — W1: Reasoned Governance Envelope v0.2 RFC

- **RGE v0.2 6-file RFC artifact set** in [`examples/envelopes/rge_v0_2/`](examples/envelopes/rge_v0_2/) — schema (Draft 2020-12), RFC text (motivation, design, signature scope, alternatives), worked examples, MCP-envelope sample, migration matrix v0.1 → v0.2. Four optional blocks (`reasoning`, `retrieval`, `subagent_chain`, `mcp_tool_audit`) reserve the surface for downstream features; v0.1 envelopes validate against v0.2 after bumping the `schema` string.

### Added — W2: MCP trust boundary governance layer

- **`phionyx-mcp-server` companion package** ([github.com/halvrenofviryel/phionyx-mcp-server](https://github.com/halvrenofviryel/phionyx-mcp-server), AGPL-3.0). MCP trust boundary for any MCP-capable host (Claude Desktop, Cursor, Zed, VS Code, JetBrains). Eight-capability surface aligned with arXiv:2512.06556 (Jamshidi et al., *Securing the Model Context Protocol*) — tool poisoning, shadowing, rug pulls. Five capabilities fully implemented (descriptor hash, change detection, I/O hash, signed envelope, chain verification CLI), three stubbed with explicit `not_implemented` markers (permission scope, user approval state, runtime anomaly flag). Persists envelopes under `~/.phionyx/mcp_audit/<trace_id>/` with HMAC signing in demo mode (Ed25519 in production).

### Added — W2.1: Shared-trace integration (ADR-0006)

- **`phionyx-pipeline-mcp` companion package** ([github.com/halvrenofviryel/phionyx-pipeline-mcp](https://github.com/halvrenofviryel/phionyx-pipeline-mcp), AGPL-3.0). Self-governance MCP for Claude Code — three-layer claim verification: LLM declaration → `git diff` truth → deterministic physics gate (a 9-block composition from the 46-block runtime). Returns a directive: `pass | regenerate | reject`.
- **Shared trace contract** between the two MCPs via `PHIONYX_TRACE_ID` env var with `~/.phionyx/active_trace` file fallback. One Claude Code session = one trace = end-to-end view of every third-party tool call AND every agent self-claim gate decision. `phionyx_session_report` surfaces the server-MCP envelope chain head + validity inline (count, head_hash, valid, broken_at) so a reviewer can join both layers in one JSON. Read-only across the package boundary; no cross-package write coupling.

### Added — W3: OpenTelemetry GenAI exporter (experimental, version-pinned)

- **`phionyx_core.telemetry.otel_export`** — maps RGE v0.1 / v0.2 envelopes to OpenTelemetry GenAI spans with hybrid attribute namespace: standard `gen_ai.*` for vendor-portable identification (system, request.model, response.id, usage tokens, operation name) plus `phionyx.*` for governance evidence with no spec counterpart (trace_id, decision, policy basis, path blocks, integrity chain, MCP tool audit fields).
- **Version-pinning** via `phionyx_core/telemetry/otel_semantic_v1_36_0.py` — frozen attribute name table pinned to OpenTelemetry GenAI semantic conventions v1.36.0 (status: Development). Override with `PHIONYX_OTEL_SEMANTIC_VERSION`. Unsupported versions raise `ValueError` at first call rather than silently emitting against the wrong spec. Bump policy: [`docs/conventions/otel_semantic_bump_policy.md`](docs/conventions/otel_semantic_bump_policy.md) — two-version compatibility window, CHANGELOG entry on every spec change we tracked.
- **Opt-in** via `PHIONYX_OTEL_EXPORT_ENVELOPES=true`. Default is OFF. Clean no-op when the OpenTelemetry SDK isn't installed (the SDK remains an optional dependency).
- **Examples** at [`examples/otel_export/`](https://github.com/halvrenofviryel/phionyx-research/tree/main/examples/otel_export) — one-command Tempo + Grafana docker-compose stack with `run_example.py` emitting one envelope as an OTLP span.

### Added — W4: Inspect AI interoperability bridge

- **`phionyx-eval-inspect` companion package** ([github.com/halvrenofviryel/phionyx-eval-inspect](https://github.com/halvrenofviryel/phionyx-eval-inspect), AGPL-3.0). One-way interoperability adapter: RGE envelope chain → Inspect AI `.eval` log file. Phionyx-specific evidence (trace id, decision, policy basis, pipeline path, integrity chain, MCP tool audit fields) lives under `sample.metadata.phionyx` — namespaced so native Inspect tooling ignores it; Phionyx-aware tools surface it. CLI: `phionyx-eval-inspect convert` / `show`. Schema pinned to Inspect log format v0.3.x.
- **Strict framing — what this is NOT.** Not a partnership with, or endorsement by, UK AISI, US CAISI, EU AI Office, Japan AISI, or Korea AISI. Not a scorer. Not a required dependency on `inspect-ai` (the adapter writes the standard `.eval` JSON shape directly; the `[inspect]` extra exists only for `inspect view`). The framing is interoperability, not endorsement.
- **Wiring documentation** ([`phionyx-eval-inspect/docs/wiring_phionyx_mcp_in_inspect_task.md`](https://github.com/halvrenofviryel/phionyx-eval-inspect/blob/main/docs/wiring_phionyx_mcp_in_inspect_task.md)) — concrete code snippet for registering `phionyx-mcp-server` as a tool source inside an Inspect AI eval task, closing the loop so the agent under evaluation goes through Phionyx's outward trust boundary on every tool call.

### Tests

- `phionyx_core/telemetry/` OTel exporter: 22 unit tests (mapping, namespace split, mcp_tool_audit branch, None scrubbing, events, opt-in env var, version pinning, no-op fallbacks).
- W2.1 shared-trace integration: 7 tests (env precedence, file fallback, generate+persist, cross-MCP convergence, session_report join, tamper detection, graceful degradation).
- Server MCP regression: 22 tests stay green.
- `phionyx-eval-inspect` standalone: 22 tests (adapter shape, sample fields, events, metadata.phionyx, None scrubbing, schema pinning, write_log persistence + path-traversal sanitisation, CLI smoke).

### Companion-package ecosystem

| Package | Role |
|---|---|
| **`phionyx-core`** (this) | Deterministic AI runtime governance — 46-block pipeline, kill switch, ethics + safety gates, signed audit envelopes, OTel exporter |
| **`phionyx-mcp-server`** | MCP trust boundary (descriptor + audit chain) |
| **`phionyx-pipeline-mcp`** | Self-governance gate over the agent's own claims (three-layer verification) |
| **`phionyx-eval-inspect`** | Interoperability bridge into Inspect AI eval logs |

All four are AGPL-3.0. The three companions live in their own GitHub repositories under `halvrenofviryel/*` and follow `phionyx-core`'s release cadence.

---

## [0.3.0] — 2026-05-03

**Theme: from "self-asserted claims" to "reviewer-verifiable artifact."**

The headline change is the **reproducibility pack** that now ships
alongside every tagged release. It bundles JUnit XML, coverage XML,
determinism hashes, a benchmark JSON, the canonical governed-response
envelope, an audit-chain example, and a sample OpenTelemetry trace —
small enough (< 1 MB) to attach to a GitHub release and ship to Zenodo
for DOI minting. The point is that an external reviewer can verify
every load-bearing claim on `phionyx.ai/evidence` without trusting any
prose in this repo.

### Added

- **Reproducibility pack** (`scripts/make_reproducibility_pack.py`) —
  one-shot generator that produces `pytest_report.xml`, `coverage.xml`,
  `determinism_hashes.json`, `benchmark_results.json`,
  `governed_response_example.json`, `audit_chain_example.json`,
  `otel_trace_example.json`, and `reproducibility_report.md`. Runs
  locally; `--zip` attaches a versioned archive. CI release workflow
  builds the pack on every tag and uploads it as a GitHub release
  asset via `softprops/action-gh-release`.
- **JSON Schema for the governed-response envelope**
  (`examples/envelopes/governed_response.schema.json`) — Draft 2020-12,
  fully constrained, plus a small `validate.py` that reports
  JSON-Pointer-precise failures. Ensures downstream consumers can
  validate Phionyx envelopes deterministically.
- **OpenTelemetry sample trace** — hand-crafted span tree (one span per
  executed pipeline block) shipped in the reproducibility pack. The real
  exporter is wired by the `[telemetry]` extra; this file documents the
  expected attribute names so external OTel tooling can validate before
  the optional dependency is installed.
- **mypy strict gate (full SDK)** — every module under `phionyx_core/`
  is now type-checked. 327 source files, zero errors. Six waves of
  cleanup (#43, #45, #46, #48, #49, #50) folded the entire tree under
  `mypy phionyx_core` in CI.

### Changed

- **Honest-positioning sweep across the public surface (Phase 1).**
  Test count corrected: README now reports the public CI subset (was
  conflated with the internal monorepo corpus). FastAPI example status:
  "Planned" → "Runnable" (it always was; the doc was wrong). New
  "Scope: what Phionyx is, and is not" + "Known limitations" sections
  in README and on phionyx.ai. New tagline:
  *"Phionyx makes the governance path deterministic — not the model."*
  L3 evaluation level renamed from "Certification-Grade" to
  "Certification-Oriented Evidence Profile" to avoid self-certification
  framing. New Evidence Matrix at `phionyx.ai/evidence` with 19
  itemised claims, each with evidence path + reproducibility command +
  status (public / beta / planned / pending) and a 10-minute Reviewer
  Quick Path.
- **Pytest markers registered** in `pyproject.toml` (`unit`, `contract`,
  `critical`, `smoke`, `safety`, `adversarial`) so `--strict-markers`
  no longer breaks collection when marker-using suites run together.
  With markers registered the combined collection is now 1,137 tests
  (was effectively 4-error-on-collect when run together).
- **Pydantic V2 plugin** wired into mypy (`pydantic.mypy`) — `Field(None, ...)`
  defaults now type-check correctly.

### Fixed

- `state_adapter.py` was reading `tag.semantic_context` on
  `EventReference`, which no longer has that attribute. Switched to
  `tag.tag`. Surfaced by mypy wave 4.
- `compiler.py:compile_profiles()` was calling a non-existent
  `loader.load_all_profiles()`. Replaced with
  `[loader.load_profile(name) for name in loader._load_profiles()]`.
  Surfaced by mypy wave 5.
- `complexity_engine.py` was calling `ast.walk(node.orelse)` on a
  `list[stmt]`. `ast.walk` requires an `AST`; rewrote to walk each
  statement.
- `examples/fastapi/main.py` migrated `datetime.utcnow()` →
  `datetime.now(timezone.utc)`.

### Documentation

- `docs/strategic/MASTER_PLAN_2026_05.md` (v2.0) — twelve-week roadmap
  from "self-asserted claims" to "independently validated artifact",
  revised after three rounds of external review. Reproducibility Pack
  is the centre, not a side dish.
- README "Known limitations" grounded in implementation reality
  (controlled benchmarks, no third-party audit, no production
  deployment claims, LLM quality not guaranteed, compliance mappings
  are evidence not legal certification, Φ/entropy metrics
  experimental).

### Repo metadata

- GitHub repo description tightened to: *"Deterministic AI runtime
  governance for LLM systems — treating model output as measurement,
  not authority. 46-block pipeline, audit trail, kill switch."*

---

## [0.2.1] — 2026-05-01

First PyPI release. Public surface is unchanged from the v0.2.0
GitHub release (2026-04-26); the work in this version is packaging
hygiene, dependency correctness, and CI / release infrastructure so
`pip install phionyx-core` behaves as advertised on a clean machine.

The version bump from 0.2.0 to 0.2.1 is bookkeeping: the v0.2.0 tag
was already attached to the GitHub-only release that introduced the
public source drop, never reached PyPI, and stays untouched. v0.2.1
is the first artifact that lives on pypi.org.

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
