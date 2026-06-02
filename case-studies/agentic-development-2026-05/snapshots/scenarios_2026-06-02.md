# Runtime-Evidence Test Scenarios — 2026-06-02

**When:** 2026-06-02T23:51:06
**Runner:** `scripts/active/runtime_evidence_test_scenarios.py`
**Result:** **13 / 13 scenarios passed**

## Summary

| # | Group | Scenario | Pass |
|---|-------|----------|:----:|
| A1 | Pipeline MCP | phionyx_response_gate produces a non-pass directive when confidence and evidence are low under claim_fixed. | ✓ |
| A2 | Pipeline MCP | phionyx_session_report returns the active trace_id and exposes the mcp_envelope_chain join field. | ✓ |
| B1 | Server MCP | verify_tool_descriptor detects post-approval descriptor drift (the rug-pull defence). | ✓ |
| B2 | Server MCP | verify_tool_descriptor passes when the descriptor matches the baseline hash (no false-positive on unchanged tools). | ✓ |
| C1 | Hook layer | check_mcp_gate (hook-mode) passes through non-commit Bash commands without gating them. | ✓ |
| C2 | Hook layer | check_mcp_gate (hook-mode) ignores non-Bash tool invocations. | ✓ |
| C3 | Hook layer | check_mcp_gate (hook-mode) matches the extended regex on merge/rebase/cherry-pick (commit M1, 0963610a). | ✓ |
| C4 | Hook layer | check_edit_gate blocks large edits (> 20 lines) in strict mode when the session has no recent gate call. | ✓ |
| C5 | Hook layer | SessionStart hook unlinks active_trace on source=startup. | ✓ |
| C6 | Hook layer | SessionStart hook preserves active_trace on source=resume (also clear and compact). | ✓ |
| C7 | Hook layer | auto_attest_commit writes a commit_attestation entry to the most-recent session telemetry on a synthetic git commit stdout payload. | ✓ |
| C8 | Hook layer | Stop hook check_claim_grounding blocks responses that reference a named artifact not opened this turn. | ✓ |
| D1 | Cross-layer | Pipeline MCP and server MCP resolve the same active trace_id from the canonical file (ADR-0006). | ✓ |

## Details

### A1 — PASS (Pipeline MCP)

*phionyx_response_gate produces a non-pass directive when confidence and evidence are low under claim_fixed.*

**Result:** directive='reject' (correctly non-pass)

**Evidence:**

```
{"input": "low conf + no evidence", "directive": "reject"}
```

### A2 — PASS (Pipeline MCP)

*phionyx_session_report returns the active trace_id and exposes the mcp_envelope_chain join field.*

**Result:** trace_id='trace-4dffb4eb270c49d3', chain.trace_id='trace-4dffb4eb270c49d3', matches active_trace file=True

**Evidence:**

```
{"trace_id": "trace-4dffb4eb270c49d3", "chain": {"trace_id": "trace-4dffb4eb270c49d3", "count": 20, "head_hash": "sha256:b7f7eb6813cc49b8467acc8be25ebf37f6d186193155715432fdaba889196d5e", "valid": true, "broken_at": null, "reason": null}, "file": "trace-4dffb4eb270c49d3"}
```

### B1 — PASS (Server MCP)

*verify_tool_descriptor detects post-approval descriptor drift (the rug-pull defence).*

**Result:** change_detected=True (drift correctly identified)

**Evidence:**

```
{"change_detected": true, "baseline_exists": true, "current_hash": "sha256:df2ca58fe3209d8f6061b828236fea9c80cbe7514bd815d7b30b7fae15eaf35e", "baseline_hash": "sha256:88a6414288e1dc242858517324e60fcbbd221638e8e7dd732d113d5d137ef4d4"}
```

### B2 — PASS (Server MCP)

*verify_tool_descriptor passes when the descriptor matches the baseline hash (no false-positive on unchanged tools).*

**Result:** change_detected=False (no false positive)

**Evidence:**

```
{"change_detected": false, "baseline_exists": true, "current_hash": "sha256:05b0d01bd29a7d42a16af6684f84a6bac4188073f64b3939e07293ea03e663f5", "baseline_hash": "sha256:05b0d01bd29a7d42a16af6684f84a6bac4188073f64b3939e07293ea03e663f5"}
```

### C1 — PASS (Hook layer)

*check_mcp_gate (hook-mode) passes through non-commit Bash commands without gating them.*

**Result:** stdout '{}' (pass-through)

**Evidence:**

```
stdout='{}\n', stderr=''
```

### C2 — PASS (Hook layer)

*check_mcp_gate (hook-mode) ignores non-Bash tool invocations.*

**Result:** stdout '{}' (non-Bash ignored)

**Evidence:**

```
stdout='{}\n'
```

### C3 — PASS (Hook layer)

*check_mcp_gate (hook-mode) matches the extended regex on merge/rebase/cherry-pick (commit M1, 0963610a).*

**Result:** gate fired (pass or block) for all 4 extended-regex commands

**Evidence:**

```
{"git merge feature": true, "git rebase main": true, "git cherry-pick abc123": true, "make release-commit": true}
```

### C4 — PASS (Hook layer)

*check_edit_gate blocks large edits (> 20 lines) in strict mode when the session has no recent gate call.*

**Result:** hook emitted hard {decision:block} JSON

**Evidence:**

```
reason='BLOCKED by check_edit_gate (no gate calls yet this session):\nNo phionyx_response_gate / phionyx_verify_claim call in this MCP session yet.\nTool: Edit  target: /tmp/x.md  estimated lines: 40\nCLAUDE.md '
```

### C5 — PASS (Hook layer)

*SessionStart hook unlinks active_trace on source=startup.*

**Result:** trace file unlinked on startup

**Evidence:**

```
path=/tmp/claude-1000/tmpe98a9mr3/active_trace
```

### C6 — PASS (Hook layer)

*SessionStart hook preserves active_trace on source=resume (also clear and compact).*

**Result:** trace preserved for resume/clear/compact

### C7 — PASS (Hook layer)

*auto_attest_commit writes a commit_attestation entry to the most-recent session telemetry on a synthetic git commit stdout payload.*

**Result:** commit_attestation entry added (count 23→24)

**Evidence:**

```
stdout='{}\n'
```

### C8 — PASS (Hook layer)

*Stop hook check_claim_grounding blocks responses that reference a named artifact not opened this turn.*

**Result:** hook emitted hard {decision:block} JSON for unread-artifact reference

**Evidence:**

```
reason="BLOCKED by Phionyx Stop hook (check_claim_grounding):\n  Draft asserts/asks about source(s) not opened this turn: ['foo.md']\n    - foo.md: Far outside knowledge boundary (score=0.16): high OOD (0.90); "
```

### D1 — PASS (Cross-layer)

*Pipeline MCP and server MCP resolve the same active trace_id from the canonical file (ADR-0006).*

**Result:** both resolved to 'trace-4dffb4eb270c49d3'

**Evidence:**

```
{"pipeline": "trace-4dffb4eb270c49d3", "server": "trace-4dffb4eb270c49d3"}
```

## Reproduction

```bash
python3 scripts/active/runtime_evidence_test_scenarios.py
```

_Generated 2026-06-02T23:51:06 by_
_`scripts/active/runtime_evidence_test_scenarios.py`._
