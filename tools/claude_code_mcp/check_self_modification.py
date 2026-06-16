#!/usr/bin/env python3
"""PreToolUse hook — FAIL-CLOSED self-modification lockout (M1, criteria #4 + #7).

THE INVARIANT: a controlled agent must not edit the control plane that governs it.

This is the FIRST fail-closed gate in the system (every other hook fails OPEN). For
a *protected-path* edit, any ambiguity or error → DENY, because a control-plane
edit is exactly what an adversarial agent would attempt and exactly what must not
be allowed by accident. (For paths we cannot identify as protected we pass through —
fail-closing on an unparseable payload would brick all editing, which is its own
denial-of-service.)

PROTECTED control-plane paths (Edit/Write/MultiEdit/NotebookEdit DENIED unless
out-of-band approved):
  - .claude/                     (settings.json, rules/, skills/, CLAUDE.md)
  - tools/claude_code_mcp/       (the hooks + gate code themselves)
  - tools/phionyx_mcp_server/    (audit signer + chain verifier)
  - .git/hooks/                  (git-native pre-commit governance)
  - scripts/active/leak_scan.py  (publish-gate scanner)

OUT-OF-BAND APPROVAL (founder, NOT the agent): create the sentinel file
  ~/.phionyx/control_plane_edit_approved   (override path: PHIONYX_CONTROL_APPROVAL_FILE)
with a one-line reason. While it exists, control-plane edits are ALLOWED and logged
as approved mutations.

HONEST SCOPE (this is the Edit-tool half of M1 #4, not the whole thing):
  - Residual bypass [Phase 3]: direct Bash file writes (echo/sed/python) to a
    protected path are NOT gated here (only the Edit-family tools are). A capability
    sandbox / read-only mount closes that.
  - Residual bypass [M1 full]: the sentinel lives in the agent-writable filesystem,
    so the agent could create it. True control needs the sentinel/approval off-agent
    or signed. Until then this raises the cost and leaves evidence; it is not
    tamper-proof. (Same scope-honesty as the control review packet.)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _telemetry import append_attestation  # noqa: E402
except Exception:  # pragma: no cover
    append_attestation = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Protected control-plane locations, relative to the repo root.
PROTECTED_PREFIXES = (
    ".claude/",
    "tools/claude_code_mcp/",
    "tools/phionyx_mcp_server/",
    ".git/hooks/",
)
PROTECTED_FILES = (
    "scripts/active/leak_scan.py",
)

GATED_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

_DEFAULT_SENTINEL = "~/.phionyx/control_plane_edit_approved"


def _passthrough() -> NoReturn:
    sys.stdout.write("{}\n")
    sys.exit(0)


def _log(extra: dict) -> None:
    if append_attestation is None:
        return
    try:
        append_attestation(extra)
    except Exception:
        pass


def _is_protected(target: str) -> bool:
    """True if `target` resolves inside a protected control-plane location.

    Robust against absolute or relative paths and against `..` traversal: we
    resolve against the repo root and compare the repo-relative posix path.
    """
    if not target:
        return False
    p = Path(target)
    if not p.is_absolute():
        p = REPO_ROOT / p
    try:
        rel = p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        # Outside the repo entirely (e.g. /tmp, $HOME) — not a repo control-plane edit.
        return False
    if rel in PROTECTED_FILES:
        return True
    return any(rel == pre.rstrip("/") or rel.startswith(pre) for pre in PROTECTED_PREFIXES)


def _approved() -> tuple[bool, str]:
    """Out-of-band founder approval.

    M1 #6: a SIGNED human override (Ed25519, scope ``control_plane_edit``, verified
    with the PUBLIC key) is the STRONG, unforgeable path — checked first. The plain
    sentinel file below remains as a documented COOPERATIVE-DEV fallback (it is
    agent-writable, so it is not tamper-proof until off-agent key custody lands)."""
    # strong, signed (M1 #6)
    try:
        import control_override
        ok, claims = control_override.verify_override("control_plane_edit")
        if ok:
            return True, "signed-override: " + str((claims or {}).get("reason", ""))[:160]
    except Exception:
        pass
    # weak cooperative-dev fallback: presence of the plain sentinel file
    path = Path(os.environ.get("PHIONYX_CONTROL_APPROVAL_FILE", _DEFAULT_SENTINEL)).expanduser()
    try:
        if path.exists():
            reason = ""
            try:
                reason = path.read_text(encoding="utf-8").strip()[:200]
            except Exception:
                reason = "(unreadable sentinel)"
            return True, reason
    except Exception:
        return False, ""
    return False, ""


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        _passthrough()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _passthrough()  # cannot identify a protected edit → pass (do not brick all edits)

    if payload.get("tool_name") not in GATED_TOOLS:
        _passthrough()

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        _passthrough()
    target = str(tool_input.get("file_path") or tool_input.get("path") or "")

    if not _is_protected(target):
        _passthrough()

    # --- From here the edit IS a protected control-plane edit: FAIL-CLOSED. ---
    approved, reason = _approved()
    if approved:
        # M1 #6: a signed human override records a DISTINCT attestation kind from the
        # plain cooperative-dev sentinel, so the audit trail tells them apart.
        if reason.startswith("signed-override:"):
            _log({"tool": "signed_override_used", "kind": "signed_override_used",
                  "scope": "control_plane_edit", "gate": "check_self_modification",
                  "target": target[:200], "approval_reason": reason})
        else:
            _log({"tool": "control_plane_edit_approved", "kind": "control_plane_edit",
                  "target": target[:200], "approval_reason": reason})
        sys.stdout.write("{}\n")
        sys.exit(0)

    block_reason = (
        "BLOCKED by check_self_modification (M1 fail-closed self-modification lockout):\n"
        f"  '{target}' is part of the CONTROL PLANE that governs the agent.\n"
        "  A controlled agent must not edit the system that controls it.\n"
        "  Out-of-band approval (founder): create the sentinel\n"
        f"    {os.environ.get('PHIONYX_CONTROL_APPROVAL_FILE', _DEFAULT_SENTINEL)}\n"
        "  with a one-line reason, then retry. Remove it afterwards.\n"
        "  (Scope: this gates the Edit-family tools; Bash writes to these paths are a\n"
        "   known residual gap pending the Phase-3 capability sandbox.)"
    )
    _log({"tool": "block_event", "kind": "block_event", "verdict": "block",
          "hook": "check_self_modification", "target": target[:200],
          "reason": block_reason[:300]})
    sys.stdout.write(json.dumps({"decision": "block", "reason": block_reason}) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        # We only reach here on an unexpected error before the protected branch. If we
        # could not complete the protected-path determination, pass through rather than
        # brick all editing; the protected branch above denies on its own errors.
        sys.stderr.write(f"check_self_modification: unexpected error, passing through — {exc!r}\n")
        sys.stdout.write("{}\n")
        sys.exit(0)
