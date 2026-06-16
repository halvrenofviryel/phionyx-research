#!/usr/bin/env python3
"""Signed human override (M1 #6) — Ed25519-signed, scoped, time-boxed approval.

A manual override of a fail-closed gate must be a SIGNED human approval, not a plain
agent-writable sentinel. The founder signs a scoped, expiring token with the off-agent
PRIVATE key (OUTSIDE the sandbox); the gates verify it with the PUBLIC key. An agent
holding only the public key can VERIFY but cannot FORGE — so even an agent that can
write the override FILE cannot mint approval.

The verification key is loaded from a HARDCODED trusted path (``~/.phionyx/pub/``,
provisioned off-agent by tools/offagent/setup.sh, ro-bound into the sandbox), NOT from
``control_state.PHIONYX_KEY_DIR`` — that env is agent-writable, and reading the verify key
through it would let an agent point at its own keypair and verify a self-signed token.
Pinning the path is what makes "no agent-writable env can relocate the key" true.

Same honest scope as M1 #1-3: the MECHANISM is unforgeable; the TRUST becomes real only
once the private key is off-agent (custody-pending on this dev box — the agent can
currently read the key AND overwrite the trusted pub, so it could still sign; once the
key + trusted-pub dir are off-agent this is unforgeable with NO further code change). The
legacy plain sentinels remain as documented COOPERATIVE-DEV fallbacks.

Override file — hardcoded (no env override) at the path run-agent.sh ro-binds into the
sandbox, so it is readable by the gate inside the sandbox yet writable only off-agent:
    ~/.phionyx/state/control_override.signed.json

Sign (FOUNDER, off-agent — needs the private key, fails inside the sandbox by design):
    python3 tools/claude_code_mcp/control_override.py --sign \\
        --scope unsandboxed_commit --reason "release v0.9 cut" --ttl 3600
    python3 tools/claude_code_mcp/control_override.py --show     # inspect current token
    python3 tools/claude_code_mcp/control_override.py --revoke   # delete the token

Scopes: control_plane_edit | unsandboxed_commit | external_effect | any
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Hardcoded — the file lives in the dir run-agent.sh ro-binds into the sandbox.
OVERRIDE_FILE = Path("~/.phionyx/state/control_override.signed.json").expanduser()

# Trusted VERIFICATION key — HARDCODED, deliberately NOT control_state.PHIONYX_KEY_DIR
# (which is an agent-writable env). Provisioned ONCE off-agent by tools/offagent/setup.sh
# (it copies the pubkey here) and ro-bound into the sandbox. Pinning this is what stops an
# agent pointing PHIONYX_KEY_DIR at its OWN keypair to verify a self-signed token — without
# the pin, env relocation is a full fail-open of both gates (diff-review finding, M1 #6).
_TRUSTED_PUB = Path("~/.phionyx/pub/control_ed25519.pub").expanduser()
VALID_SCOPES = ("control_plane_edit", "unsandboxed_commit", "external_effect", "any")
DEFAULT_TTL_SEC = 3600


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_trusted_public():
    """Load the pinned Ed25519 PUBLIC key from the hardcoded trusted path (env-independent)."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    raw = base64.b64decode(_TRUSTED_PUB.read_text().strip())
    return Ed25519PublicKey.from_public_bytes(raw)


# --------------------------------------------------------------------------- signer
def sign_override(scope: str, reason: str, ttl_sec: int = DEFAULT_TTL_SEC) -> dict:
    """Sign a scoped, expiring override token. SIGNER side (founder, off-agent).

    Requires the PRIVATE key (``control_state.ensure_keypair`` / ``_load_private``).
    Inside the sandbox the key dir is tmpfs-masked, so this raises by design — a
    signed override can only be minted off-agent.
    """
    if scope not in VALID_SCOPES:
        raise ValueError(f"scope must be one of {VALID_SCOPES}, got {scope!r}")
    import control_state
    control_state.ensure_keypair()
    now = time.time()
    payload = {
        "override": {"scope": scope, "reason": str(reason)[:200],
                     "nonce": base64.b64encode(os.urandom(9)).decode()},
        "ts": now,
        "exp": now + max(1, int(ttl_sec)),
    }
    body = _canonical(payload)
    sig = control_state._load_private().sign(body)
    record = {"alg": "ed25519", "payload_b64": base64.b64encode(body).decode(),
              "sig_b64": base64.b64encode(sig).decode()}
    OVERRIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OVERRIDE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(record))
    tmp.replace(OVERRIDE_FILE)
    return record


# ----------------------------------------------------------------------------- gate
def verify_override(scope: str) -> tuple[bool, dict | None]:
    """Return (ok, claims) IFF a token exists, its signature verifies with the PUBLIC
    key, it has NOT expired, and its scope covers `scope` (exact match or "any").
    GATE side. Fail-closed: ANY failure (missing / unparseable / bad signature /
    expired / wrong scope) returns (False, None). Records nothing — the calling gate
    attests the USE so the override leaves an audit trail."""
    try:
        record = json.loads(OVERRIDE_FILE.read_text())
        body = base64.b64decode(record["payload_b64"])
        sig = base64.b64decode(record["sig_b64"])
        _load_trusted_public().verify(sig, body)  # raises on bad signature (PINNED key)
        payload = json.loads(body)
        exp = float(payload.get("exp", 0))
        if time.time() >= exp:
            return False, None  # expired
        claims = payload.get("override")
        if not isinstance(claims, dict):
            return False, None
        token_scope = claims.get("scope")
        if token_scope == scope or token_scope == "any":
            return True, claims
        return False, None
    except Exception:
        return False, None


# ----------------------------------------------------------------------------- cli
def _main(argv: list[str]) -> int:
    if "--sign" in argv:
        def _opt(name: str, default: str | None = None) -> str | None:
            return argv[argv.index(name) + 1] if name in argv else default
        scope = _opt("--scope") or ""
        reason = _opt("--reason") or "(no reason given)"
        ttl = int(_opt("--ttl") or str(DEFAULT_TTL_SEC))
        try:
            sign_override(scope, reason, ttl)
        except Exception as exc:
            print(f"sign FAILED: {exc!r}", file=sys.stderr)
            print("(inside the sandbox the private key is masked — sign off-agent.)", file=sys.stderr)
            return 1
        ok, claims = verify_override(scope)
        print(f"signed override -> {OVERRIDE_FILE}")
        print(f"  scope={scope} ttl={ttl}s reason={reason!r}  self-verify={ok}")
        return 0 if ok else 2
    if "--revoke" in argv:
        try:
            OVERRIDE_FILE.unlink()
            print(f"revoked (deleted) {OVERRIDE_FILE}")
        except FileNotFoundError:
            print("nothing to revoke (no token present)")
        return 0
    if "--show" in argv:
        if not OVERRIDE_FILE.exists():
            print("no override token present")
            return 0
        for sc in VALID_SCOPES:
            ok, claims = verify_override(sc)
            if ok:
                exp_in = "?"
                try:
                    payload = json.loads(base64.b64decode(json.loads(OVERRIDE_FILE.read_text())["payload_b64"]))
                    exp_in = f"{int(float(payload['exp']) - time.time())}s"
                except Exception:
                    pass
                print(f"VALID token: scope={claims.get('scope')} reason={claims.get('reason')!r} expires_in={exp_in}")
                return 0
        print("token present but INVALID (bad signature / expired / unknown scope)")
        return 1
    # default: self-test (temp keys; never touches real keys/state)
    return _selftest()


def _selftest() -> int:
    import importlib
    import tempfile
    d = Path(tempfile.mkdtemp())
    os.environ["PHIONYX_KEY_DIR"] = str(d / "keys")
    global OVERRIDE_FILE, _TRUSTED_PUB
    OVERRIDE_FILE = d / "control_override.signed.json"
    import control_state
    importlib.reload(control_state)  # pick up the temp PHIONYX_KEY_DIR
    control_state.ensure_keypair()
    # publish the real pubkey to a temp trusted path (mirrors setup.sh) — verify pins to it
    _TRUSTED_PUB = d / "pub" / "control_ed25519.pub"
    _TRUSTED_PUB.parent.mkdir(parents=True, exist_ok=True)
    _TRUSTED_PUB.write_text((d / "keys" / "control_ed25519.pub").read_text())
    sign_override("unsandboxed_commit", "selftest", ttl_sec=60)
    ok_match, _ = verify_override("unsandboxed_commit")
    ok_wrong, _ = verify_override("control_plane_edit")
    # wrong-KEY: sign with a DIFFERENT keypair; trusted pub is unchanged -> must reject
    os.environ["PHIONYX_KEY_DIR"] = str(d / "evilkeys")
    importlib.reload(control_state)
    sign_override("any", "forged", ttl_sec=60)
    ok_wrongkey, _ = verify_override("unsandboxed_commit")
    # restore the legitimate signer for the remaining tamper/expiry checks
    os.environ["PHIONYX_KEY_DIR"] = str(d / "keys")
    importlib.reload(control_state)
    sign_override("unsandboxed_commit", "selftest", ttl_sec=60)
    # tamper
    rec = json.loads(OVERRIDE_FILE.read_text())
    bad = json.loads(base64.b64decode(rec["payload_b64"]))
    bad["override"]["scope"] = "any"
    rec["payload_b64"] = base64.b64encode(_canonical(bad)).decode()
    OVERRIDE_FILE.write_text(json.dumps(rec))
    ok_tamper, _ = verify_override("unsandboxed_commit")
    print("scope match  :", ok_match)          # True
    print("wrong scope  :", not ok_wrong)      # True (rejected)
    print("wrong key    :", not ok_wrongkey)   # True (rejected — env-pinned pub)
    print("tamper reject:", not ok_tamper)     # True (rejected)
    ok = ok_match and not ok_wrong and not ok_wrongkey and not ok_tamper
    print("SELFTEST", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
