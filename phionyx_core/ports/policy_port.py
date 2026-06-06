"""
Policy Port Interface
=====================

Port interface for Policy SDK module.
Enables swapping Policy with different implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PolicyPort(ABC):
    """Port interface for Policy operations."""

    @abstractmethod
    async def select_policy(
        self,
        context_mode: Optional[str] = None,
        risk_level: int = 0,
        user_role: Optional[str] = None
    ) -> Optional[Any]:
        """
        Select appropriate policy based on context.

        Returns:
            Policy object or None
        """
        pass

    @abstractmethod
    async def evaluate_content(
        self,
        content: str,
        policy: Any,
        physics_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate content against policy.

        Returns:
            Dictionary with decision, blocking_reason, etc.
        """
        pass

    @abstractmethod
    def get_default_policy(self) -> Any:
        """Get default policy."""
        pass

