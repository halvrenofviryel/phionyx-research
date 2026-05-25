# Subagent Chain v0.1 — Extended Walkthroughs

> **Companion to:** [`subagent_chain_v0_1.md`](./subagent_chain_v0_1.md) (RFC).
> **Worked examples in this directory:**
>
> - [`subagent_chain_v0_1_minimal_envelope.json`](./subagent_chain_v0_1_minimal_envelope.json) — LangGraph supervisor 3-agent chain (canonical reference).
> - [`subagent_chain_v0_1_a2a_envelope.json`](./subagent_chain_v0_1_a2a_envelope.json) — A2A protocol mapping.
>
> **Predecessor:** RGE v0.2 §2.2.3 [reserved-for-v0.6.0-f5](../rge_v0_2/rge_v0_2.md).

This document walks through the four protocol mappings the v0.1 schema names — what each one looks like in practice, what `protocol_data` carries, and what is left to the v1.1 full-protocol adapters.

## 1. LangGraph supervisor (already shipped, v0.5.0 → v0.6.0 W1.3)

LangGraph compositions thread a `StateGraph` through a supervisor node that registers worker children and dispatches handoffs between them. Phionyx's `PhionyxLangGraphSupervisor` adapter records each `register` and `handoff` call as a signed envelope whose `subagent_chain` block describes the supervisor's view of the agent transition being audited.

**Canonical 3-agent flow** (`researcher` → `writer` → `editor`):

```python
from phionyx_langchain_langgraph import PhionyxLangGraphSupervisor

sup = PhionyxLangGraphSupervisor()
sup.register(child_node="researcher")   # emit 1 — root, depth 0, child_agent_ids=["researcher"]
sup.register(child_node="writer")       # emit 2 — root, depth 0, child_agent_ids=["researcher", "writer"]
sup.register(child_node="editor")       # emit 3 — root, depth 0, child_agent_ids=["researcher", "writer", "editor"]

sup.handoff(from_node="supervisor", to_node="researcher",
            payload={"task": "gather sources"})            # emit 4 — child, depth 1
sup.handoff(from_node="researcher", to_node="writer",
            payload={"sources": ["s1", "s2"]})             # emit 5 — child, depth 2
sup.handoff(from_node="writer", to_node="editor",
            payload={"draft": "..."}, role="leaf")         # emit 6 — leaf, depth 3
```

Each emission carries:

| Field | Register emits (1, 2, 3) | Handoff emits (4, 5, 6) |
|---|---|---|
| `agent_id` | `"supervisor"` | the receiving node (`researcher`, `writer`, `editor`) |
| `role` | `"root"` | `"child"` for non-terminal, `"leaf"` for terminal |
| `chain_depth` | `0` | inherited from `from_node`, +1 |
| `protocol` | `"langgraph_subgraph"` | `"langgraph_subgraph"` |
| `parent_envelope_hash` | `null` | prior emission's `integrity.current` |
| `parent_agent_id` | `null` | the `from_node` name |
| `handoff_signature` | `null` | `signer.sign(SHA-256(canonical_body))` |
| `handoff_timestamp_utc` | `null` | parent's emission timestamp |
| `child_agent_ids` | accumulates across registers | empty (or future delegations, but each emit records only one turn) |
| `protocol_data` | `{"langgraph_thread_id": <parent_trace_id>}` | same |

The full byte-level expansion is in [`subagent_chain_v0_1_minimal_envelope.json`](./subagent_chain_v0_1_minimal_envelope.json). The integration test that exercises this flow end-to-end lives at `tools/phionyx_langchain_langgraph/tests/test_multi_agent_chain.py`.

## 2. A2A — Linux Foundation Agent2Agent

A2A is the agent-to-agent protocol governed by the Linux Foundation's Agentic AI Foundation since April 2026, with 150+ supporting organisations. A2A defines:

- **Agent cards** — cryptographically domain-verified identity documents per agent.
- **Tasks** — units of delegated work, each with an `a2a_task_id`.
- **Task-acknowledgement signatures** — A2A's own protocol-level signature on task receipt.

A Phionyx-instrumented A2A bridge records each cross-agent task transition as a signed envelope. **v0.1 does NOT bind to A2A's protocol-level task-acknowledgement signature** — that is the v1.1 full A2A adapter's responsibility. v0.1 binds to its own `handoff_signature`, which proves the **producer runtime** authorised the handoff under its own key. The two signatures coexist when the full adapter ships in v1.1; v0.1 producers can already emit interoperable envelope chains.

**Mapping:**

| v0.1 field | A2A source |
|---|---|
| `agent_id` | A2A agent-card URI fragment (e.g. `"agents.example.com/research-agent"`) |
| `protocol` | `"a2a"` |
| `protocol_data.a2a_task_id` | The A2A task identifier this turn served. |
| `protocol_data.a2a_agent_card_fragment` | Optional — the part of the agent card URI that names the agent. Useful for inspector UIs that don't want to re-parse the URI. |
| `handoff_signature` | Phionyx signature (Ed25519 over the canonical RFC §2.4 body), **not** the A2A task-acknowledgement signature. |

**3-agent example** (`research-agent` → `drafting-agent` → `review-agent`): see [`subagent_chain_v0_1_a2a_envelope.json`](./subagent_chain_v0_1_a2a_envelope.json). The producer is a Phionyx-instrumented A2A bridge prototype; the wire-level A2A traffic itself is outside this example (covered by the v1.1 adapter spec).

## 3. AGNTCY / ACP (Cisco / Outshift)

The AGNTCY consortium's Agent Communication Protocol (ACP) carries an `acp_envelope_id` per inter-agent message and uses Decentralized Identifiers (DIDs) for agent identity. Mapping mirrors the A2A pattern but with different protocol-specific keys:

| v0.1 field | AGNTCY source |
|---|---|
| `agent_id` | ACP agent DID (e.g. `"did:web:agents.example.com:research"`) |
| `protocol` | `"agntcy"` |
| `protocol_data.agntcy_acp_envelope_id` | The ACP envelope identifier this turn served. |
| `handoff_signature` | Phionyx signature over the canonical RFC §2.4 body. |

No worked example is shipped in this directory for AGNTCY — the wire shape is identical to A2A modulo the `protocol`, `agent_id`, and `protocol_data.*` substitutions. A future v0.6.x release will add a dedicated example if adoption signals justify the maintenance burden.

## 4. CrewAI / AutoGen (in-process Python composition)

CrewAI and AutoGen compose multi-agent flows in Python with no wire protocol — agents are objects inside one process. The v0.1 block still applies, with two adjustments:

- `agent_id` is the framework-assigned agent name (e.g. CrewAI's `agent.role` field, AutoGen's `agent.name`).
- `protocol_data` carries the framework's session identifier (`crewai_crew_id`, `autogen_groupchat_id`).
- `parent_envelope_hash` and `handoff_signature` work exactly as for any other producer — they bind to the producer runtime's signing key, not to any CrewAI/AutoGen-internal state.

No worked example is shipped for these frameworks in v0.1; the block shape is fully determined by the schema and a worked example would add no new information beyond what the LangGraph example already shows.

## 5. `phionyx_native`

For handoffs between two Phionyx-instrumented runtimes that do **not** speak A2A / AGNTCY / LangGraph / CrewAI / AutoGen — for example, two `phionyx-core` runtimes in the same process tree, or one `phionyx-core` plus one Phionyx Inspect adapter — set `protocol="phionyx_native"`. `protocol_data` MAY be empty. This is the catch-all for compositions that don't fit any of the named third-party protocols.

## 6. Verifying a published chain

Given any of the worked examples in this directory, a third-party verifier executes:

```python
import json
from jsonschema import Draft202012Validator
from phionyx_core.contracts.envelopes import SubagentChainV0

schema = json.load(open("subagent_chain_v0_1.schema.json"))
validator = Draft202012Validator(schema)
Draft202012Validator.check_schema(schema)

envelopes = json.load(open("subagent_chain_v0_1_a2a_envelope.json"))["envelopes"]

for i, env in enumerate(envelopes):
    block = env["subagent_chain"]
    # 1. Schema validation
    errors = list(validator.iter_errors(block))
    assert errors == [], f"envelope[{i}] fails schema: {errors}"
    # 2. Pydantic round-trip (cross-checks role invariants)
    SubagentChainV0.model_validate(block)
    # 3. Hash chain integrity
    if block["role"] != "root":
        prior_current = envelopes[i - 1]["integrity"]["current"]
        assert block["parent_envelope_hash"] == prior_current, (
            f"envelope[{i}] parent_envelope_hash does not bind to "
            f"envelope[{i-1}].integrity.current"
        )
```

A verifier that does NOT have the producer's signing key still gets:

- **Schema validity** — every field is well-formed.
- **Role / depth / leaf invariants** — Pydantic catches structural violations.
- **Cross-envelope hash chain** — every `parent_envelope_hash` binds to a real prior envelope; tampering any segment breaks the chain.

A verifier that **does** have the producer's signing key additionally gets:

- **Per-envelope signature verification** — proves each envelope was emitted under that key.
- **Handoff-signature verification** — re-computes `compute_handoff_signing_body(...)`, hashes it with SHA-256, and verifies against the producer's key; proves the parent runtime authorised the specific handoff (not just that the envelope was emitted).

## 7. What v0.1 does NOT cover

- **Cross-organisation attestation.** v0.1 assumes the verifier has access to every envelope in the chain. Distributed cross-organisation attestation (organisation A's parent → organisation B's child) is deferred to v2.0.
- **A2A protocol-level signature integration.** v1.1 adapter populates `protocol_data.a2a_task_acknowledgement_signature` alongside Phionyx's own `handoff_signature`.
- **AGNTCY DID resolution.** v0.1 records the DID as a string; resolving it to a key for verification is the consumer's responsibility.
- **Cross-chain compaction.** A long chain (e.g. 100+ agent hops) accumulates 100+ envelopes; v0.1 does not specify chain compaction, snapshotting, or pruning. Deferred to v0.7.0 retention work if real-world deployments need it.
