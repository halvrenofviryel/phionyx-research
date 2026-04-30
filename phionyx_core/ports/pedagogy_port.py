"""
Pedagogy Port Interface
=======================

Port interface for Pedagogy SDK module.
Enables swapping Pedagogy with different strictness levels.
"""

from abc import ABC, abstractmethod
from typing import Any


class PedagogyPort(ABC):
    """Port interface for Pedagogy operations."""

    @abstractmethod
    async def assess_risk(
        self,
        user_input: str,
        physics_state: dict[str, float],
        actor_ref: str | None = None,
        tenant_ref: str | None = None
    ) -> dict[str, Any]:
        """
        Assess risk level for user input.

        Args:
            user_input: User input text
            physics_state: Physics state dictionary
            actor_ref: Actor reference (core-neutral identifier)
            tenant_ref: Tenant reference (core-neutral identifier)

        Returns:
            Dictionary with risk_level, risk_type, recommendations
        """
        pass

    @abstractmethod
    async def calculate_vygotsky_level(
        self,
        actor_ref: str,
        current_phi: float
    ) -> float:
        """
        Calculate Vygotsky scaffolding level.

        Args:
            actor_ref: Actor reference (core-neutral identifier)
            current_phi: Current phi value

        Returns:
            Vygotsky level (0.0 to 1.0)
        """
        pass

    @abstractmethod
    async def get_safe_template(
        self,
        risk_type: str,
        language: str = "tr",
        physics_state: dict[str, float] | None = None
    ) -> str | None:
        """
        Get safe template for risk type.

        Returns:
            Safe template text or None
        """
        pass

    @abstractmethod
    def get_strictness_level(self) -> str:
        """
        Get pedagogy strictness level.

        Returns:
            'strict', 'moderate', 'light', or 'off'
        """
        pass

