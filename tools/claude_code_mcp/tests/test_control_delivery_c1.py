"""C1 — control-channel delivery evidence (issuer / enforcement-point pair).

A successful WRITE is not delivery. Before this, `sign_override` returned as soon as the
atomic rename succeeded, so the signer could report a valid token while the enforcement
point saw nothing — the failure recorded on 2026-06-17, where a correctly signed
off-agent token never surfaced at the path the gate reads and nothing could tell that
apart from an instruction never issued.

These tests pin the two properties that fix it:

  1. the signer reads back through the VERIFIER's own path and reports failure loudly
     instead of returning success;
  2. an instruction the issuer recorded but no enforcement point ever acknowledged is
     detectable after the fact.

The second is the important one: no single side can prove non-delivery on its own — a
receiver cannot know what it never received. Only the comparison can.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CCM = Path(__file__).resolve().parents[1]
OVERRIDE = CCM / "control_override.py"


def _env(home: Path) -> dict:
    return {"HOME": str(home), "PATH": "/usr/bin:/bin"}


def _provision(home: Path, *, trust_key: bool = True) -> None:
    """Create a keypair. With trust_key=False the verify key is never pinned, so the
    verifier cannot validate what the signer just wrote — the readback fails the way a
    cross-boundary delivery failure does, without needing a real sandbox."""
    subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, {str(CCM)!r}); import control_state as c; c.ensure_keypair()"],
        env=_env(home), capture_output=True, check=True, timeout=30)
    if trust_key:
        src = home / ".phionyx" / "keys" / "control_ed25519.pub"
        dst = home / ".phionyx" / "pub"
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "control_ed25519.pub").write_text(src.read_text())


def _run(home: Path, args: list[str]):
    return subprocess.run([sys.executable, str(OVERRIDE)] + args,
                          capture_output=True, text=True, env=_env(home), timeout=30)


def _events(home: Path) -> list[dict]:
    log = home / ".phionyx" / "state" / "control_delivery.jsonl"
    if not log.exists():
        return []
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]


def _ack(home: Path) -> None:
    subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, {str(CCM)!r}); import control_override as c; "
         "c.record_enforcement_acknowledgement('external_effect')"],
        env=_env(home), capture_output=True, timeout=30)


def test_successful_sign_records_issued_and_delivered(tmp_path):
    _provision(tmp_path)
    assert _run(tmp_path, ["--sign", "--scope", "external_effect",
                           "--reason", "t", "--ttl", "300"]).returncode == 0
    phases = [(e["phase"], e["observed_by"]) for e in _events(tmp_path)]
    assert ("issued", "issuer") in phases
    assert ("delivered", "issuer") in phases


def test_readback_failure_is_reported_not_swallowed(tmp_path):
    """The signature is valid; delivery is not established. The signer must say so."""
    _provision(tmp_path, trust_key=False)
    proc = _run(tmp_path, ["--sign", "--scope", "external_effect",
                           "--reason", "t", "--ttl", "300"])
    assert proc.returncode != 0, "a token that cannot be read back must not report success"
    assert "readback FAILED" in proc.stderr, proc.stderr
    ev = _events(tmp_path)
    assert ev[-1]["phase"] == "delivery_failed"
    assert ev[-1]["observed_by"] == "issuer"
    assert ev[-1]["failure"]["reason"]
    # Honesty field: we did not determine the cause, and the record says so.
    assert ev[-1]["failure"]["root_cause_isolated"] is False


def test_issued_without_acknowledgement_is_detectable(tmp_path):
    """THE point of the pair: silence becomes a finding."""
    _provision(tmp_path)
    _run(tmp_path, ["--sign", "--scope", "external_effect", "--reason", "t", "--ttl", "300"])
    proc = _run(tmp_path, ["--delivery-audit"])
    assert proc.returncode == 3, "an unacknowledged instruction must not audit clean"
    assert "NEVER acknowledged" in proc.stdout


def test_acknowledgement_closes_the_gap(tmp_path):
    _provision(tmp_path)
    _run(tmp_path, ["--sign", "--scope", "external_effect", "--reason", "t", "--ttl", "300"])
    _ack(tmp_path)
    proc = _run(tmp_path, ["--delivery-audit"])
    assert proc.returncode == 0, proc.stdout
    assert "no unacknowledged" in proc.stdout
    phases = [(e["phase"], e["observed_by"]) for e in _events(tmp_path)]
    assert ("acknowledged", "enforcement_point") in phases


def test_both_sides_agree_on_the_instruction_identity(tmp_path):
    """Correlation is by instruction_id AND hash; two sides reporting different hashes
    have not seen the same instruction."""
    _provision(tmp_path)
    _run(tmp_path, ["--sign", "--scope", "external_effect", "--reason", "t", "--ttl", "300"])
    _ack(tmp_path)
    ev = _events(tmp_path)
    issuer = [e for e in ev if e["observed_by"] == "issuer"]
    gate = [e for e in ev if e["observed_by"] == "enforcement_point"]
    assert issuer and gate
    assert issuer[0]["instruction_id"] == gate[0]["instruction_id"]
    assert issuer[0]["instruction_hash"] == gate[0]["instruction_hash"]


def test_delivery_audit_is_clean_when_nothing_was_issued(tmp_path):
    """No log at all must not read as a failure."""
    proc = _run(tmp_path, ["--delivery-audit"])
    assert proc.returncode == 0
    assert "no unacknowledged" in proc.stdout


def test_selftest_does_not_write_to_the_production_delivery_log(tmp_path):
    """An instrument must not write to the record it measures.

    The selftest signs six times, two of them SUPPOSED to fail (wrong key, tamper).
    It redirects OVERRIDE_FILE to a temp dir but originally left DELIVERY_LOG pointing
    at the real one, so every diagnostic run injected synthetic delivery_failed records
    into production evidence — indistinguishable from real ones, and duly reported by
    --delivery-audit as findings. Caught by running the audit on the real log: 6 of 7
    findings were this.
    """
    proc = _run(tmp_path, [])           # no args -> selftest
    assert proc.returncode == 0, proc.stderr
    assert "SELFTEST OK" in proc.stdout
    log = tmp_path / ".phionyx" / "state" / "control_delivery.jsonl"
    assert not log.exists(), (
        f"selftest wrote {len(_events(tmp_path))} record(s) to the production delivery log"
    )


def test_evidence_recording_never_breaks_signing(tmp_path, monkeypatch):
    """Evidence must not become a new way to fail."""
    sys.path.insert(0, str(CCM))
    import control_override as co
    monkeypatch.setattr(co, "DELIVERY_LOG", Path("/proc/cannot/write/here.jsonl"))
    co.record_delivery_observation(instruction_id="x", phase="issued", observed_by="issuer")
