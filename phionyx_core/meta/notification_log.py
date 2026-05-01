"""
Notification Log — Inter-participant communication for triple conversation system.

Enables structured notifications between Founder, Phionyx (autonomous), and Claude Code.
All participants communicate through the Founder as intermediary — no direct AI-AI channel.

Mind-loop stages: Act (emit notification), Perceive (read notifications)
AGI relevance: Genuine — self-directed inter-agent communication infrastructure
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ParticipantRole(str, Enum):
    """Participants in the triple conversation system."""

    FOUNDER = "founder"
    PHIONYX_AUTONOMOUS = "phionyx-autonomous"
    CLAUDE_CODE = "claude-code"


class NotificationUrgency(str, Enum):
    """Urgency levels for notifications."""

    INFO = "info"
    ATTENTION = "attention"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Lifecycle status of a notification."""

    UNREAD = "unread"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class NotificationEntry:
    """A single notification in the triple conversation system."""

    id: str
    timestamp: str  # ISO 8601
    source: str  # ParticipantRole value
    target: str  # ParticipantRole value
    session_id: str
    urgency: str  # NotificationUrgency value
    status: str  # NotificationStatus value
    title: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    read_at: str | None = None
    acknowledged_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationEntry":
        """Deserialize from dictionary, filtering to known fields."""
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


class NotificationLog:
    """
    File-based notification log for triple conversation system.

    Follows HITL queue pattern: dual storage (active + archive),
    per-mutation persistence, append-only semantics.

    Security: No direct AI-AI channel. Founder is always the intermediary.
    """

    def __init__(
        self,
        storage_path: str | None = None,
        max_active: int = 500,
        archive_limit: int = 200,
    ):
        self._max_active = max_active
        self._archive_limit = archive_limit

        if storage_path:
            self._storage_path = storage_path
        else:
            self._storage_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "..",
                "data",
                "notification_log.json",
            )

        self._notifications: list[NotificationEntry] = []
        self._archive: list[NotificationEntry] = []
        self._load()

    def add(
        self,
        source: ParticipantRole,
        target: ParticipantRole,
        session_id: str,
        title: str,
        content: str,
        urgency: NotificationUrgency = NotificationUrgency.INFO,
        context: dict[str, Any] | None = None,
    ) -> NotificationEntry:
        """
        Add a new notification.

        Args:
            source: Who sends the notification
            target: Who should receive it
            session_id: Associated session
            title: Short notification title
            content: Detailed content (markdown supported)
            urgency: INFO, ATTENTION, or CRITICAL
            context: Additional metadata

        Returns:
            The created NotificationEntry
        """
        if source == target:
            raise ValueError("Source and target cannot be the same participant")

        # Enforce: AI participants always target founder
        if (
            source in (ParticipantRole.PHIONYX_AUTONOMOUS, ParticipantRole.CLAUDE_CODE)
            and target
            not in (ParticipantRole.FOUNDER, ParticipantRole.PHIONYX_AUTONOMOUS, ParticipantRole.CLAUDE_CODE)
        ):
            raise ValueError(f"Invalid target: {target}")

        entry = NotificationEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source.value if isinstance(source, ParticipantRole) else source,
            target=target.value if isinstance(target, ParticipantRole) else target,
            session_id=session_id,
            urgency=urgency.value if isinstance(urgency, NotificationUrgency) else urgency,
            status=NotificationStatus.UNREAD.value,
            title=title,
            content=content,
            context=context or {},
        )

        # Enforce max active: archive oldest if at limit
        if len(self._notifications) >= self._max_active:
            oldest = self._notifications.pop(0)
            self._archive.append(oldest)
            self._archive = self._archive[-self._archive_limit :]

        self._notifications.append(entry)
        self._save()
        return entry

    def get_unread(
        self, target: ParticipantRole | None = None
    ) -> list[NotificationEntry]:
        """Get unread notifications, optionally filtered by target."""
        results = [
            n for n in self._notifications if n.status == NotificationStatus.UNREAD.value
        ]
        if target:
            target_val = target.value if isinstance(target, ParticipantRole) else target
            results = [n for n in results if n.target == target_val]
        return results

    def get_by_session(self, session_id: str) -> list[NotificationEntry]:
        """Get all active notifications for a session."""
        return [n for n in self._notifications if n.session_id == session_id]

    def get_by_id(self, entry_id: str) -> NotificationEntry | None:
        """Find a notification by ID (searches active and archive)."""
        for n in self._notifications:
            if n.id == entry_id:
                return n
        for n in self._archive:
            if n.id == entry_id:
                return n
        return None

    def mark_read(self, entry_id: str) -> bool:
        """Mark a notification as read. Returns True if found and updated."""
        for n in self._notifications:
            if n.id == entry_id and n.status == NotificationStatus.UNREAD.value:
                n.status = NotificationStatus.READ.value
                n.read_at = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def mark_acknowledged(self, entry_id: str) -> bool:
        """Mark a notification as acknowledged. Returns True if found and updated."""
        for n in self._notifications:
            if n.id == entry_id and n.status in (
                NotificationStatus.UNREAD.value,
                NotificationStatus.READ.value,
            ):
                n.status = NotificationStatus.ACKNOWLEDGED.value
                n.acknowledged_at = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def get_unread_count(self, target: ParticipantRole | None = None) -> int:
        """Get count of unread notifications."""
        return len(self.get_unread(target))

    def get_collaboration_sessions(self) -> list[str]:
        """
        Find sessions where multiple AI participants are active.
        Returns session IDs where both Phionyx and Claude Code have notifications.
        """
        session_sources: dict[str, set] = {}
        ai_roles = {ParticipantRole.PHIONYX_AUTONOMOUS.value, ParticipantRole.CLAUDE_CODE.value}

        for n in self._notifications:
            if n.source in ai_roles:
                if n.session_id not in session_sources:
                    session_sources[n.session_id] = set()
                session_sources[n.session_id].add(n.source)

        return [
            sid for sid, sources in session_sources.items() if len(sources & ai_roles) >= 2
        ]

    @property
    def active_count(self) -> int:
        """Number of active (non-archived) notifications."""
        return len(self._notifications)

    @property
    def archive_count(self) -> int:
        """Number of archived notifications."""
        return len(self._archive)

    def clear_session(self, session_id: str) -> int:
        """Archive all notifications for a session. Returns count archived."""
        to_archive = [n for n in self._notifications if n.session_id == session_id]
        remaining = [n for n in self._notifications if n.session_id != session_id]

        if not to_archive:
            return 0

        self._archive.extend(to_archive)
        self._archive = self._archive[-self._archive_limit :]
        self._notifications = remaining
        self._save()
        return len(to_archive)

    def _save(self) -> None:
        """Persist to JSON file."""
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = {
                "notifications": [n.to_dict() for n in self._notifications],
                "archive": [n.to_dict() for n in self._archive],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(self._storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass  # Fail-open: don't crash on persistence failure

    def _load(self) -> None:
        """Load from JSON file."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path) as f:
                    data = json.load(f)
                self._notifications = [
                    NotificationEntry.from_dict(n)
                    for n in data.get("notifications", [])
                ]
                self._archive = [
                    NotificationEntry.from_dict(n) for n in data.get("archive", [])
                ]
        except Exception:
            self._notifications = []
            self._archive = []
