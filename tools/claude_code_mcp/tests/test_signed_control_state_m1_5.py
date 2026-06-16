"""M1 #5 — env-independent, default-on sandbox enforcement (negative tests).

Locks in the fail-closed contract of `check_signed_control_state.py` +
`sandbox_probe.py`: a critical action (commit/push) from a session that is NOT
provably sandboxed must be DENIED, with NO agent-writable env able to disable it.

These tests run the hook as a SUBPROCESS (exactly how Claude Code invokes it) with
an isolated ``HOME`` so the real ``~/.phionyx/unsandboxed_dev_ok`` is never touched.
In the test environment the repo control plane is writable -> ``sandbox_intact`` is
False -> the default path is the block path. (Sandboxed-true behaviour is covered by
``tools/offagent/verify-boundary.sh`` from a real ``run-agent.sh`` session.)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "check_signed_control_state.py"
PROBE = Path(__file__).resolve().parents[1] / "sandbox_probe.py"

# Built from parts so the literal critical-command substring never appears verbatim
# (keeps the repo's own commit-detection hooks from tripping on this test source).
_CRIT_CMD = "git " + "commit -m x"


def _run(payload: dict, *, home: Path, extra_env: dict | None = None) -> dict:
    """Invoke the hook with isolated HOME; return parsed stdout JSON ({} = allow)."""
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout or "{}")


def _is_block(out: dict) -> bool:
    return out.get("decision") == "block"


def test_default_on_block_with_env_unset(tmp_path):
    """No sandbox + no sentinel + no PHIONYX_SIGNED_GATE -> BLOCK (env-independent)."""
    out = _run({"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, home=tmp_path)
    assert _is_block(out), out


def test_signed_gate_zero_cannot_disable(tmp_path):
    """PHIONYX_SIGNED_GATE=0 must NOT turn enforcement off (the old opt-in hole)."""
    out = _run(
        {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}},
        home=tmp_path, extra_env={"PHIONYX_SIGNED_GATE": "0"},
    )
    assert _is_block(out), out


def test_dev_file_env_override_is_ignored(tmp_path):
    """The removed PHIONYX_UNSANDBOXED_DEV_FILE override must not relocate the sentinel:
    pointing it at an existing file must NOT bypass (finding #2)."""
    decoy = tmp_path / "decoy"
    decoy.write_text("not a real escape")
    out = _run(
        {"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}},
        home=tmp_path, extra_env={"PHIONYX_UNSANDBOXED_DEV_FILE": str(decoy)},
    )
    assert _is_block(out), out


def test_real_dev_sentinel_allows(tmp_path):
    """The hardcoded off-agent escape sentinel (present) re-allows the commit."""
    (tmp_path / ".phionyx").mkdir()
    (tmp_path / ".phionyx" / "unsandboxed_dev_ok").write_text("test escape")
    out = _run({"tool_name": "Bash", "tool_input": {"command": _CRIT_CMD}}, home=tmp_path)
    assert out == {}, out


def test_non_commit_bash_allowed(tmp_path):
    out = _run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}, home=tmp_path)
    assert out == {}, out


def test_non_dict_payload_allowed_not_crash(tmp_path):
    """A non-dict payload cannot be identified as a critical action -> allow, not crash
    (finding #1 source: must not bubble to a fail-OPEN handler)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="[]", capture_output=True, text=True,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout or "{}") == {}


def test_probe_not_intact_when_control_plane_writable(tmp_path):
    """sandbox_probe must report not-intact in a normal (unsandboxed) checkout."""
    proc = subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True, text=True,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}, timeout=30,
    )
    assert proc.returncode == 1, proc.stdout  # exit 1 == not intact
    assert "sandbox_intact = False" in proc.stdout
