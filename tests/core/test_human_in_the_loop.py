"""
Tests for Human-in-the-Loop Review Queue — v4 §9.2
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta

from phionyx_core.governance.human_in_the_loop import (
    HumanReviewQueue,
    HITLConfig,
    ReviewItem,
    ReviewStatus,
    ReviewPriority,
)


@pytest.fixture
def tmp_queue_path():
    """Temporary file for queue storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def queue(tmp_queue_path):
    """Fresh queue with temp storage."""
    config = HITLConfig(storage_path=tmp_queue_path)
    return HumanReviewQueue(config=config)


class TestSubmission:
    """Submit items for review."""

    def test_submit_creates_pending_item(self, queue):
        item = queue.submit_for_review(
            trigger_type="ethics_escalate",
            trigger_reason="Harm risk exceeded",
        )
        assert item.status == ReviewStatus.PENDING.value
        assert item.trigger_type == "ethics_escalate"
        assert item.review_id is not None

    def test_submit_increments_pending_count(self, queue):
        assert queue.pending_count == 0
        queue.submit_for_review("test", "reason1")
        assert queue.pending_count == 1
        queue.submit_for_review("test", "reason2")
        assert queue.pending_count == 2

    def test_submit_with_ethics_data(self, queue):
        item = queue.submit_for_review(
            trigger_type="ethics_escalate",
            trigger_reason="High harm risk",
            ethics_verdict="escalate",
            ethics_max_risk=0.87,
            ethics_triggered_risks=["harm_risk"],
            turn_id=5,
        )
        assert item.ethics_max_risk == 0.87
        assert item.ethics_triggered_risks == ["harm_risk"]
        assert item.turn_id == 5

    def test_high_risk_auto_sets_critical_priority(self, queue):
        item = queue.submit_for_review(
            trigger_type="ethics_escalate",
            trigger_reason="Very high risk",
            ethics_max_risk=0.95,
        )
        assert item.priority == ReviewPriority.CRITICAL.value

    def test_medium_risk_auto_sets_high_priority(self, queue):
        item = queue.submit_for_review(
            trigger_type="ethics_escalate",
            trigger_reason="Medium risk",
            ethics_max_risk=0.75,
        )
        assert item.priority == ReviewPriority.HIGH.value


class TestReview:
    """Approve and deny review items."""

    def test_approve(self, queue):
        item = queue.submit_for_review("test", "reason")
        result = queue.approve(item.review_id, reviewed_by="toygar", notes="OK")
        assert result is not None
        assert result.status == ReviewStatus.APPROVED.value
        assert result.reviewed_by == "toygar"
        assert queue.pending_count == 0

    def test_deny(self, queue):
        item = queue.submit_for_review("test", "reason")
        result = queue.deny(item.review_id, reviewed_by="toygar", notes="Not safe")
        assert result is not None
        assert result.status == ReviewStatus.DENIED.value

    def test_cannot_review_twice(self, queue):
        item = queue.submit_for_review("test", "reason")
        queue.approve(item.review_id, reviewed_by="toygar")
        result = queue.approve(item.review_id, reviewed_by="toygar")
        assert result is None  # Already reviewed

    def test_review_nonexistent_returns_none(self, queue):
        result = queue.approve("nonexistent-id", reviewed_by="toygar")
        assert result is None


class TestExpiry:
    """Item expiry behavior."""

    def test_expired_item_auto_denied(self, queue):
        item = queue.submit_for_review("test", "reason")
        # Manually expire the item
        item.expires_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        queue._expire_stale()
        assert queue.pending_count == 0

    def test_is_pending_false_for_expired(self, queue):
        item = queue.submit_for_review("test", "reason")
        item.expires_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        assert not queue.is_pending(item.review_id)


class TestPersistence:
    """File-based persistence."""

    def test_save_and_load(self, tmp_queue_path):
        config = HITLConfig(storage_path=tmp_queue_path)
        q1 = HumanReviewQueue(config=config)
        item = q1.submit_for_review("test", "reason")

        # Create new queue from same file
        q2 = HumanReviewQueue(config=config)
        assert q2.pending_count == 1
        loaded_item = q2.get_item(item.review_id)
        assert loaded_item is not None
        assert loaded_item.trigger_type == "test"

    def test_archive_persists(self, tmp_queue_path):
        config = HITLConfig(storage_path=tmp_queue_path)
        q1 = HumanReviewQueue(config=config)
        item = q1.submit_for_review("test", "reason")
        q1.approve(item.review_id, reviewed_by="toygar")

        q2 = HumanReviewQueue(config=config)
        archived = q2.get_item(item.review_id)
        assert archived is not None
        assert archived.status == ReviewStatus.APPROVED.value


class TestHelpers:
    """Helper methods."""

    def test_is_approved(self, queue):
        item = queue.submit_for_review("test", "reason")
        assert not queue.is_approved(item.review_id)
        queue.approve(item.review_id, reviewed_by="toygar")
        assert queue.is_approved(item.review_id)

    def test_get_pending_sorted_by_priority(self, queue):
        queue.submit_for_review("test", "low priority", priority=ReviewPriority.LOW.value)
        queue.submit_for_review("test", "critical", priority=ReviewPriority.CRITICAL.value)
        queue.submit_for_review("test", "normal", priority=ReviewPriority.NORMAL.value)

        pending = queue.get_pending()
        assert pending[0].priority == ReviewPriority.CRITICAL.value
        assert pending[-1].priority == ReviewPriority.LOW.value

    def test_to_dict(self, queue):
        queue.submit_for_review("test", "reason")
        d = queue.to_dict()
        assert d["pending_count"] == 1
        assert "config" in d

    def test_queue_size_limit(self, tmp_queue_path):
        config = HITLConfig(storage_path=tmp_queue_path, max_queue_size=3)
        queue = HumanReviewQueue(config=config)

        for i in range(5):
            queue.submit_for_review("test", f"reason {i}")

        assert len(queue._queue) <= 3


class TestReviewItem:
    """ReviewItem serialization."""

    def test_to_dict_and_from_dict(self):
        item = ReviewItem(
            review_id="test-123",
            submitted_at="2026-03-17T00:00:00",
            trigger_type="ethics_escalate",
            trigger_reason="test",
        )
        d = item.to_dict()
        restored = ReviewItem.from_dict(d)
        assert restored.review_id == "test-123"
        assert restored.trigger_type == "ethics_escalate"

    def test_is_expired(self):
        item = ReviewItem(
            review_id="test",
            submitted_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
        )
        assert item.is_expired()
