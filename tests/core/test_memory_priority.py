"""
Memory Priority Consolidation Tests
======================================

Tests for feedback channel 4: Reflect → UpdateMemory.
set_priority_boost() + get_effective_strength() + clear_priority_boosts().

Mind-loop stage: Reflect → UpdateMemory (priority consolidation)
"""

import pytest
from phionyx_core.memory.consolidation import MemoryConsolidator


@pytest.fixture
def consolidator():
    """Fresh MemoryConsolidator instance."""
    return MemoryConsolidator()


class TestSetPriorityBoost:
    """Test priority boost setting."""

    def test_set_boost(self, consolidator):
        """Boost is applied to specified memory IDs."""
        count = consolidator.set_priority_boost(["m1", "m2"], boost=1.5)
        assert count == 2
        boosts = consolidator.get_priority_boosts()
        assert boosts["m1"] == 1.5
        assert boosts["m2"] == 1.5

    def test_boost_clamped_upper(self, consolidator):
        """Boost above 2.0 is clamped."""
        consolidator.set_priority_boost(["m1"], boost=5.0)
        assert consolidator.get_priority_boosts()["m1"] == 2.0

    def test_boost_clamped_lower(self, consolidator):
        """Boost below 1.0 is clamped."""
        consolidator.set_priority_boost(["m1"], boost=0.5)
        assert consolidator.get_priority_boosts()["m1"] == 1.0

    def test_empty_ids(self, consolidator):
        """Empty list → 0 boosts."""
        count = consolidator.set_priority_boost([])
        assert count == 0


class TestGetEffectiveStrength:
    """Test effective strength calculation."""

    def test_no_boost_returns_base(self, consolidator):
        """Without boost, returns base strength."""
        memory = {"id": "m1", "current_strength": 0.6}
        assert consolidator.get_effective_strength(memory) == 0.6

    def test_boosted_strength(self, consolidator):
        """Boosted memory gets higher effective strength."""
        consolidator.set_priority_boost(["m1"], boost=1.5)
        memory = {"id": "m1", "current_strength": 0.6}
        effective = consolidator.get_effective_strength(memory)
        assert effective == pytest.approx(0.9, abs=0.01)

    def test_effective_capped_at_1(self, consolidator):
        """Effective strength never exceeds 1.0."""
        consolidator.set_priority_boost(["m1"], boost=2.0)
        memory = {"id": "m1", "current_strength": 0.8}
        effective = consolidator.get_effective_strength(memory)
        assert effective <= 1.0


class TestClearBoosts:
    """Test boost clearing."""

    def test_clear_removes_all(self, consolidator):
        """clear_priority_boosts removes all boosts."""
        consolidator.set_priority_boost(["m1", "m2"], boost=1.5)
        consolidator.clear_priority_boosts()
        assert consolidator.get_priority_boosts() == {}
