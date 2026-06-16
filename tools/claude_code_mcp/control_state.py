#!/usr/bin/env python3
"""Signed off-agent control state (M1 #1-#3) — Ed25519 sign / verify.

The gate-relevant facts (last directive, freshness) are signed with an Ed25519
PRIVATE key held by the off-agent signer, and verified by the gates with the
PUBLIC key. An agent that holds only the public key can VERIFY but cannot FORGE —
this is what lets a real-time gate trust state the agent cannot fabricate.

KEY CUSTODY (the trust depends on this, not on the code):
  - off-agent (target): the private key is owned by a SEPARATE OS user the agent
    cannot read (provision with scripts/active/provision_offagent_control.sh), and
    the signer runs as that user. Then signed state is unforgeable by the agent.
  - custody-pending (this dev box): the private key is generated under the agent's
    own user (~/.phionyx/keys). The MECHANISM is identical and fully tested; the
    trust is NOT yet real (the agent could read the key). Honest-scope: "signed,
    custody-pending". Moving the key off-agent makes it real with ZERO code change.

Paths (env-overridable):
  PHIONYX_KEY_DIR            default ~/.phionyx/keys
  PHIONYX_CONTROL_STATE_FILE default ~/.phionyx/control_state.signed.json
  PHIONYX_CONTROL_STATE_FRESH_SEC  default 300
"""
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

KEY_DIR = Path(os.environ.get("PHIONYX_KEY_DIR", "~/.phionyx/keys")).expanduser()
PRIV_PATH = KEY_DIR / "control_ed25519"
PUB_PATH = KEY_DIR / "control_ed25519.pub"
STATE_FILE = Path(
    os.environ.get("PHIONYX_CONTROL_STATE_FILE", "~/.phionyx/control_state.signed.json")
).expanduser()
FRESH_SEC = float(os.environ.get("PHIONYX_CONTROL_STATE_FRESH_SEC", "300"))

_TELEMETRY_DIR = Path(
    os.environ.get("PHIONYX_TELEMETRY_DIR",
                   str(Path(__file__).resolve().parent.parent.parent / "data" / "mcp_telemetry"))
)


# --------------------------------------------------------------------------- keys
def ensure_keypair() -> tuple[Path, Path]:
    """Generate an Ed25519 keypair if absent (custody-pending bootstrap).

    The off-agent provisioning script regenerates this AS THE SEPARATE USER and
    locks the private key down; that path is preferred. Here we only bootstrap so
    the mechanism is testable on a fresh box.
    """
    if PRIV_PATH.exists() and PUB_PATH.exists():
        return PRIV_PATH, PUB_PATH
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(KEY_DIR, 0o700)
    except OSError:
        pass
    priv = Ed25519PrivateKey.generate()
    PRIV_PATH.write_bytes(
        priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        os.chmod(PRIV_PATH, 0o600)
    except OSError:
        pass
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    PUB_PATH.write_text(base64.b64encode(pub_raw).decode() + "\n")
    return PRIV_PATH, PUB_PATH


def _load_private() -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(PRIV_PATH.read_bytes(), password=None)  # type: ignore[return-value]


def _load_public() -> Ed25519PublicKey:
    raw = base64.b64decode(PUB_PATH.read_text().strip())
    return Ed25519PublicKey.from_public_bytes(raw)


# --------------------------------------------------------------------------- sign
def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_state(state: dict) -> dict:
    """Sign `state` (+ a server timestamp) and write the signed record. SIGNER side."""
    ensure_keypair()
    payload = {"state": state, "ts": time.time()}
    body = _canonical(payload)
    sig = _load_private().sign(body)
    record = {"alg": "ed25519", "payload_b64": base64.b64encode(body).decode(),
              "sig_b64": base64.b64encode(sig).decode()}
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(record))
    tmp.replace(STATE_FILE)
    return record


def read_verified_state() -> dict | None:
    """Return the signed state IFF signature verifies AND it is fresh. GATE side.

    Returns None on any failure (missing / unparseable / bad signature / stale).
    Callers treat None as 'no trustworthy state' and, for critical actions,
    FAIL CLOSED.
    """
    try:
        record = json.loads(STATE_FILE.read_text())
        body = base64.b64decode(record["payload_b64"])
        sig = base64.b64decode(record["sig_b64"])
        _load_public().verify(sig, body)  # raises on bad signature
        payload = json.loads(body)
        ts = float(payload.get("ts", 0))
        if time.time() - ts > FRESH_SEC:
            return None  # stale
        state = payload.get("state")
        return state if isinstance(state, dict) else None
    except Exception:
        return None


# --------------------------------------------------------- refresh from telemetry
def _latest_session() -> dict | None:
    try:
        files = sorted(_TELEMETRY_DIR.glob("session_*.json"),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            return None
        data = json.loads(files[0].read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def refresh_from_telemetry() -> dict | None:
    """Read the latest gate facts from telemetry and SIGN them. Best-effort.

    Runs on the SIGNER side (off-agent in production; the custody-pending signer
    hook for now). Returns the signed record, or None if there is nothing to sign.
    """
    session = _latest_session()
    if session is None:
        return None
    timeline = session.get("timeline", [])
    gate_ts = 0.0
    for e in timeline:
        if e.get("tool") in ("phionyx_verify_claim", "phionyx_response_gate"):
            t = e.get("timestamp", 0)
            if isinstance(t, (int, float)) and t > gate_ts:
                gate_ts = float(t)
    state = {
        "last_directive": session.get("drift_metrics", {}).get("last_directive", "unknown"),
        "last_gate_ts": gate_ts,
        "session_id": str(session.get("session_id", ""))[:64],
    }
    return sign_state(state)


if __name__ == "__main__":
    # Self-test: roundtrip, tamper, stale, wrong-key all behave correctly.
    import sys
    import tempfile
    if len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        rec = refresh_from_telemetry()
        print("refreshed" if rec else "nothing-to-sign")
        sys.exit(0)
    # Sandbox the test in a temp dir so it never touches real keys/state.
    d = Path(tempfile.mkdtemp())
    os.environ["PHIONYX_KEY_DIR"] = str(d / "keys")
    import importlib
    import control_state as cs  # type: ignore
    importlib.reload(cs)
    cs.sign_state({"last_directive": "pass", "last_gate_ts": time.time()})
    print("roundtrip verifies:", cs.read_verified_state() is not None)
    # tamper
    rec = json.loads(cs.STATE_FILE.read_text())
    bad = json.loads(base64.b64decode(rec["payload_b64"]))
    bad["state"]["last_directive"] = "forged"
    rec["payload_b64"] = base64.b64encode(cs._canonical(bad)).decode()
    cs.STATE_FILE.write_text(json.dumps(rec))
    print("tampered rejected:", cs.read_verified_state() is None)
    # stale
    cs.sign_state({"x": 1})
    cs.FRESH_SEC = -1
    print("stale rejected:", cs.read_verified_state() is None)
