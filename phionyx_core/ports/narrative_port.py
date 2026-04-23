"""
Narrative Port Interface
=========================

Port interface for Narrative generation.
Enables swapping between SIMPLE, RICH, and THERAPEUTIC modes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class NarrativePort(ABC):
    """Port interface for Narrative generation."""

    @abstractmethod
    async def generate_narrative(
        self,
        user_input: str,
        context: str,
        physics_state: Dict[str, float],
        model_id: str,
        system_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate narrative response.

        Returns:
            Generated narrative text
        """
        pass

    @abstractmethod
    def get_mode(self) -> str:
        """
        Get narrative mode.

        Returns:
            'simple', 'rich', or 'therapeutic'
        """
        pass

    @abstractmethod
    async def apply_filters(
        self,
        narrative: str,
        filters: List[str]
    ) -> str:
        """Apply safety/content filters to narrative."""
        pass

