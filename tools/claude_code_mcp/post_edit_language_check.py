#!/usr/bin/env python3
"""post_edit_language_check.py — PostToolUse hook for v0.7.2 P2.

After every Edit/Write/MultiEdit to a source file, run the cheapest
appropriate language check (type-check / lint / syntax) and print any
findings to stderr so the assistant sees them in the same turn.

Dispatch by file extension:

  *.py       → python3 -m py_compile + ruff check (if available)
  *.ts/*.tsx → tsc --noEmit (scoped to the Next.js app the file lives in)
  *.json     → python3 -m json.tool sanity
  *.md       → only check memory files via check_memory_schema.py
  *.yaml/.yml→ python3 -c "import yaml; yaml.safe_load(...)"

Design rules:

  * **Never block.** This hook is informational-only. It writes findings
    to stderr; Claude reads them in the next turn. Exit 0 always.
  * **Bounded time.** Per-file check ≤ 8 seconds. Hard cap.
  * **Bounded output.** ≤ 25 lines per check. Truncate with "...".
  * **Skip if tool missing.** If `tsc` / `ruff` / `npx` not available,
    silently skip — the hook degrades gracefully on machines without
    the toolchain.

Reads tool input from stdin as JSON (Claude Code hook protocol).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import which

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MAX_OUTPUT_LINES = 25
MAX_SECONDS = 8


def _trim(text: str, n: int = MAX_OUTPUT_LINES) -> str:
    lines = text.splitlines()
    if len(lines) <= n:
        return text
    return "\n".join(lines[:n]) + f"\n... ({len(lines) - n} more lines omitted)"


def _read_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _extract_file_path(payload: dict) -> Path | None:
    """The Claude Code hook payload carries `tool_input` which for Edit/
    Write/MultiEdit has `file_path` (absolute or project-relative)."""
    ti = payload.get("tool_input") or {}
    fp = ti.get("file_path") or ti.get("notebook_path")
    if not fp:
        return None
    p = Path(fp)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def _run(cmd: list[str], cwd: Path, timeout: int = MAX_SECONDS) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f"(timed out after {timeout}s)"
    except FileNotFoundError:
        return 127, "(tool not on PATH — skipping)"
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, _trim(out)


# ── per-language checkers ────────────────────────────────────────────


def _check_python(path: Path) -> str | None:
    # py_compile catches syntax errors fast.
    rc, out = _run([sys.executable, "-m", "py_compile", str(path)], cwd=PROJECT_ROOT, timeout=4)
    if rc != 0 and out.strip():
        return f"py_compile {path.relative_to(PROJECT_ROOT)}:\n{out}"

    # ruff (if available) for lint findings — informational only.
    if which("ruff"):
        rc, out = _run(
            ["ruff", "check", str(path), "--no-cache", "--quiet"],
            cwd=PROJECT_ROOT,
            timeout=MAX_SECONDS,
        )
        if rc != 0 and out.strip():
            return f"ruff {path.relative_to(PROJECT_ROOT)}:\n{out}"
    return None


def _find_nextjs_root(path: Path) -> Path | None:
    """Walk up from `path` looking for tsconfig.json + node_modules/typescript."""
    for parent in path.parents:
        if (parent / "tsconfig.json").exists() and (parent / "node_modules").exists():
            return parent
        if parent == PROJECT_ROOT:
            break
    return None


def _check_typescript(path: Path) -> str | None:
    root = _find_nextjs_root(path)
    if root is None:
        return None  # no tsconfig context — skip silently
    # Scope: full project type-check (Next.js apps are small enough).
    # Use `npx --no-install tsc` so missing typescript is treated as
    # "tool absent" not "command failed".
    rc, out = _run(["npx", "--no-install", "tsc", "--noEmit"], cwd=root, timeout=MAX_SECONDS)
    if rc == 0:
        return None
    # Only surface errors that mention the just-edited file path; full
    # `tsc` output across the project would drown the signal.
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else path.name
    matching = "\n".join(ln for ln in out.splitlines() if rel in ln)
    if not matching:
        # File itself is clean but project has errors elsewhere — say so
        # without dumping unrelated lines.
        first = next((ln for ln in out.splitlines() if ".ts" in ln or ".tsx" in ln), "")
        return f"tsc (project @ {root.relative_to(PROJECT_ROOT)}) reports errors elsewhere; first: {first[:160]}"
    return f"tsc {rel} (@ {root.relative_to(PROJECT_ROOT)}):\n{_trim(matching, 15)}"


def _check_json(path: Path) -> str | None:
    try:
        json.loads(path.read_text())
    except Exception as e:
        return f"json {path.relative_to(PROJECT_ROOT)}: {e}"
    return None


def _check_yaml(path: Path) -> str | None:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        yaml.safe_load(path.read_text())
    except Exception as e:
        return f"yaml {path.relative_to(PROJECT_ROOT)}: {e}"
    return None


def _check_memory_md(path: Path) -> str | None:
    """Memory files (~/.claude/projects/.../memory/*.md) get the F-MS1 schema check."""
    if "claude/projects" not in str(path) or "memory" not in str(path):
        return None
    # Reuse check_memory_schema.py
    script = PROJECT_ROOT / "tools/claude_code_mcp/check_memory_schema.py"
    if not script.exists():
        return None
    rc, out = _run([sys.executable, str(script), str(path.parent)], cwd=PROJECT_ROOT, timeout=MAX_SECONDS)
    # script exits 0 always (informational) but surfaces failures in stdout
    if "failed:        0" in out:
        return None
    # Show only the lines about THIS file
    lines = [ln for ln in out.splitlines() if path.name in ln or path.name[:30] in ln]
    if lines:
        return f"memory_schema {path.name}:\n" + "\n".join(lines[:6])
    return None


# ── dispatch ─────────────────────────────────────────────────────────


CHECKERS = [
    (lambda p: p.suffix == ".py", _check_python),
    (lambda p: p.suffix in {".ts", ".tsx"}, _check_typescript),
    (lambda p: p.suffix == ".json", _check_json),
    (lambda p: p.suffix in {".yaml", ".yml"}, _check_yaml),
    (lambda p: p.suffix == ".md", _check_memory_md),
]


def main() -> int:
    payload = _read_input()
    path = _extract_file_path(payload)
    if path is None or not path.exists():
        return 0  # no-op; nothing to check

    # Skip generated / vendored paths up front.
    s = str(path)
    if any(seg in s for seg in (".next/", "node_modules/", "__pycache__/", ".git/", "dist/", "build/")):
        return 0

    findings = None
    for pred, checker in CHECKERS:
        if pred(path):
            try:
                findings = checker(path)
            except Exception as e:
                findings = f"{checker.__name__} crashed: {e!r}"
            break

    if findings:
        # stderr so the next assistant turn picks it up as a hook signal.
        # Hard-cap output to keep token cost bounded.
        out = _trim(findings, MAX_OUTPUT_LINES)
        sys.stderr.write(
            f"[post_edit_language_check] {path.relative_to(PROJECT_ROOT)}\n{out}\n"
        )
    return 0  # NEVER block


if __name__ == "__main__":
    sys.exit(main())
