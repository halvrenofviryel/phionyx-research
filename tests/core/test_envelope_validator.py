"""
Tests for EnvelopeValidator — Patent SF2-22
Composed validation orchestrator: TTL + nonce + causal + cognitive.
"""

import pytest
from datetime import datetime, timezone, timedelta

from phionyx_core.contracts.envelopes.agent_envelope import (
    AgentMessageEnvelope,
    CognitiveMetrics,
)
from phionyx_core.contracts.envelopes.causal_chain_tracker import CausalChainTracker
from phionyx_core.contracts.envelopes.envelope_validator import (
    EnvelopeValidator,
    EnvelopeValidationResult,
)
from phionyx_core.contracts.participants import ParticipantRef, ParticipantType


def _make_envelope(
    turn_id=1,
    nonce=None,
    ttl_seconds=3600,
    timestamp_utc=None,
    cognitive_metrics=None,
    sender_id="agent_a",
):
    """Helper to create a valid envelope with customizable fields."""
    import secrets
    return AgentMessageEnvelope.create(
        protocol="generic-json",
        sender_participant_ref=ParticipantRef(id=sender_id, type=ParticipantType.AI_AGENT),
        receiver_participant_ref=ParticipantRef(id="agent_b", type=ParticipantType.AI_AGENT),
        trace_id="trace-001",
        turn_id=turn_id,
        payload={"message": "test"},
        ttl_seconds=ttl_seconds,
        nonce=nonce or secrets.token_hex(16),
        timestamp_utc=timestamp_utc or datetime.now(timezone.utc).isoformat(),
        cognitive_metrics=cognitive_metrics,
    )


class TestEnvelopeValidatorAllPass:
    """Valid envelopes pass all 4 checks."""

    def test_valid_envelope_passes_all(self):
        """A fresh, valid envelope passes all 4 checks."""
        validator = EnvelopeValidator()
        env = _make_envelope()
        result = validator.validate(env)
        assert result.valid is True
        assert len(result.checks_passed) == 4
        assert len(result.checks_failed) == 0

    def test_result_details_populated(self):
        """Result details contain messages for all 4 checks."""
        validator = EnvelopeValidator()
        result = validator.validate(_make_envelope())
        assert "ttl_expiry" in result.details
        assert "nonce_uniqueness" in result.details
        assert "causal_chain" in result.details
        assert "cognitive_integrity" in result.details


class TestTTLCheck:
    """TTL expiry check (check 1)."""

    def test_expired_envelope_fails_ttl(self):
        """Envelope with past timestamp + short TTL fails."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        env = _make_envelope(ttl_seconds=60, timestamp_utc=old_ts)
        validator = EnvelopeValidator()
        result = validator.validate(env)
        assert "ttl_expiry" in result.checks_failed

    def test_no_expiration_passes(self):
        """Envelope with ttl_seconds=0 never expires."""
        env = _make_envelope(ttl_seconds=0)
        validator = EnvelopeValidator()
        result = validator.validate(env)
        assert "ttl_expiry" in result.checks_passed


class TestNonceCheck:
    """Nonce uniqueness check (check 2)."""

    def test_duplicate_nonce_fails(self):
        """Same nonce used twice is rejected."""
        validator = EnvelopeValidator()
        env1 = _make_envelope(nonce="same-nonce-123", turn_id=1)
        env2 = _make_envelope(nonce="same-nonce-123", turn_id=2)
        validator.validate(env1)
        result = validator.validate(env2)
        assert "nonce_uniqueness" in result.checks_failed

    def test_nonce_store_eviction(self):
        """Old nonces evicted when max exceeded, allowing reuse."""
        validator = EnvelopeValidator(nonce_store_max=3)
        # Fill nonce store
        for i in range(1, 4):
            validator.validate(_make_envelope(nonce=f"nonce-{i}", turn_id=i))

        # Add a 4th — should evict nonce-1
        validator.validate(_make_envelope(nonce="nonce-4", turn_id=4))

        # nonce-1 should be reusable now
        result = validator.validate(_make_envelope(nonce="nonce-1", turn_id=5))
        assert "nonce_uniqueness" in result.checks_passed


class TestCausalCheck:
    """Causal chain check (check 3)."""

    def test_non_monotonic_turn_id_fails(self):
        """Decreasing turn_id for same participant fails causal check."""
        validator = EnvelopeValidator()
        validator.validate(_make_envelope(turn_id=5, sender_id="agent_a"))
        result = validator.validate(_make_envelope(turn_id=3, sender_id="agent_a"))
        assert "causal_chain" in result.checks_failed

    def test_different_participants_independent(self):
        """Different senders have independent causal chains."""
        validator = EnvelopeValidator()
        validator.validate(_make_envelope(turn_id=5, sender_id="agent_a"))
        result = validator.validate(_make_envelope(turn_id=1, sender_id="agent_b"))
        assert "causal_chain" in result.checks_passed


class TestCognitiveCheck:
    """Cognitive integrity check (check 4)."""

    def test_low_phi_fails(self):
        """Phi below threshold fails cognitive check."""
        validator = EnvelopeValidator(min_phi=0.5)
        env = _make_envelope(
            cognitive_metrics=CognitiveMetrics(phi=0.2, entropy=0.3, coherence=0.8)
        )
        result = validator.validate(env)
        assert "cognitive_integrity" in result.checks_failed

    def test_no_metrics_passes(self):
        """Envelope without cognitive_metrics passes (backward compatible)."""
        validator = EnvelopeValidator(min_phi=0.5)
        env = _make_envelope(cognitive_metrics=None)
        result = validator.validate(env)
        assert "cognitive_integrity" in result.checks_passed

    def test_default_thresholds_pass_all(self):
        """Default thresholds (0.0/1.0/0.0) accept any valid metrics."""
        validator = EnvelopeValidator()
        env = _make_envelope(
            cognitive_metrics=CognitiveMetrics(phi=0.01, entropy=0.99, coherence=0.01)
        )
        result = validator.validate(env)
        assert "cognitive_integrity" in result.checks_passed


class TestMultipleFailures:
    """Multiple checks can fail simultaneously."""

    def test_ttl_and_nonce_both_fail(self):
        """Expired envelope with duplicate nonce fails 2 checks."""
        validator = EnvelopeValidator()
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        env1 = _make_envelope(nonce="dup-nonce", ttl_seconds=60, timestamp_utc=old_ts, turn_id=1)
        # First validate to record nonce
        validator.validate(env1)
        # Second with same nonce + expired
        env2 = _make_envelope(nonce="dup-nonce", ttl_seconds=60, timestamp_utc=old_ts, turn_id=2)
        result = validator.validate(env2)
        assert result.valid is False
        assert "ttl_expiry" in result.checks_failed
        assert "nonce_uniqueness" in result.checks_failed


class TestValidatorWithSharedTracker:
    """Validator can share a CausalChainTracker instance."""

    def test_shared_tracker(self):
        """External tracker state is used by validator."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent_a", 10)  # Pre-seed
        validator = EnvelopeValidator(causal_tracker=tracker)
        result = validator.validate(_make_envelope(turn_id=5, sender_id="agent_a"))
        assert "causal_chain" in result.checks_failed
