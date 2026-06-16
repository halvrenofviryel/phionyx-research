#!/usr/bin/env python3
"""PreToolUse hook — FAIL-CLOSED gate on SIGNED off-agent control state (M1 #1-3).

This is the core of M1: a real-time gate whose verdict comes from a SIGNED state
the agent cannot forge (verified with the Ed25519 PUBLIC key), NOT from the
agent-writable telemetry file. For a critical action (commit / push) it FAILS
CLOSED: missing / invalid / stale signature → DENY.

ROLLOUT FLAG: enabled only when PHIONYX_SIGNED_GATE in {1,true,yes}. Default OFF
during rollout so landing + testing the mechanism cannot brick a live session.
Flipping it default-ON is the final step of M1 — to be done ONLY AFTER the private
key is moved off-agent (separate user / host), because until then the signed state
is forgeable by the agent and the gate would be theatre. (control_state.py +
provision_offagent_control.sh.)

Scope: gates commit-producing Bash (the critical action). Edits stay under
check_edit_gate; broadening to edits is a later step.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).resolve().parent))

_COMMIT_RE = re.compile(r"git commit|git push|git merge|git rebase|git cherry-pick|make [a-z-]*commit")


def _allow() -> NoReturn:
    sys.stdout.write("{}\n")
    sys.exit(0)


def _block(reason: str) -> NoReturn:
    try:
        from _telemetry import append_attestation
        append_attestation({"tool": "block_event", "kind": "block_event", "verdict": "block",
                            "hook": "check_signed_control_state", "reason": reason[:300]})
    except Exception:
        pass
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}) + "\n")
    sys.exit(0)


def _enabled() -> bool:
    return os.environ.get("PHIONYX_SIGNED_GATE", "").lower() in {"1", "true", "yes"}


def _dev_unsandboxed_ok() -> tuple[bool, str]:
    """Off-agent escape: presence of the dev sentinel allows an unsandboxed commit.

    The path is HARDCODED — M1 #5 requires enforcement NOT be controlled by an
    agent-writable env. (An env override would let an agent point the sentinel at any
    pre-existing readable file, e.g. /etc/hostname, and bypass with no write at all.)
    Honest residual: the sentinel still lives in the agent-writable filesystem, so the
    agent could CREATE it — that raises cost + leaves evidence; it is NOT tamper-proof.
    Full closure needs off-agent custody (Phase 3). The escape PERSISTS until manually
    removed (it is not consumed on use, so a commit+push pair both pass)."""
    path = Path("~/.phionyx/unsandboxed_dev_ok").expanduser()
    try:
        if path.exists():
            # errors="replace": a non-UTF-8 sentinel must not raise (would otherwise
            # bubble to the fail-closed handler — handled, but cleaner to absorb here).
            return True, path.read_text(encoding="utf-8", errors="replace").strip()[:200]
    except Exception:
        return False, ""  # any error reading the escape -> treat as absent (deny)
    return False, ""


def _sandbox_intact() -> tuple[bool, list[str]]:
    """Ground-truth sandbox check; fail-closed (not intact) on any probe error."""
    try:
        import sandbox_probe
        return sandbox_probe.sandbox_intact()
    except Exception as exc:  # missing/broken probe on a critical action -> not trusted
        return False, [f"sandbox probe error: {exc!r}"]


def _signed_override(scope: str) -> tuple[bool, dict | None]:
    """M1 #6 — a valid Ed25519-signed human override for `scope`, verified with the
    PUBLIC key (unforgeable by an agent). Fail-closed (not approved) on any error.
    This is the STRONG override path; the plain dev sentinel stays as a documented
    cooperative-dev fallback (agent-writable — honest residual until off-agent custody)."""
    try:
        import control_override
        return control_override.verify_override(scope)
    except Exception:
        return False, None


def _attest(kind: str, extra: dict) -> None:
    try:
        from _telemetry import append_attestation
        append_attestation({"tool": kind, "kind": kind, **extra})
    except Exception:
        pass


def _verify_signed_state_or_block() -> NoReturn:
    """Existing M1 #1-3 enforcement: require a valid, fresh, Ed25519-signed state."""
    try:
        import control_state
        state = control_state.read_verified_state()
    except Exception as exc:
        _block(
            "BLOCKED by check_signed_control_state (M1 fail-closed): could not read/verify "
            f"the signed control state ({exc!r}). A critical action requires a valid, fresh, "
            "Ed25519-signed control state. Ensure the off-agent signer is running."
        )
    if state is None:
        _block(
            "BLOCKED by check_signed_control_state (M1 fail-closed):\n"
            "  No valid + fresh Ed25519-signed control state present.\n"
            "  A commit/push requires signed off-agent state (missing/invalid/stale = deny).\n"
            "  Call phionyx_response_gate first (the signer refreshes the signed state), or\n"
            "  ensure the off-agent signer process is running."
        )
    directive = str(state.get("last_directive", "unknown"))
    if directive in ("reject", "regenerate"):
        _block(
            "BLOCKED by check_signed_control_state — signed state shows last directive "
            f"'{directive.upper()}'. Resolve the gate before committing."
        )
    _allow()


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        _allow()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _allow()
    if not isinstance(payload, dict):
        _allow()  # non-dict payload cannot be identified as a critical action
    if payload.get("tool_name") != "Bash":
        _allow()
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        _allow()
    cmd = tool_input.get("command", "") or ""
    if not _COMMIT_RE.search(cmd):
        _allow()  # not a critical (commit-producing) action

    # === From here we KNOW this is a critical action: FAIL CLOSED on ANY error. ===
    # _allow()/_block()/_verify_signed_state_or_block() exit via SystemExit (must
    # propagate); any OTHER exception here must DENY, not silently allow.
    try:
        # ARM ON GROUND TRUTH, not an agent-writable env (M1 #5).
        intact, reasons = _sandbox_intact()
        if intact:
            _verify_signed_state_or_block()  # sandboxed: enforce signed off-agent state

        # Not provably sandboxed -> the signed gate cannot be trusted. Default-on: DENY,
        # unless an override is present. M1 #6: a SIGNED human override (unforgeable,
        # scoped, expiring) is the STRONG path, checked first and recorded.
        sig_ok, claims = _signed_override("unsandboxed_commit")
        if sig_ok:
            _attest("signed_override_used", {
                "scope": "unsandboxed_commit", "gate": "check_signed_control_state",
                "approval_reason": (claims or {}).get("reason", ""), "reasons": reasons})
            _allow()

        # Weak cooperative-dev fallback: the plain (agent-writable) escape sentinel.
        approved, why = _dev_unsandboxed_ok()
        if approved:
            _attest("unsandboxed_dev_approved", {"reasons": reasons, "approval_reason": why})
            if _enabled():
                _verify_signed_state_or_block()  # legacy env opt-in still enforces if set
            _allow()

        _block(
            "BLOCKED by check_signed_control_state (M1 #5 default-on): this session is NOT "
            "provably sandboxed, so the signed control gate cannot be trusted for a commit/push.\n"
            f"  reasons: {'; '.join(reasons) or 'no read-only control plane found'}\n"
            "  Relaunch sandboxed:  tools/offagent/run-agent.sh\n"
            "  Signed human override (M1 #6, off-agent): python3 "
            "tools/claude_code_mcp/control_override.py --sign --scope unsandboxed_commit --reason '...' --ttl 3600\n"
            "  Or (dev, cooperative): create ~/.phionyx/unsandboxed_dev_ok with a one-line reason."
        )
    except SystemExit:
        raise
    except Exception as exc:
        _block(
            "BLOCKED by check_signed_control_state (M1 #5 fail-closed): unexpected error while "
            f"evaluating a commit/push ({exc!r}). A critical action denies on error."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        # Backstop: any unexpected error reaching here FAILS CLOSED, unconditionally.
        # Do NOT key this on PHIONYX_SIGNED_GATE — under M1 #5 that env is unset on the
        # default path, so keying fail-closed on it reintroduces an agent-flippable
        # allow (the exact hole #5 closes). The critical section in main() already
        # denies on error; this is defence in depth. Benign non-critical commands are
        # _allow()'d (SystemExit) before any error-prone code, so this rarely fires.
        sys.stdout.write(json.dumps({"decision": "block",
            "reason": f"check_signed_control_state fail-closed on unexpected error: {exc!r}"}) + "\n")
        sys.exit(0)
