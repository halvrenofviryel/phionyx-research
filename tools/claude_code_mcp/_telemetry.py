"""Shared helpers for Claude Code hook scripts.

All hook scripts under tools/claude_code_mcp/ follow the same contract:
- Read JSON event payload from stdin
- Decide: allow (stdout `{}`) | block (stdout `{"decision":"block","reason":...}`) | warn (stderr message)
- Fail-open on every error so hooks NEVER disrupt the Claude Code session

This module factors out the common pieces: telemetry path discovery,
auto-attestation appending, gate-age checks, strict-mode detection.

Attestation entries written here use `directive="auto_attest"` and are
NOT counted toward the `/runtime-evidence` dashboard's `gate_calls`
metric — inflating that would defeat the audit. They contribute to
`all_calls` so density/coverage signals are still visible.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Default telemetry path. `PHIONYX_TELEMETRY_DIR` env var overrides for
# test/debug invocations (parallels the override in check_edit_gate.py).
TELEMETRY_DIR = Path(
    os.environ.get("PHIONYX_TELEMETRY_DIR", str(REPO_ROOT / "data" / "mcp_telemetry"))
)
GATE_TOOLS = {"phionyx_verify_claim", "phionyx_response_gate"}
_DEFAULT_ACTIVE_TRACE_FILE = "~/.phionyx/active_trace"


def active_trace_id() -> str:
    """Resolve active trace_id with the same precedence as the MCP servers.

    Order (matches ADR-0006 + phionyx_claude_mcp + phionyx_mcp_server.trace):
      1. PHIONYX_TRACE_ID env var
      2. PHIONYX_ACTIVE_TRACE_FILE (default ~/.phionyx/active_trace)
      3. empty string (fail-open — hooks must NEVER block on missing trace)
    """
    env_value = os.environ.get("PHIONYX_TRACE_ID")
    if env_value:
        return env_value.strip()
    path = Path(
        os.environ.get("PHIONYX_ACTIVE_TRACE_FILE", _DEFAULT_ACTIVE_TRACE_FILE)
    ).expanduser()
    try:
        if path.exists():
            return path.read_text().strip()
    except Exception:
        pass
    return ""


def fail_open(note: str = "") -> None:
    if note:
        sys.stderr.write(f"hook: fail-open — {note}\n")
    sys.stdout.write("{}\n")
    sys.exit(0)


def block(reason: str, hook: str | None = None) -> None:
    # §6 (L2→L3 plan): persist the block event before signalling the block, so
    # the most valuable governance events (refusals) are not lost to stdout-only.
    # Reuses append_attestation (directive=auto_attest, excluded from gate-coverage
    # math). Best-effort; never raises — fail-open behaviour is preserved.
    try:
        append_attestation({
            "tool": "block_event",
            "kind": "block_event",
            "verdict": "block",
            "hook": hook or "",
            "reason": (reason or "")[:300],
        })
    except Exception:
        pass
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}) + "\n")
    sys.exit(0)


def warn(message: str) -> None:
    sys.stderr.write(f"hook WARN: {message}\n")
    sys.stdout.write("{}\n")
    sys.exit(0)


def strict_mode() -> bool:
    return os.environ.get("PHIONYX_MCP_GATE_STRICT", "").lower() in {"1", "true", "yes"}


def latest_session_path() -> Path | None:
    if not TELEMETRY_DIR.exists():
        return None
    files = sorted(
        TELEMETRY_DIR.glob("session_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def load_latest_session() -> tuple[Path | None, dict | None]:
    path = latest_session_path()
    if path is None:
        return None, None
    try:
        return path, json.loads(path.read_text())
    except Exception:
        return None, None


def last_gate_age_seconds(session: dict) -> float | None:
    """Age in seconds since the most recent verify_claim/response_gate call."""
    timeline = session.get("timeline", [])
    latest_ts = 0.0
    for entry in timeline:
        if entry.get("tool") in GATE_TOOLS:
            ts = entry.get("timestamp", 0)
            if ts > latest_ts:
                latest_ts = ts
    if latest_ts == 0:
        return None
    return max(0.0, time.time() - latest_ts)


def append_attestation(extra: dict) -> bool:
    """Append a directive=auto_attest entry to the latest session telemetry.

    Caller passes `extra` with at minimum `tool` (string identifying the
    attestation kind, e.g. "subagent_spawn"). Any other fields are
    preserved verbatim.

    Returns True if written, False on any failure (caller decides what to
    do — typically fail-open silent).
    """
    path, data = load_latest_session()
    if path is None or data is None:
        return False
    now = time.time()
    iso = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
    timeline = data.setdefault("timeline", [])
    call_count = data.get("call_count", 0) + 1
    entry = {
        "call_number": call_count,
        "timestamp": now,
        "iso_time": iso,
        "directive": "auto_attest",
        "drift_severity": "none",
        **extra,
    }
    timeline.append(entry)
    data["call_count"] = call_count
    data["last_update"] = now
    data["last_update_iso"] = iso
    try:
        path.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def read_stdin_json() -> dict | None:
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
