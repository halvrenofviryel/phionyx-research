"""
Ed25519 Audit Signer — v4 §6
================================

Signs audit records with Ed25519 digital signatures
for immutable audit trail integrity.

Requires: pip install PyNaCl (or cryptography)
Falls back to HMAC-SHA256 if Ed25519 is not available.
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Ed25519 from cryptography or nacl
_ED25519_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,  # noqa: F401
    )
    from cryptography.hazmat.primitives import serialization
    _ED25519_AVAILABLE = True
except ImportError:
    logger.info("cryptography package not available — falling back to HMAC-SHA256")


class Ed25519Signer:
    """
    Ed25519 digital signature service.

    Used to sign AuditRecord hashes for tamper-proof audit trail.
    Falls back to HMAC-SHA256 if Ed25519 library is not installed.
    """

    def __init__(self, private_key_hex: Optional[str] = None):
        """
        Initialize signer.

        Args:
            private_key_hex: Hex-encoded Ed25519 private key seed (32 bytes).
                            If None, generates a new key pair.
        """
        self._ed25519 = _ED25519_AVAILABLE
        self._private_key = None
        self._public_key = None
        self._public_key_hex = ""
        self._hmac_key = os.urandom(32)

        if self._ed25519:
            if private_key_hex:
                seed = bytes.fromhex(private_key_hex)
                self._private_key = Ed25519PrivateKey.from_private_bytes(seed)
            else:
                self._private_key = Ed25519PrivateKey.generate()

            self._public_key = self._private_key.public_key()
            self._public_key_hex = self._public_key.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ).hex()
        else:
            # HMAC fallback
            if private_key_hex:
                self._hmac_key = bytes.fromhex(private_key_hex)
            self._public_key_hex = hashlib.sha256(self._hmac_key).hexdigest()[:64]

    def sign(self, data: str) -> str:
        """
        Sign data and return hex-encoded signature.

        Args:
            data: String data to sign (typically record_hash)

        Returns:
            Hex-encoded signature
        """
        data_bytes = data.encode("utf-8")

        if self._ed25519 and self._private_key:
            signature = self._private_key.sign(data_bytes)
            return signature.hex()
        else:
            # HMAC-SHA256 fallback
            mac = hmac.new(self._hmac_key, data_bytes, hashlib.sha256)
            return mac.hexdigest()

    def verify(self, data: str, signature_hex: str) -> bool:
        """
        Verify a signature.

        Args:
            data: Original data that was signed
            signature_hex: Hex-encoded signature

        Returns:
            True if valid, False otherwise
        """
        data_bytes = data.encode("utf-8")

        try:
            if self._ed25519 and self._public_key:
                sig_bytes = bytes.fromhex(signature_hex)
                self._public_key.verify(sig_bytes, data_bytes)
                return True
            else:
                # HMAC verification
                expected = hmac.new(self._hmac_key, data_bytes, hashlib.sha256).hexdigest()
                return hmac.compare_digest(expected, signature_hex)
        except Exception:
            return False

    @property
    def public_key_hex(self) -> str:
        """Get hex-encoded public key."""
        return self._public_key_hex

    @property
    def is_ed25519(self) -> bool:
        """Whether real Ed25519 is being used (vs HMAC fallback)."""
        return self._ed25519
