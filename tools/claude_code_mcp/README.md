# Phionyx Claude Code substrate

The runtime-evidence harness scripts that bind Claude Code's lifecycle events to the Phionyx pipeline-MCP gate. Subject of [`docs/arxiv/paper_03_runtime_evidence_case_study/`](../../docs/arxiv/paper_03_runtime_evidence_case_study/) (Paper 03 §4.4–§4.5).

## What's here

| File | Purpose | Version |
|---|---|---|
| `reasoning_memory_graph.py` | Typed Pydantic graph view over pipeline-MCP telemetry (`data/mcp_telemetry/session_*.json`). 5 node types · 6 edge types · 6 canonical queries. | v0.7.1 (F-RM1) |
| `memory_schema.py` | Pydantic `MemoryFrontmatter` model + parser + per-file / per-directory validator for the Claude Code auto-memory directory. | v0.7.1 (F-MS1) |
| `check_memory_schema.py` | CLI gate + `SessionStart` hook entry point. Informational by default; `PHIONYX_MEMORY_STRICT=1` blocks. | v0.7.1 (F-MS1) |
| `post_edit_language_check.py` | PostToolUse hook. After every `Edit/Write/MultiEdit`, dispatches by file extension: `py_compile + ruff` / `tsc --noEmit` / `json.tool` / `yaml.safe_load` / memory schema. Writes findings to stderr. | v0.7.2 (P2) |
| `run_targeted_tests.py` | `Stop` hook. Reads `git diff` + `git diff --cached` + last commit, routes changed paths to pytest target directories. Honors `stop_hook_active`. | v0.7.2 (P4) |
| `tests/` | Unit tests for the modules above (27 tests total across `test_reasoning_memory_graph.py` + `test_memory_schema.py`). | v0.7.1 |

## Reproduce the unit-test suite

```bash
python3 -m pytest tools/claude_code_mcp/tests/ -q
# Expected: 27 passed
```

## Wire the hooks into a Claude Code project

Add to `.claude/settings.json`. The full inventory (15 hooks + the `diff-reviewer` subagent) is described in [`docs/arxiv/paper_03_runtime_evidence_case_study/paper.md`](../../docs/arxiv/paper_03_runtime_evidence_case_study/paper.md) §4.4 Table 1.

Skill files at [`.claude/skills/`](../../.claude/skills/) and the subagent prompt at [`.claude/agents/diff-reviewer.md`](../../.claude/agents/diff-reviewer.md) document the on-demand layer above the hooks.
