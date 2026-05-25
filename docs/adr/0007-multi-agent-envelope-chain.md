# ADR-0007: Multi-Agent Envelope Chain — Subagent Chain v0.1

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Toygar (founder)
**Supersedes:** N/A
**Related:**
[ADR-0005 (Governance Layering)](./0005-governance-layering.md),
[ADR-0006 (MCP Shared-Trace Integration)](./0006-mcp-integration.md),
`examples/envelopes/rge_v0_2/rge_v0_2.md` §2.2.3,
`examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.md` (RFC),
`phionyx_core/contracts/envelopes/subagent_chain.py` (Pydantic model),
`tools/phionyx_langchain_langgraph/src/phionyx_langchain_langgraph/langgraph_handler.py` (LangGraph adapter).

---

## Context

Phionyx's per-turn signed evidence envelope (Reasoned Governance Envelope v0.2) reserves a `subagent_chain` block at §2.2.3 for multi-agent / subagent audit. The v0.2 sketch defined the *intent* of the block but left five concrete points unspecified:

1. The **canonical bytes** signed by `handoff_signature` (so two compliant runtimes can interoperate).
2. The **hash binding semantics** that let a verifier walk parent envelopes from any child envelope.
3. The **replay protection** discipline.
4. The **chain-depth** bound and the runtime anomaly behaviour when it is exceeded.
5. The **A2A / AGNTCY mappings** that let a Phionyx-instrumented runtime emit an evidence chain whose protocol identifier matches what downstream protocol-conformance verifiers expect.

v0.6.0 W1 of the public roadmap commits to F5 ("Multi-agent / subagent audit chain") as the first feature of the release. The decision to make here is the **shape** of the block — what runtimes interoperate on once v0.6.0 ships.

Three industry signals shaped this decision:

- **A2A protocol production adoption.** The Linux Foundation Agentic AI Foundation announced 150+ supporting organisations and production deployments for A2A in April 2026.
- **MCP + framework-adapter trend.** Phionyx already ships LangChain + LangGraph + OpenAI Agents adapters (v0.5.0) and the MCP server + pipeline-MCP layer (v0.4.0). The cross-agent evidence surface needs to compose with all four.
- **AGNTCY / ACP.** Cisco / Outshift's Agent Communication Protocol is a second cross-agent standard. Phionyx needs a place for it in the schema even before the full adapter ships.

## Decision

Phionyx ships `subagent_chain` v0.1 as the **protocol-agnostic active specification** of the block. The block is:

- **Required-fields rich.** Five fields that the v0.2 sketch left optional become required: `chain_depth`, `protocol`, `parent_envelope_hash`, `handoff_signature`, `handoff_timestamp_utc`. The first three of these are the minimum surface required for a verifier to walk the chain and verify each segment; the last two are required for replay protection.

- **Protocol enum, not protocol prose.** The `protocol` field is a closed enum (`a2a`, `agntcy`, `phionyx_native`, `langgraph_subgraph`, `crewai`, `autogen`). Producers cannot smuggle arbitrary protocol identifiers in. Adding a new protocol requires bumping this RFC.

- **Open `protocol_data` for extension.** Protocol-specific data (A2A task IDs, ACP envelope IDs, LangGraph thread IDs) lives in a free-form `protocol_data` object with reserved keys defined per protocol. Non-reserved keys MUST be namespaced by protocol (`a2a_*`, `crewai_*`, etc.) to keep storage collision-free across runtimes.

- **`handoff_signature` over the producer's own key.** The signature on a handoff binds the receiver's view to the parent runtime's signing key (the same key used for the parent envelope's `integrity.signature`). Two reasons:
  - A verifier needs to trust exactly **one** key per runtime, not a separate "handoff key."
  - The handoff signature does not interact with the cross-protocol signature surface (A2A task acknowledgement, ACP envelope signature) — those are protocol-internal and remain the v1.1 full-adapter responsibility.

- **Canonical-JSON signing body.** `compute_handoff_signing_body(...)` returns the byte-deterministic encoding (sort_keys, no whitespace, ASCII-safe) of five fields in alphabetical order. Two compliant runtimes given the same inputs produce byte-identical signing bodies — the precondition for cross-runtime signature verification.

- **Role enforced by schema invariants.** `root`, `child`, and `leaf` have schema-level `if/then` invariants (root depth=0 + parent fields null; non-root depth≥1 + parent fields non-empty; leaf has zero child_agent_ids). The same invariants are enforced by the Pydantic model's `model_validator(mode="after")`. Both surfaces are bit-compatible.

## Why protocol-agnostic instead of A2A-only

A2A has industry momentum and would be the "obvious" target — but:

- **The shape problem is the same across protocols.** A2A handoff and LangGraph supervisor handoff and AGNTCY ACP handoff all need the same fields: parent envelope reference, handoff signature, replay window, depth, role. Locking the schema to A2A would force separate schemas for non-A2A producers — multiplying the verifier's job and the documentation burden.
- **Phionyx already has LangGraph in production (v0.5.0).** Locking to A2A would create a schema mismatch with the supervisor adapter Phionyx is already shipping. v0.1's `langgraph_subgraph` protocol slot lets the existing adapter populate the block on day one.
- **A2A v1.1 adapter is separately scoped.** The full A2A adapter (v1.1 of the public roadmap) will populate the A2A protocol-level task-acknowledgement signature alongside Phionyx's `handoff_signature`. v0.1 reserves the wire shape for that coexistence without taking on the A2A wire-format work prematurely.

## Why this lives in phionyx_core/contracts/envelopes/

`subagent_chain.py` lives in the **core** contracts namespace, not in a bridge adapter package, because:

- The schema is the **wire contract** between any two Phionyx-instrumented producers. Bridge adapters (LangGraph supervisor, future A2A adapter, AGNTCY adapter) must import the same Pydantic model and the same `compute_handoff_signing_body` helper to guarantee interoperability.
- The core/contracts boundary is exactly the place for "what every adapter must agree on" surfaces. The W1.2 implementation adds no delivery-framework imports (Pydantic only); the core boundary rules in `.claude/rules/core-boundary.md` are preserved.
- Founder-approved core/contracts escalation was obtained 2026-05-25 specifically for W1.2; the escalation rule in `.claude/CLAUDE.md` was followed.

## Why role+depth+parent_envelope_hash instead of an alternative model

Alternatives considered:

- **Per-agent envelope chains only** — no cross-agent linkage. Rejected: makes "verify the full multi-agent flow" require side-channel metadata the v0.6.0 theme explicitly works to eliminate.
- **Merkle tree of agent envelopes** — agents publish a tree root; verifier walks tree. Rejected: more complex, not better. Linear `parent_envelope_hash` chain composes with the existing single-runtime hash chain pattern Phionyx already uses for per-turn evidence; one mechanism, not two.
- **Centralised handoff log** — a coordinator collects all handoffs into one signed chain. Rejected: a centralised log is a single point of failure and would conflict with cross-organisation deployments where no single party owns the log.

`role + depth + parent_envelope_hash` keeps the chain reconstruction local (each agent emits its own envelopes, no coordinator needed), composable (the same hash chain mechanism applies inside one runtime and across runtimes), and verifier-cheap (any verifier with access to the envelopes can walk the chain in O(N) without indexing).

## Consequences

**Positive:**

- The LangGraph supervisor adapter (already shipping in v0.5.0) gains evidence-chain-level multi-agent audit with no API change for callers — `register()` and `handoff()` retain their existing signatures, only the emitted envelope shape extends.
- A2A bridge prototypes can emit interoperable envelopes immediately. The full A2A wire-level adapter (v1.1) will only add `protocol_data.a2a_task_acknowledgement_signature` alongside the Phionyx signature.
- Phionyx's "framework-agnostic" identity is preserved — the schema does not commit to any third-party framework's identity model.
- Verifiers can reconstruct cross-agent flows from the envelope chain alone with no side-channel metadata.

**Negative / accepted:**

- Protocol enum is closed — adding a new protocol requires a schema bump and a coordinated release.
- v0.1 does not specify cross-organisation attestation. Distributed cross-org verification remains v2.0 work.
- Chain compaction / snapshotting is not specified. Producers emitting very long chains (100+ hops) currently pay full storage for every envelope. Deferred to v0.7.0 retention scope if real-world deployments require it.

## Verification

- 30 unit tests in `tests/unit/core/test_subagent_chain.py` — Pydantic model invariants + canonical-JSON signing body.
- 12 contract tests in `tests/contract/test_subagent_chain_schema.py` — schema ↔ model parity + structural field-set match.
- 7 integration tests in `tools/phionyx_langchain_langgraph/tests/test_multi_agent_chain.py` — end-to-end 3-agent chain + hash chain verification + tamper detection.
- W1.2 + W1.3 commits (`e4d20cc6`, `0324343e`) carry the full test counts and zero-regression evidence.

## Test plan (ongoing)

- W1.5 will mark the RGE v0.2 §2.2.3 `subagent_chain` block status `reserved-for-v0.6.0-f5` → `active` and cross-link this RFC.
- W2 (F9 LLM-as-judge) and W3 (F13 cross-runtime import) of v0.6.0 do not touch this schema; they consume it.
- v0.6.0 final ship will bundle the langchain-langgraph package PyPI release with `phionyx_core` dependency bumped to whatever core version v0.6.0 publishes.

## Alternatives considered (not chosen)

- **Wait for A2A protocol standardisation maturity.** Rejected: A2A is at production-deployment stage already; waiting forfeits the position.
- **Ship a separate `subagent_chain` schema per protocol.** Rejected: see "Why protocol-agnostic instead of A2A-only" above.
- **Skip multi-agent audit until v0.7.0.** Rejected: the v0.6.0 release theme is multi-agent evidence; this is the core feature, not a side concern.

## Open follow-ups (not blocking v0.6.0)

- Worked AGNTCY/ACP example in `examples/envelopes/subagent_chain_v0_1/`.
- v0.6.0 W4: `/phionyx:replay-trace` command in the Claude Code plugin (v0.5.1) extended to walk multi-agent envelope chains.
- v1.1: full A2A protocol adapter populating `protocol_data.a2a_task_acknowledgement_signature`.
- Cross-organisation distributed attestation (deferred to v2.0).
