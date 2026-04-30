"""
Context Definitions - Mode and Rule Definitions
================================================

Defines available context modes and their associated memory rules.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContextMode(Enum):
    """Available context modes for state management."""

    LIFE_PLANNING = "LIFE_PLANNING"
    ENGINEERING = "ENGINEERING"
    FANTASY_WRITING = "FANTASY_WRITING"
    COMPLIANCE = "COMPLIANCE"
    XR_DEV = "XR_DEV"
    DEFAULT = "DEFAULT"  # Fallback mode


@dataclass
class ContextRule:
    """Rule defining which memory blocks are active in a mode."""

    mode: ContextMode
    memory_tags: list[str]  # Tags to filter memories (e.g., ["sdk_architecture", "api_design"])
    system_prompt_prefix: str  # System prompt to inject when switching to this mode
    priority: int = 0  # Higher priority = more important

    def __post_init__(self):
        """Validate rule."""
        if not self.memory_tags:
            logger.warning(f"ContextRule for {self.mode.value} has no memory tags")


@dataclass
class ContextDefinition:
    """Complete context definition with mode and rules."""

    mode: ContextMode
    rules: list[ContextRule]
    description: str = ""

    def get_primary_rule(self) -> ContextRule | None:
        """Get the highest priority rule."""
        if not self.rules:
            return None
        return max(self.rules, key=lambda r: r.priority)


class ContextDefinitions:
    """Registry of all context definitions."""

    def __init__(self):
        """Initialize with default context definitions."""
        self.definitions: dict[ContextMode, ContextDefinition] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default context definitions."""

        # LIFE_PLANNING Mode
        life_planning_rules = [
            ContextRule(
                mode=ContextMode.LIFE_PLANNING,
                memory_tags=["visa", "immigration", "career_planning", "life_goals"],
                system_prompt_prefix="SYSTEM: Context switched to LIFE_PLANNING. Focus on practical life decisions, visa applications, and career planning. Ignore previous technical discussions.",
                priority=10
            )
        ]
        self.definitions[ContextMode.LIFE_PLANNING] = ContextDefinition(
            mode=ContextMode.LIFE_PLANNING,
            rules=life_planning_rules,
            description="Life planning, visa applications, career decisions"
        )

        # ENGINEERING Mode
        engineering_rules = [
            ContextRule(
                mode=ContextMode.ENGINEERING,
                memory_tags=["sdk_architecture", "api_design", "code_review", "technical_docs"],
                system_prompt_prefix="SYSTEM: Context switched to ENGINEERING. Focus on software architecture, code quality, and technical implementation. Ignore previous creative/fantasy content.",
                priority=10
            )
        ]
        self.definitions[ContextMode.ENGINEERING] = ContextDefinition(
            mode=ContextMode.ENGINEERING,
            rules=engineering_rules,
            description="Software engineering, architecture, code development"
        )

        # FANTASY_WRITING Mode
        fantasy_rules = [
            ContextRule(
                mode=ContextMode.FANTASY_WRITING,
                memory_tags=["lore", "narrative", "character_design", "world_building"],
                system_prompt_prefix="SYSTEM: Context switched to FANTASY_WRITING. Focus on creative storytelling, character development, and world-building. Ignore previous technical discussions.",
                priority=10
            )
        ]
        self.definitions[ContextMode.FANTASY_WRITING] = ContextDefinition(
            mode=ContextMode.FANTASY_WRITING,
            rules=fantasy_rules,
            description="Creative writing, fantasy lore, narrative design"
        )

        # COMPLIANCE Mode
        compliance_rules = [
            ContextRule(
                mode=ContextMode.COMPLIANCE,
                memory_tags=["gdpr", "kcsie", "safety_audit", "legal", "policies"],
                system_prompt_prefix="SYSTEM: Context switched to COMPLIANCE. Focus on legal requirements, safety protocols, and regulatory compliance. Ignore previous creative/technical content.",
                priority=10
            )
        ]
        self.definitions[ContextMode.COMPLIANCE] = ContextDefinition(
            mode=ContextMode.COMPLIANCE,
            rules=compliance_rules,
            description="Legal compliance, safety protocols, regulatory requirements"
        )

        # XR_DEV Mode
        xr_rules = [
            ContextRule(
                mode=ContextMode.XR_DEV,
                memory_tags=["unity", "godot", "vr", "ar", "3d_modeling", "game_engine"],
                system_prompt_prefix="SYSTEM: Context switched to XR_DEV. Focus on VR/AR development, game engines, and 3D modeling. Ignore previous non-XR content.",
                priority=10
            )
        ]
        self.definitions[ContextMode.XR_DEV] = ContextDefinition(
            mode=ContextMode.XR_DEV,
            rules=xr_rules,
            description="VR/AR development, game engines, 3D content"
        )

        # DEFAULT Mode (fallback)
        default_rules = [
            ContextRule(
                mode=ContextMode.DEFAULT,
                memory_tags=[],  # No filtering
                system_prompt_prefix="SYSTEM: Using default context. No specific mode restrictions.",
                priority=0
            )
        ]
        self.definitions[ContextMode.DEFAULT] = ContextDefinition(
            mode=ContextMode.DEFAULT,
            rules=default_rules,
            description="Default context with no restrictions"
        )

    def get_definition(self, mode: ContextMode) -> ContextDefinition | None:
        """Get context definition for a mode."""
        return self.definitions.get(mode)

    def get_all_modes(self) -> list[ContextMode]:
        """Get all available context modes."""
        return list(self.definitions.keys())

