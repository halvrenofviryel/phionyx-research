"""
Human-in-the-Loop Review Queue — v4 §9.2
==========================================

When EthicsDecision.verdict == ESCALATE or ActionIntent.requires_approval == True,
the action is queued for human review instead of being executed.

Design:
- File-based persistence (JSON) with Supabase upgrade path
- FIFO queue with priority override for CRITICAL items
- Timeout: unreviewed items auto-DENY after configurable period
- Audit: every submission, review, and expiry is logged
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """Status of a review item."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ReviewPriority(str, Enum):
    """Priority of review item."""
    CRITICAL = "critical"   # Safety-related, review ASAP
    HIGH = "high"           # Ethics escalation
    NORMAL = "normal"       # Standard approval
    LOW = "low"             # Informational


@dataclass
class ReviewItem:
    """An item in the human review queue."""
    review_id: str
    submitted_at: str  # ISO format
    status: str = ReviewStatus.PENDING.value
    priority: str = ReviewPriority.NORMAL.value

    # What triggered the review
    trigger_type: str = ""  # "ethics_escalate", "action_approval", "kill_switch"
    trigger_reason: str = ""

    # Action details
    action_type: str | None = None
    action_description: str | None = None
    action_parameters: dict[str, Any] | None = None

    # Ethics context
    ethics_verdict: str | None = None
    ethics_max_risk: float | None = None
    ethics_triggered_risks: list[str] | None = None

    # Session context
    turn_id: int | None = None
    session_id: str | None = None
    user_input_hash: str | None = None  # SHA-256, not raw input

    # Review outcome
    reviewed_at: str | None = None
    reviewed_by: str | None = None
    review_decision: str | None = None
    review_notes: str | None = None

    # Expiry
    expires_at: str | None = None

    def is_expired(self) -> bool:
        """Check if this review item has expired."""
        if not self.expires_at:
            return False
        expires = datetime.fromisoformat(self.expires_at)
        now = datetime.now(timezone.utc)
        # Handle naive datetimes by assuming UTC
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= expires

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ReviewItem':
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class HITLConfig:
    """Configuration for Human-in-the-Loop queue."""
    storage_path: str = ""  # File-based storage path, auto-set if empty
    expiry_hours: float = 24.0  # Items expire after 24 hours
    max_queue_size: int = 100
    auto_deny_on_expiry: bool = True  # Expired items are auto-denied (fail-closed)


class HumanReviewQueue:
    """
    Queue for actions requiring human approval.

    When the ethics engine returns ESCALATE or an action requires approval,
    the item is placed in this queue. The system blocks execution until
    a human reviewer approves or denies the action.

    Usage:
        queue = HumanReviewQueue()
        item = queue.submit_for_review(
            trigger_type="ethics_escalate",
            trigger_reason="Harm risk 0.87 requires human review",
            action_type="respond",
            ethics_max_risk=0.87,
        )
        # Later, human reviews:
        queue.approve(item.review_id, reviewed_by="toygar", notes="Safe to proceed")
        # Or:
        queue.deny(item.review_id, reviewed_by="toygar", notes="Block this action")
    """

    def __init__(self, config: HITLConfig | None = None):
        self.config = config or HITLConfig()
        self._queue: list[ReviewItem] = []
        self._archive: list[ReviewItem] = []  # Completed/expired items

        # Set default storage path
        if not self.config.storage_path:
            self.config.storage_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "data", "hitl_queue.json"
            )

        self._load()

    @property
    def pending_count(self) -> int:
        """Number of items awaiting review."""
        self._expire_stale()
        return sum(1 for item in self._queue if item.status == ReviewStatus.PENDING.value)

    @property
    def queue(self) -> list[ReviewItem]:
        """Get current queue (read-only copy)."""
        self._expire_stale()
        return list(self._queue)

    def submit_for_review(
        self,
        trigger_type: str,
        trigger_reason: str,
        action_type: str | None = None,
        action_description: str | None = None,
        action_parameters: dict[str, Any] | None = None,
        ethics_verdict: str | None = None,
        ethics_max_risk: float | None = None,
        ethics_triggered_risks: list[str] | None = None,
        turn_id: int | None = None,
        session_id: str | None = None,
        user_input_hash: str | None = None,
        priority: str = ReviewPriority.NORMAL.value,
    ) -> ReviewItem:
        """
        Submit an action for human review.

        Args:
            trigger_type: What triggered the review
            trigger_reason: Why review is needed
            action_type: Type of action (respond, modify_state, etc.)
            action_description: Human-readable action description
            action_parameters: Action parameters (sanitized)
            ethics_verdict: Ethics decision verdict
            ethics_max_risk: Maximum ethics risk score
            ethics_triggered_risks: Which risk types triggered
            turn_id: Current turn ID
            session_id: Current session ID
            user_input_hash: SHA-256 of user input (not raw)
            priority: Review priority

        Returns:
            Created ReviewItem
        """
        # Enforce queue size limit
        if len(self._queue) >= self.config.max_queue_size:
            self._expire_stale()
            if len(self._queue) >= self.config.max_queue_size:
                # Archive oldest pending items
                oldest = [i for i in self._queue if i.status == ReviewStatus.PENDING.value]
                if oldest:
                    oldest[0].status = ReviewStatus.EXPIRED.value
                    oldest[0].reviewed_at = datetime.now(timezone.utc).isoformat()
                    self._archive.append(oldest[0])
                    self._queue.remove(oldest[0])

        # Determine priority from ethics risk
        if ethics_max_risk and ethics_max_risk > 0.9:
            priority = ReviewPriority.CRITICAL.value
        elif ethics_max_risk and ethics_max_risk > 0.7:
            priority = ReviewPriority.HIGH.value

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.config.expiry_hours)

        item = ReviewItem(
            review_id=str(uuid.uuid4()),
            submitted_at=now.isoformat(),
            priority=priority,
            trigger_type=trigger_type,
            trigger_reason=trigger_reason,
            action_type=action_type,
            action_description=action_description,
            action_parameters=action_parameters,
            ethics_verdict=ethics_verdict,
            ethics_max_risk=ethics_max_risk,
            ethics_triggered_risks=ethics_triggered_risks,
            turn_id=turn_id,
            session_id=session_id,
            user_input_hash=user_input_hash,
            expires_at=expires_at.isoformat(),
        )

        self._queue.append(item)
        self._save()

        logger.info(
            f"HITL: Submitted for review [{item.priority}]: "
            f"{trigger_type} — {trigger_reason} (id={item.review_id[:8]})"
        )
        return item

    def approve(
        self,
        review_id: str,
        reviewed_by: str,
        notes: str = "",
    ) -> ReviewItem | None:
        """
        Approve a pending review item.

        Args:
            review_id: Review item ID
            reviewed_by: Who approved
            notes: Review notes

        Returns:
            Updated ReviewItem or None if not found
        """
        return self._review(review_id, ReviewStatus.APPROVED, reviewed_by, notes)

    def deny(
        self,
        review_id: str,
        reviewed_by: str,
        notes: str = "",
    ) -> ReviewItem | None:
        """
        Deny a pending review item.

        Args:
            review_id: Review item ID
            reviewed_by: Who denied
            notes: Review notes

        Returns:
            Updated ReviewItem or None if not found
        """
        return self._review(review_id, ReviewStatus.DENIED, reviewed_by, notes)

    def get_item(self, review_id: str) -> ReviewItem | None:
        """Get a review item by ID."""
        for item in self._queue:
            if item.review_id == review_id:
                return item
        for item in self._archive:
            if item.review_id == review_id:
                return item
        return None

    def get_pending(self) -> list[ReviewItem]:
        """Get all pending review items, sorted by priority."""
        self._expire_stale()
        pending = [i for i in self._queue if i.status == ReviewStatus.PENDING.value]
        priority_order = {
            ReviewPriority.CRITICAL.value: 0,
            ReviewPriority.HIGH.value: 1,
            ReviewPriority.NORMAL.value: 2,
            ReviewPriority.LOW.value: 3,
        }
        return sorted(pending, key=lambda x: priority_order.get(x.priority, 99))

    def is_approved(self, review_id: str) -> bool:
        """Check if a specific review item was approved."""
        item = self.get_item(review_id)
        return item is not None and item.status == ReviewStatus.APPROVED.value

    def is_pending(self, review_id: str) -> bool:
        """Check if a specific review item is still pending."""
        item = self.get_item(review_id)
        if item is None:
            return False
        if item.is_expired():
            return False
        return item.status == ReviewStatus.PENDING.value

    def _review(
        self,
        review_id: str,
        status: ReviewStatus,
        reviewed_by: str,
        notes: str,
    ) -> ReviewItem | None:
        """Internal review handler."""
        for item in self._queue:
            if item.review_id == review_id:
                if item.status != ReviewStatus.PENDING.value:
                    logger.warning(
                        f"HITL: Cannot review item {review_id[:8]} — "
                        f"status is {item.status}, not pending"
                    )
                    return None

                item.status = status.value
                item.reviewed_at = datetime.now(timezone.utc).isoformat()
                item.reviewed_by = reviewed_by
                item.review_decision = status.value
                item.review_notes = notes

                # Move to archive
                self._archive.append(item)
                self._queue.remove(item)
                self._save()

                logger.info(
                    f"HITL: Item {review_id[:8]} {status.value} by {reviewed_by}"
                )
                return item

        logger.warning(f"HITL: Review item {review_id[:8]} not found in queue")
        return None

    def _expire_stale(self) -> int:
        """Expire stale items. Returns count of expired items."""
        expired_count = 0
        for item in list(self._queue):
            if item.status == ReviewStatus.PENDING.value and item.is_expired():
                if self.config.auto_deny_on_expiry:
                    item.status = ReviewStatus.EXPIRED.value
                    item.reviewed_at = datetime.now(timezone.utc).isoformat()
                    item.reviewed_by = "system_expiry"
                    item.review_decision = "expired_auto_deny"
                    self._archive.append(item)
                    self._queue.remove(item)
                    expired_count += 1
                    logger.warning(
                        f"HITL: Item {item.review_id[:8]} expired (auto-deny)"
                    )
        if expired_count:
            self._save()
        return expired_count

    def _save(self) -> None:
        """Persist queue to file."""
        try:
            storage_path = Path(self.config.storage_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "queue": [item.to_dict() for item in self._queue],
                "archive": [item.to_dict() for item in self._archive[-100:]],  # Keep last 100
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            with open(storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"HITL: Failed to save queue: {e}")

    def _load(self) -> None:
        """Load queue from file."""
        try:
            storage_path = Path(self.config.storage_path)
            if not storage_path.exists():
                return

            with open(storage_path) as f:
                data = json.load(f)

            self._queue = [ReviewItem.from_dict(d) for d in data.get("queue", [])]
            self._archive = [ReviewItem.from_dict(d) for d in data.get("archive", [])]

            logger.info(
                f"HITL: Loaded {len(self._queue)} pending, "
                f"{len(self._archive)} archived items"
            )
        except Exception as e:
            logger.error(f"HITL: Failed to load queue: {e}")
            self._queue = []
            self._archive = []

    def to_dict(self) -> dict[str, Any]:
        """Serialize queue state for monitoring."""
        return {
            "pending_count": self.pending_count,
            "queue_size": len(self._queue),
            "archive_size": len(self._archive),
            "config": {
                "expiry_hours": self.config.expiry_hours,
                "max_queue_size": self.config.max_queue_size,
                "auto_deny_on_expiry": self.config.auto_deny_on_expiry,
            },
        }
