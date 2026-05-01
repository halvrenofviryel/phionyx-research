"""
Play Card Use Case
==================

Business logic for playing a card in card-based interactive fiction.
Extracted from API route handler to core layer.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PlayCardInput:
    """Input for play card use case."""
    character_id: str
    card_id: str
    user_input: str | None = None
    scene_context: str | None = None
    user_id: str | None = None


@dataclass
class PlayCardOutput:
    """Output from play card use case."""
    result: dict[str, Any]
    character_name: str
    character_archetype: str
    background: str | None = None
    user_age_category: str | None = None


class PlayCardUseCase:
    """
    Use case for playing a card.

    This encapsulates the business logic for:
    - Character data fetching
    - Background retrieval
    - Engine initialization
    - Card processing
    """

    def __init__(
        self,
        get_engine_func: Any,  # Function to get engine instance
        user_profile_service: Any = None  # UserProfileService
    ):
        """
        Initialize use case.

        Args:
            get_engine_func: Function to get engine instance
            user_profile_service: User profile service
        """
        self.get_engine_func = get_engine_func
        self.user_profile_service = user_profile_service

    async def execute(self, input_data: PlayCardInput) -> PlayCardOutput:
        """
        Execute the play card use case.

        Args:
            input_data: Input data for the use case

        Returns:
            PlayCardOutput with result and character info
        """
        # Book characters mapping
        BOOK_CHARACTERS = {
            "targaven": {"name": "Targaven", "class": "Sacred", "archetype": "sacred"},
            "zyrelthe": {"name": "Zyrelthé", "class": "Silent", "archetype": "silent"},
            "elion": {"name": "Elion", "class": "Fractured", "archetype": "fractured"},
            "althea": {"name": "Althea", "class": "Shadow", "archetype": "shadow"},
            "elandor": {"name": "Elandor", "class": "Sacred", "archetype": "sacred"},
            "zaremor": {"name": "ZareMor", "class": "Fractured", "archetype": "fractured"},
            "nyra": {"name": "Nyra", "class": "Shadow", "archetype": "shadow"},
            "halvren": {"name": "Halvren", "class": "Sacred", "archetype": "sacred"},
        }

        # Fetch character
        if input_data.character_id in BOOK_CHARACTERS:
            character_name = BOOK_CHARACTERS[input_data.character_id]["name"]
            character_archetype = BOOK_CHARACTERS[input_data.character_id]["archetype"]
        else:
            character_name = "Yolcu"
            character_archetype = "shadow"

        # Get character background from DB if available
        background = None
        if self.user_profile_service and input_data.user_id:
            try:
                if self.user_profile_service.is_connected():
                    if hasattr(self.user_profile_service, 'client'):
                        response = self.user_profile_service.client.table("characters").select("background").eq("id", input_data.character_id).execute()
                        if response and response.data and response.data[0].get("background"):
                            background = response.data[0]["background"]
            except Exception as e:
                logger.warning(f"Could not fetch character background: {e}")

        # Get user age category for ethics evaluation
        user_age_category = None
        if self.user_profile_service and input_data.user_id:
            try:
                if self.user_profile_service.is_connected():
                    if hasattr(self.user_profile_service, 'client'):
                        response = self.user_profile_service.client.table("profiles").select("age_category").eq("id", input_data.user_id).execute()
                        if response and response.data and response.data[0].get("age_category"):
                            user_age_category = response.data[0]["age_category"]
            except Exception as e:
                logger.warning(f"Could not fetch user age category: {e}")

        # Get engine instance
        _engine = self.get_engine_func(
            character_id=input_data.character_id,
            character_archetype=character_archetype,
            user_id=input_data.user_id,
            background=background
        )

        # Map card_id to card_type
        card_type_map = {
            "A": "shadow",
            "B": "sacred",
            "C": "silent"
        }
        selected_card_type = card_type_map.get(input_data.card_id, "shadow")

        # Process card selection (this would call engine method)
        # For now, return structure - actual processing would be in engine
        result = {
            "card_id": input_data.card_id,
            "card_type": selected_card_type,
            "processed": True
        }

        return PlayCardOutput(
            result=result,
            character_name=character_name,
            character_archetype=character_archetype,
            background=background,
            user_age_category=user_age_category
        )

