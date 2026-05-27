---
name: binding-enforcement
description: Claude Code hook configuration that binds Phionyx self-governance to lifecycle events. Loaded when the assistant is editing .claude/settings.json, writing a new hook script under tools/claude_code_mcp/, or asked about hook coverage / strict mode / why a hook fired.
---

# Binding enforcement layer (Claude Code hooks)

The hooks below are wired into `.claude/settings.json` (committed) to close
the *stochastic input generation* gap originally measured at **7.5%
coverage** (`docs/strategic/runtime_evidence_self_audit_2026-05-25.md`).
Coverage was expanded 2026-05-26 to all major Claude Code lifecycle events
so runtime-evidence aspires to 100% activity visibility. v0.7.2 adds
PostToolUse language-tool feedback + Stop test runner + a fresh-context
diff-reviewer subagent.

**Blocking hooks (gate-style — strict mode escalates WARN → BLOCK):**

1. **`PreToolUse` on `Bash` — commit/push** — when command contains
   `git commit` or `git push`, invokes `check_mcp_gate.py --mode pre-tool`.
   `PHIONYX_MCP_GATE_STRICT=1` → BLOCK without recent (≤ 5 min) gate call.

2. **`PreToolUse` on `Bash` — external-effect** — matches
   `gh pr|release|issue` mutations, `npm/twine/pip/cargo publish`,
   destructive git (`push --force`, `reset --hard`, `branch -D`,
   `tag -d`), and deploy patterns (`make deploy/publish`, `docker push`,
   `kubectl apply`, `terraform apply`). Invokes
   `check_bash_external_effect.py`. Stricter recency: 5 min (tunable via
   `PHIONYX_MCP_EXTERNAL_GATE_MAX_AGE_SEC`).

3. **`PreToolUse` on `Edit|Write|MultiEdit|NotebookEdit`** — invokes
   `check_edit_gate.py`. Edits ≤ 20 lines exempt; larger edits require a
   gate call within last 30 min (tunable via `PHIONYX_MCP_EDIT_GATE_SIZE`
   and `PHIONYX_MCP_EDIT_GATE_MAX_AGE_SEC`).

4. **`PreToolUse` on `Agent`** — invokes
   `check_agent_spawn.py`. Subagents propagate claims upward, so a gate
   call must precede the spawn (≤ 30 min, tunable via
   `PHIONYX_MCP_AGENT_GATE_MAX_AGE_SEC`). Always writes a
   `subagent_spawn` attestation (subagent_type + prompt hash).

5. **`Stop` hook — question grounding** — invokes `check_question_grounding.py`
   before any assistant response is finalised. BLOCKs questions referencing
   named artifacts not opened this turn (always-on, no env-var disable).

**Observability hooks (always pass; never block; write `auto_attest`
entries so activity shows in `/runtime-evidence` `all_calls` without
inflating `gate_calls`):**

6. **`SessionStart`** — `session_start_attest.py` writes a `session_start`
   entry with source (startup|resume|clear|compact) and the previous
   session's `PHIONYX_TRACE_ID`. On `source=startup` it also resets
   `~/.phionyx/active_trace` so the new conversation generates a fresh
   trace_id (closes ADR-0006 open follow-up).

7. **`SessionStart` — memory schema (v0.7.1 F-MS1)** —
   `check_memory_schema.py` validates every memory frontmatter against
   the `MemoryFrontmatter` Pydantic model on session boot. Informational
   by default; `PHIONYX_MEMORY_STRICT=1` blocks malformed files.

8. **`UserPromptSubmit`** — `log_user_prompt.py` writes a `user_prompt`
   entry with SHA256 hash (not raw text) + length + word count. Each
   gate call can be traced back to the prompt that motivated it.

9. **`PreCompact`** — `pre_compact_checkpoint.py` writes a
   `pre_compact_checkpoint` entry with gate-call age and last directive
   before context compression destroys conversational evidence.

10. **`SubagentStop`** — `attest_subagent_stop.py` writes a
    `subagent_complete` entry. Main session is still responsible for
    `verify_claim` on the subagent's output before acting on it.

11. **`PreToolUse` on `mcp__.*`** — `check_mcp_tool_call.py` writes
    an `mcp_tool_invocation` entry for every third-party MCP call
    (skips `mcp__phionyx-pipeline__*` and `mcp__phionyx-mcp-server__*`).

12. **`PostToolUse` on `Bash` — git commit** — `auto_attest_commit.py`
    writes a `commit_attestation` entry on successful commit, with SHA.

13. **`PostToolUse` on `WebFetch|WebSearch`** —
    `log_external_ingress.py` writes an `external_ingress` entry with
    URL or query + response size.

14. **`PostToolUse` on `Edit|Write|MultiEdit|NotebookEdit` (v0.7.2 P2)** —
    `post_edit_language_check.py` runs the appropriate language tool
    (py_compile + ruff for .py, tsc --noEmit for .ts/.tsx, json.tool for
    .json, yaml.safe_load for .yml, check_memory_schema.py for memory
    .md files). Findings written to stderr so the next assistant turn
    sees them. Bounded: ≤ 8 s per file, ≤ 25 output lines.

15. **`Stop` — targeted tests (v0.7.2 P4)** — `run_targeted_tests.py`
    inspects git diff for changed code paths, routes each to its test
    directory (via internal ROUTES table), runs pytest with a per-target
    timeout. Honors `stop_hook_active=true` to avoid infinite loops.
    Writes pass/fail summary to stderr.

## Subagent layer (v0.7.2 P1)

Separate from the hook layer:

* **`.claude/agents/diff-reviewer.md`** — adversarial review of an
  uncommitted (or just-committed) diff. Fresh context (no bias from
  the implementing session's reasoning). Read-only tools (Read / Grep /
  Glob / Bash). Looks for schema/interface drift, exit-code anti-patterns,
  bucketing bugs, version drift, missing tests, public-state-claim
  drift, AGI/governance labelling. Invoke with: *"Use the diff-reviewer
  subagent to check this commit."*

**Design rule:** `auto_attest` entries are recorded as activity but
explicitly **excluded from gate-coverage math** in the
`/runtime-evidence` dashboard. Inflating the metric would defeat the
audit. The hooks make visibility binding without making the score
meaningless.

Enable strict mode in your shell:
```bash
export PHIONYX_MCP_GATE_STRICT=1
```

Re-run the self-audit to measure improvement:
```bash
python3 scripts/active/runtime_evidence_self_audit.py --days 30
```
