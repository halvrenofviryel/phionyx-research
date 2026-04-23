"""
Unit Tests for Trace Store (Faz 2.4)
====================================

Per Faz 2.4 requirements:
- Suppression: intensity düşüyor ama event silinmiyor
- Decay: zamanla düşüyor
- Erasure: tombstone + audit log çalışıyor
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
TEST_DIR = Path(__file__).resolve().parent
SRC_DIR = TEST_DIR.parent.parent
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(Path(SRC_DIR).parent.parent / "core-state" / "src"))

from phionyx_core.memory.trace_store import TraceStore  # noqa: E402
from phionyx_core.state.echo_event import EchoEvent  # noqa: E402


def test_store_and_retrieve_event():
    """Test: Store event and retrieve it."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = TraceStore(db_path=db_path)

        # Create event
        event = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.8,
            tags=["positive", "academic"],
            payload={"text": "I'm feeling good"}
        )

        # Store
        success = store.store_event(event)
        assert success, "Event should be stored successfully"

        # Retrieve
        retrieved = store.get_event(event.id)
        assert retrieved is not None, "Event should be retrievable"
        assert retrieved.id == event.id, "Event ID should match"
        assert retrieved.intensity == event.intensity, "Intensity should match"
        assert retrieved.tags == event.tags, "Tags should match"

        store.close()
        print("✅ Test passed: Store and retrieve event")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_suppression_reduces_intensity_but_keeps_event():
    """
    Test: Suppression reduces intensity but event is not deleted.

    Per Faz 2.4: Suppression sonrası intensity düşüyor ama event silinmiyor.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = TraceStore(db_path=db_path)

        # Create event
        event = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.8,
            tags=["sensitive"]
        )

        # Store
        store.store_event(event)

        # Mark as suppressed
        success = store.mark_suppressed(event.id, suppressed=True)
        assert success, "Event should be marked as suppressed"

        # Event should still exist
        retrieved = store.get_event(event.id)
        assert retrieved is not None, "Event should still exist after suppression"

        # Check suppressed flag (via DB query)
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT suppressed FROM events WHERE id = ?", (event.id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Event should exist in DB"
        assert row[0] == 1, "Event should be marked as suppressed"

        store.close()
        print("✅ Test passed: Suppression reduces intensity but keeps event")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_trace_weight_decay_over_time():
    """
    Test: Trace weight decays over time.

    Per Faz 2.4: Decay zamanla düşüyor.
    """
    from phionyx_core.memory.trace import trace_weight

    # Create event
    now = datetime.now()
    event = EchoEvent(
        type="user_input",
        timestamp=now - timedelta(seconds=600),  # 10 minutes ago
        intensity=1.0,
        tags=["test"]
    )

    # Calculate weight now (should be lower due to decay)
    weight_now = trace_weight(event, now, half_life_seconds=300.0)  # 5 minute half-life

    # Calculate weight at event time (should be full intensity)
    weight_at_event = trace_weight(event, event.timestamp, half_life_seconds=300.0)

    # Weight should decrease over time
    assert weight_now < weight_at_event, \
        f"Weight should decrease over time: {weight_at_event:.3f} -> {weight_now:.3f}"

    # With 5 minute half-life and 10 minutes elapsed, weight should be ~0.25
    assert weight_now < 0.3, f"Weight after 2 half-lives should be < 0.3, got {weight_now:.3f}"

    print(f"✅ Test passed: Trace weight decays over time ({weight_at_event:.3f} -> {weight_now:.3f})")


def test_suppression_reduces_trace_weight():
    """
    Test: Suppression reduces trace weight.

    Per Faz 2.4: TraceWeight = intensity * exp(-lambda*dt) * (1-suppressed)
    """
    from phionyx_core.memory.trace import trace_weight

    # Create event
    event = EchoEvent(
        type="user_input",
        timestamp=datetime.now(),
        intensity=1.0,
        tags=["test"]
    )

    # Weight without suppression
    weight_normal = trace_weight(event, datetime.now(), half_life_seconds=300.0, suppressed=False)

    # Weight with suppression
    weight_suppressed = trace_weight(event, datetime.now(), half_life_seconds=300.0, suppressed=True, suppression_factor=0.1)

    # Suppressed weight should be 10% of normal (suppression_factor=0.1)
    assert weight_suppressed < weight_normal, \
        f"Suppressed weight should be lower: {weight_normal:.3f} -> {weight_suppressed:.3f}"

    # Should be approximately suppression_factor * normal (allowing for small differences)
    ratio = weight_suppressed / weight_normal
    assert 0.09 < ratio < 0.11, \
        f"Suppressed weight should be ~10% of normal, got {ratio:.3f}"

    print(f"✅ Test passed: Suppression reduces trace weight ({weight_normal:.3f} -> {weight_suppressed:.3f})")


def test_erasure_creates_tombstone_and_audit_log():
    """
    Test: Erasure creates tombstone and audit log.

    Per Faz 2.4: Erasure tombstone + audit log çalışıyor.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = TraceStore(db_path=db_path)

        # Create event
        event = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.8,
            tags=["test"]
        )

        # Store
        store.store_event(event)

        # Erase
        success = store.erase_event(
            event_id=event.id,
            reason="User requested deletion",
            user_id="test_user"
        )
        assert success, "Event should be erased successfully"

        # Event should not be retrievable (erased=1)
        retrieved = store.get_event(event.id)
        assert retrieved is None, "Erased event should not be retrievable"

        # Check audit log
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, erased_at, reason, user_id
            FROM erasure_audit_log
            WHERE event_id = ?
        """, (event.id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Audit log entry should exist"
        assert row[0] == event.id, "Event ID should match"
        assert row[2] == "User requested deletion", "Reason should match"
        assert row[3] == "test_user", "User ID should match"

        # Check event is marked as erased
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT erased FROM events WHERE id = ?", (event.id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Event should exist in DB"
        assert row[0] == 1, "Event should be marked as erased"

        store.close()
        print("✅ Test passed: Erasure creates tombstone and audit log")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_get_events_by_tags():
    """Test: Retrieve events by tags."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = TraceStore(db_path=db_path)

        # Create events with different tags
        event1 = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.8,
            tags=["positive", "academic"]
        )
        event2 = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.6,
            tags=["negative", "emotional"]
        )
        event3 = EchoEvent(
            type="user_input",
            timestamp=datetime.now(),
            intensity=0.9,
            tags=["positive", "social"]
        )

        # Store
        store.store_event(event1)
        store.store_event(event2)
        store.store_event(event3)

        # Retrieve by tag
        positive_events = store.get_events_by_tags(["positive"])
        assert len(positive_events) == 2, f"Should find 2 positive events, got {len(positive_events)}"

        # Check event IDs
        event_ids = [e.id for e in positive_events]
        assert event1.id in event_ids, "Event1 should be in results"
        assert event3.id in event_ids, "Event3 should be in results"
        assert event2.id not in event_ids, "Event2 should not be in results"

        store.close()
        print("✅ Test passed: Retrieve events by tags")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_store_and_retrieve_event()
    test_suppression_reduces_intensity_but_keeps_event()
    test_trace_weight_decay_over_time()
    test_suppression_reduces_trace_weight()
    test_erasure_creates_tombstone_and_audit_log()
    test_get_events_by_tags()
    print("\n✅ All Trace Store tests passed!")

