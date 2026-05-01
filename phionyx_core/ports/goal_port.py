"""
Goal Port — v4
=================

Port interface for goal management (AD-2: port-adapter pattern).
"""

from abc import ABC, abstractmethod
from typing import Any


class GoalPort(ABC):
    """Abstract port for goal management."""

    @abstractmethod
    async def register_goal(self, goal: Any) -> Any:
        """Register a new goal."""
        ...

    @abstractmethod
    async def get_active_goals(self) -> list[Any]:
        """Get active goals."""
        ...

    @abstractmethod
    async def evaluate_goals(self, context: Any) -> list[Any]:
        """Evaluate goals against context."""
        ...

    @abstractmethod
    async def complete_goal(self, goal_id: str) -> Any | None:
        """Mark goal as completed."""
        ...


class NullGoalPort(GoalPort):
    """Null implementation for when goal management is not needed."""

    async def register_goal(self, goal: Any) -> Any:
        return goal

    async def get_active_goals(self) -> list[Any]:
        return []

    async def evaluate_goals(self, context: Any) -> list[Any]:
        return []

    async def complete_goal(self, goal_id: str) -> Any | None:
        return None
