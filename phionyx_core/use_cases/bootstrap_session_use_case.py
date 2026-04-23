"""
Bootstrap Session Use Case
==========================

Business logic for bootstrapping a new game session with dynamic scenario generation.
Extracted from API route handler to core layer.
"""

import logging
from typing import Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BootstrapSessionInput:
    """Input for bootstrap session use case."""
    actor_ref: str
    character_id: str
    content_profile: Optional[str] = None


@dataclass
class BootstrapSessionOutput:
    """Output from bootstrap session use case."""
    scenario: Any  # EchoScenario
    persona: Optional[Any] = None  # Persona object


class BootstrapSessionUseCase:
    """
    Use case for bootstrapping a session.

    This encapsulates the business logic for:
    - Persona loading/creation
    - Scenario template selection
    - Fallback scenario creation
    """

    def __init__(
        self,
        persona_manager: Any,  # PersonaManager
        get_scenario_func: Any,  # Function to get scenario
        get_persona_manager_func: Any = None  # Function to get persona manager
    ):
        """
        Initialize use case.

        Args:
            persona_manager: Persona manager instance
            get_scenario_func: Function to get scenario
            get_persona_manager_func: Function to get persona manager (optional)
        """
        self.persona_manager = persona_manager
        self.get_scenario_func = get_scenario_func
        self.get_persona_manager_func = get_persona_manager_func

    async def execute(self, input_data: BootstrapSessionInput) -> BootstrapSessionOutput:
        """
        Execute the bootstrap session use case.

        Args:
            input_data: Input data for the use case

        Returns:
            BootstrapSessionOutput with scenario and persona
        """
        # Load or create persona
        persona = await self.persona_manager.get_or_create_persona(
            user_id=input_data.actor_ref,
            character_id=input_data.character_id,
            content_profile=input_data.content_profile
        )

        # Use default scenario template for now
        if input_data.content_profile == "school_13":
            scenario_id = "lyris_city_session_1"
        else:
            scenario_id = "lyris_city_session_1"  # Default

        try:
            scenario = self.get_scenario_func(scenario_id)
            # Update player character with persona data
            if persona:
                scenario.player_character.echo_profile = persona.echo_profile

            logger.info(
                f"Bootstrap session: {input_data.actor_ref}/{input_data.character_id} "
                f"(profile: {input_data.content_profile}, using template: {scenario_id})"
            )
            return BootstrapSessionOutput(
                scenario=scenario,
                persona=persona
            )
        except Exception as e:
            logger.error(f"Failed to load template scenario {scenario_id}: {e}")
            # Return minimal fallback scenario with at least one playable scene
            # Use case should not depend on echo_server schemas - delegating to handler
            logger.warning("Fallback scenario creation delegated to handler (layer isolation maintained)")
            return BootstrapSessionOutput(
                scenario=None,  # Handler will create fallback
                persona=persona
            )

