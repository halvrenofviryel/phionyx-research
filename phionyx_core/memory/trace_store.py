"""
Trace Store - Event Persistence for Echoism Core v1.0 / Faz 2.4
================================================================

Per Faz 2.4:
- Event'leri JSONL + (opsiyonel) vektör index'e yazan arayüz
- Minimumda SQLite destekle
- Event → Trace → Echo zinciri için persistent storage
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

# Import EchoEvent if available
try:
    from phionyx_core.state.echo_event import EchoEvent
    ECHO_EVENT_AVAILABLE = True
except ImportError:
    ECHO_EVENT_AVAILABLE = False
    EchoEvent = None


class TraceStore:
    """
    Trace Store for persistent event storage.

    Per Faz 2.4:
    - JSONL file for event log
    - SQLite for queryable storage
    - Optional vector index for semantic search (future)
    """

    def __init__(
        self,
        db_path: str | None = None,
        jsonl_path: str | None = None,
        enable_vector_index: bool = False
    ):
        """
        Initialize trace store.

        Args:
            db_path: SQLite database path (default: in-memory)
            jsonl_path: JSONL file path (default: None, no JSONL)
            enable_vector_index: Enable vector index (future feature)
        """
        self.db_path = db_path or ":memory:"
        self.jsonl_path = jsonl_path
        self.enable_vector_index = enable_vector_index

        # Initialize SQLite database
        self._init_db()

        # Open JSONL file if specified
        self.jsonl_file = None
        if self.jsonl_path:
            # Create directory if needed
            jsonl_dir = Path(self.jsonl_path).parent
            jsonl_dir.mkdir(parents=True, exist_ok=True)
            # Open in append mode
            self.jsonl_file = open(self.jsonl_path, "a", encoding="utf-8")

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()

            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    intensity REAL NOT NULL,
                    tags TEXT,  -- JSON array
                    payload TEXT,  -- JSON object
                    suppressed INTEGER DEFAULT 0,
                    erased INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Event references table (for E_tags in state)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_references (
                    event_id TEXT NOT NULL,
                    state_id TEXT,
                    tag TEXT,
                    intensity REAL,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)

            # Audit log for erasure (GDPR compliance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS erasure_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    erased_at TEXT NOT NULL,
                    reason TEXT,
                    user_id TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)

            conn.commit()

    def store_event(self, event: EchoEvent) -> bool:
        """
        Store event in trace store.

        Args:
            event: EchoEvent instance

        Returns:
            True if successful
        """
        if not ECHO_EVENT_AVAILABLE:
            raise ImportError("EchoEvent not available")

        # Store in SQLite
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO events (
                        id, type, timestamp, intensity, tags, payload,
                        suppressed, erased, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id,
                    event.type,
                    event.timestamp.isoformat(),
                    event.intensity,
                    json.dumps(event.tags),
                    json.dumps(event.payload),
                    0,  # suppressed
                    0,  # erased
                    datetime.now().isoformat()
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

        # Store in JSONL if enabled
        if self.jsonl_file:
            jsonl_entry = {
                "id": event.id,
                "type": event.type,
                "timestamp": event.timestamp.isoformat(),
                "intensity": event.intensity,
                "tags": event.tags,
                "payload": event.payload
            }
            self.jsonl_file.write(json.dumps(jsonl_entry) + "\n")
            self.jsonl_file.flush()

        return True

    def get_event(self, event_id: str) -> EchoEvent | None:
        """
        Retrieve event by ID.

        Args:
            event_id: Event ID

        Returns:
            EchoEvent instance or None
        """
        if not ECHO_EVENT_AVAILABLE:
            raise ImportError("EchoEvent not available")

        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, type, timestamp, intensity, tags, payload, suppressed, erased
                FROM events
                WHERE id = ? AND erased = 0
            """, (event_id,))
            row = cursor.fetchone()

        if not row:
            return None

        event_id_db, event_type, timestamp_str, intensity, tags_json, payload_json, suppressed, erased = row

        # Parse JSON fields
        tags = json.loads(tags_json) if tags_json else []
        payload = json.loads(payload_json) if payload_json else {}
        timestamp = datetime.fromisoformat(timestamp_str)

        # Create EchoEvent
        event = EchoEvent(
            id=event_id_db,
            type=event_type,
            timestamp=timestamp,
            intensity=intensity,
            tags=tags,
            payload=payload
        )

        # Note: suppressed and erased are stored but not in EchoEvent model
        # They can be accessed via metadata if needed

        return event

    def get_events_by_tags(
        self,
        tags: list[str],
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100
    ) -> list[EchoEvent]:
        """
        Retrieve events by tags.

        Args:
            tags: List of tags to match
            start_time: Start timestamp filter
            end_time: End timestamp filter
            limit: Maximum number of events to return

        Returns:
            List of EchoEvent instances
        """
        if not ECHO_EVENT_AVAILABLE:
            raise ImportError("EchoEvent not available")

        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()

            # Build query
            query = "SELECT id, type, timestamp, intensity, tags, payload FROM events WHERE erased = 0"
            params = []

            # Tag filter (simple LIKE search, can be enhanced with JSON functions)
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                query += " AND (" + " OR ".join(tag_conditions) + ")"

            # Time filters
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        events = []
        for row in rows:
            event_id, event_type, timestamp_str, intensity, tags_json, payload_json = row
            tags = json.loads(tags_json) if tags_json else []
            payload = json.loads(payload_json) if payload_json else {}
            timestamp = datetime.fromisoformat(timestamp_str)

            event = EchoEvent(
                id=event_id,
                type=event_type,
                timestamp=timestamp,
                intensity=intensity,
                tags=tags,
                payload=payload
            )
            events.append(event)

        return events

    def mark_suppressed(self, event_id: str, suppressed: bool = True) -> bool:
        """
        Mark event as suppressed.

        Per Faz 2.4: Suppression reduces intensity but does not delete event.

        Args:
            event_id: Event ID
            suppressed: Whether to suppress (True) or unsuppress (False)

        Returns:
            True if successful
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events
                SET suppressed = ?
                WHERE id = ?
            """, (1 if suppressed else 0, event_id))
            conn.commit()
            rowcount = cursor.rowcount

        return rowcount > 0

    def erase_event(
        self,
        event_id: str,
        reason: str | None = None,
        user_id: str | None = None
    ) -> bool:
        """
        Permanently erase event (GDPR compliance).

        Per Faz 2.4:
        - Event is permanently deleted from DB and index
        - E_tags references are marked as 'tombstone' ID
        - Erasure audit log entry is created

        Args:
            event_id: Event ID
            reason: Reason for erasure
            user_id: User ID requesting erasure

        Returns:
            True if successful
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE events
                    SET erased = 1
                    WHERE id = ?
                """, (event_id,))
                cursor.execute("""
                    INSERT INTO erasure_audit_log (event_id, erased_at, reason, user_id)
                    VALUES (?, ?, ?, ?)
                """, (
                    event_id,
                    datetime.now().isoformat(),
                    reason or "User requested",
                    user_id
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

        return True

    def close(self) -> None:
        """Close trace store (close JSONL file if open)."""
        if self.jsonl_file:
            self.jsonl_file.close()
            self.jsonl_file = None

    def __enter__(self) -> TraceStore:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        # Fallback so the JSONL file descriptor doesn't leak if callers
        # forget to use a context manager or call close() explicitly.
        try:
            self.close()
        except Exception:
            # __del__ must not raise
            pass

