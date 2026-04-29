"""
Edge-case tests for core physics formulas.
===========================================

Tests boundary values, extreme inputs, and determinism for:
- calculate_phi_v2_1 (Hybrid Resonance Model)
- calculate_phi_cognitive (Cognitive Resonance)
- calculate_phi_physical (Physical Resonance)

Verifies:
- All outputs are within documented ranges
- Determinism: same inputs always produce same outputs
- Edge cases at boundary values

Issue: https://github.com/halvrenofviryel/phionyx-research/issues/13
"""
import math

import pytest

from phionyx_core.physics.formulas import (
    calculate_phi_v2_1,
    calculate_phi_cognitive,
    calculate_phi_physical,
)
from phionyx_core.physics.constants import (
    PHI_MIN,
    PHI_MAX,
)


class TestCalculatePhiV21EdgeCases:
    """Edge-case tests for calculate_phi_v2_1 (Hybrid Resonance Model)."""

    def test_all_zero_inputs(self):
        """All-zero inputs (A=0, V=0, H=0) should not crash and phi >= 0.

        Note: time_delta=0.0 is safe here because calculate_phi_physical
        uses exponential decay (A * e^(-γt)), not division. At t=0 the
        exponent evaluates to e^0 = 1, so no division-by-zero occurs.
        """
        result = calculate_phi_v2_1(
            valence=0.0,
            arousal=0.0,
            amplitude=0.0,
            time_delta=0.0,
            gamma=0.15,
            stability=0.0,
            entropy=0.0,
            w_c=0.75,
            w_p=0.25,
        )
        assert "phi" in result
        assert result["phi"] >= 0.0
        assert not math.isnan(result["phi"])

    def test_maximum_values(self):
        """Maximum values (A=1.0, V=1.0, H=1.0) should produce valid phi."""
        result = calculate_phi_v2_1(
            valence=1.0,
            arousal=1.0,
            amplitude=10.0,
            time_delta=0.1,
            gamma=0.15,
            stability=1.0,
            entropy=1.0,
            w_c=0.75,
            w_p=0.25,
        )
        assert "phi" in result
        assert PHI_MIN <= result["phi"] <= PHI_MAX
        assert not math.isnan(result["phi"])

    def test_negative_valence(self):
        """Negative valence (V=-1.0) should still produce positive phi.

        v2.2 'Base Life Support' fix ensures negative emotions create
        resonance instead of collapsing Phi to zero.
        """
        result = calculate_phi_v2_1(
            valence=-1.0,
            arousal=0.5,
            amplitude=5.0,
            time_delta=0.1,
            gamma=0.15,
            stability=0.9,
            entropy=0.3,
            w_c=0.75,
            w_p=0.25,
        )
        assert result["phi"] > 0.0, "Negative valence should not collapse phi to zero"
        assert result["phi_cognitive"] >= 0.05, "Phi minimum floor should prevent collapse"

    def test_very_small_time_delta(self):
        """Very small time_delta (0.001) should produce valid output without overflow."""
        result = calculate_phi_v2_1(
            valence=0.5,
            arousal=0.5,
            amplitude=5.0,
            time_delta=0.001,
            gamma=0.15,
            stability=0.9,
            entropy=0.3,
            w_c=0.75,
            w_p=0.25,
        )
        assert result["phi"] >= 0.0
        assert not math.isnan(result["phi"])
        assert not math.isinf(result["phi"])

    def test_very_large_amplitude(self):
        """Very large amplitude (100.0) should be clamped internally, not crash."""
        result = calculate_phi_v2_1(
            valence=0.5,
            arousal=0.5,
            amplitude=100.0,
            time_delta=0.1,
            gamma=0.15,
            stability=0.9,
            entropy=0.3,
            w_c=0.75,
            w_p=0.25,
        )
        assert "phi" in result
        assert PHI_MIN <= result["phi"] <= PHI_MAX

    def test_weights_not_summing_to_one(self):
        """Weights that don't sum to 1.0 should be normalized automatically."""
        result = calculate_phi_v2_1(
            valence=0.5,
            arousal=0.5,
            amplitude=5.0,
            time_delta=0.1,
            gamma=0.15,
            stability=0.9,
            entropy=0.3,
            w_c=0.5,
            w_p=0.8,
        )
        # Should normalize weights, not crash
        assert result["phi"] >= 0.0
        # Verify weights were normalized to sum to ~1.0
        assert abs(result["weight_cognitive"] + result["weight_physical"] - 1.0) < 0.01


class TestPhiCognitiveEdgeCases:
    """Edge-case tests for calculate_phi_cognitive."""

    def test_minimum_floor(self):
        """Phi cognitive has a 0.05 minimum floor (Base Life Support).

        Even with worst-case inputs (high entropy, zero stability),
        the minimum floor prevents total collapse.
        """
        result = calculate_phi_cognitive(
            entropy=1.0, stability=0.0, valence=0.0
        )
        assert result >= 0.05, "Minimum floor (0.05) should prevent total collapse"

    @pytest.mark.parametrize("valence", [-1.0, -0.5, 0.0, 0.5, 1.0])
    def test_output_range_across_valence(self, valence: float):
        """Phi cognitive should always be in [0.0, 1.0] for any valence."""
        result = calculate_phi_cognitive(
            entropy=0.5, stability=0.8, valence=valence
        )
        assert 0.0 <= result <= 1.0, f"Out of range for valence={valence}: {result}"


class TestPhiPhysicalEdgeCases:
    """Edge-case tests for calculate_phi_physical."""

    @pytest.mark.parametrize("amplitude", [0.0, 1.0, 5.0, 10.0])
    def test_output_non_negative(self, amplitude: float):
        """Phi physical should always be >= 0 for any valid amplitude."""
        result = calculate_phi_physical(
            amplitude=amplitude, time_delta=1.0,
            gamma=0.15, arousal=0.5,
        )
        assert result >= 0.0, f"Negative result for amplitude={amplitude}: {result}"


class TestDeterminism:
    """Verify determinism: same inputs must always produce the exact same outputs."""

    def test_phi_v2_1_determinism(self):
        """calculate_phi_v2_1 should be deterministic: same inputs → same outputs."""
        kwargs = dict(
            valence=0.5,
            arousal=0.7,
            amplitude=5.0,
            time_delta=1.0,
            gamma=0.15,
            stability=0.9,
            entropy=0.3,
            w_c=0.75,
            w_p=0.25,
        )
        result1 = calculate_phi_v2_1(**kwargs)
        result2 = calculate_phi_v2_1(**kwargs)
        assert result1["phi"] == result2["phi"], "Phi must be deterministic"
        assert result1["phi_cognitive"] == result2["phi_cognitive"]
        assert result1["phi_physical"] == result2["phi_physical"]

    def test_phi_cognitive_determinism(self):
        """calculate_phi_cognitive should be deterministic."""
        r1 = calculate_phi_cognitive(entropy=0.5, stability=0.8, valence=0.3)
        r2 = calculate_phi_cognitive(entropy=0.5, stability=0.8, valence=0.3)
        assert r1 == r2, "Phi cognitive must be deterministic"


class TestOutputRanges:
    """Verify all outputs are within documented ranges."""

    def test_phi_total_within_bounds(self):
        """Total phi should always be within [PHI_MIN, PHI_MAX]."""
        result = calculate_phi_v2_1(
            valence=0.8,
            arousal=0.9,
            amplitude=9.0,
            time_delta=0.1,
            gamma=0.1,
            stability=0.95,
            entropy=0.1,
            w_c=0.6,
            w_p=0.4,
        )
        assert PHI_MIN <= result["phi"] <= PHI_MAX

    def test_worst_case_non_negative(self):
        """Even with worst-case inputs, phi should never be negative."""
        result = calculate_phi_v2_1(
            valence=-1.0,
            arousal=0.0,
            amplitude=0.0,
            time_delta=100.0,
            gamma=0.5,
            stability=0.0,
            entropy=1.0,
            w_c=0.5,
            w_p=0.5,
        )
        assert result["phi"] >= 0.0, "Phi should never be negative"
        assert not math.isnan(result["phi"]), "Phi should never be NaN"
