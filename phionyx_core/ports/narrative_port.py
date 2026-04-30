"""
Narrative Port Interface
=========================

Port interface for Narrative generation.
Enables swapping between SIMPLE, RICH, and THERAPEUTIC modes.
"""

from abc import ABC, abstractmethod


class NarrativePort(ABC):
    """Port interface for Narrative generation."""

    @abstractmethod
    async def generate_narrative(
        self,
        user_input: str,
        context: str,
        physics_state: dict[str, float],
        model_id: str,
        system_prompt: str,
        temperature: float | None = None
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
        filters: list[str]
    ) -> str:
        """Apply safety/content filters to narrative."""
        pass

