"""
Echo Self Threshold Guard Unit Tests
=====================================

Tests for EchoSelfThresholdGuard — phi threshold monitoring + reset mechanism.

Markers: @pytest.mark.safety, @pytest.mark.critical, @pytest.mark.unit
"""

import pytest
from phionyx_core.cep import (
    EchoSelfThresholdGuard,
    CEPResult,
    CEPMetrics,
    CEPThresholds,
    CEPFlags,
)


@pytest.fixture
def guard():
    """Default guard with standard thresholds."""
    return EchoSelfThresholdGuard(
        phi_threshold=0.72,
        echo_density_threshold=0.5,
        max_self_reference_ratio=0.3,
    )


def _make_cep_result(
    phi_echo_quality=0.5,
    phi_echo_density=0.3,
    self_reference_ratio=0.1,
    **kwargs,
):
    """Helper to create a CEPResult with given metric overrides."""
    metrics = CEPMetrics(
        phi_echo_quality=phi_echo_quality,
        phi_echo_density=phi_echo_density,
        echo_stability=kwargs.get("echo_stability", 0.8),
        temporal_delay=kwargs.get("temporal_delay", 0.0),
        self_reference_ratio=self_reference_ratio,
        trauma_language_score=kwargs.get("trauma_language_score", 0.0),
        mirror_self_score=kwargs.get("mirror_self_score", 0.0),
        variation_novelty_score=kwargs.get("variation_novelty_score", 1.0),
    )
    return CEPResult(
        metrics=metrics,
        thresholds=CEPThresholds(),
        flags=CEPFlags(),
        notes=[],
    )


@pytest.mark.unit
@pytest.mark.safety
@pytest.mark.critical
class TestEchoSelfThresholdGuard:
    """Tests for EchoSelfThresholdGuard threshold checking and reset."""

    def test_below_threshold_passthrough(self, guard):
        """Below-threshold metrics should pass through unchanged."""
        result = _make_cep_result(phi_echo_quality=0.5, self_reference_ratio=0.1)
        guarded = guard.check_and_guard(result)
        assert not guarded.flags.is_self_narrative_blocked
        assert guarded.sanitized_text is None

    def test_phi_and_self_ref_triggers_guard(self, guard):
        """High phi + high self-reference should trigger guard."""
        result = _make_cep_result(
            phi_echo_quality=0.8,  # > 0.72 threshold
            self_reference_ratio=0.4,  # > 0.3 threshold
            phi_echo_density=0.3,  # below threshold
        )
        guarded = guard.check_and_guard(result)
        assert guarded.flags.is_self_narrative_blocked
        assert guarded.sanitized_text is not None

    def test_phi_and_echo_density_triggers_guard(self, guard):
        """High phi + high echo density should trigger guard."""
        result = _make_cep_result(
            phi_echo_quality=0.8,  # > 0.72
            self_reference_ratio=0.1,  # below threshold
            phi_echo_density=0.6,  # > 0.5 threshold
        )
        guarded = guard.check_and_guard(result)
        assert guarded.flags.is_self_narrative_blocked
        assert guarded.sanitized_text is not None

    def test_all_exceeded_triggers_hard_reset(self, guard):
        """All three thresholds exceeded should trigger hard reset."""
        result = _make_cep_result(
            phi_echo_quality=0.9,
            self_reference_ratio=0.5,
            phi_echo_density=0.7,
        )
        guarded = guard.check_and_guard(result)
        assert guarded.flags.requires_hard_reset
        assert guarded.sanitized_text is not None
        assert any("Hard reset" in n for n in guarded.notes)

    def test_unified_state_phi_normalization(self, guard):
        """Phi from unified_state (0-10 range) should be normalized to 0-1."""
        result = _make_cep_result(
            phi_echo_quality=0.5,  # below threshold alone
            self_reference_ratio=0.4,
        )
        # unified_state phi=8.0 → normalized to 0.8 → exceeds 0.72
        guarded = guard.check_and_guard(result, unified_state={"phi": 8.0})
        assert guarded.flags.is_self_narrative_blocked
