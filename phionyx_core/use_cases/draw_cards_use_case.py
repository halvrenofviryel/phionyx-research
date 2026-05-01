"""
Draw Cards Use Case
===================

Business logic for drawing initial cards in card-based interactive fiction.
Extracted from API route handler to core layer.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DrawCardsInput:
    """Input for draw cards use case."""
    character_id: str
    profile_name: str | None = None
    content_profile: str | None = None
    user_id: str | None = None


@dataclass
class DrawCardsOutput:
    """Output from draw cards use case."""
    cards: dict[str, Any]
    character_name: str
    character_archetype: str
    profile_name: str
    character_class: str = "Shadow"
    initial_integrity: float | None = None
    background: str | None = None


class DrawCardsUseCase:
    """
    Use case for drawing initial cards.

    This encapsulates the business logic for:
    - Character data fetching
    - Profile name mapping
    - Engine initialization
    - Card generation
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

    async def execute(self, input_data: DrawCardsInput) -> DrawCardsOutput:
        """
        Execute the draw cards use case.

        Args:
            input_data: Input data for the use case

        Returns:
            DrawCardsOutput with cards and character info
        """
        # Book characters mapping
        BOOK_CHARACTERS = {
            "targaven": {"name": "Targaven", "class": "Sacred", "title": "Sözün Gücü", "archetype": "sacred"},
            "zyrelthe": {"name": "Zyrelthé", "class": "Silent", "title": "Sessizliğin Derinliği", "archetype": "silent"},
            "elion": {"name": "Elion", "class": "Fractured", "title": "Rüyalarda Yankı", "archetype": "fractured"},
            "althea": {"name": "Althea", "class": "Shadow", "title": "Dengede Aşk (Kuzey)", "archetype": "shadow"},
            "elandor": {"name": "Elandor", "class": "Sacred", "title": "Dengede Aşk (Güney)", "archetype": "sacred"},
            "zaremor": {"name": "ZareMor", "class": "Fractured", "title": "Düzenin Yıkılışı", "archetype": "fractured"},
            "nyra": {"name": "Nyra", "class": "Shadow", "title": "Gölgede Yürüyen", "archetype": "shadow"},
            "halvren": {"name": "Halvren", "class": "Sacred", "title": "Terazi'nin Bekçisi", "archetype": "sacred"},
        }

        # Fetch or create character data
        if input_data.character_id in BOOK_CHARACTERS:
            char_data = BOOK_CHARACTERS[input_data.character_id]
            character_name = char_data["name"]
            character_class = char_data["class"]
            archetype = char_data["archetype"]
            initial_integrity = None
            background = None
        else:
            # Try to get custom character from DB
            character_name = "Yolcu"
            character_class = "Shadow"
            archetype = "shadow"
            initial_integrity = None
            background = None

            if self.user_profile_service and input_data.user_id:
                try:
                    if self.user_profile_service.is_connected():
                        response = self.user_profile_service.client.table("characters").select("*").eq("id", input_data.character_id).execute()
                        if response.data:
                            char_data = response.data[0]
                            character_name = char_data.get("name", "Yolcu")
                            character_class = char_data.get("echo_type", "Shadow")
                            archetype = char_data.get("archetype", "shadow")
                            initial_integrity = float(char_data.get("echo_integrity", 100.0))
                            background = char_data.get("background", None)
                except Exception as db_error:
                    logger.warning(f"Database error (running offline): {db_error}")

        # Determine profile_name from query params or default
        profile_name_for_engine = "edu"  # Default
        if input_data.profile_name:
            profile_name_lower = input_data.profile_name.lower()
            if "school" in profile_name_lower or profile_name_lower == "edu":
                profile_name_for_engine = "edu"
            elif "game" in profile_name_lower or profile_name_lower == "game":
                profile_name_for_engine = "game"
            elif "clinical" in profile_name_lower or profile_name_lower == "clinical":
                profile_name_for_engine = "clinical"
        elif input_data.content_profile:
            if input_data.content_profile == "school_13":
                profile_name_for_engine = "edu"
            elif input_data.content_profile == "wanderer_16":
                profile_name_for_engine = "game"

        # Get engine instance
        _engine = self.get_engine_func(
            character_id=input_data.character_id,
            character_archetype=archetype,
            user_id=input_data.user_id,
            initial_integrity=initial_integrity,
            background=background,
            profile_name=profile_name_for_engine
        )

        # Generate cards (this would call engine method)
        # For now, return structure - actual card generation would be in engine
        cards = {
            "scene": "Initial scene text",
            "cards": [
                {"id": "A", "text": "Card A", "type": "shadow"},
                {"id": "B", "text": "Card B", "type": "sacred"},
                {"id": "C", "text": "Card C", "type": "silent"}
            ]
        }

        return DrawCardsOutput(
            cards=cards,
            character_name=character_name,
            character_archetype=archetype,
            profile_name=profile_name_for_engine,
            character_class=character_class,
            initial_integrity=initial_integrity,
            background=background
        )

