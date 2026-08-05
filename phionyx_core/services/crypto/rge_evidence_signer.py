"""
RGE Evidence Signer — Ed25519 non-repudiable signing for the runtime evidence chain
====================================================================================

Provides real Ed25519 signing for the runtime evidence chain (the non-repudiable
upgrade from the demo HMAC signer).

The RGE / AIREP evidence envelope is signed today by a **demo HMAC** signer
(``phionyx_mcp_server.audit_chain.HmacSigner`` → ``demo-hmac:<16hex>``). HMAC is a
*symmetric* MAC: anyone holding the shared secret can forge it, so it proves
*tamper-evidence* (via the hash chain) but **not non-repudiation**. This module
provides the real thing: Ed25519 asymmetric signatures over the envelope chain
head, verifiable from a **published PUBLIC key alone** — the producer's private
key is never needed to verify, which is exactly the "don't trust the producer"
property the evidence claim requires.

Two objects, matching the ``audit_chain`` structural protocols
(``sign(current_hash: str) -> str`` / ``verify(current_hash, signature) -> bool``):

- :class:`RgeEd25519Signer` — holds a private key (inject one, or load-or-generate
  and persist), signs the chain head. Produces a self-describing ``ed25519:<hex>``
  signature so a mixed chain can dispatch by prefix.
- :class:`RgeEd25519Verifier` — holds only a **public key**; verifies. This is the
  standalone object a third party (or the B3 verifier CLI) runs to re-check any
  ``ed25519:``-signed envelope without trusting — or even contacting — the producer.

Core-boundary safe: stdlib + ``cryptography`` only (already used by
``ed25519_signer.py`` and the control plane). No delivery-framework imports. The
mcp-server companion imports this (it already depends on ``phionyx-core``); the
one-line default swap lives there (an off-agent patch, since the producer surface
is read-only to the agent by design).
"""

from __future__ import annotations

import os
from pathlib import Path

SIG_PREFIX = "ed25519:"
SIG_ALG = "Ed25519"

# Evidence signing key lives in its OWN trust domain, separate from the
# control-plane key (``control_ed25519``): the evidence producer legitimately
# holds its signing key (it signs its own decisions); third parties verify with
# the published public key. Paths are env-overridable for tests / deployment.
_KEY_DIR = Path(os.environ.get("PHIONYX_EVIDENCE_KEY_DIR", "~/.phionyx/keys")).expanduser()
_PUB_DIR = Path(os.environ.get("PHIONYX_EVIDENCE_PUB_DIR", "~/.phionyx/pub")).expanduser()
DEFAULT_PRIV_PATH = _KEY_DIR / "evidence_ed25519"
DEFAULT_PUB_PATH = _PUB_DIR / "evidence_ed25519.pub"

try:  # pragma: no cover - import guard
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )

    _ED25519_AVAILABLE = True
except ImportError:  # pragma: no cover - environment without cryptography
    _ED25519_AVAILABLE = False


class Ed25519Unavailable(RuntimeError):
    """Raised when Ed25519 signing is requested but ``cryptography`` is absent.

    Callers that need a graceful degradation should catch this and fall back to
    the demo HMAC signer *explicitly* — the evidence layer must never *silently*
    downgrade to a non-repudiable-looking signature it cannot actually produce.
    """


def _pub_hex(pub: Ed25519PublicKey) -> str:
    return pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()


def verify_rge_signature(current_hash: str, signature: str, public_key_hex: str) -> bool:
    """Verify one ``ed25519:<hex>`` signature over ``current_hash`` against a
    published public key. Pure function — the heart of independent verification.

    Returns ``False`` (never raises) on any malformation, wrong key, tamper, or
    missing library, so it is safe to call on untrusted input.
    """
    if not _ED25519_AVAILABLE:
        return False
    if not isinstance(signature, str) or not signature.startswith(SIG_PREFIX):
        return False
    try:
        sig = bytes.fromhex(signature[len(SIG_PREFIX):])
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        pub.verify(sig, current_hash.encode("utf-8"))  # raises on invalid
        return True
    except Exception:
        return False


class RgeEd25519Signer:
    """Ed25519 signer for the RGE evidence chain head.

    Construct with an injected key (tests), a raw 32-byte seed hex, or nothing
    (generates an ephemeral key). Use :meth:`load_or_generate` for the persistent
    production key.
    """

    def __init__(
        self,
        *,
        private_key: Ed25519PrivateKey | None = None,
        seed_hex: str | None = None,
    ) -> None:
        if not _ED25519_AVAILABLE:
            raise Ed25519Unavailable("cryptography Ed25519 backend not available")
        if private_key is not None:
            self._priv = private_key
        elif seed_hex is not None:
            self._priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
        else:
            self._priv = Ed25519PrivateKey.generate()
        self._pub = self._priv.public_key()

    @classmethod
    def load_or_generate(
        cls,
        priv_path: str | os.PathLike[str] = DEFAULT_PRIV_PATH,
        pub_path: str | os.PathLike[str] = DEFAULT_PUB_PATH,
    ) -> RgeEd25519Signer:
        """Load the persistent evidence key, generating + persisting it on first use.

        Publishing the public key is best-effort: in the agent sandbox the ``pub``
        directory is a read-only bind, so a failed publish is non-fatal (the key
        still signs; the public key is published from the off-agent context).
        """
        priv_path = Path(priv_path)
        pub_path = Path(pub_path)
        if priv_path.exists():
            signer = cls(seed_hex=priv_path.read_text(encoding="utf-8").strip())
        else:
            signer = cls()
            priv_path.parent.mkdir(parents=True, exist_ok=True)
            seed = signer._priv.private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption(),
            )
            priv_path.write_text(seed.hex(), encoding="utf-8")
            try:
                os.chmod(priv_path, 0o600)  # no-op on NTFS; holds on ext4
            except OSError:
                pass
        try:
            pub_path.parent.mkdir(parents=True, exist_ok=True)
            pub_path.write_text(signer.public_key_hex, encoding="utf-8")
        except OSError:
            pass  # read-only pub dir (sandbox) — publish happens off-agent
        return signer

    @property
    def public_key_hex(self) -> str:
        return _pub_hex(self._pub)

    @property
    def alg(self) -> str:
        return SIG_ALG

    def sign(self, current_hash: str) -> str:
        """Sign the chain head; returns ``ed25519:<hex>``."""
        sig = self._priv.sign(current_hash.encode("utf-8"))
        return SIG_PREFIX + sig.hex()

    def verify(self, current_hash: str, signature: str) -> bool:
        return verify_rge_signature(current_hash, signature, self.public_key_hex)


class RgeEd25519Verifier:
    """Public-key-only verifier — the independent "don't trust the producer" object.

    Built from a published public key hex alone (no private key, no producer
    contact). This is what the B3 verifier CLI and any third party run.
    """

    def __init__(self, public_key_hex: str) -> None:
        if not _ED25519_AVAILABLE:
            raise Ed25519Unavailable("cryptography Ed25519 backend not available")
        # Fail fast on a malformed key so a verifier is never silently inert.
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        self._pub_hex = public_key_hex

    @property
    def public_key_hex(self) -> str:
        return self._pub_hex

    def verify(self, current_hash: str, signature: str) -> bool:
        return verify_rge_signature(current_hash, signature, self._pub_hex)


def ed25519_available() -> bool:
    """True iff the Ed25519 backend is importable (else callers must fall back)."""
    return _ED25519_AVAILABLE
