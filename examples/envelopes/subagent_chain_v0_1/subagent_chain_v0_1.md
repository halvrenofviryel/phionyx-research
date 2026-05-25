# Subagent Chain Block v0.1 — Specification

> **Status:** Draft RFC (2026-05-25). v0.6.0 W1 deliverable; founder approval pending W1.2 (Pydantic + tests).
> **Predecessor:** `subagent_chain` block reserved in [RGE v0.2 §2.2.3](../rge_v0_2/rge_v0_2.md) (`reserved-for-v0.6.0-f5`, 2026-05-19).
> **Scope:** Active specification of the per-turn multi-agent handoff evidence block carried inside a Reasoned Governance Envelope. v0.1 is protocol-agnostic — it covers A2A, AGNTCY/ACP, LangGraph subgraphs, CrewAI, AutoGen, and Phionyx-native handoffs without prescribing any one protocol's transport.
> **Out of scope:** Full A2A protocol adapter (separately delivered in v1.1); cross-organisation attestation (deferred v2.0+); browser/computer-use action audit (separately delivered as F17 v1.1).
> **Author:** Phionyx Research (`founder@phionyx.ai`, ORCID `0009-0002-3718-4010`).
> **License:** AGPL-3.0-or-later (schema), CC-BY-4.0 (this RFC document).
> **Companion artefacts (this directory):**
> - `subagent_chain_v0_1.schema.json` — canonical JSON Schema (Draft 2020-12).
> - `subagent_chain_v0_1_minimal_envelope.json` — 3-agent worked example (researcher → writer → editor).
> - `subagent_chain_v0_1_examples.md` — extended walkthroughs (LangGraph + A2A + AGNTCY) — *W1.4 deliverable*.
> - `migration_rge_v0_2_to_subagent_v0_1.md` — how an RGE v0.2 producer adopts this block — *W1.4 deliverable*.
> - `subagent_chain_v0_1_a2a_envelope.json` — A2A-protocol-mapped worked example — *W1.4 deliverable*.

## 1. Motivation

Multi-agent compositions are increasingly the production deployment pattern: LangGraph supervisor + worker subgraphs; CrewAI role-played teams; AutoGen group chats; Cisco/Outshift AGNTCY (ACP); and the Linux Foundation Agentic AI Foundation's Agent2Agent (A2A) protocol with 150+ supporting organisations as of mid-2026 ([Linux Foundation press release](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year)). All of these surfaces emit handoffs — events where one agent delegates work to another — that are typically logged for debugging but are **not tamper-evident** and do not provide a verifier-runnable evidence chain.

The Phionyx Reasoned Governance Envelope (RGE) v0.2 reserves a `subagent_chain` block at §2.2.3 for exactly this evidence, with the block initially marked `reserved-for-v0.6.0-f5`. The RGE v0.2 sketch defines `agent_id`, `role` ∈ {root, child, leaf}, and the existence of a `parent_envelope_hash` and `handoff_signature`, but does not yet specify:

1. The **canonical bytes** signed by `handoff_signature` (so two compliant runtimes can interoperate).
2. The **hash binding semantics** that let a verifier walk parent envelopes from any child envelope without side-channel metadata.
3. The **replay protection** discipline (timestamp window, anomaly-flag interaction).
4. The **chain-depth** bound and the runtime anomaly behaviour when it is exceeded.
5. The **A2A / AGNTCY mappings** that let a Phionyx-instrumented runtime emit an evidence chain whose protocol identifier matches what the downstream protocol-conformance verifier expects.

v0.1 fixes these. It is the first version of the block that producers may emit with `status: "active"` rather than `status: "reserved-for-v0.6.0-f5"`.

## 2. Design

### 2.1 Required fields

The block is `additionalProperties: false`. Eight fields are required; one optional object (`protocol_data`) carries protocol-specific extension data.

| Field | Type | Purpose |
|---|---|---|
| `status` | const `"active"` | v0.1 envelopes set this exactly. The RGE v0.2 reserved value `reserved-for-v0.6.0-f5` is migrated to `active` upon F5 adoption. |
| `agent_id` | string (1–256) | Stable identifier of THIS agent. LangGraph node name / A2A agent-card URI fragment / AGNTCY DID. |
| `role` | enum {root, child, leaf} | Position in the chain *for this turn*. |
| `chain_depth` | integer ≥ 0 | `root` MUST have depth=0; every child increments. |
| `protocol` | enum {a2a, agntcy, phionyx_native, langgraph_subgraph, crewai, autogen} | Inter-agent protocol identifier. |
| `parent_envelope_hash` | string \| null | Parent's `integrity.current`, copied verbatim. NULL when `role=root`. |
| `handoff_signature` | string \| null | Signed handoff payload from the parent. NULL when `role=root`. |
| `handoff_timestamp_utc` | string (ISO-8601) \| null | Parent's `subject.timestamp_utc` at handoff. NULL when `role=root`. |

Three further fields are optional but RECOMMENDED:

| Field | Type | Purpose |
|---|---|---|
| `parent_agent_id` | string \| null | The parent's `agent_id`. Lets evidence-inspector UIs render the chain without resolving `parent_envelope_hash` against the store. |
| `child_agent_ids[]` | string[] | For non-leaf nodes, the children this agent handed off to in this turn. Empty for leaves. Fan-out allowed. |
| `protocol_data` | object | Protocol-specific extension (see §2.5). |

### 2.2 Role and depth invariants

The schema enforces three `if/then` invariants via JSON Schema `allOf`:

1. **root invariants** (`role=root`): `chain_depth=0`; `parent_envelope_hash`, `parent_agent_id`, `handoff_signature`, `handoff_timestamp_utc` are all NULL.
2. **non-root requireds** (`role∈{child, leaf}`): `chain_depth≥1`; `parent_envelope_hash`, `handoff_signature`, `handoff_timestamp_utc` are strings (required).
3. **leaf cap** (`role=leaf`): `child_agent_ids` has zero items.

Validators MUST reject envelopes that violate any of these.

A `chain_depth` bound is RECOMMENDED at 16 (matching the LangGraph supervisor recursion-limit default). Producers that exceed the bound MUST set `protocol_data.depth_exceeded = true` AND emit a `runtime_anomaly_flag` on the same turn's RGE envelope (Capability 6 of the MCP block; see [RGE v0.2 §2.2.4](../rge_v0_2/rge_v0_2.md)).

### 2.3 Hash binding semantics

The chain is built turn-by-turn: every child envelope carries the SHA-256 hash of its parent envelope's `integrity.current` field, verbatim, in `subagent_chain.parent_envelope_hash`. The format is `sha256:<hex>` matching the RGE v0.2 `integrity` hash format. The truncated 16-hex form documented in [RGE v0.2 §2.3](../rge_v0_2/rge_v0_2.md) for the launch wrapper applies here unchanged; Core uses the full 64-hex digest.

A verifier validates the chain by:

1. Locating the parent envelope by its `integrity.current` (matching the child's `parent_envelope_hash`).
2. Verifying the parent envelope's own `integrity` chain (recursively to root).
3. Verifying `handoff_signature` against the parent's signing key (§2.4).

The chain is **double-bound**: the cross-agent evidence is preserved by `parent_envelope_hash` (without trusting any agent's narration), and additionally signed by `handoff_signature` (which proves the handoff was authorised by the parent runtime's key, not synthesised after the fact by an adversary holding the parent's envelope).

### 2.4 Handoff signature

The signed body is the canonical-JSON encoding (`sort_keys=True`, no whitespace, ASCII-safe) of:

```json
{
  "child_agent_id":        "<this agent_id>",
  "child_protocol":        "<this protocol>",
  "handoff_timestamp_utc": "<parent's subject.timestamp_utc>",
  "parent_agent_id":       "<parent's agent_id>",
  "parent_envelope_hash":  "<parent's integrity.current>"
}
```

(Key order is alphabetical because the encoding sorts keys.)

The signature format follows [RGE v0.2 §2.3](../rge_v0_2/rge_v0_2.md) integrity-signature format: `ed25519:<hex>` in Core, `demo-hmac:<hex>` in the launch wrapper. The signing key MUST be **the parent runtime's own signing key** — the same key used to sign the parent envelope's `integrity.signature`. This ties evidence of the handoff to the same identity that signed the parent envelope, so a verifier needs to trust exactly one key per agent runtime, not a separate "handoff key".

If the parent runtime cannot expose its signing key to a handoff-time helper (for instance, an isolated process owns the key and exposes only a sign-rpc surface), the runtime MAY implement the signature inside its own boundary and pass only the resulting `handoff_signature` string to the child runtime.

### 2.5 protocol_data

`protocol_data` is an open object: producers MAY carry arbitrary protocol-specific extension data. Reserved keys (namespaced to avoid clashes):

| Reserved key | Type | Used by |
|---|---|---|
| `depth_exceeded` | boolean | Any protocol; flag with `runtime_anomaly_flag`. |
| `replay_window_seconds_used` | integer | Any protocol; the value the producer enforced (see §4.2). |
| `a2a_task_id` | string | A2A protocol only. |
| `agntcy_acp_envelope_id` | string | AGNTCY / ACP only. |
| `langgraph_thread_id` | string | LangGraph supervisor only. |
| `crewai_crew_id` | string | CrewAI only. |
| `autogen_groupchat_id` | string | AutoGen group-chat only. |

Producers MUST namespace any non-reserved key by protocol (`a2a_*`, `crewai_*`, etc.) to keep the object collision-free across runtimes that share storage.

### 2.6 Relationship to RGE v0.2 §2.2.3

The reserved RGE v0.2 §2.2.3 block has three required fields (`status`, `agent_id`, `role`) and four optional (`parent_envelope_hash`, `handoff_signature`, `protocol`, plus implicit nullable behaviour). v0.1 adds five required fields (`chain_depth`, `protocol`, `parent_envelope_hash`, `handoff_signature`, `handoff_timestamp_utc`) and two optional (`parent_agent_id`, `child_agent_ids`, `protocol_data`). The set of valid v0.1 envelopes is a strict subset of envelopes whose `subagent_chain` was previously valid under RGE v0.2's reserved shape, because v0.1 only requires fields that were optional-but-allowed under v0.2.

Migration: a producer that emitted RGE v0.2 envelopes with `subagent_chain.status: reserved-for-v0.6.0-f5` can adopt v0.1 by:

1. Changing `status` to `active`.
2. Computing and populating `chain_depth` (locally derived from the producer's known position in the chain).
3. Populating `handoff_timestamp_utc` from the parent's envelope.
4. Optionally populating `parent_agent_id`, `child_agent_ids`, and `protocol_data`.

No re-signing of historical envelopes is required because `status: reserved-for-v0.6.0-f5` envelopes were explicitly placeholder; they did not assert active multi-agent evidence.

## 3. Protocol mapping

Phionyx's evidence chain is protocol-agnostic. The `protocol` field tells a downstream verifier which third-party shape the producer emitted alongside the Phionyx envelope; it does NOT determine the Phionyx hash binding (§2.3) or signature format (§2.4), both of which are uniform across protocols.

### 3.1 A2A (Linux Foundation Agent2Agent)

A2A v2026.05 carries an `agent_card` document (cryptographically domain-verified) and a `task_id` per delegated task. When the producer is an A2A-conformant runtime:

- `agent_id` = A2A agent-card URI fragment.
- `protocol` = `"a2a"`.
- `protocol_data.a2a_task_id` = the A2A task identifier this turn served.
- `handoff_signature` is the Phionyx signature (Ed25519 over the canonical-JSON body in §2.4), NOT the A2A protocol's task-acknowledgement signature. The two coexist; the Phionyx signature is the verifier-runnable evidence chain.

The full A2A adapter (v1.1) will populate the A2A task-acknowledgement signature alongside, in a separate field outside the `subagent_chain` block; v0.1 does NOT bind to that signature.

### 3.2 AGNTCY / ACP (Cisco / Outshift)

ACP envelopes carry an `acp_envelope_id`. When the producer is AGNTCY/ACP-conformant:

- `agent_id` = ACP agent DID.
- `protocol` = `"agntcy"`.
- `protocol_data.agntcy_acp_envelope_id` = the ACP envelope ID this turn served.

### 3.3 LangGraph supervisor

The v0.5.0 `PhionyxLangGraphSupervisor` adapter already creates derived child trace IDs of the form `<parent_trace_id>:child:<child_node>`. When that adapter populates `subagent_chain`:

- `agent_id` = LangGraph node name (e.g. `researcher`, `writer`, `editor`).
- `protocol` = `"langgraph_subgraph"`.
- `protocol_data.langgraph_thread_id` = the LangGraph supervisor's thread identifier.

### 3.4 CrewAI / AutoGen

Both frameworks compose multi-agent flows in Python without a wire protocol. For these:

- `agent_id` = framework-assigned agent name.
- `protocol` = `"crewai"` or `"autogen"`.
- `protocol_data.crewai_crew_id` / `protocol_data.autogen_groupchat_id` carry the framework's session identifier.

### 3.5 Phionyx-native

When two Phionyx-instrumented runtimes hand off to each other without a third-party protocol (for example, two `phionyx-core` runtimes in the same process tree):

- `protocol` = `"phionyx_native"`.
- `protocol_data` MAY be empty.

## 4. Security considerations

### 4.1 Signature scope

`handoff_signature` proves the parent **authorised** the handoff. It does NOT prove the parent's narration is correct (that is bounded by the parent's own envelope discipline) and it does NOT prove the child's narration is correct (that is bounded by the child's own envelope discipline). The verifier's trust is layered: each agent's envelope chain is verified against its own signing key; the cross-agent `parent_envelope_hash` chain composes those local proofs.

A child runtime that wants to attest "the parent really authorised this handoff" relies on this signature. A child runtime that wants to attest "the parent's claim is true" cannot do so from `subagent_chain` alone — that requires inspecting the parent's full envelope and the parent's claim-verification path inside that envelope (`path`, `metrics`, `reasoning` if populated).

### 4.2 Replay protection

A child envelope whose `handoff_timestamp_utc` is older than the runtime's `replay_window_seconds` (RECOMMENDED 300s; producers MAY tighten) MUST be flagged. The flag goes into the child envelope's `path` (canonical block `replay_protection_gate`, disposition `block` or `defer`) and the child envelope's `mcp_tool_audit.runtime_anomaly_flag` if the MCP block is populated. v0.1 does NOT silently accept stale handoffs.

The replay window does NOT need to be cryptographically committed inside `subagent_chain` itself; it is a deployment-time policy. Producers MAY record the enforced window in `protocol_data.replay_window_seconds_used` for auditor-visible documentation.

### 4.3 Cross-agent key compromise

If a parent agent's signing key is compromised, every child envelope downstream of that parent inherits the trust loss for the chain segment originating from that parent. This is the same trust model as a single-runtime hash chain — the cross-agent extension does NOT introduce a new key-compromise blast radius. v0.1 does NOT specify key rotation; that is a runtime / KMS concern out of scope.

If the child detects that the parent's `integrity.signature` (in the parent envelope) does not verify against the expected key, the child MUST treat the handoff as unauthenticated regardless of whether `handoff_signature` itself appears well-formed. Implementers SHOULD link the two verifications in the same code path.

### 4.4 Fan-out attribution

`child_agent_ids[]` permits fan-out. Each downstream child envelope carries a DIFFERENT `handoff_signature` (because the canonical body in §2.4 includes the child's own `agent_id` and `protocol`). This means a parent that fans out to N children produces N distinct handoff signatures. A verifier inspecting two child envelopes whose `parent_envelope_hash` is identical can independently verify that both signatures originated from the parent — without the children having to share their signatures with each other.

### 4.5 Out-of-scope: cross-organisation attestation

v0.1 assumes all envelopes in the chain are stored in or accessible to the verifier. It does NOT specify how a cross-organisation verifier reconstructs chains spanning trust boundaries (organisation A's parent → organisation B's child). That is the v2.0 distributed attestation work tracked in `PHIONYX_V1_0_ROADMAP_2026_05_23.md` §A.6+ deferred-scope.

## 5. Extension hooks

Future versions of the block MAY add:

- `agent_card_pointer` — URI to the protocol-native agent identity document (A2A agent card, AGNTCY DID document). Out of scope v0.1.
- `delegation_intent` — a short structured statement of what the parent asked the child to do. Currently producers carry this in the parent envelope's `output.text`; promoting it to a structured field is v0.2 work.
- `policy_basis[]` — explicit list of policies the parent consulted before delegating. Composes with RGE v0.2 §2.2.1 `reasoning.runtime_policy_basis[]`. Decision deferred until F4 (reasoning surface audit) lands and shows whether the cross-agent surface adds enough beyond what the per-turn reasoning block already provides.

## 6. Adoption path

| Stage | Deliverable | When |
|---|---|---|
| W1.1 (this RFC) | Schema + minimal example + this `.md` | 2026-05-25 |
| W1.2 | Pydantic model in `phionyx_core/contracts/envelopes/subagent_chain.py` + contract test | W1.2 (~3-5h) |
| W1.3 | LangGraph supervisor populates the block; integration test exercises a 3-agent chain end-to-end | W1.3 (~5-8h) |
| W1.4 | A2A worked example + migration doc + ADR-0007 | W1.4 (~2-3h) |
| W1.5 | RGE v0.2 §2.2.3 `status` migrated `reserved-for-v0.6.0-f5` → `active` + cross-link to this RFC | W1.5 (~2-3h) |

This RFC freezes the wire shape so the W1.2 Pydantic model, the W1.3 LangGraph adapter, and the W1.4 worked examples cannot drift from each other. Founder approval after W1.1 is required before W1.2 touches `phionyx_core/contracts/envelopes/` (escalation rule per `.claude/CLAUDE.md`).

## 7. References

- [Reasoned Governance Envelope v0.2 RFC](../rge_v0_2/rge_v0_2.md) — §2.2.3 reserves this block; §2.3 fixes hash format; §2.4 fixes canonical-JSON encoding.
- [`tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/langgraph_handler.py`](../../tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/langgraph_handler.py) — the v0.5.0 `PhionyxLangGraphSupervisor` adapter that W1.3 will extend to populate `subagent_chain`.
- [Linux Foundation Agent2Agent (A2A) press release](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year) — 150+ supporting organisations, production deployments, mid-2026.
- `PHIONYX_V1_0_ROADMAP_2026_05_23.md` §A.2 — v0.6.0 Multi-Agent Evidence scope; F5 = 3-week effort.
