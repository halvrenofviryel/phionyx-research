"""
Meta Port Interface
==================

Port interface for Meta-Cognition (Confidence Estimation).
Enables swapping Meta with Null implementation.
"""

from abc import ABC, abstractmethod
from typing import Any


class MetaPort(ABC):
    """Port interface for Meta-Cognition operations."""

    @abstractmethod
    async def estimate_confidence(
        self,
        user_input: str,
        context: str | None = None,
        memory_matches: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Estimate confidence in response.

        Returns:
            Dictionary with confidence_score, is_uncertain, recommendation
        """
        pass

    @abstractmethod
    def get_hedging_phrase(
        self,
        language: str = "tr"
    ) -> str:
        """Get hedging phrase for uncertain responses."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if Meta-Cognition is available."""
        pass

