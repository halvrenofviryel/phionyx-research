# Migration: RGE v0.2 `subagent_chain` reserved → v0.1 active

> **Scope:** Producers that previously emitted RGE v0.2 envelopes with
> `subagent_chain.status = "reserved-for-v0.6.0-f5"` (or no `subagent_chain`
> block at all) and now want to populate the v0.1 active shape.
>
> **TL;DR:** v0.1 is a strict extension of the v0.2 reserved sketch. No
> historical envelopes need re-signing; existing chains stay verifiable.
> Adoption is per-producer and per-emission — producers may switch from
> "reserved" to "active" between any two consecutive envelopes.

## 1. What changed between v0.2 reserved and v0.1 active

### 1.1 New required fields

The v0.2 sketch in [`rge_v0_2.md`](../rge_v0_2/rge_v0_2.md) §2.2.3 declared three required fields (`status`, `agent_id`, `role`) and four implicitly optional ones. v0.1 promotes five additional fields to required-when-active:

| Field | v0.2 reserved | v0.1 active |
|---|---|---|
| `status` | enum: `reserved-for-v0.6.0-f5`, `active` | const `active` |
| `agent_id` | required | required |
| `role` | required | required |
| `chain_depth` | not specified | **required** (≥0; root MUST be 0) |
| `protocol` | optional | **required** |
| `parent_envelope_hash` | optional | **required** (null when role=root) |
| `handoff_signature` | optional | **required** (null when role=root) |
| `handoff_timestamp_utc` | not specified | **required** (null when role=root) |

The intent has not changed — every concept the v0.2 sketch named is preserved. v0.1 simply removes the "everything is optional, producers figure it out" license that v0.2 retained for the placeholder phase.

### 1.2 New optional fields

| Field | Purpose |
|---|---|
| `parent_agent_id` | The parent's `agent_id`. Lets evidence inspector UIs render the chain without resolving `parent_envelope_hash` against the store first. |
| `child_agent_ids` | For non-leaf nodes, the children this agent handed off to. Empty for leaves. Fan-out allowed. |
| `protocol_data` | Open object for protocol-specific extension. Reserved keys: `depth_exceeded`, `replay_window_seconds_used`, `a2a_task_id`, `agntcy_acp_envelope_id`, `langgraph_thread_id`, `crewai_crew_id`, `autogen_groupchat_id`. |

### 1.3 New invariants

The schema's `allOf` block enforces three constraints v0.2 left to producer discipline:

1. `role == "root"` ⇒ `chain_depth == 0` AND all four parent fields are `null`.
2. `role ∈ {"child", "leaf"}` ⇒ `chain_depth ≥ 1` AND `parent_envelope_hash` + `handoff_signature` + `handoff_timestamp_utc` are non-empty strings.
3. `role == "leaf"` ⇒ `child_agent_ids` is empty.

Existing producers that already followed these conventions need no behavioural change — only the schema declaration.

## 2. Migration paths

### 2.1 If your existing envelopes carry `status: reserved-for-v0.6.0-f5` only

Such envelopes were placeholder declarations — they asserted "this producer intends to participate in multi-agent evidence but does not yet have F5 implementation." They are NOT signed evidence about a real handoff.

**No re-signing is required.** Migrate at the producer:

```diff
- block = {
-     "status": "reserved-for-v0.6.0-f5",
-     "agent_id": "researcher",
-     "role": "root",
- }
+ block = SubagentChainV0(
+     agent_id="researcher",
+     role="root",
+     chain_depth=0,
+     protocol="langgraph_subgraph",  # or "a2a", "agntcy", etc.
+     parent_envelope_hash=None,
+     handoff_signature=None,
+     handoff_timestamp_utc=None,
+     child_agent_ids=[],              # or accumulated list at emit time
+     protocol_data={...},             # protocol-specific extension
+ ).model_dump(mode="json")
```

The next envelope your producer emits will carry the v0.1 active block. Historical envelopes with the reserved placeholder remain valid (they never claimed to carry active evidence).

### 2.2 If your existing envelopes have no `subagent_chain` block at all

This is the common case — RGE v0.2 made the block optional. Adopting v0.1 means starting to populate the block on emissions that involve multi-agent transitions.

**No historical migration is required.** Old envelopes remain valid and chain-verifiable. New envelopes opt in by including the v0.1 active block:

```python
from phionyx_core.contracts.envelopes import SubagentChainV0

block = SubagentChainV0(
    agent_id=...,
    role="root",        # or "child", "leaf"
    chain_depth=...,    # 0 for root, +1 per handoff
    protocol=...,
    parent_envelope_hash=...,
    handoff_signature=...,
    handoff_timestamp_utc=...,
    parent_agent_id=...,
    child_agent_ids=[...],
    protocol_data={...},
)
# Then include block.model_dump(mode="json") as the "subagent_chain" key
# on your RGE envelope (sibling of subject/input/path/output/metrics/integrity).
```

The hash chain is computed over the entire envelope including the new block, so verifiers will validate the new envelopes correctly out of the box.

### 2.3 If you previously rolled your own handoff signature scheme

Replace it with `compute_handoff_signing_body(...)` from `phionyx_core.contracts.envelopes`. This guarantees byte-identical canonical body across producers, which is what makes the chain verifiable across runtime boundaries:

```python
from phionyx_core.contracts.envelopes import compute_handoff_signing_body
import hashlib

body = compute_handoff_signing_body(
    parent_envelope_hash=parent_env["integrity"]["current"],
    parent_agent_id="researcher",
    child_agent_id="writer",
    child_protocol="langgraph_subgraph",
    handoff_timestamp_utc=parent_env["subject"]["timestamp_utc"],
)
body_hash = hashlib.sha256(body).hexdigest()
handoff_signature = signer.sign(body_hash)
```

Producer-private encodings will NOT be accepted by future versions of this RFC — interoperability requires the canonical form.

## 3. Coexistence with v0.2 reserved consumers

v0.1 envelopes have `subagent_chain.status: "active"`. Older consumers that only recognise `subagent_chain.status: "reserved-for-v0.6.0-f5"` should treat `"active"` envelopes as opaque pass-through evidence:

- Schema validation will pass (v0.1 is a strict refinement of v0.2's open shape for the block; an `active` block validates against any consumer that does not require the reserved sentinel).
- Older consumers that hard-code `status == "reserved-for-v0.6.0-f5"` MUST be updated to accept `active` as well. This is the only breaking behaviour, and it affects consumers, not producers.

## 4. Verification checklist

After migration, run these checks before declaring the chain ready:

- [ ] Every emission's `subagent_chain` block validates against `subagent_chain_v0_1.schema.json`.
- [ ] Every emission's block loads into `SubagentChainV0.model_validate(...)` without raising.
- [ ] For every non-root emission, `block.parent_envelope_hash == prior_envelope.integrity.current`.
- [ ] For every non-root emission, `signer.verify(SHA-256(compute_handoff_signing_body(...)), block.handoff_signature)` succeeds (if the producer's verifier API exposes `verify`).
- [ ] For every leaf emission, `block.child_agent_ids == []`.
- [ ] Outer envelope's `integrity.current` is unchanged when the block is recomputed from inputs (proves the block is in the hash domain, not a passenger field).

## 5. Reference implementation

The `PhionyxLangGraphSupervisor` adapter in `tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/langgraph_handler.py` is the v0.6.0 W1.3 reference implementation. The 3-agent integration test in `tools/phionyx_langchain_langgraph/tests/test_multi_agent_chain.py` exercises every clause of this migration.
