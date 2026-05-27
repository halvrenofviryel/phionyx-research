#!/usr/bin/env python3
"""check_memory_schema.py — pre-commit + CLI gate for memory frontmatter.

v0.7.1 F-MS1.

Walks ``~/.claude/projects/<project>/memory/`` (or a directory supplied
on the CLI) and validates every ``*.md`` against ``MemoryFrontmatter``.

Behaviour matches the other Claude Code governance hooks
(check_mcp_gate.py et al.):

  * Default — informational. Prints errors + warnings, exits 0.
  * ``PHIONYX_MEMORY_STRICT=1`` — block. Exits non-zero if any file
    failed schema validation. Warnings still don't block.

Designed to be wired into ``.claude/settings.json`` as a PreToolUse
``Edit|Write`` hook for any file under the memory directory, or as a
plain pre-commit step that runs against the whole tree on every commit.
Either way the script is self-contained — invoke with no args to validate
the default memory directory; invoke with a path to validate that path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from anywhere — resolve the schema module relative to self.
SELF_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SELF_DIR))

from memory_schema import validate_directory, DirectoryReport  # noqa: E402


def _default_memory_dir() -> Path:
    home = Path.home()
    # Match the actual on-disk pattern: ~/.claude/projects/-mnt-data-claude-phionyx/memory/
    project_root_slug = "-mnt-data-claude-phionyx"
    return home / ".claude" / "projects" / project_root_slug / "memory"


def _render(report: DirectoryReport, strict: bool) -> int:
    print(f"Memory schema validation — {report.directory}")
    print(f"  files checked: {report.files_checked}")
    print(f"  ok:            {report.files_ok}")
    print(f"  failed:        {report.files_failed}")
    print(f"  strict mode:   {'ON (failures block)' if strict else 'OFF (informational)'}")
    print()

    # Errors first, warnings second
    any_errors = False
    for r in report.results:
        if r.errors:
            any_errors = True
            print(f"✗ {r.path}")
            for err in r.errors:
                # Some pydantic errors are multi-line; collapse to first 200 chars
                err_one = " ".join(err.splitlines())[:240]
                print(f"    error: {err_one}")
        if r.warnings:
            print(f"⚠ {r.path}")
            for w in r.warnings:
                print(f"    warning: {w}")

    if not any_errors:
        print("✓ no errors")

    if strict and any_errors:
        return 1
    return 0


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        target = Path(argv[1]).expanduser().resolve()
    else:
        target = _default_memory_dir()

    if not target.is_dir():
        print(
            f"check_memory_schema: directory does not exist: {target}",
            file=sys.stderr,
        )
        return 0  # do not block on missing directory in non-strict mode

    strict = os.environ.get("PHIONYX_MEMORY_STRICT") == "1"
    report = validate_directory(target)
    return _render(report, strict=strict)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
