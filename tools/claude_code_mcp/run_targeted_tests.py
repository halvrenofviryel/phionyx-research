#!/usr/bin/env python3
"""run_targeted_tests.py — Stop hook for v0.7.2 P4.

When the assistant signals "done", look at the recently-changed code paths
and run the targeted tests for those paths. The assistant sees test
failures (or unconfigured paths) in the same turn and can continue
fixing without manual intervention.

Honors the Claude Code hook protocol:

  * stdin: JSON payload with `stop_hook_active` (true if this hook already
    fired and Claude is continuing because of it — exit immediately to
    avoid infinite loops, per Anthropic guidance).
  * stderr: any test-failure output the assistant should read.
  * exit code: always 0 (informational; never blocks).

Discovery rules:

  * Read git diff (staged + unstaged + last commit) for changed files.
  * Map each file to a test directory using the routing table below.
  * Run only the matching test sets, deduplicated. Cap at 4 runs.
  * Bounded time: 60s total (raise PHIONYX_STOP_TEST_TIMEOUT to override).

If no recognised code-path changed, the hook is a silent no-op.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TIMEOUT = int(os.environ.get("PHIONYX_STOP_TEST_TIMEOUT", "60"))
MAX_RUNS = 4
MAX_OUTPUT_LINES = 30

# Routing: (path-prefix substring → pytest target). First match wins.
# Designed to be tight (only the directly relevant test dir) so the run
# stays under the global timeout even when several modules change.
ROUTES: list[tuple[str, list[str]]] = [
    # v0.7.1 substrate
    ("tools/claude_code_mcp/reasoning_memory_graph.py",
     ["tools/claude_code_mcp/tests/test_reasoning_memory_graph.py"]),
    ("tools/claude_code_mcp/memory_schema.py",
     ["tools/claude_code_mcp/tests/test_memory_schema.py"]),
    ("tools/claude_code_mcp/check_memory_schema.py",
     ["tools/claude_code_mcp/tests/test_memory_schema.py"]),
    # Compliance + Letta companion packages
    ("tools/phionyx_compliance/",
     ["tools/phionyx_compliance/tests/"]),
    ("tools/phionyx_letta/",
     ["tools/phionyx_letta/tests/"]),
    # Core / contract / RE (when in repo)
    ("phionyx_core/governance/",
     ["tests/unit/core/", "-k", "governance or kill_switch or ethics"]),
    ("phionyx_core/contracts/",
     ["tests/contract/"]),
    ("phionyx_core/research_engine/",
     ["tests/research_engine/"]),
    ("phionyx_core/pipeline/",
     ["tests/contract/", "tests/unit/core/", "-k", "pipeline"]),
    # Bridge
    ("phionyx_bridge/",
     ["tests/unit/bridge/"]),
]


def _read_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _changed_files() -> list[str]:
    """All files changed since the last clean state — staged + unstaged + last commit."""
    files: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only"],            # unstaged
        ["git", "diff", "--cached", "--name-only"],  # staged
        ["git", "show", "--name-only", "--format=", "HEAD"],  # last commit
    ):
        try:
            out = subprocess.check_output(cmd, cwd=PROJECT_ROOT, text=True, timeout=5)
            for ln in out.splitlines():
                ln = ln.strip()
                if ln:
                    files.add(ln)
        except Exception:
            continue
    return sorted(files)


def _route_for(file_path: str) -> list[str] | None:
    for prefix, target in ROUTES:
        if file_path.startswith(prefix) or prefix in file_path:
            return target
    return None


def _run_pytest(args: list[str], timeout: int) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=line"] + args
    try:
        proc = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f"(timed out after {timeout}s)"
    except FileNotFoundError:
        return 127, "(pytest not on PATH — skipping)"
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main() -> int:
    payload = _read_input()
    if payload.get("stop_hook_active"):
        # Already firing in a re-entry — exit immediately per
        # Anthropic guidance to prevent infinite Stop loop.
        return 0

    changed = _changed_files()
    if not changed:
        return 0

    targets: dict[str, list[str]] = {}
    for f in changed:
        target = _route_for(f)
        if target is None:
            continue
        key = " ".join(target)
        if key not in targets:
            targets[key] = target
        if len(targets) >= MAX_RUNS:
            break

    if not targets:
        return 0  # nothing recognisable changed

    per_target_timeout = max(15, DEFAULT_TIMEOUT // max(1, len(targets)))

    any_failure = False
    summary_lines: list[str] = []
    for key, target in targets.items():
        rc, out = _run_pytest(target, timeout=per_target_timeout)
        if rc == 5:
            # Pytest exit code 5 = "no tests collected" — silently skip.
            continue
        head = out.strip().splitlines()
        # Compact: keep first error line + final passed/failed summary
        compact = "\n".join(head[:MAX_OUTPUT_LINES])
        status = "PASS" if rc == 0 else f"FAIL (rc={rc})"
        if rc != 0:
            any_failure = True
        summary_lines.append(f"### pytest {' '.join(target)}  →  {status}")
        # Only show output on failure
        if rc != 0:
            summary_lines.append(compact)

    if not summary_lines:
        return 0

    # Always emit to stderr so the assistant turn picks it up.
    header = "[run_targeted_tests]  changed files routed to "
    header += f"{len(targets)} test target(s); failure={any_failure}\n"
    sys.stderr.write(header + "\n".join(summary_lines) + "\n")
    return 0  # NEVER block


if __name__ == "__main__":
    sys.exit(main())
