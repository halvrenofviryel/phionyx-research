# Reasoned Governance Envelope (RGE) v0.2 — Specification

> **Status:** Draft RFC (2026-05-19). Reviewer pass 2 approved scope; founder approval pending W1 kickoff merge.
> **Predecessor:** `phionyx.governed_response_envelope.v0_1` (de-facto schema implicit in an early launch-wrapper prototype, ~2026-05-08).
> **Scope:** Per-turn signed evidence envelope for governed AI runtime decisions. Backward-compatible extension of v0.1.
> **Author:** Phionyx Research (`founder@phionyx.ai`, ORCID `0009-0002-3718-4010`).
> **License:** AGPL-3.0-or-later (schema), CC-BY-4.0 (this RFC document).
> **Companion artifacts (this directory):**
> - `rge_v0_2.schema.json` — canonical JSON Schema (Draft 2020-12)
> - `rge_v0_2_examples.md` — worked walkthroughs
> - `migration_v0_1_to_v0_2.md` — compatibility matrix + opt-in pattern
> - `rge_v0_2_minimal_envelope.json` — v0.1 surface only (no v0.2 blocks)
> - `rge_v0_2_mcp_envelope.json` — full mcp_tool_audit populated

## 1. Motivation

The Phionyx governance wrapper emits a per-turn envelope that records (a) the runtime decision, (b) the pipeline-block path taken, (c) numeric coherence metrics, and (d) a hash-chained integrity record. We refer to this as the **Reasoned Governance Envelope (RGE)** — the Phionyx reference producer of the [AI Runtime Evidence Protocol (AIREP)](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol). v0.1 was implicit in the wrapper implementation; this RFC fixes it as a versioned schema and extends it for four 2026 trends:

1. **MCP trust boundaries.** The MCP specification ([2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)) explicitly defers protocol-level security to implementors: *"MCP itself cannot enforce these security principles at the protocol level, implementors SHOULD..."*. Recent literature (arXiv:[2512.06556](https://arxiv.org/abs/2512.06556), Jamshidi et al., "Securing the Model Context Protocol") describes a three-class threat taxonomy: tool poisoning, shadowing, and rug pulls. RGE v0.2 reserves an `mcp_tool_audit` block (8 capabilities) so an MCP host using Phionyx can attest descriptor integrity, change detection, scope, I/O hashes, approval, anomaly, and chain verification per call.
2. **RAG evidence chains.** Retrieval-augmented generation systems admit, cite, contradict, or reject candidate documents. Existing audit logs record retrieval scores; RGE v0.2 reserves a `retrieval` block that records the **operational role chain** (retrieved → admitted → cited → contradicted → rejected → signed) with per-document signed evidence pointers.
3. **Multi-agent handoffs.** A2A, AGNTCY/ACP, LangGraph subgraphs, CrewAI, and AutoGen all rely on cross-agent handoffs that are currently logged but not tamper-evident. RGE v0.2 reserves a `subagent_chain` block carrying parent envelope hash + handoff signature + protocol identifier.
4. **Reasoning surface metadata.** o1/o3 reasoning_summary, Claude thinking blocks, DeepSeek-R1, and Gemini Flash Thinking surface partial rationale to the runtime. Phionyx does **not** store raw chain-of-thought (provider-private); it stores **decision rationale + confidence delta + evidence links**. RGE v0.2 schematises the v0.1 `reasoning` block, adds `confidence_delta` and `evidence_links[]`, and documents the scope discipline ("audit the decision the thinking led to, not the thinking itself").

The v0.2 schema is **strictly additive**: every new field is optional, and every v0.1-shape payload validates against v0.2 after the single change of bumping the `schema` string from `..._v0_1` to `..._v0_2`. Producers may adopt v0.2 blocks one at a time as their downstream consumers grow capability.

## 2. Design

### 2.1 Required core (v0.1 surface, frozen)

The seven required top-level properties carry forward unchanged from v0.1:

| Property | Purpose |
|---|---|
| `schema` | Schema identifier. v0.2 envelopes set `phionyx.governed_response_envelope.v0_2`. |
| `subject` | Runtime identity, producer label, turn index, timestamp. |
| `input` | User text, governance state vector, input safety verdict. |
| `path` | Ordered pipeline-block dispositions (admit/block/record/defer/bypass). |
| `output` | Final emitted text + `redacted` flag. |
| `metrics` | Φ_cognitive, Φ_physical, Φ_total, cognitive verdict. |
| `integrity` | `previous`/`current` SHA-256 hashes + signature + canonical-JSON flag. |

The v0.1 baseline is fixed by `governance_wrapper_demo/wrapper.py::govern_turn` output as captured in `rge_v0_2_minimal_envelope.json`. Any departure from that baseline is a v0.2 break, not a v0.1 break.

### 2.2 Optional v0.2 blocks

Four optional top-level properties extend the surface. All carry a `status` field that distinguishes a placeholder envelope (reserved for a future implementation) from a runtime-populated envelope (`active`).

#### 2.2.1 `reasoning` (Phionyx Feature F4)

Decision rationale + confidence delta + evidence links. **NOT raw chain-of-thought storage.**

Required keys: `runtime_decision` (enum: release / block / defer / redact), `decision_reason` (string).

Optional keys:

- `model_proposed_action` — tool call shape the producer proposed.
- `model_stated_rationale` — publicly stated model rationale (NULL if none).
- `runtime_policy_basis[]` — ordered policy/gate identifiers fed into the runtime decision.
- `rationale_action_consistency` / `policy_alignment_score` — `[0, 1]` floats or NULL.
- `confidence_delta` — producer-reported confidence delta across the turn (provider semantics vary; document in `scoring_method`).
- `evidence_links[]` — typed pointers (retrieval / tool_call / memory / policy / external_url) to evidence the rationale depends on.
- `scoring_method` — scorer identifier so downstream consumers can interpret scores.

**v0.7.0 W2.1 (F4) extension — three additional optional fields:**

- `rationale_summary` — runtime-produced, length-bounded one-line distillation of the reasoning surface, distinct from `model_stated_rationale` (which captures whatever the producer publicly stated). Surfaces in dashboards and compliance reports. NULL when no rationale surface was produced.
- `knowledge_sources_consulted[]` — ordered list of typed sources the producer consulted while forming this turn's reasoning, even sources that did not become citations. Enum kinds: `retrieval_corpus`, `memory_block`, `tool_output`, `tool_descriptor_clause`, `static_doc`, `system_prompt`, `external_api`. Complements `evidence_links[]` (which lists artefacts the rationale depends on).
- `constraints_acknowledged[]` — ordered list of constraints the producer publicly acknowledged. Enum kinds: `policy`, `user_directive`, `safety_boundary`, `tool_descriptor_clause`, `regulatory`, `self_imposed`. Each carries an optional `satisfied` boolean. Surfaces constraint-awareness even when no constraint was binding for the decision.

The block is partially live in v0.1 (the wrapper populates a subset). F4 ("Reasoning surface audit") delivers the full structured surface in v0.7.0.

#### 2.2.2 `retrieval` (Phionyx Feature F8)

Operational role chain for RAG evidence. `status` distinguishes reserved (`reserved-for-v0.4.1-f8`) from active.

Required keys: `documents[]` (each with `id`, `role` ∈ {retrieved, admitted, cited, contradicted, rejected}).

Optional per-document keys: `score`, `hash`, `signed_evidence_ref`. Optional block-level keys: `store_id`, `query_hash`.

The block's job is to make RAG **trajectories** auditable, not just retrieval scores. *"Document X was admitted at step 2, cited in the answer at step 5, contradicted by document Y at step 7, signed into the audit chain at step 8"* is the kind of replay this block enables.

**v0.7.0 W2.2 (F8) extension — block-level + per-document provenance:**

Block-level:
- `corpus` (object | null) — named corpus metadata (more semantic than `store_id`). Fields: `name` (required), `version` (optional, may be semver / content hash / snapshot timestamp), `language` (optional BCP-47 tag).
- `similarity_threshold` (number 0.0–1.0 | null) — block-level minimum-similarity cutoff used to gate documents from `retrieved` into the candidate set. NULL when no threshold was applied.
- `query_text_hash` (string | null) — SHA-256 of the user-or-system-formatted query TEXT (distinct from `query_hash`, which may hash the structured store-query object).

Per-document:
- `chunk_offset` (integer ≥0 | null) — zero-indexed chunk offset within the source document when chunked retrieval is used.
- `source_url` (string | null) — human-resolvable URL to the source document (distinct from `id`, which may be a store-internal key).
- `retrieved_at` (ISO-8601 | null) — when this specific document was retrieved (may predate the envelope's `timestamp_utc` when retrieval is cached).

F8 ("Retrieval audit") delivers the populating logic in v0.7.0. The reserved phase ran 2026-04-26 → 2026-05-26; v0.7.0 W2.2 flips Phionyx's own producers from `reserved-for-v0.4.1-f8` to `active`. Builder helper: `phionyx_mcp_server.audit_chain.build_retrieval_block(RetrievalContext)`.

#### 2.2.3 `subagent_chain` (Phionyx Feature F5)

> **Status as of 2026-05-25:** **active** — v0.1 specification published as a sibling RFC bundle at [`examples/envelopes/subagent_chain_v0_1/`](../subagent_chain_v0_1/subagent_chain_v0_1.md). The full schema (`subagent_chain_v0_1.schema.json`), Pydantic model (`phionyx_core/contracts/envelopes/subagent_chain.py`), LangGraph supervisor adapter, and worked examples (LangGraph + A2A) all shipped in v0.6.0 W1 (commits `a5795cca` → `31d523c2`). See [ADR-0007](../../docs/adr/0007-multi-agent-envelope-chain.md) for the decision record.

Multi-agent handoff chain. v0.2-era `status` enum (`reserved-for-v0.6.0-f5`, `active`) is retained on the wire for backward-compatibility with envelopes emitted during the reserved phase; new producers MUST set `status: "active"` and populate the full v0.1 surface defined in the sibling RFC.

The v0.2 sketch named three required fields (`agent_id`, `role` ∈ {root, child, leaf}) and four optional ones (`parent_envelope_hash`, `handoff_signature`, `protocol` enum, plus implicit nullability). v0.1 active promotes five fields to required when `status == "active"`: `chain_depth`, `protocol`, `parent_envelope_hash`, `handoff_signature`, `handoff_timestamp_utc`. It also adds three optional fields (`parent_agent_id`, `child_agent_ids[]`, `protocol_data`) and three role-based invariants (root depth=0 + null parent fields; non-root depth≥1 + non-null parent fields; leaf has zero `child_agent_ids`). See the [v0.1 RFC §2](../subagent_chain_v0_1/subagent_chain_v0_1.md#2-design) for the full field table and [migration doc](../subagent_chain_v0_1/migration_rge_v0_2_to_subagent_v0_1.md) for adoption paths.

#### 2.2.4 `mcp_tool_audit` (Phionyx Feature F1)

MCP trust boundary governance. The 8-capability MVP scope of F1 maps 1:1 onto the eight optional fields of this block (besides `status`). `status` distinguishes reserved (`reserved-for-v0.4.0-f1`) from active.

| Capability | Field | Purpose |
|---|---|---|
| 1 | `tool_descriptor_hash` | Ed25519-signed snapshot of the tool descriptor at this turn |
| 2 | `descriptor_change_detected` | Boolean; rug-pull detection vs user-approved baseline |
| 3 | `tool_permission_scope[]` | Capability profile entries authorised for this tool |
| 4 | `tool_call_io_hash` | `{input_hash, output_hash}` for this call |
| 5 | `user_approval_state` | `{approved, approval_ref, approved_at_utc}` consent capture |
| 6 | `runtime_anomaly_flag` | `{anomaly, source, severity, detail}` from behavioral_drift / action_intent_gate |
| 7 | `signed_envelope_ref` | URI/hash pointing back to the signed RGE envelope record |
| 8 | `chain_verify_command` | CLI command users can run to verify the chain (e.g. `phionyx-mcp verify-chain --trace ... --turn ...`) |

F1 ("MCP trust boundary governance layer") delivers populating logic in v0.4.0. Reviewer pass 2 (2026-05-19) explicitly enumerated these eight capabilities as the MVP surface; this RFC freezes the wire shape so F1 implementation does not invalidate envelopes produced during the W1 (this) RFC window.

### 2.3 Hash chain semantics

Unchanged from v0.1: each envelope carries `integrity.previous` (hash of the prior envelope's `integrity.current`) and `integrity.current` (SHA-256 over canonical-JSON-encoded payload + previous). Genesis envelopes use `sha256:0000000000000000`. v0.2 hashes the entire envelope **including** any populated v0.2 blocks; populating `reasoning` after the fact (e.g. by a downstream scorer) is therefore a fork, not an in-place mutation.

The launch wrapper uses HMAC signatures (`demo-hmac:<hex>`) for transparency; production Core uses Ed25519 (`ed25519:<hex>`). Key identity / rotation is tracked separately and is out of scope for this RFC.

### 2.4 Canonical JSON

`integrity.canonical_json = true` indicates the hash was computed over RFC-8785-style canonical JSON (`sort_keys=true`, no whitespace, `ensure_ascii=true`). v0.2 envelopes MUST be canonical-JSON-hashable; the field exists so a non-canonical implementation can emit envelopes for development without breaking the schema, but their hashes are not verifiable.

## 3. Alternatives Considered

### 3.1 Break compatibility and ship v1.0

Discarded. v0.1 has already shipped in an earlier launch-wrapper prototype and is depended on by existing producers. A breaking v1.0 would invalidate those without proportionate benefit. v0.2's strictly-additive extension preserves the v0.1 surface and lets each v0.2 block adopt independently.

### 3.2 Separate schemas per concern (MCP-envelope.schema.json, RAG-envelope.schema.json, ...)

Discarded. The whole point of RGE is that **one envelope shape** records one turn's full evidence trail. Splitting would force downstream consumers (Inspect AI storage adapter, OTel exporter, audit replay tooling) to join across schemas. Single schema with optional blocks is the disciplined choice.

### 3.3 Use OpenTelemetry GenAI span format directly

Discarded. OTel GenAI semantic conventions are Status = Development (per opentelemetry.io/docs/specs/semconv/gen-ai as of 2026-05-19); conventions are still in flux. RGE is a signed evidence envelope; OTel spans are a streaming observability format. F2 (OTel exporter) is the bridge between RGE and OTel spans, version-pinned + opt-in env-var. Adopting OTel as the canonical contract would couple RGE to a still-evolving spec.

### 3.4 Store raw chain-of-thought in `reasoning`

Discarded on two grounds. (1) Providers (OpenAI, Anthropic, DeepSeek, Google) keep reasoning tokens private; the model the runtime sees is the **summary surface**, not the raw chain. (2) Storing raw CoT (even if available) creates a regulatory and privacy hazard. Phionyx's claim is *"audit the decision the thinking led to"* — decision rationale + confidence delta + evidence links. The `reasoning` block enforces this scope by typing.

### 3.5 Defer MCP audit until F1 implementation

Discarded. The 8-capability surface is documented enough to freeze the wire shape now; deferring would force a v0.3 schema bump when F1 lands, breaking RGE consumers built against v0.2. Reserved-status fields with explicit `reserved-for-v0.4.0-f1` markers solve the timing problem without delaying the schema.

## 4. Security Considerations

### 4.1 Signature scope

`integrity.signature` covers `integrity.current` (which transitively covers all envelope content via the canonical-JSON hash) **with one explicit exclusion**: `mcp_tool_audit.signed_envelope_ref` is OUTSIDE the hash domain because it is a self-reference (`envelope://<integrity.current>`) that would otherwise create a hash-fixpoint paradox. Builders and verifiers MUST normalise this field to `None` before hashing; the field is persisted alongside the envelope so external consumers can resolve it, but it is NOT covered by `integrity.signature`. A consumer relying on `signed_envelope_ref` for trust SHOULD instead derive it from `integrity.current`. Forging a v0.2 envelope requires either (a) the signing key (Ed25519 private key for Core; HMAC secret for the launch wrapper) or (b) finding a SHA-256 preimage that matches a chain neighbour — both outside the threat model of practical attackers as of 2026.

### 4.2 Replay protection

Replaying an old envelope at the same `(trace_id, turn_index)` position is detectable only via external state (the verifier knows what `turn_index` was last legitimately admitted). RGE does not solve replay alone; it provides the evidence basis for a replay detector.

### 4.3 mcp_tool_audit threat model

Aligns with arXiv:2512.06556 Jamshidi et al. taxonomy:

- **Tool poisoning** (adversarial instructions hidden in descriptors): `tool_descriptor_hash` + signed baseline detects post-load tampering; `descriptor_change_detected` catches drift after approval.
- **Shadowing** (trusted tools indirectly compromised through contaminated shared context): `runtime_anomaly_flag` from `behavioral_drift` and `action_intent_gate` records the runtime's observation; the envelope does **not** prove the input context was uncontaminated — that's an LLM-on-LLM semantic-vetting concern outside RGE's scope.
- **Rug pulls** (post-approval descriptor changes): `descriptor_change_detected` flags the divergence; `user_approval_state.approved_at_utc` anchors the baseline timestamp.

Jamshidi et al. propose three mitigations (RSA manifest signing, LLM-on-LLM semantic vetting, runtime heuristic guardrail). RGE supports mitigations 1 and 3 directly; mitigation 2 is downstream of this block (a separate `semantic_review` block is out of scope for v0.2 but a candidate for v0.3).

### 4.4 Evidence links integrity

`reasoning.evidence_links[]` and `retrieval.documents[].signed_evidence_ref` are pointers, not embedded content. A verifier MUST follow the pointer and verify the referenced content's hash against the envelope's claim. RGE does not store evidence inline because (a) evidence sizes vary unboundedly and (b) GDPR/privacy regimes may require evidence redaction without invalidating the envelope chain.

### 4.5 Provider rationale fidelity

`reasoning.model_stated_rationale` is whatever the producer surfaced. RGE does **not** claim the rationale faithfully reflects the model's internal reasoning; it claims the rationale was the *publicly stated* surface and the runtime decision was made against it. This distinction matters for legal admissibility: the runtime can defend "I acted on the rationale the model surfaced", not "I knew what the model was actually thinking".

## 5. Extension Hooks

v0.2 is the first schema-formal RGE release. Hooks for future versions:

- **v0.3 candidate:** `semantic_review` block for LLM-on-LLM tool descriptor vetting (Jamshidi et al. mitigation 2).
- **v0.3 candidate:** `memory_diff` block for stateful-agent memory mutations per turn (Letta / mem0 / Zep alignment).
- **v0.3 candidate:** `action_audit` block for browser / computer-use action chains (F6 prerequisite).
- **v0.3 candidate:** OpenTelemetry GenAI span correlation IDs as a sub-block of `integrity` (after OTel GenAI exits Development status).

All extension blocks MUST be optional and carry a `status` field with explicit `reserved-for-<version>-<feature>` markers, matching the v0.2 reservation pattern.

## 6. Adoption Path

1. **W1 (this RFC, 2026-05-19 → 2026-05-29 est.)** — RFC + schema + 2 envelopes + migration + examples (this directory). Public sync to `phionyx-research/examples/envelopes/rge_v0_2/`.
2. **W2 (F1 MCP, 2026-06-01 → 2026-06-22 est.)** — `phionyx-mcp-server` populates `mcp_tool_audit` block with `status: "active"`.
3. **W3 (F2 OTel, ~2026-06-23 → 2026-06-30 est.)** — OTel exporter maps RGE blocks onto OTel GenAI agent/framework spans (version-pinned).
4. **W4 (F10 Inspect, ~2026-07-01 → 2026-07-09 est.)** — Phionyx storage adapter persists RGE envelopes as Inspect AI log entries.
5. **v0.4.1 (F8, ~+2 weeks post v0.4.0)** — RAG runtime populates `retrieval` block.
6. **v0.5 (F4)** — Reasoning surface fully populates `reasoning.confidence_delta` and `reasoning.evidence_links[]`.
7. **v0.6 (F5)** — Multi-agent runtimes populate `subagent_chain`.

Each step extends what is **populated** at runtime; the v0.2 schema accommodates all of it without further schema bumps until v0.3.

## 7. Resolved Decisions (founder-approved 2026-05-19)

### Q1 — Signature public-key handling: **sidecar registry, not inline**

`integrity.signature` carries only the signed digest (e.g. `ed25519:<hex>`). The verification public key identity is tracked in a sidecar registry keyed by `subject.runtime + subject.version`. Rationale: inlining the public key fingerprint would bloat every envelope by 32-64 bytes for evidence the verifier already has, and key rotation policy is a separate operational concern that should not couple to the envelope shape. Schema: no change. Operational note: the sidecar registry lives at `phionyx_core/contracts/keys/` (Core) or `~/.phionyx/keys/` (wrapper) and is itself signed + checked into the audit chain at rotation events.

### Q2 — `path[].block` enum strictness: **free string + Core contract test**

`path_step.block` remains a free string in the schema. A separate Core-side contract test (`tests/contract/test_canonical_block_alphabet.py`, to be added) enforces that production envelopes only use blocks from the canonical 46-block alphabet (`phionyx_core/contracts/telemetry/canonical_blocks_v3_8_0.json::canonical_block_order`). Rationale: enumerating blocks in the schema would force a schema bump on every Core block addition (today 46, growing), churning external consumers; the Core-side contract test catches typos and unknown blocks without coupling external schema to internal pipeline evolution. Schema: no change.

### Q3 — Descriptor-hash semantics: **canonical-JSON of full descriptor including `protocolVersion`**

`mcp_tool_audit.tool_descriptor_hash` is computed as `sha256:` + hex(SHA-256(canonical_json(descriptor))) where `descriptor` is the **complete** MCP tool descriptor as received from the server, **including** the MCP `protocolVersion` field. Rationale: a tool descriptor identical in name/schema but received under a different MCP protocol version is materially a different trust object (spec semantics may have shifted); hashing the full descriptor catches spec-version drift in addition to descriptor-content drift. Schema: `tool_descriptor_hash` description updated to make this explicit; field type unchanged.

---

Q1/Q2/Q3 closed 2026-05-19 with founder approval. No further open questions block W1 → W2.

## 8. References

- MCP Specification 2025-11-25 — https://modelcontextprotocol.io/specification/2025-11-25
- Jamshidi et al., "Securing the Model Context Protocol" — arXiv:2512.06556
- OpenTelemetry GenAI Semantic Conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/ (Status: Development as of 2026-05-19)
- Inspect AI — https://inspect.aisi.org.uk (UK AISI + Meridian Labs; standard at UK/US/EU/JP/KR AISIs)
- AI Runtime Evidence Protocol (AIREP) — https://github.com/halvrenofviryel/ai-runtime-evidence-protocol (RGE is its reference producer)
- RFC 8785 — JSON Canonicalization Scheme

---

*RFC author: Phionyx Research (Ali Toygar Abak, ORCID 0009-0002-3718-4010). Reviewer pass 2 founder-approved 2026-05-19. This document is the W1 deliverable of the v0.4.0 hot lane.*
