#!/usr/bin/env python3
"""Ground-truth sandbox probe for M1 #5 (default-on, env-independent enforcement).

`sandbox_intact()` answers "is THIS process actually running inside the off-agent
bubblewrap sandbox?" using FILESYSTEM GROUND TRUTH, never an agent-writable env var.

Two facts hold ONLY inside `tools/offagent/run-agent.sh`:
  1. the control plane is a kernel read-only bind mount  -> writes raise EROFS
  2. the private signing key dir is masked by a tmpfs    -> the key file is absent

Inside the sandbox an agent CANNOT forge these (it cannot remount the ro-bind rw,
nor reveal the masked key). OUTSIDE the sandbox an agent COULD fake them — which is
exactly why the critical-action gate FAILS CLOSED when this returns not-intact: a
session that is not provably sandboxed is not trusted to commit/push.

Reads NO environment variable on purpose — `PHIONYX_OFFAGENT` / `PHIONYX_SIGNED_GATE`
are agent-writable, and relying on them is the M1 #5 hole this closes. The
control-plane-read-only probe is the load-bearing signal (the ro-bind is the sandbox's
defining feature); the key-mask probe is defence in depth.

Final home: tools/claude_code_mcp/sandbox_probe.py  (must be edited UNSANDBOXED — EROFS otherwise).
"""
from __future__ import annotations

import errno
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Representative protected control-plane dirs. If these are read-only we are inside
# the sandbox ro-bind; if writable we are not. (The hooks' own home is the cleanest
# probe; kept consistent with check_self_modification.PROTECTED_PREFIXES.)
_CONTROL_PROBE_DIRS = (
    REPO_ROOT / "tools" / "claude_code_mcp",
    REPO_ROOT / ".claude",
)

# The REAL private-key path — HARDCODED, not PHIONYX_KEY_DIR (which is agent-writable).
_PRIVATE_KEY = Path("~/.phionyx/keys/control_ed25519").expanduser()


def _control_plane_read_only() -> tuple[bool, str]:
    """True iff writing to EVERY probed control-plane dir is rejected with the sandbox
    read-only signal (EROFS / EACCES / EPERM). A successful write -> NOT sandboxed. A
    DIFFERENT error (dir missing, not-a-dir, …) is inconclusive: we cannot prove the
    plane is read-only, so we fail closed (report not-read-only) rather than mistake an
    absent dir for an intact sandbox."""
    for d in _CONTROL_PROBE_DIRS:
        probe = d / f".sandbox_probe.{os.getpid()}"
        try:
            with open(probe, "w") as fh:
                fh.write("x")
        except OSError as exc:
            if exc.errno in (errno.EROFS, errno.EACCES, errno.EPERM):
                continue  # write rejected by the ro-bind / perms -> this dir is read-only: good
            # some other failure (e.g. ENOENT) -> can't conclude read-only -> not intact
            return False, f"control plane probe inconclusive on {d}: {exc!r}"
        # write succeeded -> NOT read-only. Clean up; report litter if cleanup fails.
        try:
            probe.unlink()
        except OSError as exc:
            return False, f"control plane writable: {d} (probe litter left: {exc!r})"
        return False, f"control plane writable: {d}"
    return True, ""


def _key_masked() -> tuple[bool, str]:
    """True iff the private signing key is NOT readable (tmpfs-masked in the sandbox)."""
    try:
        with open(_PRIVATE_KEY, "rb") as fh:
            fh.read(1)
    except OSError:
        return True, ""  # absent / unreadable -> masked: good
    return False, f"private key readable: {_PRIVATE_KEY}"


def sandbox_intact() -> tuple[bool, list[str]]:
    """(intact, reasons). intact only if control plane read-only AND key masked."""
    reasons: list[str] = []
    ro, r1 = _control_plane_read_only()
    if not ro:
        reasons.append(r1)
    masked, r2 = _key_masked()
    if not masked:
        reasons.append(r2)
    return (not reasons), reasons


if __name__ == "__main__":
    ok, why = sandbox_intact()
    print(f"sandbox_intact = {ok}")
    for w in why:
        print(f"  - {w}")
    raise SystemExit(0 if ok else 1)
