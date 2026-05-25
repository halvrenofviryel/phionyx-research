# RGE v0.2 — Worked Examples

> Companion to `rge_v0_2.md` (RFC) and `rge_v0_2.schema.json` (canonical schema).
> Read the RFC first; this document walks through three end-to-end scenarios using the example envelopes in this directory.

## Index

1. [Minimal envelope (no v0.2 blocks)](#1-minimal-envelope-no-v02-blocks) — `rge_v0_2_minimal_envelope.json`
2. [Full MCP tool call](#2-full-mcp-tool-call) — `rge_v0_2_mcp_envelope.json`
3. [Chained envelopes — turn N → N+1](#3-chained-envelopes--turn-n--n1)

Each section walks the example field-by-field with the *why*, not just the *what*.

---

## 1. Minimal envelope (no v0.2 blocks)

File: [`rge_v0_2_minimal_envelope.json`](./rge_v0_2_minimal_envelope.json).

**Scenario:** A LangGraph research node answers a benign user query about the EU AI Act timeline. No retrieval, no tool calls, no multi-agent handoff. This envelope shows the **minimum a v0.2 envelope must carry** — exactly the v0.1 surface, with the schema field bumped.

### 1.1 Walkthrough

```json
"schema": "phionyx.governed_response_envelope.v0_2"
```

The single mandatory v0.2 change vs v0.1: this string MUST be `phionyx.governed_response_envelope.v0_2`. Validators reject anything else against the v0.2 schema. Migration cost from v0.1: change this one field.

```json
"subject": {
  "runtime": "phionyx-governance-wrapper",
  "version": "0.1.0",
  "producer": "langgraph.research_node",
  "turn_index": 1,
  "timestamp_utc": "2026-05-19T14:00:00.000000+00:00"
}
```

`runtime` identifies the governance shell. `version` is the wrapper's SemVer, **not** the schema version (schema is in the top-level `schema` field). `producer` is per-turn — different turns of the same trace may have different producers (e.g. node A then node B in a LangGraph). `turn_index` is monotonic from 1.

```json
"input": {
  "user_text": "Summarise the EU AI Act high-risk timeline.",
  "state_vector": {
    "valence": 0.30, "arousal": 0.42, "stability": 0.85, "entropy": 0.18,
    "time_delta": 0.1, "amplitude": 5.0, "context_profile": "DEFAULT", "gamma": 0.15
  },
  "safety": {"allowed": true, "reason": null}
}
```

`state_vector` is the eight-axis governance state (per Paper 1). `time_delta = 0.1` flags this as the first turn in the trace. `safety` carries the input-safety-gate verdict; `reason` is NULL when admitted, a string when blocked (e.g. `"blocked patterns: ['ignore previous instructions']"`).

```json
"path": [
  {"block": "input_safety_gate", "disposition": "admit", "reason": null},
  {"block": "phi", "disposition": "admit", "phi_cog": 0.612, "phi_phy": 0.488},
  {"block": "audit_layer", "disposition": "record"}
]
```

Three pipeline blocks fired this turn. `path_step` allows arbitrary additional properties (`phi_cog`, `phi_phy` here) for block-specific data. The block alphabet (`input_safety_gate`, `phi`, `audit_layer`, ...) is enforced separately by a Core-side contract test, not by the JSON Schema (see RFC §7 Q2).

```json
"output": {"redacted": false, "text": "High-risk obligations..."}
```

`redacted = false` because no block intervened. When `redacted = true`, `text` MUST be NULL (the runtime suppresses the model output).

```json
"metrics": {
  "phi_cognitive": 0.612, "phi_physical": 0.488,
  "phi_total": 0.550, "cognitive_verdict": "coherent"
}
```

Numeric coherence summary. `cognitive_verdict` is the normalised resonance class (`coherent`, `unstable`, `degraded`, ...).

```json
"integrity": {
  "previous": "sha256:0000000000000000",
  "current": "sha256:a1b2c3d4e5f60718",
  "signature": "demo-hmac:9f3a52ce4b8d2147",
  "canonical_json": true
}
```

`previous = sha256:0000000000000000` (the genesis marker — `GENESIS_HASH` in `wrapper.py`) confirms this is the chain's first envelope. `current` is SHA-256 over canonical JSON of `{"record": payload, "previous": previous}`, truncated to 16 hex chars in the demo (full 64 hex in Core). `signature` is HMAC-style in this example because the producer is the launch wrapper; Core uses `ed25519:<hex>`. `canonical_json = true` documents that the hash is computable from the canonical JSON form.

### 1.2 What's deliberately absent

This envelope contains **no** `reasoning`, `retrieval`, `subagent_chain`, or `mcp_tool_audit` blocks. The producer surfaced no rationale, did not retrieve, did not hand off, and did not call MCP tools. v0.2 schema accepts this perfectly — every v0.2 block is optional.

A v0.1 envelope from `wrapper.py::govern_turn` is bit-identical to this **except** for the `schema` field. That is the migration contract.

---

## 2. Full MCP tool call

File: [`rge_v0_2_mcp_envelope.json`](./rge_v0_2_mcp_envelope.json).

**Scenario:** Claude Desktop, with the `phionyx-mcp-server` companion package installed, calls a GitHub MCP server's `get_issue` tool. Phionyx records the trust boundary evidence end-to-end.

### 2.1 What changes vs the minimal envelope

```json
"subject": {
  "runtime": "phionyx-core",
  "version": "0.4.0-rc1",
  "producer": "claude-desktop.mcp.github_server",
  ...
}
```

Runtime is now `phionyx-core` (the production Core, not the launch wrapper) and the producer encodes "Claude Desktop initiated this turn, the MCP server in question is `github_server`". Producer naming is **not** schema-enforced; it's a host convention.

The `path` now includes MCP-relevant blocks:

```json
"path": [
  {"block": "input_safety_gate", "disposition": "admit", "reason": null},
  {"block": "mcp_tool_descriptor_verify", "disposition": "admit", "reason": "descriptor hash matches user-approved baseline"},
  {"block": "action_intent_gate", "disposition": "admit", "reason": "scope: read-only github tool call"},
  {"block": "phi", "disposition": "admit", "phi_cog": 0.541, "phi_phy": 0.502},
  {"block": "behavioral_drift", "disposition": "admit", "anomaly_score": 0.08},
  {"block": "audit_layer", "disposition": "record"}
]
```

Three new blocks fired: `mcp_tool_descriptor_verify` (checks the descriptor hash hasn't drifted), `action_intent_gate` (validates the proposed tool call against the capability scope), and `behavioral_drift` (reports an anomaly score; `0.08` is below alarm threshold).

### 2.2 Walking the `reasoning` block

```json
"reasoning": {
  "model_proposed_action": {
    "tool": "github.get_issue",
    "arguments": {"owner": "halvrenofviryel", "repo": "phionyx-research", "number": 42}
  },
  "model_stated_rationale": "User asked to read issue #42; the github.get_issue tool is the most direct way...",
  "runtime_policy_basis": ["input_safety_gate", "action_intent_gate", "mcp_tool_descriptor_verify"],
  "runtime_decision": "release",
  "decision_reason": "Tool call scope is read-only and matches user-approved capability profile; descriptor unchanged; no anomaly raised.",
  "rationale_action_consistency": 0.92,
  "policy_alignment_score": 0.88,
  "confidence_delta": null,
  "evidence_links": [
    {"kind": "tool_call", "ref": "mcp://github.get_issue/halvrenofviryel/phionyx-research/42", "hash": "sha256:b471e92f4c83a1d0"}
  ],
  "scoring_method": "phionyx.core.v0_4.reasoning_surface.placeholder"
}
```

- `model_proposed_action` records the **producer's** action proposal (the model said "I want to call this tool with these arguments"). This is **not** an action Phionyx took — it's the proposal Phionyx evaluated.
- `model_stated_rationale` is whatever public rationale the producer surfaced. NULL when the producer surfaced nothing. Phionyx does **not** reconstruct private chain-of-thought.
- `runtime_policy_basis` lists, in order, the gates Phionyx consulted. This is what the runtime is *standing on* when it made the decision.
- `runtime_decision` ∈ `{release, block, defer, redact}`. Here `release` because the action was admitted unchanged.
- `rationale_action_consistency` and `policy_alignment_score` ∈ `[0, 1]` measure how well the stated rationale and the proposed action / policy basis line up. The scorer is identified by `scoring_method` so downstream consumers can interpret values.
- `confidence_delta` is NULL — this producer did not surface a self-rated confidence change across the turn.
- `evidence_links[]` records pointers to evidence the rationale relies on. Here one tool-call pointer with a content hash. A verifier wishing to replay this turn would dereference the pointer and verify the content hash matches.

### 2.3 Walking the `mcp_tool_audit` block

```json
"mcp_tool_audit": {
  "status": "active",
  "tool_descriptor_hash": "sha256:7a3f912ce41b8d05",
  "descriptor_change_detected": false,
  "tool_permission_scope": ["read_issues", "read_pull_requests", "read_repository_metadata"],
  "tool_call_io_hash": {
    "input_hash": "sha256:c0ffee1234abcd56",
    "output_hash": "sha256:b471e92f4c83a1d0"
  },
  "user_approval_state": {
    "approved": true,
    "approval_ref": "audit://approval/2026-06-10T09:22:01Z/github_server",
    "approved_at_utc": "2026-06-10T09:22:01.000000+00:00"
  },
  "runtime_anomaly_flag": {
    "anomaly": false, "source": "behavioral_drift", "severity": "info", "detail": null
  },
  "signed_envelope_ref": "envelope://sha256:f8e7d6c5b4a30219",
  "chain_verify_command": "phionyx-mcp verify-chain --trace trace_b471e92f --turn 7"
}
```

All eight F1 capabilities populated (`status: "active"`):

1. `tool_descriptor_hash` — the descriptor as observed *this turn*.
2. `descriptor_change_detected = false` — the hash matches the baseline approved on 2026-06-10. If `true`, the runtime would have blocked or required re-approval (rug-pull defense).
3. `tool_permission_scope` — the capability profile entries this tool was authorised under.
4. `tool_call_io_hash` — per-call signed evidence. `input_hash` covers the arguments Phionyx forwarded; `output_hash` covers the tool's response.
5. `user_approval_state` — captures consent. `approval_ref` points to the approval audit record.
6. `runtime_anomaly_flag` — Phionyx's runtime view; `anomaly = false` here.
7. `signed_envelope_ref` — back-reference to this envelope's signed record.
8. `chain_verify_command` — a verifier can run this exact command to verify the whole chain ends here.

### 2.4 What downstream consumers do with this

- **Inspect AI storage adapter (F10):** persists the full envelope as one log entry; the eval task can query `mcp_tool_audit.descriptor_change_detected` to flag suspicious runs.
- **OTel GenAI exporter (F2):** emits an `agent.tool.call` span with `mcp_tool_audit.tool_call_io_hash` attached as attributes; the trace shows the call in any OTel backend.
- **Phionyx MCP server CLI:** `phionyx-mcp verify-chain` follows the `signed_envelope_ref` chain from `mcp_tool_audit.signed_envelope_ref`, verifying each hash and signature.

---

## 3. Chained envelopes — turn N → N+1

The two example envelopes form a two-turn chain:

```
Genesis ───►  envelope #1 (minimal)  ───►  envelope #2 (MCP call)
sha256:00...   integrity.current      integrity.previous
              sha256:a1b2...718         sha256:a1b2...718
                                        integrity.current
                                        sha256:f8e7...219
```

The chain rule:

```
envelope_N.integrity.previous == envelope_{N-1}.integrity.current
```

In `rge_v0_2_minimal_envelope.json`: `previous = sha256:0000000000000000` (genesis) and `current = sha256:a1b2c3d4e5f60718`.

In `rge_v0_2_mcp_envelope.json`: `previous = sha256:a1b2c3d4e5f60718` (= minimal's current) and `current = sha256:f8e7d6c5b4a30219`.

A chain verifier walks envelopes in order, recomputes each envelope's hash from canonical JSON of its content + the verified-previous hash, and matches against `integrity.current`. Any mismatch (tampering, missing envelope, reorder) breaks the chain at exactly the point of compromise.

### 3.1 What the chain proves and does not prove

**Proves:**
- This envelope's content was not modified after `integrity.signature` was applied.
- This envelope correctly follows the prior envelope in the trace.
- Specific MCP tool descriptor hash, approval state, runtime anomaly verdict at this turn.

**Does not prove:**
- The model's private reasoning was correctly summarised in `reasoning.model_stated_rationale`. Phionyx defends "we acted on the rationale surfaced", not "we knew what the model was thinking".
- The retrieval store wasn't compromised before retrieval. Evidence hashes are valid only as far back as the storage layer's own integrity.
- The user understood what they approved. `user_approval_state.approved = true` records the approval event; UX faithfulness is a separate concern.

---

## 4. Producing v0.2 envelopes

The launch wrapper (`docs/strategic/launch_drafts/governance_wrapper_demo/wrapper.py`) currently emits v0.1 envelopes. To produce a v0.2 envelope:

1. Change the wrapper's `inner["schema"]` from `"phionyx.governed_response_envelope.v0_1"` to `"phionyx.governed_response_envelope.v0_2"`.
2. (Optional) Populate v0.2 blocks where the producer has data.

Step 1 alone is sufficient — a v0.1-shape envelope with the schema string bumped is a valid v0.2 envelope. That is the **opt-in pattern** central to v0.2's adoption story.

For Core integration (post-W1), see `migration_v0_1_to_v0_2.md`.

---

*Examples authored alongside the v0.2 RFC, 2026-05-19. Synced to the public `phionyx-research` repo as part of the v0.4.0 W1 deliverable.*
