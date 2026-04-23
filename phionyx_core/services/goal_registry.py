"""
Goal Registry Service — v4
============================

Manages system-level goals with legitimacy scoring,
priority management, and conflict detection.
Port-adapter pattern (AD-2): implements GoalRegistryProtocol.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..contracts.v4.goal_object import GoalObject, GoalPriority, GoalStatus
from ..meta.arbitration_math import compute_goal_utility

logger = logging.getLogger(__name__)


class GoalRegistry:
    """
    In-memory goal registry.

    Production: back with PostgreSQL via port adapter.
    """

    def __init__(self):
        self._goals: Dict[str, GoalObject] = {}

    async def register_goal(self, goal: GoalObject) -> GoalObject:
        """Register a new goal."""
        # Compute legitimacy
        legitimacy = goal.compute_legitimacy()
        if legitimacy < 0.3:
            goal.status = GoalStatus.REJECTED
            goal.metadata["rejection_reason"] = f"Low legitimacy: {legitimacy:.2f}"
            logger.warning(f"Goal rejected: {goal.name} (L={legitimacy:.2f})")
        else:
            goal.status = GoalStatus.PROPOSED

        self._goals[goal.goal_id] = goal
        return goal

    async def activate_goal(self, goal_id: str) -> Optional[GoalObject]:
        """Activate a proposed goal."""
        goal = self._goals.get(goal_id)
        if goal and goal.status == GoalStatus.PROPOSED:
            goal.status = GoalStatus.ACTIVE
            goal.activated_at = datetime.now(timezone.utc)
        return goal

    async def get_active_goals(self) -> List[GoalObject]:
        """Get all active goals sorted by priority."""
        priority_order = {
            GoalPriority.CRITICAL: 0,
            GoalPriority.HIGH: 1,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 3,
        }
        active = [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]
        return sorted(active, key=lambda g: priority_order.get(g.priority, 99))

    async def evaluate_goals(self, context: Any) -> List[GoalObject]:
        """Evaluate all active goals against current context."""
        active = await self.get_active_goals()
        for goal in active:
            # Recompute legitimacy with current state
            goal.metadata["legitimacy"] = goal.compute_legitimacy()
            goal.metadata["utility"] = compute_goal_utility(
                legitimacy=goal.metadata["legitimacy"],
                expected_value=goal.metadata.get("expected_value", 0.5),
                conflict_penalty=len(goal.conflict_with) * 0.1,
            )
        return active

    async def complete_goal(self, goal_id: str) -> Optional[GoalObject]:
        """Mark a goal as completed."""
        goal = self._goals.get(goal_id)
        if goal:
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.now(timezone.utc)
        return goal

    def get_goal(self, goal_id: str) -> Optional[GoalObject]:
        """Get a goal by ID."""
        return self._goals.get(goal_id)
