#!/usr/bin/env python3
"""SessionEnd hook — record HOW a Claude Code session ended.

Companion to ``session_start_attest.py``. Without it, a session that the founder
force-quit because the agent would not stop is indistinguishable, in every
Phionyx-side record, from a clean exit. Verified 2026-07-26: no SessionEnd hook
was configured, and the richest record (the Claude Code transcript) rotates —
the 2026-06-17 control incident could be neither confirmed nor refuted six weeks
later because its transcript no longer existed.

The governing principle: a control event that leaves no trace is indistinguishable
from one that never happened. An abrupt ending is a control signal; it must be
recorded as one.

Captures: the termination reason, the active trace_id, how long the session ran,
how many gate calls it made, and whether the ending looks operator-forced.

Never blocks. Fail-open on every error — a session is already ending; a hook
error here must not become the last thing that goes wrong.

Input (Claude Code SessionEnd format):
    {
        "session_id": "...",
        "reason": "clear" | "resume" | "logout" | "prompt_input_exit"
                  | "bypass_permissions_disabled" | "other"
    }
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _telemetry import (  # noqa: E402
    active_trace_id,
    append_attestation,
    fail_open,
    load_latest_session,
    read_stdin_json,
    strict_mode,
)

# Endings that are ordinary session hygiene: the founder moved on deliberately.
_ROUTINE = {"clear", "resume", "logout"}

# Everything else is notable BY DEFAULT — including "unknown" and any reason value a
# future Claude Code release introduces. `prompt_input_exit` is the one that matters:
# typing exit is also what an operator does when the agent will not stop. We do NOT claim
# that is why it happened; we record that the distinction is unavailable, which is the
# whole point. An ending we cannot classify is the least explained one there is, so the
# default must be "notable", never silence.


def _session_shape() -> dict:
    """Best-effort snapshot of the newest MCP TELEMETRY session.

    Deliberately named `telemetry_*`: `load_latest_session()` picks the newest
    `session_*.json` by mtime, and that file spans the MCP server's session, which can
    cover several Claude sessions or a day or more. It is NOT the duration of the Claude
    session that is ending, and must not be read as one — a force-quit timed against an
    unrelated window is worse than no timing at all.
    """
    out: dict = {}
    try:
        path, data = load_latest_session()
        if not data:
            return out
        out["telemetry_session"] = (path.name if path else None)
        out["telemetry_call_count"] = data.get("call_count")
        start = data.get("session_start")
        last = data.get("last_update")
        if isinstance(start, (int, float)) and isinstance(last, (int, float)):
            out["telemetry_span_s"] = round(float(last) - float(start), 1)
        out["telemetry_last_update_iso"] = data.get("last_update_iso")
    except Exception:
        pass
    return out


def main() -> None:
    payload = read_stdin_json() or {}

    reason = str(payload.get("reason", "unknown"))
    session_id = str(payload.get("session_id", ""))[:64]

    record = {
        "tool": "session_end",
        "kind": "session_end",
        "hook": "session_end_attest",
        "reason": reason,
        "claude_session_id": session_id,
        "trace_id": active_trace_id(),
        "strict_mode": strict_mode(),
        # An ending we cannot explain is itself the finding. `routine` is False for
        # prompt_input_exit precisely because that value cannot distinguish "done for
        # the day" from "the agent would not stop and I quit".
        "routine": reason in _ROUTINE,
        # Default-notable: anything not on the routine list, including "unknown" and any
        # reason value a future release adds.
        "notable": reason not in _ROUTINE,
    }
    record.update(_session_shape())

    try:
        append_attestation(record)
    except Exception as exc:  # pragma: no cover — fail-open by contract
        fail_open(f"session_end attestation failed: {exc!r}")
        return

    if record["notable"]:
        sys.stderr.write(
            f"hook NOTE: session ended with reason='{reason}'. Recorded as notable — this "
            "value does not distinguish a deliberate exit from an operator force-quit. If "
            "the session was ended because something would not stop, write it down now; "
            "the transcript will not survive.\n"
        )

    sys.stdout.write("{}\n")


if __name__ == "__main__":
    # The docstring promises "never blocks, fail-open on every error"; without this guard
    # that was untrue — read_stdin_json() raises on non-UTF-8 stdin and the hook would exit
    # non-zero with a traceback. Every sibling hook carries the same guard.
    try:
        main()
    except Exception as exc:  # pragma: no cover — fail-open by contract
        fail_open(f"session_end hook error: {exc!r}")
