"""
Tests for Risk Vector Normalization — Patent SF2-7
====================================================

Proves normalize_risk_vector produces [0,1] range output.
"""

import pytest

from phionyx_core.governance.deliberative_ethics import normalize_risk_vector


class TestNormalizeRiskVector:
    """SF2-7: Risk vector min-max normalization to [0, 1]."""

    def test_basic_normalization(self):
        """Values mapped to [0, 1] via min-max."""
        result = normalize_risk_vector([10.0, 20.0, 30.0])
        assert result == pytest.approx([0.0, 0.5, 1.0])

    def test_already_normalized(self):
        """Values already in [0,1] stay correct."""
        result = normalize_risk_vector([0.0, 0.5, 1.0])
        assert result == pytest.approx([0.0, 0.5, 1.0])

    def test_single_value(self):
        """Single value clamped to [0, 1]."""
        assert normalize_risk_vector([0.7]) == pytest.approx([0.7])
        assert normalize_risk_vector([1.5]) == pytest.approx([1.0])
        assert normalize_risk_vector([-0.3]) == pytest.approx([0.0])

    def test_all_same_values(self):
        """All equal values → uniform 0.5."""
        result = normalize_risk_vector([5.0, 5.0, 5.0])
        assert result == pytest.approx([0.5, 0.5, 0.5])

    def test_empty_list(self):
        """Empty list returns empty."""
        assert normalize_risk_vector([]) == []

    def test_negative_values(self):
        """Negative values handled correctly."""
        result = normalize_risk_vector([-10.0, 0.0, 10.0])
        assert result == pytest.approx([0.0, 0.5, 1.0])

    def test_result_in_bounds(self):
        """All results in [0, 1] range."""
        result = normalize_risk_vector([100.0, -50.0, 0.0, 200.0, -100.0])
        for v in result:
            assert 0.0 <= v <= 1.0, f"Value {v} out of [0,1]"

    def test_two_values(self):
        """Two values normalize to 0 and 1."""
        result = normalize_risk_vector([3.0, 7.0])
        assert result == pytest.approx([0.0, 1.0])
