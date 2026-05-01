"""
State Versioning
================

Maintains versioned snapshots of world state with hash integrity,
diff computation, and rollback capability.

Roadmap Faz 4.3: World Model Hardening — World-State Versioning
"""

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StateSnapshot:
    """A versioned, hash-verified snapshot of world state."""
    version: int
    state: dict[str, Any]
    hash: str
    timestamp: str
    turn_index: int
    parent_version: int | None = None

    def verify(self) -> bool:
        """Verify hash integrity."""
        expected = StateVersioning.compute_hash(self.state)
        return self.hash == expected


@dataclass
class StateDiff:
    """Difference between two state snapshots."""
    from_version: int
    to_version: int
    added: dict[str, Any] = field(default_factory=dict)
    removed: dict[str, Any] = field(default_factory=dict)
    changed: dict[str, dict[str, Any]] = field(default_factory=dict)  # key → {old, new}

    @property
    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.changed

    @property
    def change_count(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    @property
    def changed_keys(self) -> set[str]:
        return set(self.added.keys()) | set(self.removed.keys()) | set(self.changed.keys())


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    rolled_back_to: int
    current_version: int
    reasoning: str


class StateVersioning:
    """
    Maintains versioned world state with hash integrity.

    Provides:
    - Turn-indexed snapshots with SHA256 hashes
    - Version history (last N snapshots)
    - Diff between any two versions
    - Rollback to any previous version
    """

    def __init__(self, max_versions: int = 50):
        self.max_versions = max(1, max_versions)
        self._snapshots: list[StateSnapshot] = []
        self._current_version: int = 0

    @staticmethod
    def compute_hash(state: dict[str, Any]) -> str:
        """Compute SHA256 hash of a state dict."""
        canonical = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @property
    def current_version(self) -> int:
        return self._current_version

    @property
    def version_count(self) -> int:
        return len(self._snapshots)

    def snapshot(
        self,
        state: dict[str, Any],
        turn_index: int = 0,
        timestamp: str | None = None,
    ) -> StateSnapshot:
        """
        Create a new versioned snapshot.

        Deep-copies the state to prevent external mutation.
        """
        self._current_version += 1
        state_copy = copy.deepcopy(state)
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        parent = self._snapshots[-1].version if self._snapshots else None

        snap = StateSnapshot(
            version=self._current_version,
            state=state_copy,
            hash=self.compute_hash(state_copy),
            timestamp=ts,
            turn_index=turn_index,
            parent_version=parent,
        )
        self._snapshots.append(snap)

        # Cap history
        if len(self._snapshots) > self.max_versions:
            self._snapshots = self._snapshots[-self.max_versions:]

        return snap

    def get_snapshot(self, version: int) -> StateSnapshot | None:
        """Get a specific version snapshot."""
        for snap in self._snapshots:
            if snap.version == version:
                return snap
        return None

    def get_latest(self) -> StateSnapshot | None:
        """Get the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    def diff(self, from_version: int, to_version: int) -> StateDiff | None:
        """Compute diff between two versions."""
        snap_from = self.get_snapshot(from_version)
        snap_to = self.get_snapshot(to_version)
        if not snap_from or not snap_to:
            return None

        added = {}
        removed = {}
        changed = {}

        all_keys = set(snap_from.state.keys()) | set(snap_to.state.keys())
        for key in all_keys:
            in_from = key in snap_from.state
            in_to = key in snap_to.state
            if in_to and not in_from:
                added[key] = snap_to.state[key]
            elif in_from and not in_to:
                removed[key] = snap_from.state[key]
            elif in_from and in_to:
                old_val = snap_from.state[key]
                new_val = snap_to.state[key]
                if old_val != new_val:
                    changed[key] = {"old": old_val, "new": new_val}

        return StateDiff(
            from_version=from_version,
            to_version=to_version,
            added=added,
            removed=removed,
            changed=changed,
        )

    def rollback(self, to_version: int) -> RollbackResult:
        """
        Rollback to a specific version.

        Creates a new snapshot with the old state (preserves history).
        """
        target = self.get_snapshot(to_version)
        if not target:
            return RollbackResult(
                success=False,
                rolled_back_to=to_version,
                current_version=self._current_version,
                reasoning=f"Version {to_version} not found in history",
            )

        # Create new snapshot with rolled-back state
        new_snap = self.snapshot(
            state=copy.deepcopy(target.state),
            turn_index=target.turn_index,
        )

        return RollbackResult(
            success=True,
            rolled_back_to=to_version,
            current_version=new_snap.version,
            reasoning=f"Rolled back to version {to_version}, new version {new_snap.version}",
        )

    def verify_chain(self) -> bool:
        """Verify hash integrity of all snapshots."""
        for snap in self._snapshots:
            if not snap.verify():
                return False
        return True

    def get_history(self) -> list[dict[str, Any]]:
        """Get version history summary."""
        return [
            {
                "version": s.version,
                "hash": s.hash[:12],
                "turn_index": s.turn_index,
                "timestamp": s.timestamp,
                "key_count": len(s.state),
            }
            for s in self._snapshots
        ]
