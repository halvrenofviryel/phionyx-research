# phionyx-pipeline-mcp

> A self-governance MCP server for Claude Code — gates the agent's own *"I fixed this / I tested that / this code path changed"* declarations against `git diff` truth and a deterministic gate.

`phionyx-pipeline-mcp` solves a less-discussed agent-trust problem: when an AI coding agent reports back on its own work, that report is itself a trust object. Without verification, you accept it on faith.

This package gives any MCP-capable host (Claude Desktop, Cursor, Zed, VS Code, JetBrains) a six-tool surface that turns those self-reports into reviewable evidence — coverage of paths claimed vs. paths actually touched, severity-weighted evidence taxonomy, drift tracking across a session, and an explicit `pass | regenerate | reject` directive before the agent claims "done."

## Where this sits in the Phionyx stack

Phionyx ships three distinct things, each with its own version line. This package is **the gate**:

- **Engine** — `phionyx-core` (current release on PyPI): the deterministic runtime (46-block canonical pipeline, state vector, kill switch, HITL, ethics/safety gates, audit-record contracts — the signed chain is demonstrated at the MCP boundary today).
- **Gate** — `phionyx-pipeline-mcp` (**this package**): the inward-facing self-claim gate described here. It verifies what the agent says about its own work against `git diff` truth and a deterministic gate. **v0.3.1** adds opt-in, default-off evidence binding (the `require_tool` directive + continuity binding) on top of the claim-grounding gate. It is the claim-governance layer of the Phionyx governance stack; `phionyx-mcp-server` (current release on PyPI) is the outward MCP trust boundary.
- **Format** — the **AI Runtime Evidence Protocol (AIREP)**: an experimental, vendor-neutral open format for an *AI decision receipt* — one signed, hash-chained, offline-checkable record per AI runtime decision, readable by anyone and tied to no vendor. Phionyx's **Reasoned Governance Envelope (RGE)** is developed alongside AIREP; a conformant projection between the two is **not implemented** (measured 2026-08-06: AIREP's own reference verifier rejects an RGE envelope handed to it directly). AIREP is a *proposed* format, not a ratified standard. AIREP v0.2.0-beta.1 was published on 9 September 2026 as an experimental prerelease: it ships a first-party Python producer for Decision, Control, Execution and Effect artifacts, runnable lifecycle examples and structured reconciliation; the v0.1 line remains frozen and supported. External implementation results are version- and role-specific — an independently authored producer measured against frozen v0.1.2, and an independently implemented consumer/verifier measured against an earlier v0.2 handoff — and they do not establish same-beta producer-to-consumer interoperability. See [`ai-runtime-evidence-protocol`](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol).

These three version lines — engine v0.9.1, gate v0.3.1, and AIREP v0.2.0-beta.1 (experimental prerelease; v0.1 frozen and supported) — are never cross-attributed.

## How it works — three-stage verification

```
Stage 1: LLM declaration   →   Stage 2: Repo truth          →   Stage 3: Deterministic gate
  "I fixed X, tested Y,         git diff parsed; functions       evidence + recency + revision
   affected paths a,b,c"        extracted; cross-checked         thresholds → directive
```

The gate is deterministic. Stage 1 (the agent's input) is stochastic. Stage 2 — verifying the agent's path declarations against the actual `git diff` — is what narrows the gap.

(These three stages are internal to the gate's verification flow. They are unrelated to the broader Phionyx governance-stack layers.)

## Where this fits on phionyx.ai

This package surfaces under [**phionyx.ai/bounded-authority**](https://phionyx.ai/bounded-authority) — the safety-first AI providers entry. It is the inward-facing self-claim gate that verifies the agent's own "I fixed / I tested / this code path changed" narration against the repository's actual diff and a deterministic gate, producing a `pass | regenerate | reject` directive paired with reviewer-runnable evidence.

## Companion package: phionyx-mcp-server

This package is the **inward-facing** layer: it gates what the agent says about its own work.

A companion package, [`phionyx-mcp-server`](https://github.com/halvrenofviryel/phionyx-mcp-server) (current release on PyPI), is the **outward-facing** layer: it sees the host calling a third-party MCP server and signs evidence of that call (descriptor hash, drift detection, audit chain).

When both packages are installed and registered with the same Claude Code host, they agree on a single `trace_id` per session via `PHIONYX_TRACE_ID` (with `~/.phionyx/active_trace` file fallback). One conversation = one trace = a joined view of the third-party tool calls and agent self-claim gate decisions recorded in that session.

`phionyx_session_report` (this package) surfaces the server-MCP envelope chain head + validity inline, so a reviewer can see both layers in one JSON.

## Install

```bash
# This package only:
pip install phionyx-pipeline-mcp

# With the outward-facing companion (recommended for full session evidence):
pip install "phionyx-pipeline-mcp[mcp-server-integration]"
```

## Register with Claude Code

Add to `.claude/mcp.json` in your project:

```json
{
  "mcpServers": {
    "phionyx-pipeline": {
      "command": "phionyx-pipeline-mcp"
    },
    "phionyx-mcp-server": {
      "command": "phionyx-mcp-server"
    }
  }
}
```

Both servers will share `~/.phionyx/active_trace` by default.

## Tool surface

| Tool | When to call |
|---|---|
| `phionyx_verify_claim` | **Before** claiming "fixed" or "done." Takes the claim, the evidence, the evidence type, paths tested, paths affected. Returns a directive (`pass / regenerate / reject`) plus the reasons. |
| `phionyx_causal_trace` | **While debugging.** Validates a causal chain from symptom to root cause. Chains shorter than 3 links or weaker than 40% code-specificity get a `deepen` directive. |
| `phionyx_response_gate` | **Before committing or deploying.** Action-type-specific thresholds: `claim_fixed` is strictest, `deploy` is very strict, `default` is standard. |
| `phionyx_verify_paths` | Cross-check claimed-affected and claimed-tested paths against `git diff`. Flags underreporting. |
| `phionyx_checkpoint` | Lightweight snapshot — call frequently to keep the session telemetry dense. |
| `phionyx_session_report` | End-of-session summary: claims, directives, drift metrics, evidence taxonomy, and (if the server MCP is installed) the audit chain head + validity. |

## Reviewer-runnable CLI (`phionyx`)

`pip install phionyx-pipeline-mcp` also installs a `phionyx` command that exposes the same three-stage verification as the MCP server, but reachable from a plain terminal — no Claude Code / MCP host required.

Four subcommands:

```bash
# 1. Verify a self-claim against the gate
phionyx verify-claim \
    --claim "scenario continuation bug is fixed" \
    --evidence "12 scenes played, quest_complete=True" \
    --type integration_test \
    --tested "src/foo/regression.py::regression_handler" \
    --affected "src/foo/regression.py"

# 2. Aggregate the audit chain over the last N days
phionyx audit --days 30
phionyx audit --days 7 --json   # machine-readable

# 3. Replay a specific session's timeline by trace_id (or unique prefix)
phionyx replay --trace <trace_id_or_session_id_prefix>

# 4. The killer demo — reviewer reproduces the failure mode in 5 seconds
phionyx demo broken-test-disabled
```

The demo is the entry point a reviewer should try first. It runs a scripted scenario in which Claude *claims* a fix passes and the gate detects that no tested-path coverage exists and the evidence weight is the bottom of the taxonomy — and rejects the claim. The exit code is `2` because the gate did its job.

Exit codes:

| Code | Meaning |
|---|---|
| `0` | `pass` / `proceed` — gate accepts the claim |
| `1` | `regenerate` / `rewrite` / `hedge` — claim must be revised |
| `2` | `reject` — gate rejects outright |
| `3` | error (invalid args, missing telemetry, internal failure) |

CLI and MCP-host invocations write to the same telemetry directory (`PHIONYX_PROJECT_ROOT/data/mcp_telemetry/`), so `phionyx audit` and `phionyx replay` see prior sessions started inside Claude Code or any other MCP-capable host.

## Evidence taxonomy

Not all evidence is equal. The gate weights confidence by the type of test that backs a claim:

| Evidence type | Weight |
|---|---|
| `browser_test` | 0.9 |
| `manual_repro` | 0.8 |
| `integration_test` | 0.7 |
| `endpoint_test` | 0.6 |
| `log_inspection` | 0.5 |
| `unit_test` | 0.4 |
| `code_review` | 0.3 |
| `none` | 0.0 |

A `claim_fixed` action with `evidence_type=none` will be rejected outright; even high confidence values cannot compensate for missing test evidence.

## Pre-commit gate helper

A standalone `phionyx-pipeline-check-gate` CLI reads the recent telemetry and exits non-zero if the most recent gate directive was `reject` or `regenerate`. Drop it into your pre-commit hook to enforce the discipline:

```bash
phionyx-pipeline-check-gate --mode pre-commit
```

Exit codes: `0` pass · `1` failed (recent reject/regenerate) · `2` no telemetry (warn-only).

## Shared-trace contract

When `phionyx-mcp-server` is also installed, this package extends `phionyx_session_report`'s output with:

```json
{
  "trace_id": "<active trace>",
  "mcp_envelope_chain": {
    "trace_id": "<same trace>",
    "count": 7,
    "head_hash": "sha256:...",
    "valid": true,
    "broken_at": null
  }
}
```

The integration is read-only — this package imports `FilesystemEnvelopeStore` + `verify_chain` from `phionyx-mcp-server` and reads its chain. No cross-package write coupling. When the server package isn't installed, the field reports `"phionyx-mcp-server not installed"` and the rest of the report continues to work.

## Tests

```bash
pip install -e ".[test]"
pytest tests/ -q
```

## License

AGPL-3.0-or-later. See [`LICENSE`](LICENSE).

## See also

- [phionyx.ai/bounded-authority](https://phionyx.ai/bounded-authority) — entry pillar this package surfaces under
- [phionyx.ai/evidence](https://phionyx.ai/evidence) — Evidence Matrix: every load-bearing claim paired with a reviewer-runnable command
- [`ai-runtime-evidence-protocol`](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol) — AIREP, the experimental vendor-neutral open format for per-decision AI decision receipts (signed, hash-chained, offline-checkable). Phionyx's Reasoned Governance Envelope is its developed alongside AIREP; a conformant projection between the two is **not implemented** (measured 2026-08-06: AIREP's own reference verifier rejects an RGE envelope handed to it directly). A proposed format, not a ratified standard.
- Project hub: [github.com/halvrenofviryel/phionyx-research](https://github.com/halvrenofviryel/phionyx-research)
- Engine (PyPI): [`phionyx-core`](https://pypi.org/project/phionyx-core/) — the deterministic runtime (current release on PyPI)
- Outward MCP layer: [`phionyx-mcp-server`](https://github.com/halvrenofviryel/phionyx-mcp-server) — trust boundary over third-party MCP tool calls
- Inspect AI bridge: [`phionyx-eval-inspect`](https://github.com/halvrenofviryel/phionyx-eval-inspect) — envelope chain → `.eval` log
- Framework adapters (alpha): [`phionyx-langchain-langgraph`](https://github.com/halvrenofviryel/phionyx-langchain-langgraph) · [`phionyx-openai-agents`](https://github.com/halvrenofviryel/phionyx-openai-agents)