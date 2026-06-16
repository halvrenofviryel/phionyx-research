#!/usr/bin/env python3
"""PreToolUse hook — gate Bash commands with external or destructive effect.

Runs on EVERY Bash command (no shell prefilter — same as check_mcp_gate /
check_signed_control_state). Classification is the sole filter; this closes the old
"prefilter-dodge" hole where an obfuscated command never reached the hook (Phase 3 inc-2).

Two layers:
  1. Phase 3 / T4 — FAIL-CLOSED default-deny on irreversible external effects (publish,
     gh mutation, deploy, network-write, opaque-exec). Armed env-independently; matched
     on the NORMALIZED command; denied unless a signed external_effect override or the
     plain ~/.phionyx/external_effect_ok sentinel is present. (See _T4_HARD_DENY.)
  2. Legacy recency/ethics — FAIL-OPEN, telemetry-based, for the _SENSITIVE_RE set only
     (destructive git, etc.): in strict mode BLOCK if no verify_claim / response_gate
     within PHIONYX_MCP_EXTERNAL_GATE_MAX_AGE_SEC (default 300 s); else WARN. Non-T4,
     non-sensitive commands are allowed silently and fast.

Fail-open on every UNEXPECTED error path; the T4 layer itself is fail-closed.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _telemetry import (  # noqa: E402
    block,
    fail_open,
    last_gate_age_seconds,
    load_latest_session,
    read_stdin_json,
    strict_mode,
    warn,
)


DEFAULT_MAX_AGE_SEC = 300  # 5 minutes — stricter than edit gate

# --- Phase 3 / T4 capability tier — fail-closed default-deny on irreversible
# external effects (control-grade plan §3). Unlike the recency logic below (which is
# fail-OPEN and reads agent-writable telemetry), this layer DENIES by default and is
# armed env-independently; escape is a SIGNED human override (M1 #6) or a plain
# cooperative-dev sentinel. Narrow set per founder 2026-06-15: publish · gh mutation ·
# deploy · external network write. (Package INSTALL is WARN, not deny.) git commit +
# push (incl. --force) stay with check_signed_control_state — NOT duplicated here, so a
# single signed scope is never split across two gates (diff-review fix #3).
# Classification runs on the NORMALIZED command (see _normalize) so trivial obfuscation
# (tw''ine up''load, twine\ upload, t"w"ine) cannot dodge these patterns. This hook now
# runs on EVERY Bash command (no shell prefilter — same as check_mcp_gate /
# check_signed_control_state), closing the old "prefilter-dodge" hole (Phase 3 inc-2).
# Residual (HONEST, needs the allowlist broker): in-process decoding (python -c with an
# embedded base64), variable indirection, and novel encodings that never surface a
# recognizable token still pass — a denylist cannot close those (plan §3). Also benign
# commands that merely QUOTE a token can false-positive; the easy escape covers it.
_T4_HARD_DENY = (
    ("publish",      re.compile(r"\b(twine\s+upload|npm\s+publish|cargo\s+publish|poetry\s+publish|gh\s+release\s+(create|upload|edit|delete))\b")),
    ("gh_mutation",  re.compile(r"\bgh\s+(pr|issue)\s+(create|merge|edit|close|comment|delete)\b|\bgh\s+repo\s+(create|delete|edit)\b|\bgh\s+api\b[^\n]*(-X\s*(POST|PUT|PATCH|DELETE)|\s-f\b|--field\b|--raw-field\b|--input\b|--method\b)")),
    ("deploy",       re.compile(r"\b(docker\s+push|kubectl\s+apply|terraform\s+apply|make\s+(deploy|publish)|bash\s+scripts/\S*deploy)\b")),
    ("network_write", re.compile(r"\b(curl|wget)\b[^\n;|&]*(-X\s*(POST|PUT|PATCH|DELETE)|--request\s*(POST|PUT|PATCH|DELETE)|(^|\s)(-d|--data\S*|-F|--form|-T|--upload-file|--post-data|--post-file)\b)")),
    # decode/download piped straight into an interpreter — the classic "encode and run"
    # evasion. Two branches:
    #   (a) a DECODER (base64/xxd/openssl, incl. a file argument) piped to a shell or
    #       python — decoding then executing is the danger;
    #   (b) curl/wget piped to a SHELL only — "download a script and run it". python is
    #       deliberately excluded here (curl … | python -m json.tool is a benign read).
    # In-process decode (python -c with an embedded blob) never surfaces here = residual.
    ("opaque_exec",  re.compile(
        r"((base64\s+(-d|--decode)|xxd\s+-r|openssl\s+enc[^\n|]*-d)[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|dash|python[0-9.]*)\b"
        r"|\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|dash)\b)")),
)

# Hardcoded — NOT an agent-writable env (an env override would let the agent relocate
# the escape to any existing file; same fix as M1 #5).
_PLAIN_SENTINEL = Path("~/.phionyx/external_effect_ok").expanduser()

# The legacy "sensitive command" set — what the old shell prefilter matched. Now that the
# hook runs on EVERY Bash command, this decides whether a NON-T4 command still gets the
# (fail-open) recency/ethics treatment; everything else is allowed silently and fast.
# Deliberately does NOT include bare curl/wget (a GET must not be subjected to recency).
_SENSITIVE_RE = re.compile(
    r"\bgh\s+(pr|release|issue|api|repo)\b|npm\s+publish|twine\s+upload|pip[a-z ]*\s+upload|"
    r"cargo\s+publish|poetry\s+publish|git\s+push\b[^\n;|&]*(--force|--force-with-lease|\s-f\b|--delete|--mirror)|"
    r"git\s+reset\s+--hard|git\s+branch\s+-D|git\s+tag\s+(-d|--delete)|make\s+(deploy|publish|release)|"
    r"bash\s+scripts/\S*deploy|docker\s+push|kubectl\s+apply|terraform\s+apply"
)


def _normalize(cmd: str) -> str:
    """Collapse the shell quoting/escaping the shell itself would remove, so trivial
    obfuscation can't dodge T4 classification. Used ONLY for matching, never executed.
    Does NOT defeat in-process decoding / variable indirection — those need the allowlist
    broker (documented residual, plan §3). Never raises — on any error returns the raw
    command so classification still runs (a normalize crash must not fail OPEN on T4)."""
    try:
        # Strip ALL quote characters, the way the shell does, so quote-split obfuscation
        # (tw''ine, 'twine', t"w"ine, gh "release" create) collapses to the effective
        # command before matching. (Trade-off: a token QUOTED inside a string arg — e.g.
        # a commit message — can then false-positive; the easy escape covers that, and
        # the structural fix is the allowlist broker.)
        s = cmd.replace('"', "").replace("'", "")
        s = re.sub(r"\\(.)", r"\1", s)   # \X -> X (undo within-word backslash escaping)
        s = re.sub(r"\s+", " ", s)       # collapse whitespace
        return s
    except Exception:
        return cmd


def _t4_class(cmd: str) -> str | None:
    """Return the matched T4 hard-deny class, None if not T4, or "unknown" (deny) on a
    regex error — fail-closed, because a classification error on a fail-closed layer must
    deny (with the normal escape), never silently pass."""
    try:
        for name, rx in _T4_HARD_DENY:
            if rx.search(cmd):
                return name
    except Exception:
        # fail-closed: a classification error on the fail-closed T4 layer must DENY
        # (with the normal escape), not pass.
        return "unknown"
    return None


def _external_effect_escape() -> tuple[bool, str]:
    """Escape for a T4 hard-deny: SIGNED human override (strong) or plain sentinel
    (cooperative-dev). Fail-closed: any error -> not approved."""
    try:
        import control_override
        ok, claims = control_override.verify_override("external_effect")
        if ok:
            return True, "signed-override: " + str((claims or {}).get("reason", ""))[:160]
    except Exception:
        pass
    try:
        if _PLAIN_SENTINEL.exists():
            return True, "plain-sentinel: " + _PLAIN_SENTINEL.read_text(encoding="utf-8", errors="replace").strip()[:160]
    except Exception:
        return False, ""
    return False, ""


def _attest_t4(kind: str, cls: str, cmd_head: str, why: str = "") -> None:
    try:
        from _telemetry import append_attestation
        append_attestation({"tool": kind, "kind": kind, "t4_class": cls,
                            "hook": "check_bash_external_effect", "cmd": cmd_head, "approval_reason": why})
    except Exception:
        pass


def _ethics_advisory(cmd: str) -> None:
    """Local ethics gate (#17/18) on an outward command — ADVISORY only (never blocks
    in v1, per founder: enable but keep it from slowing things). Writes a stderr note on
    deny / allow_with_guard so the next turn sees the value/harm concern. Disable with
    PHIONYX_ETHICS_GATE=0. Fail-soft: any error is swallowed."""
    try:
        import ethics_local
        v = ethics_local.deliberate(cmd[:200], action_type="outward", detail=cmd[:400])
        if v.get("deliberated") and v.get("verdict") in ("deny", "allow_with_guard"):
            sys.stderr.write(
                f"ethics[{v['verdict']}] (advisory, non-blocking): "
                f"{v.get('reason', '')[:120]} frameworks={v.get('frameworks', '')}\n")
    except Exception:
        pass


def main() -> None:
    payload = read_stdin_json()
    if payload is None:
        fail_open("empty or invalid stdin")

    if payload.get("tool_name") != "Bash":
        fail_open(f"tool {payload.get('tool_name')!r} not gated by external-effect hook")

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        fail_open("tool_input not a dict")
    cmd = tool_input.get("command", "") or ""
    cmd_head = cmd[:200]

    # --- Phase 3 / T4: fail-closed default-deny on irreversible external effects. ---
    # Runs on the NORMALIZED command so trivial obfuscation can't dodge it, on EVERY Bash
    # command (no prefilter). Armed env-independently; a matched T4 class is DENIED unless
    # a signed override or the plain cooperative sentinel is present.
    t4 = _t4_class(_normalize(cmd))
    if t4 is not None:
        approved, why = _external_effect_escape()
        if approved:
            _attest_t4("external_effect_approved", t4, cmd_head, why)
            # fall through to the existing recency/ethics path (does not re-block T4)
        else:
            # block() persists its own block_event; no pre-attest (avoids a dup row).
            block(
                "BLOCKED by check_bash_external_effect (Phase 3 / T4 default-deny): this "
                f"command is an irreversible external effect [{t4}] and is denied by default.\n"
                f"  Command: {cmd_head}\n"
                "  Signed human override (off-agent): python3 tools/claude_code_mcp/control_override.py "
                "--sign --scope external_effect --reason '...' --ttl 1800\n"
                "  Or (cooperative dev): create ~/.phionyx/external_effect_ok with a one-line reason."
            )

    # Non-T4: only the legacy sensitive set gets the (fail-open) recency/ethics treatment.
    # Everything else — the vast majority of Bash — is allowed silently and fast. This is
    # what makes running on every command cheap and non-bricking.
    if not _SENSITIVE_RE.search(cmd):
        sys.stdout.write("{}\n")
        sys.exit(0)

    # Ethics advisory (#17/18) — runs on every outward command, non-blocking.
    _ethics_advisory(cmd)

    _, session = load_latest_session()
    if session is None:
        # We only reach here for a _SENSITIVE_RE command (the recency layer's scope).
        # With no MCP session telemetry at all, strict mode must block.
        if strict_mode():
            block(
                "BLOCKED by check_bash_external_effect — no MCP session telemetry "
                "and command crosses trust boundary.\n"
                f"Command: {cmd_head}\n"
                "Start the pipeline MCP and call phionyx_response_gate before retrying."
            )
        warn(f"no MCP telemetry; allowing external-effect command: {cmd_head}")

    age = last_gate_age_seconds(session)
    max_age = float(os.environ.get("PHIONYX_MCP_EXTERNAL_GATE_MAX_AGE_SEC", str(DEFAULT_MAX_AGE_SEC)))

    if age is None:
        reason = (
            f"No phionyx_verify_claim / phionyx_response_gate calls in this session yet.\n"
            f"Command crosses trust boundary: {cmd_head}\n"
            f"CLAUDE.md §MCP rule 1: call response_gate(action_type='deploy', ...) before deploying / committing.\n"
            f"Call response_gate(action_type='claim_fixed' | 'deploy') first."
        )
        if strict_mode():
            block(f"BLOCKED by check_bash_external_effect (no gate calls):\n{reason}")
        warn(reason)

    if age > max_age:
        reason = (
            f"Last verify_claim / response_gate was {age/60:.1f} min ago "
            f"(threshold {max_age/60:.1f} min for external-effect commands).\n"
            f"Command crosses trust boundary: {cmd_head}\n"
            f"Re-call phionyx_response_gate(action_type='deploy', ...) before this command."
        )
        if strict_mode():
            block(f"BLOCKED by check_bash_external_effect (stale gate):\n{reason}")
        warn(reason)

    # Fresh gate — allow silently.
    sys.stdout.write("{}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        fail_open(f"unexpected exception: {exc!r}")
