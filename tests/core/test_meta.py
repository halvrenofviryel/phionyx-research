"""
Unit Tests: Meta-Cognition Module
==================================

Tests for:
- Confidence estimation formula
- Threshold behavior (block, hedge, proceed)
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-meta" / "src"))

try:
    from phionyx_core.meta.estimator import ConfidenceEstimator
    META_AVAILABLE = True
except ImportError:
    META_AVAILABLE = False
    pytest.skip("Meta-Cognition SDK not available", allow_module_level=True)


class TestConfidenceEstimator:
    """Test confidence estimation."""

    def test_confidence_calculation(self):
        """Test confidence calculation formula."""
        estimator = ConfidenceEstimator()

        # High confidence case: low entropy, high similarity
        confidence_result = estimator.estimate_confidence(
            physics_state={"entropy": 0.3, "phi": 0.8},  # Low entropy, high phi
            memory_similarity=0.9,
            input_length=50
        )
        # In test mode, returns float directly
        confidence = confidence_result if isinstance(confidence_result, float) else confidence_result.confidence_score
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.6  # Should be high confidence

    def test_low_confidence_anomaly(self):
        """Test low confidence for semantic anomalies."""
        estimator = ConfidenceEstimator()

        # Low similarity (semantic anomaly)
        confidence_result = estimator.estimate_confidence(
            physics_state={"entropy": 0.5, "phi": 0.5},
            memory_similarity=0.3,  # Low similarity
            input_length=10
        )
        confidence = confidence_result if isinstance(confidence_result, float) else confidence_result.confidence_score
        assert confidence < 0.5  # Should be low confidence

    def test_confidence_thresholds(self):
        """Test confidence threshold behavior."""
        estimator = ConfidenceEstimator()

        # Block threshold (< 0.4)
        confidence_result = estimator.estimate_confidence(
            physics_state={"entropy": 0.9, "phi": 0.2},
            memory_similarity=0.2,
            input_length=5
        )
        confidence = confidence_result if isinstance(confidence_result, float) else confidence_result.confidence_score
        assert confidence < 0.4  # Should trigger block

        # Hedge threshold (0.4 - 0.6)
        confidence_result = estimator.estimate_confidence(
            physics_state={"entropy": 0.6, "phi": 0.5},
            memory_similarity=0.5,
            input_length=20
        )
        confidence = confidence_result if isinstance(confidence_result, float) else confidence_result.confidence_score
        assert 0.4 <= confidence <= 0.6  # Should trigger hedge

        # Proceed threshold (> 0.6)
        confidence_result = estimator.estimate_confidence(
            physics_state={"entropy": 0.3, "phi": 0.8},
            memory_similarity=0.8,
            input_length=50
        )
        confidence = confidence_result if isinstance(confidence_result, float) else confidence_result.confidence_score
        assert confidence > 0.6  # Should proceed

