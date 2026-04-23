"""
Tests for CognitiveMetrics in AgentMessageEnvelope — Patent SF2-14
===================================================================

SF2-14: Envelope metadata includes typed cognitive state metrics
generated at message creation time, used for integrity checking.
"""

import pytest

from phionyx_core.contracts.envelopes.agent_envelope import (
    AgentMessageEnvelope,
    CognitiveMetrics,
)
from phionyx_core.contracts.participants import ParticipantRef, ParticipantType


def _make_envelope(cognitive_metrics=None):
    """Helper to create a valid envelope with optional cognitive metrics."""
    return AgentMessageEnvelope.create(
        protocol="generic-json",
        sender_participant_ref=ParticipantRef(id="agent_a", type=ParticipantType.AI_AGENT),
        receiver_participant_ref=ParticipantRef(id="agent_b", type=ParticipantType.AI_AGENT),
        trace_id="trace-001",
        turn_id=1,
        payload={"message": "test"},
        cognitive_metrics=cognitive_metrics,
    )


class TestCognitiveMetricsSchema:
    """CognitiveMetrics Pydantic model validates cognitive state."""

    def test_default_values(self):
        """Default metrics are all zero."""
        m = CognitiveMetrics()
        assert m.phi == 0.0
        assert m.entropy == 0.0
        assert m.coherence == 0.0
        assert m.trust is None
        assert m.w_final is None

    def test_valid_values(self):
        """All values within [0,1] accepted."""
        m = CognitiveMetrics(phi=0.7, entropy=0.3, coherence=0.85, trust=0.9, w_final=0.6)
        assert m.phi == 0.7
        assert m.trust == 0.9

    def test_out_of_range_rejected(self):
        """Values outside [0,1] are rejected by Pydantic."""
        with pytest.raises(Exception):
            CognitiveMetrics(phi=1.5)
        with pytest.raises(Exception):
            CognitiveMetrics(entropy=-0.1)


class TestEnvelopeCognitiveMetrics:
    """AgentMessageEnvelope with cognitive_metrics field."""

    def test_envelope_without_metrics(self):
        """Envelope works without cognitive_metrics (backward compatible)."""
        env = _make_envelope()
        assert env.cognitive_metrics is None

    def test_envelope_with_metrics(self):
        """Envelope carries structured cognitive metrics."""
        metrics = CognitiveMetrics(phi=0.6, entropy=0.4, coherence=0.8)
        env = _make_envelope(cognitive_metrics=metrics)

        assert env.cognitive_metrics is not None
        assert env.cognitive_metrics.phi == 0.6
        assert env.cognitive_metrics.entropy == 0.4
        assert env.cognitive_metrics.coherence == 0.8

    def test_to_dict_includes_metrics(self):
        """to_dict() serializes cognitive_metrics."""
        metrics = CognitiveMetrics(phi=0.5, entropy=0.3, coherence=0.7)
        env = _make_envelope(cognitive_metrics=metrics)
        d = env.to_dict()

        assert d["cognitive_metrics"] is not None
        assert d["cognitive_metrics"]["phi"] == 0.5
        assert d["cognitive_metrics"]["entropy"] == 0.3

    def test_to_dict_without_metrics(self):
        """to_dict() returns None for cognitive_metrics when absent."""
        env = _make_envelope()
        d = env.to_dict()
        assert d["cognitive_metrics"] is None

    def test_from_dict_round_trip(self):
        """from_dict() reconstructs cognitive_metrics."""
        metrics = CognitiveMetrics(phi=0.42, entropy=0.18, coherence=0.91)
        env = _make_envelope(cognitive_metrics=metrics)
        d = env.to_dict()

        env2 = AgentMessageEnvelope.from_dict(d)
        assert env2.cognitive_metrics is not None
        assert env2.cognitive_metrics.phi == pytest.approx(0.42)
        assert env2.cognitive_metrics.coherence == pytest.approx(0.91)

    def test_from_dict_without_metrics(self):
        """from_dict() handles missing cognitive_metrics gracefully."""
        env = _make_envelope()
        d = env.to_dict()
        del d["cognitive_metrics"]  # Simulate old format

        env2 = AgentMessageEnvelope.from_dict(d)
        assert env2.cognitive_metrics is None


class TestCognitiveIntegrityCheck:
    """validate_cognitive_integrity() checks embedded metrics."""

    def test_no_metrics_passes(self):
        """No metrics → passes integrity check (lenient)."""
        env = _make_envelope()
        assert env.validate_cognitive_integrity() is True

    def test_valid_metrics_pass(self):
        """Metrics within bounds pass integrity check."""
        metrics = CognitiveMetrics(phi=0.5, entropy=0.3, coherence=0.8)
        env = _make_envelope(cognitive_metrics=metrics)
        assert env.validate_cognitive_integrity(
            min_phi=0.1, max_entropy=0.5, min_coherence=0.6
        ) is True

    def test_low_phi_fails(self):
        """Phi below min_phi fails integrity check."""
        metrics = CognitiveMetrics(phi=0.05, entropy=0.3, coherence=0.8)
        env = _make_envelope(cognitive_metrics=metrics)
        assert env.validate_cognitive_integrity(min_phi=0.1) is False

    def test_high_entropy_fails(self):
        """Entropy above max_entropy fails integrity check."""
        metrics = CognitiveMetrics(phi=0.5, entropy=0.9, coherence=0.8)
        env = _make_envelope(cognitive_metrics=metrics)
        assert env.validate_cognitive_integrity(max_entropy=0.7) is False

    def test_low_coherence_fails(self):
        """Coherence below min_coherence fails integrity check."""
        metrics = CognitiveMetrics(phi=0.5, entropy=0.3, coherence=0.2)
        env = _make_envelope(cognitive_metrics=metrics)
        assert env.validate_cognitive_integrity(min_coherence=0.5) is False

    def test_default_thresholds_pass_all(self):
        """Default thresholds (0/1/0) pass any valid metrics."""
        metrics = CognitiveMetrics(phi=0.01, entropy=0.99, coherence=0.01)
        env = _make_envelope(cognitive_metrics=metrics)
        assert env.validate_cognitive_integrity() is True
