"""
Envelope Validator — Composed Validation Orchestrator
=====================================================

Patent SF2-22: Composed validation engine for AgentMessageEnvelope.
Runs 4 checks in sequence:
  1. TTL expiry (semantic freshness)
  2. Nonce uniqueness (replay protection)
  3. Causal chain (per-participant turn_id monotonicity)
  4. Cognitive integrity (phi/entropy/coherence thresholds)
"""

from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from phionyx_core.contracts.envelopes.agent_envelope import AgentMessageEnvelope
from phionyx_core.contracts.envelopes.causal_chain_tracker import CausalChainTracker


class EnvelopeValidationResult(BaseModel):
    """Composite result from all validation checks."""
    valid: bool = Field(..., description="True if all checks passed")
    checks_passed: list[str] = Field(default_factory=list, description="Names of passed checks")
    checks_failed: list[str] = Field(default_factory=list, description="Names of failed checks")
    details: dict[str, Any] = Field(default_factory=dict, description="Per-check detail messages")


class EnvelopeValidator:
    """Composed validation orchestrator for AgentMessageEnvelope (Patent SF2-22).

    Composes 4 independent validation checks into a single validate() call:
    1. TTL expiry — rejects expired envelopes
    2. Nonce uniqueness — rejects replayed envelopes
    3. Causal chain — rejects out-of-order turn_ids per participant
    4. Cognitive integrity — rejects envelopes with degraded cognitive state
    """

    def __init__(
        self,
        causal_tracker: CausalChainTracker | None = None,
        nonce_store_max: int = 10000,
        min_phi: float = 0.0,
        max_entropy: float = 1.0,
        min_coherence: float = 0.0,
    ):
        self._causal_tracker = causal_tracker or CausalChainTracker()
        self._nonce_order: deque[str] = deque(maxlen=nonce_store_max)
        self._seen_nonces: set[str] = set()
        self._nonce_store_max = nonce_store_max
        self._min_phi = min_phi
        self._max_entropy = max_entropy
        self._min_coherence = min_coherence

    def validate(self, envelope: AgentMessageEnvelope) -> EnvelopeValidationResult:
        """Run all 4 checks and return composite result."""
        checks = [
            ("ttl_expiry", self._check_ttl),
            ("nonce_uniqueness", self._check_nonce),
            ("causal_chain", self._check_causal),
            ("cognitive_integrity", self._check_cognitive),
        ]

        passed: list[str] = []
        failed: list[str] = []
        details: dict[str, Any] = {}

        for name, check_fn in checks:
            ok, detail = check_fn(envelope)
            if ok:
                passed.append(name)
            else:
                failed.append(name)
            details[name] = detail

        return EnvelopeValidationResult(
            valid=len(failed) == 0,
            checks_passed=passed,
            checks_failed=failed,
            details=details,
        )

    def _check_ttl(self, envelope: AgentMessageEnvelope) -> tuple[bool, str]:
        """Check envelope is not expired."""
        if envelope.is_expired():
            return False, "Envelope TTL expired"
        return True, "TTL valid"

    def _check_nonce(self, envelope: AgentMessageEnvelope) -> tuple[bool, str]:
        """Check nonce has not been seen before (replay protection)."""
        nonce = envelope.nonce
        if nonce in self._seen_nonces:
            return False, f"Duplicate nonce: {nonce}"

        # Record nonce with FIFO eviction
        if len(self._seen_nonces) >= self._nonce_store_max:
            oldest = self._nonce_order.popleft()
            self._seen_nonces.discard(oldest)

        self._seen_nonces.add(nonce)
        self._nonce_order.append(nonce)
        return True, "Nonce unique"

    def _check_causal(self, envelope: AgentMessageEnvelope) -> tuple[bool, str]:
        """Check per-participant turn_id monotonicity."""
        participant_id = envelope.sender_participant_ref.id
        violation = self._causal_tracker.validate_and_record(
            participant_id, envelope.turn_id
        )
        if violation is not None:
            return False, (
                f"Causal violation: participant={violation.participant_id}, "
                f"expected>={violation.expected_min_turn_id}, "
                f"got={violation.received_turn_id}"
            )
        return True, "Causal chain valid"

    def _check_cognitive(self, envelope: AgentMessageEnvelope) -> tuple[bool, str]:
        """Check cognitive integrity thresholds."""
        if not envelope.validate_cognitive_integrity(
            min_phi=self._min_phi,
            max_entropy=self._max_entropy,
            min_coherence=self._min_coherence,
        ):
            return False, "Cognitive integrity check failed"
        return True, "Cognitive integrity valid"
