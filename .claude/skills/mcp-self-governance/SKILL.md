---
name: mcp-self-governance
description: Phionyx two-layer MCP architecture rules (pipeline + server). Loaded on demand when the assistant is about to call phionyx_response_gate, phionyx_verify_claim, phionyx_causal_trace, phionyx_verify_paths, phionyx_checkpoint, phionyx_session_report, or any mcp__phionyx-* tool. Codifies ADR-0006 (two-layer MCP, shared trace_id) and the per-action invocation discipline.
---

# MCP Self-Governance (two-layer, ADR-0006)

Two MCP servers run side-by-side against this repo. They share a single
`trace_id` per Claude Code session (`PHIONYX_TRACE_ID` env var with
`~/.phionyx/active_trace` fallback). They serve different concerns:

| Server | Concern | Tool surface |
|---|---|---|
| `phionyx-pipeline` | Self-governance over Claude's own claims | `phionyx_verify_claim`, `phionyx_causal_trace`, `phionyx_response_gate`, `phionyx_verify_paths`, `phionyx_checkpoint`, `phionyx_session_report` |
| `phionyx-mcp-server` | MCP trust boundary — descriptor hash, signed RGE v0.2 envelope, audit chain over third-party MCP tool calls | `verify_tool_descriptor`, `record_tool_call`, `verify_chain_integrity`, `query_audit_history` (+ 3 stubs) |

`phionyx_session_report` surfaces `mcp_envelope_chain` (count, head_hash,
valid) for the active trace, joining the two MCPs in one view.
Full design: [`docs/adr/0006-mcp-integration.md`](../../../docs/adr/0006-mcp-integration.md).

## When using the pipeline MCP, Claude MUST:

0. **Before asking the user any question that names an artifact** (a draft file,
   a URL, a specific paper / book / post / issue / repo, any `*.md` or `*.tsx`
   file, a path under `app/` or `content/`, etc.): **READ the artifact first**.
   If for any reason the question must be asked without reading, call
   `phionyx_response_gate(action_type="ask_question", artifact_references="<csv>",
   artifact_paths_read="<csv>", confidence=..., evidence_count=...)`. The gate
   returns `directive="regenerate"` when any reference is missing from the read
   set — re-draft instead of submitting. A `Stop` hook
   (`tools/claude_code_mcp/check_question_grounding.py`) enforces this at
   submission time. Rule codified in
   `.claude/memory/feedback_read_artifact_before_asking.md`.

1. **Before claiming "fixed" or "done":** Call `phionyx_verify_claim` with the claim,
   evidence, evidence_type (from taxonomy: browser_test, manual_repro, integration_test,
   endpoint_test, log_inspection, unit_test, code_review, none), tested code paths,
   and ALL affected code paths. If directive is `reject` or `regenerate`, do NOT
   claim completion — fix the gaps first.

2. **When debugging:** Call `phionyx_causal_trace` with the symptom and your
   proposed causal chain. If directive is `incomplete`, deepen the chain before
   attempting a fix. A chain with <3 links or <40% code specificity is not ready.

3. **Before deploying or committing a fix:** Call `phionyx_response_gate` with
   action_type (claim_fixed | deploy | default), confidence, evidence_count,
   evidence_type, and affects_user_facing. Follow the directive.

4. **To verify path declarations:** Call `phionyx_verify_paths` with claimed_affected
   and claimed_tested. This cross-checks your declarations against `git diff`.

5. **Frequently — after completing a subtask or switching context:** Call
   `phionyx_checkpoint` with a brief context note. This is lightweight (no git diff)
   and keeps the telemetry timeline dense for founder monitoring.

## When using the server MCP, Claude MUST:

6. **Before a third-party MCP tool call:** Call `verify_tool_descriptor` with the
   descriptor + the user-approved baseline hash. If `change_detected` is true,
   stop and surface re-approval to the user — do NOT proceed.

7. **After a tool call:** Call `record_tool_call` with the I/O hashes, the
   descriptor hash, and the gate directive (e.g. `runtime_policy_basis=
   ["phionyx_response_gate.pass"]` to cross-reference the pipeline gate
   decision). `trace_id` defaults to the active trace — omit unless overriding.

8. **Periodically, and before reporting session completion:** Call
   `verify_chain_integrity` (or check `phionyx_session_report`'s
   `mcp_envelope_chain.valid`). Surface tamper/broken chains as a blocker.

**Rule:** Testing a different code path than the user executes is NOT evidence.
If the user hits endpoint A→B→C, test A→B→C, not A→D→E.

**Note:** CLAUDE.md rules are advisory. The gate is deterministic but Claude's
input generation is stochastic. The input verification layer (git diff) narrows
this gap. For binding enforcement, see the `binding-enforcement` skill.
