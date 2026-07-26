# Phionyx Claude Code substrate

The runtime-evidence harness that binds Claude Code's lifecycle events to the Phionyx
pipeline-MCP gate — and, from the M1 increments onward, a fail-closed control plane around the
agent itself.

The design position these scripts implement: **the availability of a control path is not
evidence that it delivered, and a control event that leaves no trace is indistinguishable from
one that never happened.** Several of the gates below exist because a control that was present,
correctly signed, and out-of-band still failed to reach the point that enforces it.

## What's here

| File | Purpose |
|---|---|
| `_telemetry.py` | Shared helpers for the hook scripts: stdin parsing, `block()` / `warn()` / `fail_open()`, attestation append, session lookup, strict-mode flag. |
| `check_bash_external_effect.py` | PreToolUse hook. Fail-closed T4 default-deny broker: irreversible external effects (publish · repo mutation · deploy · external network write · decode-and-run) are DENIED unless a signed override or the cooperative sentinel is present. Runs on **every** Bash command and classifies a shell-faithful normalised form, so quote-split obfuscation collapses before matching. Every use of the agent-writable sentinel is reported. |
| `check_self_modification.py` | PreToolUse hook. Fail-closed self-modification lockout: the controlled agent may not edit the control plane that governs it without out-of-band approval. |
| `check_signed_control_state.py` | PreToolUse hook. Fail-closed gate on **signed off-agent control state** — commit / push denied on missing, invalid, or stale state. |
| `control_state.py` | Ed25519 sign / verify for the off-agent control state the gate above reads. |
| `control_override.py` | Signed human override: Ed25519, scoped, time-boxed. The verify key is pinned on disk, not taken from the environment. |
| `sandbox_probe.py` | Ground-truth sandbox probe. Arms enforcement from filesystem reality (control plane read-only, private key masked), never from an agent-writable environment variable. |
| `session_end_attest.py` | SessionEnd hook. Records **how** a session ended. Anything not on the routine list — including an unrecognised reason — is recorded as notable, because the least-explained endings are the ones that must not be filed as unremarkable. |
| `check_memory_schema.py` | CLI gate + SessionStart hook for memory frontmatter. Informational by default; `PHIONYX_MEMORY_STRICT=1` blocks. |
| `memory_schema.py` | Pydantic `MemoryFrontmatter` model + parser + per-file / per-directory validator. |
| `post_edit_language_check.py` | PostToolUse hook. After every `Edit/Write/MultiEdit`, dispatches by file extension: `py_compile + ruff` / `tsc --noEmit` / `json.tool` / `yaml.safe_load` / memory schema. Findings to stderr. |
| `run_targeted_tests.py` | Stop hook. Reads `git diff` + `git diff --cached` + last commit, routes changed paths to pytest targets. Honours `stop_hook_active`. |
| `reasoning_memory_graph.py` | Typed Pydantic graph view over pipeline-MCP telemetry (`data/mcp_telemetry/session_*.json`). 5 node types · 6 edge types · 6 canonical queries. |
| `tests/` | Unit tests for the modules above, including negative tests that prove each gate still refuses. |

## Reproduce the unit-test suite

```bash
python3 -m pytest tools/claude_code_mcp/tests/ -q
# Expected: 71 passed
```

The suite is deliberately negative-heavy: for every escape path there is a test asserting the
gate still denies without it, and for every reporting path a test asserting that reporting cannot
change the verdict.

## Wire the hooks into a Claude Code project

Add the scripts to `.claude/settings.json` under the lifecycle event each one names in its module
docstring. The reference project wires **8 lifecycle events** (`SessionStart`, `SessionEnd`,
`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop`, `SubagentStop`) across
**23 hook scripts**, plus a `diff-reviewer` subagent for fresh-context review of uncommitted
diffs. This directory publishes the subset that is useful standalone.

Example — the SessionEnd wiring, which has no other documentation:

```json
{
  "hooks": {
    "SessionEnd": [
      { "hooks": [ { "type": "command",
                     "command": "python3 $CLAUDE_PROJECT_DIR/tools/claude_code_mcp/session_end_attest.py" } ] }
    ]
  }
}
```

## Honest limits

- **The cooperative sentinel is writable by the agent it constrains.** It is kept because the
  signed override has an unresolved cross-boundary delivery gap, and removing the only escape
  known to work would brick the session. Every use is reported instead of refused; that is a
  detection property, not a prohibition.
- **Sentinel freshness is derived from the file's own mtime**, which the controlled party can
  reset with a command no gate classifies. The age fields are hygiene against a forgotten
  sentinel, not a control against a deliberate one. Closing that needs an off-agent record of
  first use.
- **Denylist classification loses to in-process obfuscation.** A payload decoded inside an
  interpreter never surfaces a token a denylist can see. Full closure needs an allowlist broker.
- **Quote-stripping normalisation can false-positive** when a benign command quotes a denied
  token; the documented escape covers that case.
