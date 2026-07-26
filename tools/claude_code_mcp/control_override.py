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

    # C1 — a successful WRITE is not delivery. Until now this function returned as soon
    # as the rename succeeded, so the signer could report a valid token while the
    # enforcement point saw nothing: exactly the failure recorded on 2026-06-17, where a
    # correctly signed off-agent token never surfaced at the path the gate reads and
    # nothing could tell that apart from an instruction never issued.
    #
    # So: re-resolve the destination the way the VERIFIER resolves it, read it back, and
    # run the real verification. Then record the outcome as a control_delivery
    # observation from the issuer's side.
    #
    # HONEST LIMIT: this proves readability *from here*. It cannot prove the artifact is
    # visible across a mount, namespace or container boundary — the enforcement point has
    # to say that from its own side. The pair of records is the evidence; neither half is.
    instruction_id, delivery = _attest_delivery(record, scope)
    record["instruction_id"] = instruction_id
    record["delivery"] = delivery
    return record


# --------------------------------------------------------------- C1: delivery evidence
# One control instruction, observed from one side. Mirrors the AIREP `control_delivery`
# profile so the issuer's and the enforcement point's observations can be compared by
# instruction_id: an issuer record with no matching enforcement-point record is the
# detectable failure. Never raises — evidence must not become a new way to fail.

DELIVERY_LOG = Path("~/.phionyx/state/control_delivery.jsonl").expanduser()


def _instruction_hash(record: dict) -> str:
    import hashlib
    canon = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(canon).hexdigest()


def _resolved(path: Path) -> str:
    try:
        return str(path.resolve())
    except Exception:
        return str(path)


def _mount_identity(path: Path) -> str:
    try:
        st = path.stat()
        return f"dev={st.st_dev}:ino={st.st_ino}"
    except Exception:
        return ""


def record_delivery_observation(**fields) -> None:
    """Append one control_delivery observation. Fail-open by contract."""
    try:
        import datetime
        fields.setdefault("observed_at",
                          datetime.datetime.now(datetime.timezone.utc).isoformat())
        DELIVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DELIVERY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(fields, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _attest_delivery(record: dict, scope: str) -> tuple[str, dict]:
    """Issuer-side readback. Returns (instruction_id, delivery-summary)."""
    ihash = _instruction_hash(record)
    instruction_id = "ovr-" + ihash.split(":", 1)[1][:16]
    resolved = _resolved(OVERRIDE_FILE)

    record_delivery_observation(
        instruction_id=instruction_id, instruction_hash=ihash, phase="issued",
        observed_by="issuer", channel="signed-file-override", boundary="mount",
        resolved_path=resolved,
        authority={"issuer_id": "ed25519:pinned", "writable_by_controlled_system": False},
    )

    # Read back through the verifier's own code path, not a private copy of it.
    ok, _claims = verify_override(scope)
    visible = False
    try:
        visible = OVERRIDE_FILE.exists()
    except Exception:
        pass

    if ok:
        record_delivery_observation(
            instruction_id=instruction_id, instruction_hash=ihash, phase="delivered",
            observed_by="issuer", channel="signed-file-override", boundary="mount",
            resolved_path=resolved, mount_identity=_mount_identity(OVERRIDE_FILE),
        )
        return instruction_id, {"readback": "ok", "resolved_path": resolved,
                                "note": "readable from the issuer side only; the "
                                        "enforcement point must confirm separately"}

    reason = ("absent at resolved_path" if not visible
              else "present but failed verification at resolved_path")
    record_delivery_observation(
        instruction_id=instruction_id, instruction_hash=ihash, phase="delivery_failed",
        observed_by="issuer", channel="signed-file-override", boundary="mount",
        resolved_path=resolved,
        failure={"reason": reason, "root_cause_isolated": False},
    )
    sys.stderr.write(
        f"control_override WARN: token written but readback FAILED at {resolved} "
        f"({reason}). The signature is valid; delivery is not established. Do not treat "
        "this as an authorised override until the enforcement point confirms it.\n"
    )
    return instruction_id, {"readback": "failed", "resolved_path": resolved,
                            "reason": reason}


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


def record_enforcement_acknowledgement(scope: str) -> None:
    """ENFORCEMENT-POINT side. Call this when a gate has read a token and ACTED on it.

    Only the success case is recorded. A gate that finds no token is the ordinary case —
    almost every check runs with no override present — so a miss carries no information
    and logging it would drown the signal. The detection works the other way round: an
    issuer record with no matching enforcement-point acknowledgement for the same
    instruction_id is the delivery failure. See delivery_audit().
    """
    try:
        record = json.loads(OVERRIDE_FILE.read_text())
        core = {k: record[k] for k in ("alg", "payload_b64", "sig_b64") if k in record}
        record_delivery_observation(
            instruction_id=record.get("instruction_id") or
            ("ovr-" + _instruction_hash(core).split(":", 1)[1][:16]),
            instruction_hash=_instruction_hash(core),
            phase="acknowledged", observed_by="enforcement_point",
            channel="signed-file-override", boundary="mount",
            resolved_path=_resolved(OVERRIDE_FILE),
            mount_identity=_mount_identity(OVERRIDE_FILE),
            scope=scope,
        )
    except Exception:
        pass


def delivery_audit() -> list[dict]:
    """Compare the two sides. Returns one entry per instruction the issuer recorded that
    no enforcement point ever acknowledged — the condition that is otherwise silent."""
    issued: dict[str, dict] = {}
    acked: set[str] = set()
    try:
        for line in DELIVERY_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            iid = r.get("instruction_id")
            if not iid:
                continue
            if r.get("observed_by") == "issuer" and r.get("phase") in ("issued", "delivered"):
                issued.setdefault(iid, r)
            elif r.get("observed_by") == "enforcement_point":
                acked.add(iid)
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return [{"instruction_id": iid,
             "issued_at": r.get("observed_at"),
             "resolved_path_issuer": r.get("resolved_path"),
             "finding": "issued but never acknowledged by an enforcement point"}
            for iid, r in issued.items() if iid not in acked]


# ----------------------------------------------------------------------------- cli
def _main(argv: list[str]) -> int:
    if "--delivery-audit" in argv:
        gaps = delivery_audit()
        if not gaps:
            print("delivery audit: no unacknowledged instructions")
            return 0
        print(f"delivery audit: {len(gaps)} instruction(s) issued but NEVER acknowledged "
              "by an enforcement point")
        for g in gaps:
            print(f"  {g['instruction_id']}  issued={g['issued_at']}  path={g['resolved_path_issuer']}")
        print("\nAn issued instruction with no enforcement-point record did not reach the "
              "component that enforces it, or that component never recorded reading it. "
              "Both are delivery failures; neither is 'no instruction was sent'.")
        return 3
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
