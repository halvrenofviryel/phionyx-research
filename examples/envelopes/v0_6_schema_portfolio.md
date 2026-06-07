# Phionyx v0.6.0 Schema Portfolio — RC

> **Status:** Release candidate as of v0.6.0 W4 (2026-05-25).
> **Purpose:** Catalogue every schema Phionyx publishes at v0.6.0, document the additive-only versioning policy, and enumerate the integrity surfaces a third-party verifier needs to reason about.
> **Scope:** Schemas only. The Pydantic models, MCP server tool surfaces, plugin commands, and CLI helpers that *use* these schemas are documented in their respective packages.

## 1. Portfolio at a glance

Phionyx v0.6.0 publishes seven schema identifiers across the Core SDK and four companion packages:

| # | Schema ID | Where defined | First release | Status v0.6.0 |
|---|---|---|---|---|
| 1 | `phionyx.governed_response_envelope.v0_2` | [`examples/envelopes/rge_v0_2/rge_v0_2.schema.json`](./rge_v0_2/rge_v0_2.schema.json) | v0.4.0 | Stable — `subagent_chain` block marked active in W1.5 |
| 2 | `subagent_chain_v0_1.schema.json` (sibling RFC) | [`examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.schema.json`](./subagent_chain_v0_1/subagent_chain_v0_1.schema.json) | v0.6.0 W1 | Stable |
| 3 | `phionyx.langchain_event_envelope.v1` | [`tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/audit_chain.py`](../../tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/audit_chain.py) | v0.5.0 | Stable — extended with optional `subagent_chain` field in W1.3 (additive) |
| 4 | `phionyx.openai_agents_event_envelope.v1` | `tools/phionyx_openai_agents/.../audit_chain.py` | v0.5.0 | Stable |
| 5 | `phionyx.judgment_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/envelope.py`](../../tools/phionyx_eval/src/phionyx_eval/envelope.py) | v0.6.0 W2 | Stable |
| 6 | `phionyx.imported_langfuse_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/importers/langfuse.py`](../../tools/phionyx_eval/src/phionyx_eval/importers/langfuse.py) | v0.6.0 W3 | Stable |
| 7 | `phionyx.imported_langsmith_envelope.v1` | [`tools/phionyx_eval/src/phionyx_eval/importers/langsmith.py`](../../tools/phionyx_eval/src/phionyx_eval/importers/langsmith.py) | v0.6.0 W3 | Stable |

## 2. Common invariants across the portfolio

All seven schemas share the following surface conventions:

### 2.1 Hash chain

Every envelope carries an `integrity` block with four fields:

```
integrity = {
    "previous": "sha256:<64-hex>",
    "current":  "sha256:<64-hex>",
    "signature": "<algo>:<hex>",
    "canonical_json": true
}
```

- `previous` references the prior envelope's `current`; genesis is `sha256:" + "0" * 64`.
- `current` is SHA-256 over canonical-JSON-encoded `{record: payload_without_integrity, previous: previous_hash}`.
- `signature` is `hmac-sha256:<hex>` (demo signer), `demo-hmac:<hex>` (launch wrapper), or `ed25519:<hex>` (Core / production).
- `canonical_json: true` declares that the hash was computed over canonical JSON (sort_keys, no whitespace, ASCII-safe, no NaN).

The same `canonical_json` helper is used in all packages — `json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)`.

### 2.2 Subject block

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

### 2.3 Multi-agent block

When a producer is participating in a multi-agent flow, the v0.1 `subagent_chain` block is the universal extension surface. Its shape is identical across:

- Schema 1 (RGE v0.2): block is a top-level optional field per §2.2.3.
- Schema 2 (sibling RFC): block is the schema's root object.
- Schema 3 (langchain_event v1): block is an optional top-level field added in v0.6.0 W1.3 (additive — old envelopes without the field still verify).
- Schemas 4 and 5–7: do not carry the block in v0.6.0; a future minor revision MAY add it under the same shape. Cross-runtime importers (Langfuse / LangSmith) do not currently emit `subagent_chain` because the foreign formats do not commit a parent-envelope-hash equivalent.

## 3. Versioning policy

**Strictly additive within a major:** A v1 schema can grow new optional fields without breaking consumers. The v0.6.0 portfolio shipped W1.3's `subagent_chain` extension to `phionyx.langchain_event_envelope.v1` under this rule — the schema id stayed at v1; consumers that ignore the new field continue to verify old envelopes byte-identically.

**Schema id bump on breaking change:** Adding a required field, removing a field, or changing a field's type is a breaking change. Such changes increment the schema id (`...v1` → `...v2`). Phionyx v0.6.0 does NOT introduce any breaking changes; the portfolio is fully backwards-compatible with v0.5.0.

**Schema id bump on semantic shift:** When the same wire shape carries fundamentally different semantics (e.g. envelope storage moves from per-turn audit to cross-organisation attestation), the schema id bumps even if the byte shape is unchanged. Phionyx v0.6.0 does NOT introduce any semantic shifts of this kind.

**Block versioning is independent:** The `subagent_chain` block carries its own `status` enum (`reserved-for-v0.6.0-f5`, `active`) plus its own RFC version (`v0_1` in this release). Schema 1 (RGE v0.2) holds the block at the wire level; Schema 2 holds the block's own RFC and reference schema. Block bumps may happen independently of envelope schema bumps.

## 4. Schema-to-package matrix

| Package | Schemas emitted | Schemas consumed |
|---|---|---|
| `phionyx-core` v0.5.x | — (defines `SubagentChainV0` Pydantic model; emits no envelopes directly) | — |
| `phionyx-langchain-langgraph` v0.1.x | Schema 3 (langchain_event v1) | Schema 2 (subagent_chain block) |
| `phionyx-openai-agents` v0.1.x | Schema 4 (openai_agents_event v1) | — |
| `phionyx-mcp-server` v0.1.x | Schema 1 (RGE v0.2) | Schema 2 (subagent_chain block) |
| `phionyx-pipeline-mcp` v0.1.x | — (reads chains produced by the above) | All |
| `phionyx-eval` v0.1.x | Schemas 5, 6, 7 | Schema 2 (for evaluation rubrics scoped to multi-agent flows) |
| `phionyx-claude-code-plugin` v0.1.x | — (composes existing MCP tool surfaces) | All |

## 5. What v0.6.0 does NOT change

- No schema id bumps in any companion package.
- No required-field additions in any of the seven schemas (the new optional `subagent_chain` field in Schema 3 is additive).
- No canonicalisation algorithm change. The `canonical_json` helper is byte-identical across all packages.
- No signing-algorithm change. `hmac-sha256:` for demo, `ed25519:` for production; producer's choice.

## 6. What is deferred to v0.7.0 and later

- **Cross-runtime export.** v0.6.0 W3 ships import-only (Langfuse / LangSmith → Phionyx). v0.7.0 candidate work: Phionyx → Langfuse / LangSmith export.
- **OpenAI Agents `subagent_chain` integration.** Schema 4 does not yet carry the block; demand-driven add in v0.7.0 or v0.8.0.
- **AGNTCY/ACP worked example.** v0.1 RFC names the protocol mapping but ships no worked example. Deferred to v0.6.x patch if adoption signals justify the maintenance burden.
- **Full A2A protocol adapter.** v0.1 RFC is read-design only. Full A2A protocol-level signature integration ships in v1.1 per the public roadmap.

## 7. Verification surface for third-party reviewers

A third-party reviewer with access to any envelope from this portfolio (and no Phionyx insider knowledge) can do all of:

1. **Schema validation.** Each schema id maps to a Draft 2020-12 JSON Schema file; standard validators apply.
2. **Pydantic model validation.** `phionyx-core` exports `SubagentChainV0`; `phionyx-eval` exports `Rubric`, `Judgment`, `JudgmentScore`. Either surface accepts JSON for validation.
3. **Hash chain integrity.** Recompute `current` from canonical-JSON-encoded `{record, previous}` and compare to the stored `integrity.current`. Tampering any envelope's payload breaks the comparison.
4. **Cross-envelope linkage.** Walk the chain by following `integrity.previous`; for multi-agent flows, additionally walk `subagent_chain.parent_envelope_hash`.
5. **Round-trip validation for imports.** Re-run the importer over the foreign source and compare the produced chain against the persisted chain; deterministic by construction (timestamps sourced from the foreign data, not from `datetime.now()` when the foreign data provides them).

Cryptographic verification of the `signature` field requires the producer's signing key and is out of scope for the schemas themselves — keys, rotation, and revocation are operational concerns documented per package.

## 8. References

- [RGE v0.2 RFC](./rge_v0_2/rge_v0_2.md) — Schema 1.
- [subagent_chain v0.1 RFC](./subagent_chain_v0_1/subagent_chain_v0_1.md) — Schema 2.
- [ADR-0007 — Multi-Agent Envelope Chain](../../docs/adr/0007-multi-agent-envelope-chain.md) — design decisions.
- [AI Runtime Evidence Protocol (AIREP)](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol) — the experimental, vendor-neutral open format for per-decision evidence receipts that Phionyx emits; the Phionyx RGE is its reference producer.
