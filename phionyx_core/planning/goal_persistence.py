"""
Goal Persistence
================

Persistent goal memory across sessions with status tracking,
prioritization, and conflict detection.

Roadmap Faz 4.4: World Model Hardening — Persistent Goal Memory
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"


class GoalPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PersistentGoal:
    """A goal that persists across sessions."""
    goal_id: str
    name: str
    description: str = ""
    status: GoalStatus = GoalStatus.PENDING
    priority: GoalPriority = GoalPriority.MEDIUM
    created_at: str = ""
    activated_at: str | None = None
    completed_at: str | None = None
    session_created: str = ""
    session_last_active: str = ""
    progress: float = 0.0  # 0.0-1.0
    sub_goal_ids: list[str] = field(default_factory=list)
    parent_goal_id: str | None = None
    conflicts_with: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ConflictReport:
    """Report of detected goal conflicts."""
    goal_a_id: str
    goal_b_id: str
    conflict_type: str  # "contradictory", "resource", "priority"
    reasoning: str
    severity: float = 0.5  # 0.0-1.0


@dataclass
class GoalPersistenceReport:
    """Summary of goal persistence state."""
    total_goals: int
    active_goals: int
    completed_goals: int
    pending_goals: int
    blocked_goals: int
    abandoned_goals: int
    conflicts: list[ConflictReport]
    cross_session_goals: int  # Goals spanning multiple sessions


class GoalPersistence:
    """
    Manages persistent goals across sessions.

    Provides:
    - Goal CRUD with status lifecycle
    - Cross-session persistence
    - Goal conflict detection
    - Priority-based ordering
    - Progress tracking
    """

    def __init__(self):
        self._goals: dict[str, PersistentGoal] = {}
        self._session_id: str = ""
        self._conflicts: list[ConflictReport] = []
        self._auto_save_enabled: bool = False
        self._auto_save_path: str = "data/goals"

    def enable_auto_save(self, base_path: str = "data/goals") -> None:
        """Enable auto-save: mutating methods will persist goals after each change."""
        self._auto_save_enabled = True
        self._auto_save_path = base_path

    def disable_auto_save(self) -> None:
        """Disable auto-save."""
        self._auto_save_enabled = False

    def _trigger_auto_save(self) -> None:
        """Called after each mutation if auto-save is enabled."""
        if self._auto_save_enabled:
            self.auto_save(self._auto_save_path)

    def set_session(self, session_id: str):
        """Set current session context."""
        self._session_id = session_id

    def add_goal(
        self,
        goal_id: str,
        name: str,
        description: str = "",
        priority: GoalPriority = GoalPriority.MEDIUM,
        parent_goal_id: str | None = None,
    ) -> PersistentGoal:
        """Add a new goal."""
        if goal_id in self._goals:
            return self._goals[goal_id]

        goal = PersistentGoal(
            goal_id=goal_id,
            name=name,
            description=description,
            priority=priority,
            session_created=self._session_id,
            session_last_active=self._session_id,
            parent_goal_id=parent_goal_id,
        )

        # Register as sub-goal if parent exists
        if parent_goal_id and parent_goal_id in self._goals:
            self._goals[parent_goal_id].sub_goal_ids.append(goal_id)

        self._goals[goal_id] = goal
        self._trigger_auto_save()
        return goal

    def activate(self, goal_id: str) -> bool:
        """Transition goal to active status."""
        goal = self._goals.get(goal_id)
        if not goal or goal.status not in (GoalStatus.PENDING, GoalStatus.BLOCKED):
            return False
        goal.status = GoalStatus.ACTIVE
        goal.activated_at = datetime.now(timezone.utc).isoformat()
        goal.session_last_active = self._session_id
        self._trigger_auto_save()
        return True

    def complete(self, goal_id: str) -> bool:
        """Mark goal as completed."""
        goal = self._goals.get(goal_id)
        if not goal or goal.status == GoalStatus.COMPLETED:
            return False
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = datetime.now(timezone.utc).isoformat()
        goal.progress = 1.0
        goal.session_last_active = self._session_id
        self._trigger_auto_save()
        return True

    def abandon(self, goal_id: str, reason: str = "") -> bool:
        """Mark goal as abandoned."""
        goal = self._goals.get(goal_id)
        if not goal or goal.status == GoalStatus.COMPLETED:
            return False
        goal.status = GoalStatus.ABANDONED
        goal.metadata["abandon_reason"] = reason
        goal.session_last_active = self._session_id
        self._trigger_auto_save()
        return True

    def block(self, goal_id: str, blocked_by: str = "") -> bool:
        """Mark goal as blocked."""
        goal = self._goals.get(goal_id)
        if not goal:
            return False
        goal.status = GoalStatus.BLOCKED
        if blocked_by:
            goal.metadata["blocked_by"] = blocked_by
        self._trigger_auto_save()
        return True

    def update_progress(self, goal_id: str, progress: float) -> bool:
        """Update goal progress (0.0-1.0)."""
        goal = self._goals.get(goal_id)
        if not goal:
            return False
        goal.progress = max(0.0, min(1.0, progress))
        goal.session_last_active = self._session_id
        self._trigger_auto_save()
        return True

    def get_goal(self, goal_id: str) -> PersistentGoal | None:
        """Get a goal by ID."""
        return self._goals.get(goal_id)

    def get_active_goals(self) -> list[PersistentGoal]:
        """Get all active goals, sorted by priority."""
        priority_order = {
            GoalPriority.CRITICAL: 0,
            GoalPriority.HIGH: 1,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 3,
        }
        active = [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]
        return sorted(active, key=lambda g: priority_order.get(g.priority, 99))

    def get_goals_by_status(self, status: GoalStatus) -> list[PersistentGoal]:
        """Get goals filtered by status."""
        return [g for g in self._goals.values() if g.status == status]

    def detect_conflicts(self) -> list[ConflictReport]:
        """
        Detect conflicts between active goals.

        Checks for:
        - Explicitly marked conflicts (conflicts_with)
        - Multiple CRITICAL goals (resource contention)
        """
        conflicts: list[ConflictReport] = []
        active = self.get_active_goals()

        # Explicit conflicts
        for goal in active:
            for conflict_id in goal.conflicts_with:
                other = self._goals.get(conflict_id)
                if other and other.status == GoalStatus.ACTIVE:
                    # Avoid duplicates
                    pair = tuple(sorted([goal.goal_id, conflict_id]))
                    if not any(
                        tuple(sorted([c.goal_a_id, c.goal_b_id])) == pair
                        for c in conflicts
                    ):
                        conflicts.append(ConflictReport(
                            goal_a_id=goal.goal_id,
                            goal_b_id=conflict_id,
                            conflict_type="contradictory",
                            reasoning=f"Explicitly marked conflict: {goal.name} vs {other.name}",
                            severity=0.8,
                        ))

        # Critical resource contention
        critical = [g for g in active if g.priority == GoalPriority.CRITICAL]
        if len(critical) > 1:
            for i in range(len(critical)):
                for j in range(i + 1, len(critical)):
                    conflicts.append(ConflictReport(
                        goal_a_id=critical[i].goal_id,
                        goal_b_id=critical[j].goal_id,
                        conflict_type="resource",
                        reasoning=f"Multiple critical goals: {critical[i].name} and {critical[j].name}",
                        severity=0.6,
                    ))

        self._conflicts = conflicts
        return conflicts

    def get_cross_session_goals(self) -> list[PersistentGoal]:
        """Get goals that span multiple sessions."""
        return [
            g for g in self._goals.values()
            if g.session_created != g.session_last_active
            and g.status in (GoalStatus.ACTIVE, GoalStatus.PENDING)
        ]

    def get_report(self) -> GoalPersistenceReport:
        """Generate summary report."""
        by_status: dict[GoalStatus, int] = {}
        for g in self._goals.values():
            by_status[g.status] = by_status.get(g.status, 0) + 1

        return GoalPersistenceReport(
            total_goals=len(self._goals),
            active_goals=by_status.get(GoalStatus.ACTIVE, 0),
            completed_goals=by_status.get(GoalStatus.COMPLETED, 0),
            pending_goals=by_status.get(GoalStatus.PENDING, 0),
            blocked_goals=by_status.get(GoalStatus.BLOCKED, 0),
            abandoned_goals=by_status.get(GoalStatus.ABANDONED, 0),
            conflicts=self._conflicts,
            cross_session_goals=len(self.get_cross_session_goals()),
        )

    # ── Feedback Channel 3: Goal Revision (Reflect → Plan) ─────────────

    def propose_revision(
        self,
        goal_id: str,
        reason: str,
        evidence: str = "",
    ) -> dict[str, Any] | None:
        """
        Propose a revision to an existing goal (Reflect → Plan feedback).

        Records a revision proposal with audit trail. Does NOT change the goal
        status — proposals are logged for review. Apply with apply_revision().

        Args:
            goal_id: ID of the goal to revise
            reason: Why this goal should be revised
            evidence: Supporting evidence (e.g., failure count, metric)

        Returns:
            Revision proposal dict, or None if goal not found or already proposed
        """
        if not hasattr(self, '_pending_revisions'):
            self._pending_revisions: list[dict[str, Any]] = []

        if goal_id not in self._goals:
            return None

        # Prevent duplicate proposals for the same goal
        existing = [r for r in self._pending_revisions if r["goal_id"] == goal_id]
        if existing:
            return None

        goal = self._goals[goal_id]
        revision = {
            "goal_id": goal_id,
            "goal_name": goal.name,
            "current_status": goal.status.value,
            "reason": reason,
            "evidence": evidence,
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "session_id": self._session_id,
            "applied": False,
        }
        self._pending_revisions.append(revision)
        self._trigger_auto_save()
        return revision

    def get_pending_revisions(self) -> list[dict[str, Any]]:
        """Get all pending (unapplied) revision proposals."""
        if not hasattr(self, '_pending_revisions'):
            return []
        return [r for r in self._pending_revisions if not r.get("applied")]

    def apply_revision(self, goal_id: str, new_status: GoalStatus) -> bool:
        """Apply a pending revision by changing goal status."""
        if not hasattr(self, '_pending_revisions'):
            return False
        if goal_id not in self._goals:
            return False

        for revision in self._pending_revisions:
            if revision["goal_id"] == goal_id and not revision.get("applied"):
                self._goals[goal_id].status = new_status
                revision["applied"] = True
                revision["applied_at"] = datetime.now(timezone.utc).isoformat()
                revision["new_status"] = new_status.value
                self._trigger_auto_save()
                return True
        return False

    def auto_save(self, base_path: str = "data/goals") -> str | None:
        """Auto-save goals to JSON file for cross-session persistence.

        Saves to {base_path}/{session_id}.json on every state change.
        Returns the file path written, or None if save failed.
        """
        if not self._session_id:
            logger.warning("Cannot auto-save: no session_id set")
            return None

        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"{self._session_id}.json"

        try:
            data = self.to_dict()
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("Goals auto-saved to %s", file_path)
            return str(file_path)
        except (OSError, TypeError) as e:
            logger.error("Auto-save failed: %s", e)
            return None

    @classmethod
    def auto_load(cls, session_id: str, base_path: str = "data/goals") -> Optional["GoalPersistence"]:
        """Auto-load goals from JSON file for session continuity.

        Returns GoalPersistence instance or None if file not found/corrupt.
        """
        file_path = Path(base_path) / f"{session_id}.json"

        if not file_path.exists():
            logger.debug("No saved goals for session %s", session_id)
            return None

        try:
            with open(file_path) as f:
                data = json.load(f)
            instance = cls.from_dict(data)
            logger.info("Goals auto-loaded from %s (%d goals)", file_path, len(instance._goals))
            return instance
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("Auto-load failed for %s: %s", file_path, e)
            return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for persistence."""
        result: dict[str, Any] = {
            "session_id": self._session_id,
            "goals": {
                gid: {
                    "goal_id": g.goal_id,
                    "name": g.name,
                    "description": g.description,
                    "status": g.status.value,
                    "priority": g.priority.value,
                    "created_at": g.created_at,
                    "activated_at": g.activated_at,
                    "completed_at": g.completed_at,
                    "session_created": g.session_created,
                    "session_last_active": g.session_last_active,
                    "progress": g.progress,
                    "sub_goal_ids": g.sub_goal_ids,
                    "parent_goal_id": g.parent_goal_id,
                    "conflicts_with": g.conflicts_with,
                    "metadata": g.metadata,
                }
                for gid, g in self._goals.items()
            },
        }
        if hasattr(self, '_pending_revisions') and self._pending_revisions:
            result["pending_revisions"] = list(self._pending_revisions)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalPersistence":
        """Restore from serialized data."""
        instance = cls()
        instance._session_id = data.get("session_id", "")
        for gid, gdata in data.get("goals", {}).items():
            goal = PersistentGoal(
                goal_id=gdata["goal_id"],
                name=gdata["name"],
                description=gdata.get("description", ""),
                status=GoalStatus(gdata.get("status", "pending")),
                priority=GoalPriority(gdata.get("priority", "medium")),
                created_at=gdata.get("created_at", ""),
                activated_at=gdata.get("activated_at"),
                completed_at=gdata.get("completed_at"),
                session_created=gdata.get("session_created", ""),
                session_last_active=gdata.get("session_last_active", ""),
                progress=gdata.get("progress", 0.0),
                sub_goal_ids=gdata.get("sub_goal_ids", []),
                parent_goal_id=gdata.get("parent_goal_id"),
                conflicts_with=gdata.get("conflicts_with", []),
                metadata=gdata.get("metadata", {}),
            )
            instance._goals[gid] = goal
        instance._pending_revisions = list(data.get("pending_revisions", []))
        return instance
