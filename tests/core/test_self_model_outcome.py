"""
SelfModel Outcome Tracking Tests
==================================

Tests for feedback channel 1: Reflect → UpdateSelfModel.
record_outcome() + update_confidence_from_outcomes().

Mind-loop stage: Reflect → UpdateSelfModel (capability self-assessment)
"""

import pytest
from phionyx_core.meta.self_model import SelfModel


class TestRecordOutcome:
    """Test outcome recording."""

    def test_record_single_outcome(self):
        """Single outcome is recorded."""
        model = SelfModel()
        model.record_outcome("respond", True)
        assert model.get_outcome_history("respond") == [True]

    def test_record_multiple_outcomes(self):
        """Multiple outcomes accumulate."""
        model = SelfModel()
        model.record_outcome("respond", True)
        model.record_outcome("respond", False)
        model.record_outcome("respond", True)
        assert model.get_outcome_history("respond") == [True, False, True]

    def test_record_different_capabilities(self):
        """Outcomes tracked per capability."""
        model = SelfModel()
        model.record_outcome("respond", True)
        model.record_outcome("store_memory", False)
        assert model.get_outcome_history("respond") == [True]
        assert model.get_outcome_history("store_memory") == [False]

    def test_empty_history(self):
        """No outcomes → empty list."""
        model = SelfModel()
        assert model.get_outcome_history("nonexistent") == []

    def test_history_capped(self):
        """History respects max_history limit."""
        model = SelfModel()
        model._max_history = 5
        for i in range(10):
            model.record_outcome("respond", i % 2 == 0)
        assert len(model.get_outcome_history("respond")) == 5


class TestUpdateConfidence:
    """Test confidence updates from outcomes."""

    def test_all_success_increases_confidence(self):
        """All successes → confidence increases."""
        model = SelfModel()
        for _ in range(5):
            model.record_outcome("respond", True)
        updates = model.update_confidence_from_outcomes()
        assert "respond" in updates
        assert updates["respond"] > 0.5

    def test_all_failure_decreases_confidence(self):
        """All failures → confidence decreases."""
        model = SelfModel()
        for _ in range(5):
            model.record_outcome("respond", False)
        updates = model.update_confidence_from_outcomes()
        assert "respond" in updates
        assert updates["respond"] < 0.5

    def test_confidence_bounded_0_1(self):
        """Confidence stays in [0.0, 1.0]."""
        model = SelfModel()
        for _ in range(100):
            model.record_outcome("respond", True)
        updates = model.update_confidence_from_outcomes(alpha=0.5)
        assert 0.0 <= updates["respond"] <= 1.0

        model2 = SelfModel()
        for _ in range(100):
            model2.record_outcome("respond", False)
        updates2 = model2.update_confidence_from_outcomes(alpha=0.5)
        assert 0.0 <= updates2["respond"] <= 1.0

    def test_get_outcome_confidence(self):
        """get_outcome_confidence returns updated value."""
        model = SelfModel()
        assert model.get_outcome_confidence("respond") is None
        model.record_outcome("respond", True)
        model.update_confidence_from_outcomes()
        assert model.get_outcome_confidence("respond") is not None

    def test_gradual_change(self):
        """Confidence changes gradually with small alpha."""
        model = SelfModel()
        for _ in range(3):
            model.record_outcome("respond", True)
        u1 = model.update_confidence_from_outcomes(alpha=0.1)
        # Second update with more successes should increase further
        for _ in range(3):
            model.record_outcome("respond", True)
        u2 = model.update_confidence_from_outcomes(alpha=0.1)
        assert u2["respond"] >= u1["respond"]


class TestSerialization:
    """Test that outcome data survives serialization."""

    def test_to_dict_includes_outcomes(self):
        """to_dict includes outcome_history and outcome_confidences."""
        model = SelfModel()
        model.record_outcome("respond", True)
        model.update_confidence_from_outcomes()
        d = model.to_dict()
        assert "outcome_history" in d
        assert "outcome_confidences" in d

    def test_from_dict_restores_outcomes(self):
        """from_dict restores outcome data."""
        model = SelfModel()
        model.record_outcome("respond", True)
        model.record_outcome("respond", False)
        model.update_confidence_from_outcomes()
        d = model.to_dict()

        restored = SelfModel.from_dict(d)
        assert restored.get_outcome_history("respond") == [True, False]
        assert restored.get_outcome_confidence("respond") is not None
