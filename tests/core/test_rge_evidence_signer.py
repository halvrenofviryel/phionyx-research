"""Phase-5 B1 — RGE Ed25519 evidence signer + independent verifier.

Proves the non-repudiation property the evidence claim needs: a signature made
by the producer verifies from a PUBLISHED PUBLIC KEY ALONE, and fails closed on
tamper, wrong key, or forgery.
"""

import pytest

crypto = pytest.importorskip("cryptography")  # noqa: F841

from phionyx_core.services.crypto.rge_evidence_signer import (  # noqa: E402
    SIG_PREFIX,
    RgeEd25519Signer,
    RgeEd25519Verifier,
    ed25519_available,
    verify_rge_signature,
)

HASH = "a" * 64  # a plausible sha256 chain-head hex


def test_backend_available():
    assert ed25519_available() is True


def test_sign_format_is_self_describing():
    s = RgeEd25519Signer()
    sig = s.sign(HASH)
    assert sig.startswith(SIG_PREFIX)
    # ed25519 signatures are 64 bytes -> 128 hex chars after the prefix
    assert len(sig[len(SIG_PREFIX):]) == 128


def test_roundtrip_signer_self_verify():
    s = RgeEd25519Signer()
    assert s.verify(HASH, s.sign(HASH)) is True


def test_independent_verify_from_published_public_key_only():
    """The core property: verify with ONLY the public key, no producer/private key."""
    s = RgeEd25519Signer()
    sig = s.sign(HASH)
    v = RgeEd25519Verifier(s.public_key_hex)   # built from pub hex alone
    assert v.verify(HASH, sig) is True
    assert verify_rge_signature(HASH, sig, s.public_key_hex) is True


def test_tampered_hash_fails_closed():
    s = RgeEd25519Signer()
    sig = s.sign(HASH)
    assert s.verify("b" * 64, sig) is False           # different content
    assert RgeEd25519Verifier(s.public_key_hex).verify("b" * 64, sig) is False


def test_wrong_key_fails_closed():
    producer = RgeEd25519Signer()
    attacker = RgeEd25519Signer()
    sig = producer.sign(HASH)
    # verifying a genuine producer signature against the ATTACKER's key must fail
    assert RgeEd25519Verifier(attacker.public_key_hex).verify(HASH, sig) is False


def test_forged_and_malformed_signatures_fail_closed():
    s = RgeEd25519Signer()
    pub = s.public_key_hex
    for bad in [
        "ed25519:deadbeef",                 # right prefix, garbage/short body
        "demo-hmac:0123456789abcdef",       # a demo-HMAC sig must NOT verify as ed25519
        "not-a-signature",
        "",
        SIG_PREFIX + "zz" * 64,             # non-hex body
    ]:
        assert verify_rge_signature(HASH, bad, pub) is False


def test_seed_hex_is_deterministic():
    """Same seed -> same key -> a signature from one verifies under the other
    (decision-keyed determinism for replay)."""
    from cryptography.hazmat.primitives import serialization

    s1 = RgeEd25519Signer()
    seed = s1._priv.private_bytes(  # noqa: SLF001 - test reaches in intentionally
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    ).hex()
    s2 = RgeEd25519Signer(seed_hex=seed)
    assert s1.public_key_hex == s2.public_key_hex
    assert s2.verify(HASH, s1.sign(HASH)) is True


def test_load_or_generate_persists_and_reloads(tmp_path):
    priv = tmp_path / "keys" / "evidence_ed25519"
    pub = tmp_path / "pub" / "evidence_ed25519.pub"
    s1 = RgeEd25519Signer.load_or_generate(priv, pub)
    assert priv.exists() and pub.exists()
    assert pub.read_text().strip() == s1.public_key_hex
    # reload uses the same persisted key
    s2 = RgeEd25519Signer.load_or_generate(priv, pub)
    assert s2.public_key_hex == s1.public_key_hex
    assert s2.verify(HASH, s1.sign(HASH)) is True
