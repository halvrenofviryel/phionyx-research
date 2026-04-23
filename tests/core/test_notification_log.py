"""Tests for NotificationLog — triple conversation notification system."""

import json
import os
import tempfile

import pytest

from phionyx_core.meta.notification_log import (
    NotificationEntry,
    NotificationLog,
    NotificationStatus,
    NotificationUrgency,
    ParticipantRole,
)


@pytest.fixture
def tmp_log_path(tmp_path):
    """Temporary file path for notification log."""
    return str(tmp_path / "notification_log.json")


@pytest.fixture
def log(tmp_log_path):
    """Fresh NotificationLog instance."""
    return NotificationLog(storage_path=tmp_log_path)


class TestNotificationEntry:
    """Tests for NotificationEntry dataclass."""

    def test_to_dict_roundtrip(self):
        entry = NotificationEntry(
            id="test-id",
            timestamp="2026-03-28T12:00:00+00:00",
            source=ParticipantRole.PHIONYX_AUTONOMOUS.value,
            target=ParticipantRole.FOUNDER.value,
            session_id="fc-123",
            urgency=NotificationUrgency.INFO.value,
            status=NotificationStatus.UNREAD.value,
            title="Test",
            content="Test content",
        )
        d = entry.to_dict()
        restored = NotificationEntry.from_dict(d)
        assert restored.id == entry.id
        assert restored.title == entry.title
        assert restored.source == entry.source

    def test_from_dict_ignores_unknown_fields(self):
        data = {
            "id": "x",
            "timestamp": "t",
            "source": "founder",
            "target": "claude-code",
            "session_id": "s",
            "urgency": "info",
            "status": "unread",
            "title": "T",
            "content": "C",
            "unknown_field": "should be ignored",
        }
        entry = NotificationEntry.from_dict(data)
        assert entry.id == "x"
        assert not hasattr(entry, "unknown_field") or entry.__dict__.get("unknown_field") is None


class TestNotificationLogAdd:
    """Tests for adding notifications."""

    def test_add_basic(self, log):
        entry = log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-001",
            title="Drift Detected",
            content="Self-model drift magnitude: 0.45",
        )
        assert entry.id is not None
        assert entry.status == NotificationStatus.UNREAD.value
        assert entry.source == ParticipantRole.PHIONYX_AUTONOMOUS.value
        assert entry.target == ParticipantRole.FOUNDER.value
        assert log.active_count == 1

    def test_add_with_urgency_and_context(self, log):
        entry = log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-002",
            title="Code Review",
            content="Found potential issue in pipeline block",
            urgency=NotificationUrgency.ATTENTION,
            context={"related_files": ["pipeline/blocks/x.py"], "confidence": 0.85},
        )
        assert entry.urgency == NotificationUrgency.ATTENTION.value
        assert entry.context["confidence"] == 0.85

    def test_add_rejects_same_source_target(self, log):
        with pytest.raises(ValueError, match="Source and target cannot be the same"):
            log.add(
                source=ParticipantRole.FOUNDER,
                target=ParticipantRole.FOUNDER,
                session_id="fc-003",
                title="Invalid",
                content="Self-notification",
            )

    def test_add_enforces_max_active(self, tmp_log_path):
        log = NotificationLog(storage_path=tmp_log_path, max_active=3)
        for i in range(5):
            log.add(
                source=ParticipantRole.PHIONYX_AUTONOMOUS,
                target=ParticipantRole.FOUNDER,
                session_id="fc-004",
                title=f"Notification {i}",
                content=f"Content {i}",
            )
        assert log.active_count == 3
        assert log.archive_count == 2


class TestNotificationLogRead:
    """Tests for reading and filtering notifications."""

    def test_get_unread_all(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-010",
            title="A",
            content="a",
        )
        log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-010",
            title="B",
            content="b",
        )
        unread = log.get_unread()
        assert len(unread) == 2

    def test_get_unread_filtered_by_target(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-011",
            title="For founder",
            content="x",
        )
        log.add(
            source=ParticipantRole.FOUNDER,
            target=ParticipantRole.CLAUDE_CODE,
            session_id="fc-011",
            title="For claude-code",
            content="y",
        )
        founder_unread = log.get_unread(target=ParticipantRole.FOUNDER)
        assert len(founder_unread) == 1
        assert founder_unread[0].title == "For founder"

    def test_get_by_session(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-020",
            title="Session A",
            content="x",
        )
        log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-021",
            title="Session B",
            content="y",
        )
        session_a = log.get_by_session("fc-020")
        assert len(session_a) == 1
        assert session_a[0].title == "Session A"

    def test_get_by_id(self, log):
        entry = log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-030",
            title="Find me",
            content="x",
        )
        found = log.get_by_id(entry.id)
        assert found is not None
        assert found.title == "Find me"

    def test_get_by_id_not_found(self, log):
        assert log.get_by_id("nonexistent-id") is None

    def test_get_unread_count(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-040",
            title="N1",
            content="x",
        )
        log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-040",
            title="N2",
            content="y",
        )
        assert log.get_unread_count() == 2
        assert log.get_unread_count(target=ParticipantRole.FOUNDER) == 2


class TestNotificationLogStatus:
    """Tests for status transitions."""

    def test_mark_read(self, log):
        entry = log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-050",
            title="Read me",
            content="x",
        )
        assert log.mark_read(entry.id) is True
        updated = log.get_by_id(entry.id)
        assert updated.status == NotificationStatus.READ.value
        assert updated.read_at is not None

    def test_mark_read_idempotent(self, log):
        entry = log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-051",
            title="Read twice",
            content="x",
        )
        assert log.mark_read(entry.id) is True
        assert log.mark_read(entry.id) is False  # Already read

    def test_mark_acknowledged(self, log):
        entry = log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-052",
            title="Ack me",
            content="x",
        )
        assert log.mark_acknowledged(entry.id) is True
        updated = log.get_by_id(entry.id)
        assert updated.status == NotificationStatus.ACKNOWLEDGED.value
        assert updated.acknowledged_at is not None

    def test_mark_acknowledged_from_read(self, log):
        entry = log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-053",
            title="Read then ack",
            content="x",
        )
        log.mark_read(entry.id)
        assert log.mark_acknowledged(entry.id) is True

    def test_acknowledged_not_in_unread(self, log):
        entry = log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-054",
            title="Gone from unread",
            content="x",
        )
        log.mark_acknowledged(entry.id)
        assert log.get_unread_count() == 0


class TestNotificationLogPersistence:
    """Tests for file-based persistence."""

    def test_save_and_reload(self, tmp_log_path):
        log1 = NotificationLog(storage_path=tmp_log_path)
        log1.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-060",
            title="Persistent",
            content="Survives reload",
        )

        log2 = NotificationLog(storage_path=tmp_log_path)
        assert log2.active_count == 1
        assert log2.get_unread()[0].title == "Persistent"

    def test_status_persists_after_reload(self, tmp_log_path):
        log1 = NotificationLog(storage_path=tmp_log_path)
        entry = log1.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-061",
            title="Status survives",
            content="x",
        )
        log1.mark_read(entry.id)

        log2 = NotificationLog(storage_path=tmp_log_path)
        reloaded = log2.get_by_id(entry.id)
        assert reloaded.status == NotificationStatus.READ.value

    def test_corrupt_file_graceful(self, tmp_log_path):
        with open(tmp_log_path, "w") as f:
            f.write("not valid json!!!")
        log = NotificationLog(storage_path=tmp_log_path)
        assert log.active_count == 0  # Graceful fallback


class TestNotificationLogCollaboration:
    """Tests for multi-participant collaboration detection."""

    def test_detect_collaboration_session(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-070",
            title="Phionyx thought",
            content="x",
        )
        log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-070",
            title="Claude Code analysis",
            content="y",
        )
        collab = log.get_collaboration_sessions()
        assert "fc-070" in collab

    def test_no_collaboration_single_ai(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-071",
            title="Only Phionyx",
            content="x",
        )
        collab = log.get_collaboration_sessions()
        assert "fc-071" not in collab

    def test_clear_session(self, log):
        log.add(
            source=ParticipantRole.PHIONYX_AUTONOMOUS,
            target=ParticipantRole.FOUNDER,
            session_id="fc-072",
            title="To archive",
            content="x",
        )
        log.add(
            source=ParticipantRole.CLAUDE_CODE,
            target=ParticipantRole.FOUNDER,
            session_id="fc-073",
            title="Keep",
            content="y",
        )
        archived = log.clear_session("fc-072")
        assert archived == 1
        assert log.active_count == 1
        assert log.archive_count == 1
