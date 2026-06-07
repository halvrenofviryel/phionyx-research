# Phionyx v0.7.0 Schema Portfolio

> **Status:** Active as of v0.7.0 W3 (2026-05-27).
> **Purpose:** Catalogue every schema Phionyx publishes at v0.7.0, document the additive-only versioning policy, and enumerate the integrity surfaces a third-party verifier needs to reason about.
> **Scope:** Schemas only. Pydantic models, MCP server tool surfaces, plugin commands, and CLI helpers that *use* these schemas are documented in their respective packages.
> **Delta from v0.6.0:** Two additive extensions to Schema 1 (RGE v0.2) — W2.1 reasoning surface and W2.2 retrieval audit. **One new schema id** for Letta memory mutations — `phionyx.memory_mutation_envelope.v1` (W3.1). **No breaking changes.**

## 1. Portfolio at a glance

Phionyx v0.7.0 publishes eight schema identifiers (seven from v0.6.0 + one new) across the Core SDK and five companion packages:

| # | Schema ID | Where defined | First release | Status v0.7.0 |
|---|---|---|---|---|
| 1 | `phionyx.governed_response_envelope.v0_2` | [`examples/envelopes/rge_v0_2/rge_v0_2.schema.json`](./rge_v0_2/rge_v0_2.schema.json) | v0.4.0 | **Extended (additive)** — W2.1 reasoning surface fields + W2.2 retrieval block activation |
| 2 | `subagent_chain_v0_1.schema.json` (sibling RFC) | [`examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.schema.json`](./subagent_chain_v0_1/subagent_chain_v0_1.schema.json) | v0.6.0 W1 | Stable (no change) |
| 3 | `phionyx.langchain_event_envelope.v1` | [`tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/audit_chain.py`](../../tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/audit_chain.py) | v0.5.0 | Stable (no change) |
| 4 | `phionyx.openai_agents_event_envelope.v1` | `tools/phionyx_openai_agents/.../audit_chain.py` | v0.5.0 | Stable (no change) |
| 5 | `phionyx.judgment_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/envelope.py`](../../tools/phionyx_eval/src/phionyx_eval/envelope.py) | v0.6.0 W2 | Stable (no change) |
| 6 | `phionyx.imported_langfuse_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/importers/langfuse.py`](../../tools/phionyx_eval/src/phionyx_eval/importers/langfuse.py) | v0.6.0 W3 | Stable (no change) |
| 7 | `phionyx.imported_langsmith_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/importers/langsmith.py`](../../tools/phionyx_eval/src/phionyx_eval/importers/langsmith.py) | v0.6.0 W3 | Stable (no change) |
| 8 | `phionyx.memory_mutation_envelope.v1` (NEW) | [`tools/phionyx_letta/src/phionyx_letta/audit_chain.py`](../../tools/phionyx_letta/src/phionyx_letta/audit_chain.py) | **v0.7.0 W3** | **NEW — Letta memory mutations (F15)** |

## 2. v0.7.0 new schema (Schema 8 — memory mutation v1)

`phionyx.memory_mutation_envelope.v1` — emitted by `phionyx-letta` for every memory mutation event (write / append / clear / delete / forget / consolidate). Schema lives inline in `audit_chain.py` (same pattern as Schemas 3–7) and shares the canonical-JSON + SHA-256 hash chain + opt-in Ed25519 signing invariants with the rest of the portfolio.

Top-level shape:

```
{
  "schema": "phionyx.memory_mutation_envelope.v1",
  "subject": {
    "runtime": "phionyx-letta",
    "version": "<semver>",
    "producer": "<letta agent id>",
    "turn_index": <int>,
    "event_type": "memory_<kind>",
    "timestamp_utc": "<ISO-8601>",
    "metadata": {
      "memory_audit": {                     // W3.3 — cross-runtime composition (optional)
        "parent_envelope_ref": "envelope://sha256:...",
        "schema": "phionyx.memory_mutation_envelope.v1",
        "kind": "<mutation kind>"
      },
      "<producer keys>": "..."
    }
  },
  "mutation": {
    "block_id":      "<stable Letta block id>",
    "block_label":   "<e.g. core_memory.persona>",
    "mutation_kind": "write|append|clear|delete|forget|consolidate",
    "diff": {                               // computed by phionyx_letta.compute_memory_diff
      "before_hash": "sha256:<hex>",
      "after_hash":  "sha256:<hex>",
      "before_size_bytes": <int>,
      "after_size_bytes":  <int>,
      "added_chars":     <int>,
      "removed_chars":   <int>,
      "unchanged_chars": <int>,
      "diff_text": null | "<unified diff>"  // opt-in only
    },
    "forgetting_reason": null | "<string>"   // populated for forget/delete/clear
  },
  "memory_consolidation_audit": null | {     // W3.2 — only for `consolidate` mutations
    "block_ref": "pipeline_block_43:memory_consolidation",
    "from_episodic": [<mem-id>, ...],
    "to_semantic":   [<sem-id>, ...],
    "consolidation_method": "<algorithm id>",
    "decay_applied": null | true | false
  },
  "integrity": {  ...same as all other portfolio schemas...  }
}
```

**Cross-runtime composition (W3.3):** the `subject.metadata.memory_audit` reference object is the universal handle. When an upstream adapter envelope (langchain_event, openai_agents_event, RGE v0.2) causes a memory mutation, the upstream envelope's `integrity.current` becomes `memory_audit.parent_envelope_ref` here. The reference is one-way (memory envelope → upstream) because the upstream envelope is sealed.

## 3. v0.7.0 additive extensions to existing schemas

### 3.1 RGE v0.2 — `reasoning` block extension (W2.1, F4)

Three optional fields added to `reasoning`:

| Field | Type | Description |
|---|---|---|
| `rationale_summary` | `string \| null` | Runtime-produced one-line distillation of the reasoning surface (distinct from `model_stated_rationale`). Surfaces in dashboards and compliance reports. |
| `knowledge_sources_consulted` | array of `{kind, ref, hash?}` | Sources the producer consulted, even sources that did not become citations. Enum kinds: `retrieval_corpus`, `memory_block`, `tool_output`, `tool_descriptor_clause`, `static_doc`, `system_prompt`, `external_api`. Complements `evidence_links[]` (artefacts the rationale depends on). |
| `constraints_acknowledged` | array of `{kind, ref, satisfied?}` | Constraints the producer publicly acknowledged. Enum kinds: `policy`, `user_directive`, `safety_boundary`, `tool_descriptor_clause`, `regulatory`, `self_imposed`. Each carries optional `satisfied: bool \| null`. |

**Backward compat:** Envelopes from v0.6.0 and earlier (without these fields) continue to validate against the v0.7.0 schema unchanged. Old verifiers ignore the new fields.

Builder helper: `phionyx_mcp_server.audit_chain.build_envelope(...)` emits null/empty defaults for all three new fields when the producer does not surface reasoning metadata; populated values pass through unchanged.

### 3.2 RGE v0.2 — `retrieval` block activation (W2.2, F8)

The `retrieval` block was reserved (`status="reserved-for-v0.4.1-f8"`) from v0.4.0 through v0.6.0. v0.7.0 W2.2 flips Phionyx's own producers to `status="active"` and adds block-level + per-document provenance.

**Block-level additions:**

| Field | Type | Description |
|---|---|---|
| `corpus` | object \| null | `{name, version?, language?}` — semantic corpus metadata (distinct from `store_id` which is the technical handle). |
| `similarity_threshold` | `number 0.0–1.0 \| null` | Block-level cutoff used to gate documents from `retrieved` into the candidate set. |
| `query_text_hash` | `string \| null` | SHA-256 of user-or-system-formatted query text (distinct from `query_hash`, which may hash the structured store-query object). |

**Per-document additions:**

| Field | Type | Description |
|---|---|---|
| `chunk_offset` | `integer ≥0 \| null` | Zero-indexed chunk position when chunked retrieval is used. |
| `source_url` | `string \| null` | Canonical human-resolvable URL (distinct from `id`, which may be store-internal). |
| `retrieved_at` | ISO-8601 \| null | Exact retrieval timestamp; may predate envelope timestamp when retrieval is cached. |

**Backward compat:** The `retrieval` block remains optional at the envelope level. v0.6.0 envelopes without the block, and v0.6.0 envelopes with `status="reserved-for-v0.4.1-f8"`, continue to validate against the v0.7.0 schema. The reserved sentinel is preserved in the enum for historical envelopes.

Builder helper: `phionyx_mcp_server.audit_chain.build_retrieval_block(RetrievalContext)` produces a schema-compliant block dict; `build_envelope(..., retrieval=RetrievalContext(...))` integrates it into the signed envelope.

## 4. Common invariants across the portfolio (unchanged from v0.6.0)

### 4.1 Hash chain

Every envelope carries an `integrity` block with four fields:

```
integrity = {
    "previous": "sha256:<64-hex>",
    "current":  "sha256:<64-hex>",
    "signature": "<algo>:<hex>",
    "canonical_json": true
}
```

- `previous` references the prior envelope's `current`; genesis is `sha256:` + `"0" * 64`.
- `current` is SHA-256 over canonical-JSON-encoded `{record: payload_without_integrity, previous: previous_hash}`.
- `signature` is `hmac-sha256:<hex>` (demo signer), `demo-hmac:<hex>` (launch wrapper), or `ed25519:<hex>` (Core / production).
- `canonical_json: true` declares the hash was computed over canonical JSON (sort_keys, no whitespace, ASCII-safe, no NaN).

The same `canonical_json` helper is used in all packages: `json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)`.

**v0.7.0 W2.1 + W2.2 impact on hash:** Both additive extensions add new keys inside the `reasoning` and `retrieval` sub-blocks. Producers that populate these fields produce envelopes whose `integrity.current` reflects the populated state. Producers that emit empty defaults produce envelopes whose `integrity.current` is byte-stable across the v0.6.0 → v0.7.0 boundary *for the same logical content*. The portfolio-wide canonical-JSON helper is byte-identical to v0.6.0.

### 4.2 Subject block

Every envelope's `subject` block carries at minimum:

```
subject = {
    "runtime":       "<package identifier>",
    "version":       "<package SemVer>",
    "turn_index":    <int >= 0>,
    "event_type":    "<producer-defined>",
    "timestamp_utc": "<ISO-8601 UTC>"
}
```

Imported envelopes (Langfuse, LangSmith) additionally carry:

```
    "foreign_trace_id":  "<foreign system's trace id>",
    "metadata": {
        "imported_extras": { <verbatim non-mappable foreign fields> }
    }
```

### 4.3 Multi-agent block (unchanged from v0.6.0)

When a producer is participating in a multi-agent flow, the v0.1 `subagent_chain` block is the universal extension surface. Shape identical across:

- Schema 1 (RGE v0.2): top-level optional field.
- Schema 2 (sibling RFC): the schema's root object.
- Schema 3 (langchain_event v1): optional top-level field added in v0.6.0 W1.3.
- Schemas 4–7: do not carry the block in v0.7.0; a future minor revision MAY add it under the same shape.

## 5. Versioning policy (reaffirmed for v0.7.0)

**Strictly additive within a major:** A v1 schema can grow new optional fields without breaking consumers. The v0.7.0 portfolio shipped W2.1 + W2.2 additions under this rule — the schema id remains `phionyx.governed_response_envelope.v0_2`; consumers that ignore the new fields continue to validate old envelopes byte-identically.

**Schema id bump on breaking change:** Adding a required field, removing a field, or changing a field's type is a breaking change. Such changes increment the schema id (`...v0_2` → `...v0_3`). **Phionyx v0.7.0 does NOT introduce any breaking changes**; the portfolio is fully backwards-compatible with v0.6.0.

**Schema id bump on semantic shift:** When the same wire shape carries fundamentally different semantics, the schema id bumps even if the byte shape is unchanged. **Phionyx v0.7.0 does NOT introduce any semantic shifts of this kind.**

**Block versioning is independent:** Sub-blocks (`subagent_chain`, `retrieval`, `mcp_tool_audit`) carry their own `status` enums plus their own RFC versions. Block-level transitions (e.g. `retrieval.status` flipping from reserved to active in v0.7.0) happen independently of envelope schema bumps.

## 6. Schema-to-package matrix (with v0.7.0 deltas)

| Package | v0.6.0 | v0.7.0 delta |
|---|---|---|
| `phionyx-core` v0.5.x → v0.6.x → v0.7.x | — (defines `SubagentChainV0` Pydantic model; emits no envelopes directly) | No envelope-schema delta |
| `phionyx-langchain-langgraph` v0.1.x | Emits Schema 3; consumes Schema 2 | No delta |
| `phionyx-openai-agents` v0.1.x | Emits Schema 4 | No delta |
| `phionyx-mcp-server` v0.1.x | Emits Schema 1 | **Builder extended (W2.1 + W2.2) — new dataclasses `RetrievalDocument`, `RetrievalContext`, helper `build_retrieval_block`** |
| `phionyx-pipeline-mcp` v0.1.x | Reads chains | No delta |
| `phionyx-eval` v0.1.x | Emits Schemas 5, 6, 7 | No delta |
| `phionyx-claude-code-plugin` v0.1.x | Composes MCP tool surfaces | New slash command `/phionyx:evidence-report` wraps the new `phionyx-compliance` package (W1.4) |
| **`phionyx-compliance` v0.1.x (NEW in v0.7.0 W1)** | — | **Read-only over Schema 1 chains. Produces markdown drafts mapping envelope evidence to four compliance frameworks (EU AI Act Article 13, NIST AI RMF 1.0, ISO/IEC 42001, OWASP Agentic AI Threats v1.0). Does NOT emit envelopes of its own.** |

## 7. What v0.7.0 does NOT change

- No schema id bumps in any companion package.
- No required-field additions in any of the seven schemas. Both W2.1 reasoning fields and W2.2 retrieval fields are optional (or carry defaults).
- No canonicalisation algorithm change. The `canonical_json` helper is byte-identical across all packages.
- No signing-algorithm change. `hmac-sha256:` for demo, `ed25519:` for production; producer's choice.
- No new package emitting envelopes. `phionyx-compliance` is read-only over the existing chain.

## 8. What is deferred to v0.7.x patches and later

- **F15 memory diff audit (W3).** Letta adapter for per-mutation envelopes. Will land in v0.7.0 W3 within this cycle, not v0.7.1.
- **HearthOS adapter envelopes (W4.1).** Bounded-authority pattern reference. Cross-package, ships with v0.7.0 release at W4.
- **Cross-runtime export.** v0.6.0 W3 shipped import-only (Langfuse / LangSmith → Phionyx). v0.7.x candidate: Phionyx → Langfuse / LangSmith export.
- **OpenAI Agents `subagent_chain` integration.** Schema 4 does not yet carry the block; demand-driven add in v0.8.0 or later.
- **EU AI Act Article 12 template** (`phionyx-compliance`). Listed as candidate input in the 2026-05-26 Deloitte alignment audit; founder-paced per individual W block per `docs/strategic/PHIONYX_DELOITTE_ALIGNMENT_2026_05_26.md`.

## 9. Verification surface for third-party reviewers (unchanged from v0.6.0)

A third-party reviewer with access to any envelope from this portfolio (and no Phionyx insider knowledge) can do all of:

1. **Schema validation.** Each schema id maps to a Draft 2020-12 JSON Schema file; standard validators apply.
2. **Pydantic model validation.** `phionyx-core` exports `SubagentChainV0`; `phionyx-eval` exports `Rubric`, `Judgment`, `JudgmentScore`.
3. **Hash chain integrity.** Recompute `current` from canonical-JSON-encoded `{record, previous}` and compare to the stored `integrity.current`. Tampering any envelope's payload breaks the comparison.
4. **Cross-envelope linkage.** Walk the chain by following `integrity.previous`; for multi-agent flows, additionally walk `subagent_chain.parent_envelope_hash`.
5. **Round-trip validation for imports.** Re-run the importer over the foreign source and compare the produced chain against the persisted chain.
6. **v0.7.0 additions:** validate the new `reasoning.rationale_summary` etc. fields against the updated `rge_v0_2.schema.json`; verify retrieval-chain integrity by walking `retrieval.documents[].role` transitions (retrieved → admitted → cited → contradicted → rejected).

Cryptographic verification of the `signature` field requires the producer's signing key and is out of scope for the schemas themselves — keys, rotation, and revocation are operational concerns documented per package.

## 10. References

- [RGE v0.2 RFC](./rge_v0_2/rge_v0_2.md) — Schema 1 specification with W2.1 + W2.2 extensions documented in §2.2.1–§2.2.2.
- [subagent_chain v0.1 RFC](./subagent_chain_v0_1/subagent_chain_v0_1.md) — Schema 2.
- [v0.6.0 Schema Portfolio](./v0_6_schema_portfolio.md) — previous portfolio document.
- [ADR-0007 — Multi-Agent Envelope Chain](../../docs/adr/0007-multi-agent-envelope-chain.md) — design decisions.
- [AI Runtime Evidence Protocol (AIREP)](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol) — the experimental, vendor-neutral open format for per-decision evidence receipts that Phionyx emits; the Phionyx RGE is its reference producer.

## 11. Acceptance evidence (W2.3 + W3)

W2.3 (schema portfolio bump):

- ✅ All 7 v0.6.0 schema IDs unchanged; portfolio surface is byte-stable at the identifier level for those schemas.
- ✅ Both W2.1 reasoning and W2.2 retrieval extensions are additive — schema validator confirms v0.6.0 envelopes still validate against v0.7.0 schema.
- ✅ RGE v0.2 builder integration (`audit_chain.py`) covered by 20 tests in `tools/phionyx_mcp_server/tests/test_audit_chain.py` (11 baseline + 3 W2.1 + 6 W2.2). Result: 20/20 pass.
- ✅ Both example envelopes (`rge_v0_2_minimal_envelope.json`, `rge_v0_2_mcp_envelope.json`) validate against the updated schema.
- ✅ Spec doc `rge_v0_2.md` §2.2.1 (reasoning) and §2.2.2 (retrieval) document the extensions with ship target v0.7.0.

W3 (memory diff audit, F15):

- ✅ New Schema 8 `phionyx.memory_mutation_envelope.v1` defined inline in `tools/phionyx_letta/src/phionyx_letta/audit_chain.py`.
- ✅ Builder + diff helper + chain verifier covered by 20 tests in `tools/phionyx_letta/tests/test_memory_envelope.py`. Result: 20/20 pass.
- ✅ W3.2 forgetting + consolidation audit subblock implemented (`MemoryConsolidationAudit` dataclass + null-default in non-consolidation envelopes).
- ✅ W3.3 cross-runtime composition implemented (`memory_audit_parent_ref` kwarg → `subject.metadata.memory_audit` reference object).
- ✅ Canonical JSON + SHA-256 hash chain + HMAC/Ed25519 signing pattern matches phionyx-mcp-server byte-for-byte.

This portfolio document is the W2.3 deliverable (originally), updated in W3 to register Schema 8.
