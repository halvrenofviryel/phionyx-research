"""
Goal Revision Tests
=====================

Tests for feedback channel 3: Reflect → Plan.
propose_revision() + get_pending_revisions() + apply_revision().

Mind-loop stage: Reflect → Plan (goal revision)
"""

import pytest
from phionyx_core.planning.goal_persistence import (
    GoalPersistence,
    GoalStatus,
    GoalPriority,
)


@pytest.fixture
def persistence():
    """GoalPersistence with sample goals."""
    gp = GoalPersistence()
    gp.set_session("test-session")
    gp.add_goal("g1", "Improve CQS", description="Reach CQS 0.90")
    gp.add_goal("g2", "Fix bridge tests", description="0 failures")
    # Activate g1 by setting status directly
    gp.get_goal("g1").status = GoalStatus.ACTIVE
    return gp


class TestProposeRevision:
    """Test revision proposal creation."""

    def test_propose_revision_existing_goal(self, persistence):
        """Propose revision for existing goal."""
        result = persistence.propose_revision(
            "g1", reason="CQS plateau at 0.862", evidence="3 experiments no improvement"
        )
        assert result is not None
        assert result["goal_id"] == "g1"
        assert result["reason"] == "CQS plateau at 0.862"
        assert result["applied"] is False

    def test_propose_revision_nonexistent_goal(self, persistence):
        """Nonexistent goal returns None."""
        result = persistence.propose_revision("nonexistent", reason="test")
        assert result is None

    def test_duplicate_proposal_rejected(self, persistence):
        """Second proposal for same goal is rejected."""
        persistence.propose_revision("g1", reason="first")
        result = persistence.propose_revision("g1", reason="second")
        assert result is None

    def test_different_goals_both_accepted(self, persistence):
        """Proposals for different goals both accepted."""
        r1 = persistence.propose_revision("g1", reason="reason1")
        r2 = persistence.propose_revision("g2", reason="reason2")
        assert r1 is not None
        assert r2 is not None


class TestGetPendingRevisions:
    """Test pending revision retrieval."""

    def test_empty_revisions(self, persistence):
        """No proposals → empty list."""
        assert persistence.get_pending_revisions() == []

    def test_pending_revisions_returned(self, persistence):
        """Pending proposals are returned."""
        persistence.propose_revision("g1", reason="test")
        pending = persistence.get_pending_revisions()
        assert len(pending) == 1
        assert pending[0]["goal_id"] == "g1"


class TestApplyRevision:
    """Test revision application."""

    def test_apply_changes_status(self, persistence):
        """Applying revision changes goal status."""
        persistence.propose_revision("g1", reason="plateau")
        result = persistence.apply_revision("g1", GoalStatus.BLOCKED)
        assert result is True
        goal = persistence.get_goal("g1")
        assert goal.status == GoalStatus.BLOCKED

    def test_apply_marks_revision_applied(self, persistence):
        """Applied revision no longer appears in pending."""
        persistence.propose_revision("g1", reason="plateau")
        persistence.apply_revision("g1", GoalStatus.ABANDONED)
        pending = persistence.get_pending_revisions()
        assert len(pending) == 0

    def test_apply_nonexistent_returns_false(self, persistence):
        """Applying to nonexistent goal returns False."""
        result = persistence.apply_revision("nonexistent", GoalStatus.BLOCKED)
        assert result is False

    def test_apply_without_proposal_returns_false(self, persistence):
        """Applying without prior proposal returns False."""
        result = persistence.apply_revision("g1", GoalStatus.BLOCKED)
        assert result is False
