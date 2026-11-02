# phionyx-mcp-server

> The MCP trust boundary in the Phionyx runtime — descriptor signing, signed
> evidence envelopes, and a hash-chained audit chain over third-party MCP tool calls.

`phionyx-mcp-server` sits between an MCP-capable host (Claude Desktop, Cursor, Zed,
VS Code, JetBrains) and any third-party MCP server it talks to, producing
hash-chained evidence at every trust-boundary crossing (un-rechained edits are detectable; producer authenticity requires a configured signer). It closes a security gap
the MCP specification
([2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)) explicitly
defers to implementors:

> *"MCP itself cannot enforce these security principles at the protocol level;
> implementors SHOULD..."*

The threat surface is aligned with
arXiv:[2512.06556](https://arxiv.org/abs/2512.06556) (Jamshidi et al., *Securing the
Model Context Protocol*) — tool poisoning, shadowing, rug pulls.

## Where it fits

Phionyx ships three distinct things, each on its own version line — don't
cross-attribute them:

- **Engine — `phionyx-core`:** the deterministic governance runtime (46-block
  canonical pipeline, kill switch, HITL queue, ethics/safety gates, signed audit
  chain). `pip install phionyx-core`.
- **Gate — `phionyx-pipeline-mcp`:** an agent self-claim gate that verifies
  "I fixed / I tested / this changed" against the repository's actual diff.
- **Format — AI Runtime Evidence Protocol (AIREP):** an experimental,
  vendor-neutral open format for an AI **decision receipt** — one signed,
  hash-chained, offline-checkable record per runtime decision, readable by anyone
  and tied to no vendor. AIREP is a *proposed* format, not a ratified standard.
  AIREP v0.2.0-beta.1 was published on 9 September 2026 as an experimental prerelease: it ships a first-party Python producer for Decision, Control, Execution and Effect artifacts, runnable lifecycle examples and structured reconciliation; the v0.1 line remains frozen and supported. External implementation results are version- and role-specific — an independently authored producer measured against frozen v0.1.2, and an independently implemented consumer/verifier measured against an earlier v0.2 handoff — and they do not establish same-beta producer-to-consumer interoperability.
  Phionyx's **Reasoned Governance Envelope (RGE)** is developed alongside AIREP;
  a conformant projection between the two is **not implemented** (measured 2026-08-06: AIREP's own reference verifier rejects an RGE envelope handed to it directly).

**This package** is the outward MCP **trust boundary** — it produces hash-chained
evidence (optionally Ed25519-signed) over third-party MCP tool calls. The envelopes
it emits are RGE records. It interoperates with the gate through a
shared session trace, so both governance surfaces share one view.

## Status

**v0.2.2.** Five of eight capabilities are fully implemented; three are explicit
stubs that return structured `not_implemented` markers (callers can detect server
maturity). The two load-bearing capabilities — descriptor verification and
tool-call audit — are live. Envelopes follow **RGE v0.2** (Reasoned Governance
Envelope).

| # | Capability | Status |
|---|---|---|
| 1 | Tool descriptor hash | ✅ implemented |
| 2 | Descriptor change detection | ✅ implemented |
| 3 | Tool permission scope | 🟡 envelope field populated; policy logic stub |
| 4 | Tool call I/O hash | ✅ implemented |
| 5 | User approval state | 🟡 envelope field populated; UX surface stub |
| 6 | Runtime anomaly record | 🟡 records to the audit side-log; drift scoring stub |
| 7 | Signed evidence envelope | ✅ implemented (RGE v0.2) |
| 8 | Chain verification command | ✅ implemented (`phionyx-mcp verify-chain`) |

## Install

```bash
pip install phionyx-mcp-server
phionyx-mcp --help
```

## Use — as an MCP server

Add to your MCP-capable host (Claude Desktop example):

```json
{
  "mcpServers": {
    "phionyx-governance": { "command": "phionyx-mcp-server" }
  }
}
```

The host then sees four production MCP tools:

- `verify_tool_descriptor(descriptor, baseline_hash)` — hash and compare against an
  approved baseline (full descriptor, including `protocolVersion`).
- `record_tool_call(turn_index, user_text, producer, …, trace_id=None)` — emit a
  signed RGE v0.2 envelope. `trace_id` is optional; resolved from `PHIONYX_TRACE_ID`
  or `~/.phionyx/active_trace`.
- `verify_chain_integrity(trace_id=None)` — walk the chain, refuse mixed schemas.
- `query_audit_history(trace_id=None, limit=50)` — replay envelopes for review.

Plus three stub tools returning structured `not_implemented` markers.

## Shared trace with the gate

When installed alongside `phionyx-pipeline-mcp`, the two servers share a single
`trace_id` per session, so one session's evidence spans both governance surfaces:

- `PHIONYX_TRACE_ID` env var → highest precedence.
- `PHIONYX_ACTIVE_TRACE_FILE` (default `~/.phionyx/active_trace`) → file fallback.
- The first caller generates a UUID-derived trace and persists it.

## Use — as a CLI

```bash
phionyx-mcp head --trace trace-abc123          # current chain head
phionyx-mcp verify-chain --trace trace-abc123  # walk + verify the chain
phionyx-mcp show --trace trace-abc123 --turn 7 # show one envelope
```

`verify-chain` selects its verifier from the environment: `PHIONYX_MCP_VERIFY_KEY`
(Ed25519 public key, hex or path) → verify signatures; `PHIONYX_MCP_DEMO=1` → the
demo HMAC verifier; neither → **signatures are not checked** (hash continuity only).

**Exit code — the same contract the printed `assurance` block reports:**

| exit | meaning |
|---|---|
| `0` | signatures verified (`valid: true` — assurance **E2**, or **E0** in demo mode) |
| `1` | tamper/break (`valid: false`), **or** signatures not verified (`valid: null`, `NOT_MEASURED` — no verify key, so tamper-evidence is unmeasured, never a silent pass) |
| `2` | invocation error (bad path / corrupt chain) |

The result carries an `assurance` block separating the dimensions — `schema`,
`hash_continuity`, `signature_performed`, `signature_valid`, `algorithm`, `key_id`,
`key_trust`, `revocation`, `overall_assurance` (E0/E1/E2/INVALID). `key_trust` and
`revocation` are `NOT_MEASURED` here — they are concerns AIREP defines but an RGE v0.2
envelope does not carry, reported rather than faked.

## Persistence

Envelopes are written under `$PHIONYX_MCP_AUDIT_ROOT` (default `~/.phionyx/mcp_audit/`):

```
<root>/<trace_id>/chain.jsonl      (append-only index)
<root>/<trace_id>/<turn:06d>.json  (full canonical-JSON envelope)
```

Swap the persistence layer by passing an alternative `EnvelopeStore`-protocol
implementation (S3, DynamoDB, …).

## Schema — RGE v0.2

Envelopes conform to **RGE v0.2** (Reasoned Governance Envelope). RGE is being
developed toward AIREP interoperability; no AIREP-conformance claim is made. The signature
covers all envelope content except the self-referential
`mcp_tool_audit.signed_envelope_ref`. The schema, RFC, and worked examples ship in
this repository.

### Signing — the signer is chosen by the environment

| environment | signer | `integrity.signature` |
|---|---|---|
| `PHIONYX_MCP_SIGNING_KEY` set (hex or path; `PHIONYX_MCP_KEY_ID` optional) | **Ed25519** (production) | `ed25519:<hex>` |
| `PHIONYX_MCP_DEMO=1` | demo HMAC (evidence level **E0** — the secret ships in-package) | `demo-hmac:<hex>` |
| neither | **UNSIGNED** | `unsigned` |

A run with no key provisioned emits **explicitly unsigned** envelopes — the demo
HMAC is never a silent stand-in for a missing production key. A real Ed25519 key
always wins over the demo flag.

## Tests

```bash
pip install -e .
pytest -q
```

The suite pins descriptor-hash semantics (full descriptor including
`protocolVersion`), RGE v0.2 schema conformance (jsonschema Draft 2020-12), and
hash-chain integrity (tamper, reorder, and mixed-schema detection).

## See also

- **Engine** — [phionyx-core on PyPI](https://pypi.org/project/phionyx-core/)
- **Gate** — [phionyx-pipeline-mcp](https://github.com/halvrenofviryel/phionyx-pipeline-mcp)
- **Evidence format** — [AI Runtime Evidence Protocol (AIREP)](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol)
- **Runtime narrative** — [phionyx.ai](https://phionyx.ai)

## License

AGPL-3.0-or-later.
