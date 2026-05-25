# Migration: RGE v0.1 → v0.2

> Companion to `rge_v0_2.md` (RFC) and `rge_v0_2.schema.json` (canonical schema).
> v0.2 is a **strictly additive** extension of v0.1. This document is the contract between producers and consumers during the transition.

## 1. TL;DR

| Concern | Answer |
|---|---|
| **Mandatory change for v0.1 → v0.2?** | Change `schema` field from `..._v0_1` to `..._v0_2`. Nothing else. |
| **Are v0.1 envelopes valid v0.2 envelopes?** | After the schema-field bump, yes. The v0.2 schema accepts the v0.1 surface as a degenerate (no-optional-blocks) v0.2 envelope. |
| **Will my v0.1 consumer break on v0.2?** | Only if it strictly checks `schema == "...v0_1"`. Treat the schema field as a version-prefix match if you need to accept both. |
| **Can I populate v0.2 blocks now without F1/F4/F8/F5?** | Yes. Use `status: "reserved-..."` for blocks where the corresponding feature hasn't shipped. Producers may populate any subset of v0.2 blocks. |
| **Do I need to re-sign v0.1 envelopes when migrating?** | Yes. The hash covers the canonical JSON, which now includes the new schema string. Migrated envelopes have new `integrity.current` values. v0.1 chain hashes are NOT reusable. |

## 2. Compatibility Matrix

| Surface | v0.1 | v0.2 | Notes |
|---|---|---|---|
| `schema` constant | `..._v0_1` | `..._v0_2` | Only mandatory delta. Validators MUST reject mismatched constants against the active schema. |
| `subject` (5 required keys) | ✓ | ✓ | Identical surface. No field added or removed. |
| `input.user_text` | ✓ | ✓ | Same constraints (1..4000 chars). |
| `input.state_vector` (8 axes) | ✓ | ✓ | Identical surface. |
| `input.safety` | ✓ | ✓ | Identical. |
| `path[]` | ✓ | ✓ | Identical. `path_step.disposition` enum unchanged in v0.2. |
| `output.redacted` + `output.text` | ✓ | ✓ | Identical. |
| `metrics` (4 keys) | ✓ | ✓ | Identical. |
| `reasoning` block | optional, partial | optional, schematised | v0.1 fields kept verbatim. v0.2 adds `confidence_delta` (optional, NULL allowed) and `evidence_links[]` (optional, may be empty). |
| `retrieval` block | — | optional, reserved/active | New in v0.2. `status: "reserved-for-v0.4.1-f8"` until F8 ships. |
| `subagent_chain` block | — | optional, reserved/active | New in v0.2. v0.1 active spec shipped 2026-05-25 at `examples/envelopes/subagent_chain_v0_1/`. New producers set `status: "active"` and populate the full surface; reserved sentinel retained for backward compat. |
| `mcp_tool_audit` block | — | optional, reserved/active | New in v0.2. `status: "reserved-for-v0.4.0-f1"` until F1 ships. |
| `integrity` (4 keys) | ✓ | ✓ | Identical surface. Hash inputs differ because `schema` field differs. |

## 3. Opt-in Pattern

v0.2's adoption strategy is **opt-in per block**, not all-or-nothing:

```
Producer maturity ladder:

[Level 0]  v0.1 envelope (schema bump only)         ← rge_v0_2_minimal_envelope.json
   ↓
[Level 1]  + reasoning block fully populated         ← F4 reasoning_surface (v0.5.0)
   ↓
[Level 2]  + mcp_tool_audit when MCP tools used      ← F1 MCP recorder (v0.4.0)  ← rge_v0_2_mcp_envelope.json
   ↓
[Level 3]  + retrieval when RAG used                 ← F8 retrieval audit (v0.4.1)
   ↓
[Level 4]  + subagent_chain when multi-agent         ← F5 multi-agent audit (v0.6.0)
   ↓
[Level 5]  full RGE — all four optional blocks active where applicable
```

A producer at Level 0 is a fully-conformant v0.2 producer. A consumer that depends on Level-2 evidence MUST tolerate Level-0 envelopes by treating absent `mcp_tool_audit` blocks as "this turn made no MCP calls".

## 4. Mechanical migration script

For producers using `wrapper.py`-shape v0.1 envelopes:

```python
import json
from pathlib import Path

V0_1 = "phionyx.governed_response_envelope.v0_1"
V0_2 = "phionyx.governed_response_envelope.v0_2"

def migrate_envelope(env: dict) -> dict:
    """Migrate a v0.1 envelope to v0.2 surface.

    NOTE: This changes the canonical JSON, so the migrated envelope's
    integrity hashes are DIFFERENT from the v0.1 envelope's. Migrated
    envelopes break v0.1 chain continuity by design — a chain MUST be
    either all-v0.1 or all-v0.2, not mixed. Cut over at a chain boundary
    (e.g. on session restart) rather than mid-chain.
    """
    if env.get("schema") != V0_1:
        raise ValueError(f"expected v0.1 envelope, got {env.get('schema')!r}")
    env["schema"] = V0_2
    # No other changes. v0.2 schema accepts the v0.1 surface as-is.
    # Re-hash + re-sign integrity.current / integrity.signature separately.
    return env

# Example:
v0_1_env = json.loads(Path("envelope.v0_1.json").read_text())
v0_2_env = migrate_envelope(v0_1_env)
# Now re-compute v0_2_env["integrity"]["current"] and re-sign before persisting.
```

The script does *not* re-sign because key access is environment-specific. Re-signing is the producer's responsibility.

## 5. Consumer recommendations

### 5.1 Backward-compatible consumers (accept v0.1 + v0.2)

```python
ACCEPTED_SCHEMAS = {
    "phionyx.governed_response_envelope.v0_1",
    "phionyx.governed_response_envelope.v0_2",
}

def is_governed_envelope(env: dict) -> bool:
    return env.get("schema") in ACCEPTED_SCHEMAS
```

When reading v0.2-only fields (`reasoning.confidence_delta`, any of the new blocks), guard with `env.get("...")` rather than direct indexing so v0.1 envelopes don't raise.

### 5.2 v0.2-only consumers

After the cutover (founder-decided per-deployment), validate strictly:

```python
from jsonschema import Draft202012Validator

with open("rge_v0_2.schema.json") as f:
    SCHEMA = json.load(f)

V = Draft202012Validator(SCHEMA)

def must_be_v0_2(env: dict) -> None:
    errors = list(V.iter_errors(env))
    if errors:
        raise ValueError("envelope is not v0.2-conformant: " + str(errors))
```

### 5.3 Chain verifiers

Chain verifiers MUST refuse to walk across a schema boundary. Pseudocode:

```python
def verify_chain(envelopes: list[dict]) -> None:
    if not envelopes:
        return
    schemas = {e["schema"] for e in envelopes}
    if len(schemas) > 1:
        raise ValueError(f"mixed schemas in chain: {schemas} — refusing to verify")
    # ... continue with hash chain verification
```

The reason: v0.2 envelopes have different canonical-JSON forms than v0.1 envelopes (the `schema` string changed), so the hash chain breaks at the migration boundary. The chain is a tree, not a line, after migration — the post-migration chain starts a new branch.

## 6. Field-by-field migration table

| Field path | v0.1 status | v0.2 status | Action |
|---|---|---|---|
| `schema` | required, `..._v0_1` | required, `..._v0_2` | **Change string.** |
| `subject.*` | required (5) | required (5) | None. |
| `input.*` | required (3) | required (3) | None. |
| `path[]` | required, min 1 | required, min 1 | None. |
| `output.redacted` | required | required | None. |
| `output.text` | required (nullable) | required (nullable) | None. |
| `metrics.*` | required (4) | required (4) | None. |
| `reasoning.model_proposed_action` | optional | optional | None. |
| `reasoning.model_stated_rationale` | optional, str-or-null | optional, str-or-null | None. |
| `reasoning.runtime_policy_basis` | optional | optional, str[] | None. |
| `reasoning.runtime_decision` | optional (free string) | **required when reasoning present**, enum | If `reasoning` block exists, ensure `runtime_decision ∈ {release, block, defer, redact}`. |
| `reasoning.decision_reason` | optional | **required when reasoning present** | If `reasoning` block exists, populate. |
| `reasoning.rationale_action_consistency` | optional | optional, `[0,1]` or null | None. |
| `reasoning.policy_alignment_score` | optional | optional, `[0,1]` or null | None. |
| `reasoning.confidence_delta` | — | optional, number or null | Add NULL when migrating; populate when F4 ships. |
| `reasoning.evidence_links` | — | optional, typed array | Add `[]` when migrating; populate when producers surface evidence. |
| `reasoning.scoring_method` | optional | optional | None. |
| `retrieval` | — | optional block | Omit entirely when migrating; F8 populates from v0.4.1. |
| `subagent_chain` | — | optional block | Omit entirely when migrating from v0.1. v0.6.0+ producers populate per `examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.md` (RFC) and `migration_rge_v0_2_to_subagent_v0_1.md` (active migration). |
| `mcp_tool_audit` | — | optional block | Omit entirely when migrating; F1 populates from v0.4.0. |
| `integrity.*` | required (4) | required (4) | **Re-compute hashes + signature** after the schema field changes. |

The only behavioural change is to `reasoning.runtime_decision` and `reasoning.decision_reason`: when migrating an envelope whose v0.1 `reasoning` block was minimally populated, ensure the two required v0.2 keys are present. The wrapper today always sets both, so the practical change is zero.

## 7. Cutover Strategy

For Phionyx-internal traces:

1. **Schema field flip:** Cut over at the next session restart. Do not mid-chain switch.
2. **Producer instrumentation:** Update `wrapper.py` and Core's envelope serialisation to emit `..._v0_2`. Single one-line change.
3. **Consumer tolerance window:** Run both-schema consumers for ~30 days (one Substack post cycle) to absorb stale chains.
4. **v0.2-only mode:** Once all live producers ship v0.2 and stored v0.1 chains have been migrated/archived, drop the v0.1 acceptance in consumers.

For public consumers (Inspect AI storage adapter, OTel exporter, third-party tooling that reads RGE):

- Document support as `[RGE v0.1, RGE v0.2]` until v0.4.0 release.
- After v0.4.0 ships, drop v0.1 support after a 60-day grace window. v0.1 envelopes that need to be replayed past the grace window should be migrated via the script in §4.

## 8. Open Migration Risk

The only **non-trivial** migration risk is **chain continuity**. A trace that started in v0.1 must not cross into v0.2 mid-chain because the hash chain breaks at the schema change. Operationally:

- New traces after the schema bump: v0.2 from envelope #1.
- Long-running traces alive at the bump: archive at the current envelope, start a new trace under v0.2 from envelope #1.
- Historical traces: keep in v0.1 archive; never replay into v0.2 chain.

`verify_chain` MUST refuse mixed-schema chains (per §5.3) so accidental mid-chain migrations fail loudly rather than silently.

---

*Migration document authored alongside the v0.2 RFC, 2026-05-19. Founder approval required before public sync to `phionyx-research/examples/envelopes/rge_v0_2/`.*
