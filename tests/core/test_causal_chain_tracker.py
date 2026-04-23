"""
Tests for CausalChainTracker — Patent SF2-17
Per-participant turn_id monotonicity validation.
"""

import pytest

from phionyx_core.contracts.envelopes.causal_chain_tracker import (
    CausalChainTracker,
    CausalConsistencyViolation,
)


class TestCausalChainTracker:
    """Test per-participant causal consistency chain."""

    def test_first_message_always_accepted(self):
        """First message from any participant is always valid."""
        tracker = CausalChainTracker()
        result = tracker.validate_and_record("agent-A", 1)
        assert result is None
        assert tracker.get_last_turn_id("agent-A") == 1

    def test_monotonic_increasing_accepted(self):
        """Strictly increasing turn_ids are accepted."""
        tracker = CausalChainTracker()
        assert tracker.validate_and_record("agent-A", 1) is None
        assert tracker.validate_and_record("agent-A", 2) is None
        assert tracker.validate_and_record("agent-A", 5) is None  # gaps OK
        assert tracker.get_last_turn_id("agent-A") == 5

    def test_non_monotonic_rejected(self):
        """Decreasing turn_id returns violation."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent-A", 5)
        violation = tracker.validate_and_record("agent-A", 3)
        assert isinstance(violation, CausalConsistencyViolation)
        assert violation.participant_id == "agent-A"
        assert violation.expected_min_turn_id == 6
        assert violation.received_turn_id == 3
        assert violation.timestamp_utc  # non-empty

    def test_equal_turn_id_rejected(self):
        """Same turn_id (not strictly greater) returns violation."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent-A", 3)
        violation = tracker.validate_and_record("agent-A", 3)
        assert isinstance(violation, CausalConsistencyViolation)
        assert violation.expected_min_turn_id == 4
        assert violation.received_turn_id == 3

    def test_independent_chains_per_participant(self):
        """Different participants have independent chains."""
        tracker = CausalChainTracker()
        assert tracker.validate_and_record("agent-A", 1) is None
        assert tracker.validate_and_record("agent-B", 1) is None  # B starts at 1 too
        assert tracker.validate_and_record("agent-A", 2) is None
        assert tracker.validate_and_record("agent-B", 5) is None  # B jumps to 5
        assert tracker.get_last_turn_id("agent-A") == 2
        assert tracker.get_last_turn_id("agent-B") == 5

    def test_max_participants_eviction(self):
        """Oldest participant evicted when max_participants exceeded."""
        tracker = CausalChainTracker(max_participants=3)
        tracker.validate_and_record("p1", 1)
        tracker.validate_and_record("p2", 1)
        tracker.validate_and_record("p3", 1)
        assert tracker.participant_count == 3

        # Adding p4 should evict p1 (oldest)
        tracker.validate_and_record("p4", 1)
        assert tracker.participant_count == 3
        assert tracker.get_last_turn_id("p1") is None
        assert tracker.get_last_turn_id("p4") == 1

    def test_reset_participant(self):
        """Reset clears chain for specific participant."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent-A", 5)
        tracker.reset_participant("agent-A")
        assert tracker.get_last_turn_id("agent-A") is None

        # Can start fresh at any turn_id
        assert tracker.validate_and_record("agent-A", 1) is None

    def test_reset_all(self):
        """Reset all clears all chains."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent-A", 1)
        tracker.validate_and_record("agent-B", 2)
        tracker.reset_all()
        assert tracker.participant_count == 0
        assert tracker.get_last_turn_id("agent-A") is None

    def test_violation_does_not_update_chain(self):
        """A violation does not change the stored last_turn_id."""
        tracker = CausalChainTracker()
        tracker.validate_and_record("agent-A", 5)
        tracker.validate_and_record("agent-A", 3)  # violation
        assert tracker.get_last_turn_id("agent-A") == 5  # unchanged

    def test_unknown_participant_returns_none(self):
        """get_last_turn_id for unknown participant returns None."""
        tracker = CausalChainTracker()
        assert tracker.get_last_turn_id("unknown") is None

    def test_reset_nonexistent_participant_is_noop(self):
        """Resetting a non-existent participant does not raise."""
        tracker = CausalChainTracker()
        tracker.reset_participant("nonexistent")  # no error
