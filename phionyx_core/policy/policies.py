"""
Policy Definitions - Behavioral Policies
==========================================

Defines behavioral policies for different contexts (School vs Game).
Each policy controls temperature, tone, safety strictness, and interaction style.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Policy:
    """
    Behavioral policy configuration.

    Attributes:
        temperature: LLM temperature (0.0-1.0). Lower = more focused, Higher = more creative
        tone: Response tone ("didactic", "supportive", "mysterious", "clinical")
        safety_strictness: Safety enforcement level (1=lenient, 2=moderate, 3=strict)
        interaction_style: How to interact ("scaffolding" = Socratic method, "direct" = direct answers)
        max_tokens: Maximum response length (optional)
        system_prompt_modifier: Additional system prompt instructions (optional)
    """

    temperature: float
    tone: str
    safety_strictness: int
    interaction_style: str
    max_tokens: int | None = None
    system_prompt_modifier: str | None = None

    def __post_init__(self):
        """Validate policy parameters."""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {self.temperature}")

        if self.safety_strictness not in [1, 2, 3]:
            raise ValueError(f"Safety strictness must be 1, 2, or 3, got {self.safety_strictness}")

        valid_tones = ["didactic", "supportive", "mysterious", "clinical", "neutral"]
        if self.tone not in valid_tones:
            logger.warning(f"Tone '{self.tone}' not in standard list: {valid_tones}")

        valid_styles = ["scaffolding", "direct", "conversational", "supportive"]
        if self.interaction_style not in valid_styles:
            logger.warning(f"Interaction style '{self.interaction_style}' not in standard list: {valid_styles}")

    def to_dict(self) -> dict:
        """Convert policy to dictionary."""
        return {
            "temperature": self.temperature,
            "tone": self.tone,
            "safety_strictness": self.safety_strictness,
            "interaction_style": self.interaction_style,
            "max_tokens": self.max_tokens,
            "system_prompt_modifier": self.system_prompt_modifier,
        }


class PolicyPresets:
    """
    Predefined policy presets for common contexts.
    """

    # Teaching/Educational Context
    TEACHING_POLICY = Policy(
        temperature=0.4,  # Low temperature for focused, educational responses
        tone="supportive",  # Supportive but educational
        safety_strictness=3,  # Maximum safety (KCSIE compliance)
        interaction_style="scaffolding",  # Socratic method - guide, don't tell
        max_tokens=500,  # Reasonable length for educational responses
        system_prompt_modifier="You are a supportive educational assistant. Guide the user through discovery using the Socratic method. Ask questions that help them learn, rather than giving direct answers."
    )

    # Game/Lore Context
    LORE_POLICY = Policy(
        temperature=0.9,  # High temperature for creative, immersive storytelling
        tone="mysterious",  # Mysterious and immersive
        safety_strictness=1,  # Lenient (game context allows more creative freedom)
        interaction_style="direct",  # Direct narrative responses
        max_tokens=800,  # Longer responses for immersive storytelling
        system_prompt_modifier="You are a mysterious narrator in a fantasy world. Create immersive, atmospheric responses that draw the user into the story. Be creative and evocative."
    )

    # Safe Mode (High Risk)
    SAFE_MODE_POLICY = Policy(
        temperature=0.2,  # Very low temperature for predictable, safe responses
        tone="clinical",  # Clinical, supportive, non-triggering
        safety_strictness=3,  # Maximum safety enforcement
        interaction_style="supportive",  # Supportive but careful
        max_tokens=300,  # Shorter responses to avoid triggering content
        system_prompt_modifier="You are a supportive, clinical assistant. Use only safe, non-triggering language. Prioritize user safety above all else. If the user expresses self-harm thoughts, provide resources and support."
    )

    # Default/General Context
    DEFAULT_POLICY = Policy(
        temperature=0.7,  # Balanced creativity
        tone="supportive",  # Supportive and friendly
        safety_strictness=2,  # Moderate safety
        interaction_style="conversational",  # Natural conversation
        max_tokens=600,  # Standard response length
        system_prompt_modifier="You are a supportive assistant. Be helpful, empathetic, and clear in your responses."
    )

    # Compliance/Legal Context
    COMPLIANCE_POLICY = Policy(
        temperature=0.3,  # Low temperature for precise, compliant responses
        tone="didactic",  # Educational and precise
        safety_strictness=3,  # Maximum safety and compliance
        interaction_style="direct",  # Direct, clear answers
        max_tokens=400,  # Concise, compliant responses
        system_prompt_modifier="You are a compliance assistant. Provide accurate, legally compliant responses. Follow all regulatory requirements (GDPR, KCSIE). Do not provide legal advice."
    )

    @classmethod
    def get_preset(cls, preset_name: str) -> Policy | None:
        """
        Get a preset policy by name.

        Args:
            preset_name: Name of preset ("TEACHING_POLICY", "LORE_POLICY", etc.)

        Returns:
            Policy object or None if not found
        """
        preset_map = {
            "TEACHING_POLICY": cls.TEACHING_POLICY,
            "LORE_POLICY": cls.LORE_POLICY,
            "SAFE_MODE_POLICY": cls.SAFE_MODE_POLICY,
            "DEFAULT_POLICY": cls.DEFAULT_POLICY,
            "COMPLIANCE_POLICY": cls.COMPLIANCE_POLICY,
        }
        return preset_map.get(preset_name)

