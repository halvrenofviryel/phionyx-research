"""M1 #6 — signed human override (negative + positive tests).

A manual override of a fail-closed gate must be an Ed25519-SIGNED, scoped, expiring
human approval verified with the PUBLIC key — not a plain agent-writable sentinel.

Tests run the gates as SUBPROCESSES with an isolated ``HOME`` (so the real keys,
state and sentinels are never touched). ``_provision_trusted`` mirrors
tools/offagent/setup.sh: it generates the legitimate keypair and publishes its pubkey
to the hardcoded trusted path that ``verify_override`` pins to. The signer signs with
that key; a token signed by any other key (or via a relocated ``PHIONYX_KEY_DIR``)
must still be rejected, because the verify key is pinned, not env-derived.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
from pathlib import Path

CCM = Path(__file__).resolve().parents[1]
OVERRIDE = CCM / "control_override.py"
SIGNED_GATE = CCM / "check_signed_control_state.py"
SELF_MOD = CCM / "check_self_modification.py"

_CRIT_CMD = "git " + "commit -m x"  # built from parts (see test_signed_control_state_m1_5)
_PROTECTED_EDIT = {"tool_name": "Edit",
                   "tool_input": {"file_path": str(CCM / "check_signed_control_state.py")}}


def _env(home: Path, key_dir: Path | None = None) -> dict:
    e = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    if key_dir is not None:
        e["PHIONYX_KEY_DIR"] = str(key_dir)
    return e


def _provision_trusted(home: Path) -> None:
    """Mirror setup.sh: generate the legitimate keypair (default ~/.phionyx/keys) and
    publish its pubkey to the trusted path verify_override pins to (~/.phionyx/pub)."""
    subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, {str(CCM)!r}); import control_state as c; c.ensure_keypair()"],
        capture_output=True, text=True, env=_env(home), check=True, timeout=30)
    src = home / ".phionyx" / "keys" / "control_ed25519.pub"
    dst = home / ".phionyx" / "pub"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "control_ed25519.pub").write_text(src.read_text())


def _sign(home: Path, scope: str, ttl: str = "120", key_dir: Path | None = None) -> int:
    return subprocess.run(
        [sys.executable, str(OVERRIDE), "--sign", "--scope", scope, "--reason", "test", "--ttl", ttl],
        capture_output=True, text=True, env=_env(home, key_dir), timeout=30,
    ).returncode


def _run_hook(hook: Path, payload: dict, home: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(hook)], input=json.dumps(payload),
        capture_output=True, text=True, env=_env(home), timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout or "{}")


def _is_block(out: dict) -> bool:
    return out.get("decision") == "block"


# --------------------------------------------------------------- module self-test
def test_module_selftest_passes(tmp_path):
    """control_override.py self-test: scope match, wrong-scope, wrong-KEY, tamper all reject."""
    proc = subprocess.run([sys.executable, str(OVERRIDE)], capture_output=True,
                          text=True, env=_env(tmp_path), timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SELFTEST OK" in proc.stdout


def test_unsigned_commit_blocked_without_override(tmp_path):
    _provision_trusted(tmp_path)
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert _is_block(out), out


# ----------------------------------------------------- signed override -> allow path
def test_signed_override_allows_unsandboxed_commit(tmp_path):
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "unsandboxed_commit") == 0
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert out == {}, out


def test_any_scope_override_allows_commit(tmp_path):
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "any") == 0
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert out == {}, out


def test_wrong_scope_override_does_not_allow_commit(tmp_path):
    """A control_plane_edit token must NOT unlock a commit (scope is enforced)."""
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "control_plane_edit") == 0
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert _is_block(out), out


def test_expired_override_does_not_allow_commit(tmp_path):
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "unsandboxed_commit", ttl="1") == 0
    time.sleep(1.2)
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert _is_block(out), out


def test_garbage_signature_rejected(tmp_path):
    """Token bytes intact but signature overwritten with garbage -> reject."""
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "unsandboxed_commit") == 0
    f = tmp_path / ".phionyx" / "state" / "control_override.signed.json"
    rec = json.loads(f.read_text())
    rec["sig_b64"] = base64.b64encode(b"\x00" * 64).decode()
    f.write_text(json.dumps(rec))
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert _is_block(out), out


def test_forged_key_token_rejected(tmp_path):
    """The critical fail-open the diff-review caught: a token validly signed by an
    ATTACKER key reached via a relocated PHIONYX_KEY_DIR must STILL be rejected, because
    the verify key is pinned to the trusted path (not env-derived)."""
    _provision_trusted(tmp_path)                       # trusted pub = legitimate key A
    evil = tmp_path / "evilkeys"
    # token signed by attacker key B is written; CLI self-verify against the pinned pub
    # fails (exit 2) — exactly the protection. The token file still exists; gate must block.
    assert _sign(tmp_path, "any", key_dir=evil) == 2
    out = _run_hook(SIGNED_GATE, {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, tmp_path)
    assert _is_block(out), out


# ----------------------------------------------- self-modification gate honors override
def test_signed_override_allows_control_plane_edit(tmp_path):
    _provision_trusted(tmp_path)
    assert _is_block(_run_hook(SELF_MOD, _PROTECTED_EDIT, tmp_path)), "should block without override"
    assert _sign(tmp_path, "control_plane_edit") == 0
    assert _run_hook(SELF_MOD, _PROTECTED_EDIT, tmp_path) == {}


def test_commit_scope_override_does_not_unlock_edit(tmp_path):
    """An unsandboxed_commit token must NOT unlock a control-plane edit (scope split)."""
    _provision_trusted(tmp_path)
    assert _sign(tmp_path, "unsandboxed_commit") == 0
    assert _is_block(_run_hook(SELF_MOD, _PROTECTED_EDIT, tmp_path)), "commit scope must not unlock edit"


def test_forged_key_does_not_unlock_edit(tmp_path):
    _provision_trusted(tmp_path)
    evil = tmp_path / "evilkeys"
    assert _sign(tmp_path, "control_plane_edit", key_dir=evil) == 2  # self-verify fails (pinned pub)
    assert _is_block(_run_hook(SELF_MOD, _PROTECTED_EDIT, tmp_path)), "forged key must not unlock edit"
