"""
Unit Tests: Core Physics Module
================================

Tests for:
- Formula calculations (edge cases, NaN, overflow)
- Input clamping
- Phi bounds
- Resonance classification
"""
import pytest
import math
import sys
from pathlib import Path

# Add core-physics to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-physics" / "src"))

from phionyx_core.physics.formulas import (  # noqa: E402
    calculate_phi_v2,
    calculate_phi_cognitive,
    calculate_phi_physical,
    classify_resonance,
)
from phionyx_core.physics.constants import (  # noqa: E402
    PHI_MIN,
    PHI_MAX,
    ENTROPY_MIN,
    ENTROPY_MAX,
    AMPLITUDE_MIN,
    AMPLITUDE_MAX,
    GAMMA_MIN,
    GAMMA_MAX,
)


class TestPhysicsFormulas:
    """Test physics formula calculations."""

    def test_phi_cognitive_bounds(self):
        """Test phi_cognitive stays within bounds."""
        # Normal case (v2.1: includes valence, default 0.0)
        result = calculate_phi_cognitive(entropy=0.3, stability=0.7, valence=0.0)
        assert 0.0 <= result <= 1.0

        # Edge case: entropy = 0, stability = 1.0, valence = 0.0
        # v2.2+: phi_c = max{0, (V_eff * S) * (1-E*k)}
        # V_eff = base_resonance + (|V| * (1 - base_resonance))
        # With RE-optimized module-level base_resonance, |V| = 0.0
        # V_eff = base_resonance, phi_c = base_resonance * 1.0 * 1.0
        from phionyx_core.physics.formulas import base_resonance as br
        result = calculate_phi_cognitive(entropy=0.0, stability=1.0, valence=0.0)
        assert result == br  # v2.2+ formula with module-level base_resonance

        # Edge case: entropy = 1
        # v2.3+: Formül minimum floor (0.05) uygular, asla 0.0'a düşmez
        result = calculate_phi_cognitive(entropy=1.0, stability=0.5, valence=0.0)
        assert result >= 0.05  # Minimum floor prevents total collapse

    def test_phi_cognitive_input_clamping(self):
        """Test input clamping for phi_cognitive."""
        # Test negative entropy (should clamp to 0)
        result = calculate_phi_cognitive(entropy=-0.5, stability=0.5)
        assert result >= 0.0

        # Test entropy > 1 (should clamp to 1)
        result = calculate_phi_cognitive(entropy=1.5, stability=0.5)
        assert result <= 1.0

    def test_phi_physical_bounds(self):
        """Test phi_physical stays within bounds."""
        # Normal case
        result = calculate_phi_physical(amplitude=5.0, time_delta=1.0, gamma=0.15)
        assert result >= 0.0

        # Edge case: time_delta = 0
        result = calculate_phi_physical(amplitude=5.0, time_delta=0.0, gamma=0.15)
        assert result == 5.0

        # Edge case: large time_delta (should decay to near 0)
        result = calculate_phi_physical(amplitude=5.0, time_delta=100.0, gamma=0.15)
        assert result >= 0.0
        assert result < 0.1  # Should be very small

    def test_phi_physical_input_clamping(self):
        """Test input clamping for phi_physical."""
        # Test negative amplitude (should clamp)
        result = calculate_phi_physical(amplitude=-5.0, time_delta=1.0, gamma=0.15)
        assert result >= AMPLITUDE_MIN

        # Test amplitude > MAX (should clamp)
        result = calculate_phi_physical(amplitude=20.0, time_delta=1.0, gamma=0.15)
        assert result <= AMPLITUDE_MAX * math.exp(-GAMMA_MIN * 1.0)

    def test_phi_v2_total_bounds(self):
        """Test phi_total stays within [PHI_MIN, PHI_MAX]."""
        # Normal case
        result = calculate_phi_v2(
            entropy=0.3,
            stability=0.7,
            amplitude=5.0,
            time_delta=1.0,
            gamma=0.15,
            context_mode="DEFAULT"
        )
        assert PHI_MIN <= result["phi"] <= PHI_MAX

        # Edge case: high entropy
        result = calculate_phi_v2(
            entropy=0.95,
            stability=0.1,
            amplitude=1.0,
            time_delta=1.0,
            gamma=0.15,
            context_mode="DEFAULT"
        )
        assert PHI_MIN <= result["phi"] <= PHI_MAX

    def test_phi_v2_no_nan(self):
        """Test phi_v2 never returns NaN."""
        # Test with extreme values
        result = calculate_phi_v2(
            entropy=0.0,
            stability=0.0,
            amplitude=0.0,
            time_delta=0.0,
            gamma=0.0,
            context_mode="DEFAULT"
        )
        assert not math.isnan(result["phi"])
        assert not math.isinf(result["phi"])

    def test_classify_resonance(self):
        """Test resonance classification thresholds."""
        # High resonance
        assert classify_resonance(9.0) == "high"
        assert classify_resonance(8.0) == "high"

        # Medium resonance
        assert classify_resonance(7.0) == "medium"
        assert classify_resonance(5.0) == "medium"

        # Low resonance
        assert classify_resonance(3.0) == "low"
        assert classify_resonance(2.0) == "low"

        # Fractured
        assert classify_resonance(1.0) == "fractured"
        assert classify_resonance(0.0) == "fractured"

    def test_classify_resonance_bounds(self):
        """Test classification with out-of-bounds phi."""
        # Test negative (should clamp and return fractured)
        result = classify_resonance(-5.0)
        assert result in ["low", "fractured"]

        # Test very large (should clamp and return high)
        result = classify_resonance(100.0)
        assert result == "high"


class TestPhysicsContextModes:
    """Test physics behavior in different context modes."""

    def test_school_mode_weights(self):
        """Test SCHOOL mode uses high cognitive weight."""
        result = calculate_phi_v2(
            entropy=0.2,
            stability=0.9,
            amplitude=0.1,  # Very low amplitude to ensure cognitive dominates
            time_delta=10.0,  # Large time_delta so physical component decays significantly
            gamma=0.3,  # Higher gamma for faster decay
            context_mode="SCHOOL"
        )
        # SCHOOL mode should prioritize cognitive (stability) over physical (amplitude)
        assert result["weight_cognitive"] > result["weight_physical"]
        # With very low amplitude and large time_delta, cognitive should dominate
        assert result["phi_cognitive"] > result["phi_physical"]

    def test_game_mode_weights(self):
        """Test GAME mode uses high physical weight."""
        result = calculate_phi_v2(
            entropy=0.5,
            stability=0.5,
            amplitude=10.0,
            time_delta=0.1,
            gamma=0.1,
            context_mode="GAME"
        )
        # GAME mode should prioritize physical (amplitude) over cognitive
        assert result["weight_physical"] > result["weight_cognitive"]

