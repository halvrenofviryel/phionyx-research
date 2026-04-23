"""
NPC Echo Profile Schema
=======================

Schema for Emotional AI NPC echo profiles.
Integrates Plutchik → Circumplex → Φ Physics pipeline.
"""

from __future__ import annotations

from typing import Dict
from pydantic import BaseModel, Field


class NPCEchoProfile(BaseModel):
    """
    NPC Echo Profile for Emotional AI NPCs.

    This profile defines how an NPC processes emotions, memories, and social interactions
    through the Echo system. It bridges emotion mapping (Plutchik/Circumplex) with
    physics parameters (Φ calculation).

    Required fields:
        - npc_id: Unique NPC identifier
        - echo_type: High-level echo semantic label (optional, can be loaded from preset)

    All other fields can be loaded from emotion mapping presets via get_echo_preset().
    """

    # Required fields
    npc_id: str = Field(..., description="Unique NPC identifier")

    # Echo criteria (0.0 to 1.0)
    trace_half_life: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Memory decay rate. Higher = memories fade faster."
    )
    delay_tendency: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Reaction delay. Higher = NPC reacts slower (pending_reactions queue)."
    )
    propagation_radius: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Social influence radius. Higher = NPC affects more NPCs."
    )
    selectivity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Event filtering threshold. Higher = NPC ignores more events."
    )
    feedback_sensitivity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Policy learning rate. Higher = NPC adapts faster to feedback."
    )

    # 7 echo domains (weights 0.0 to 1.0)
    domain_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "physical": 0.3,
            "biological": 0.2,
            "psychological": 0.8,
            "social": 0.9,
            "technological": 0.4,
            "consciousness": 0.6,
            "metaphysical": 0.1,
        },
        description="Weights for 7 echo domains. Sum should be normalized."
    )

    # Emotion bridge (Circumplex → Physics)
    base_valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Base emotional valence from Circumplex model (-1.0 to +1.0)"
    )
    base_arousal: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Base arousal from Circumplex model (0.0 to 1.0)"
    )
    echo_type: str = Field(
        default="harmony_growth",
        description="High-level echo semantic label (e.g., 'harmony_growth', 'threat_vigilance')"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "npc_id": "npc_guard_01",
                "echo_type": "threat_vigilance",
                "trace_half_life": 0.3,
                "delay_tendency": 0.2,
                "propagation_radius": 0.4,
                "selectivity_threshold": 0.6,
                "feedback_sensitivity": 0.5,
                "domain_weights": {
                    "physical": 0.4,
                    "biological": 0.3,
                    "psychological": 0.7,
                    "social": 0.8,
                    "technological": 0.5,
                    "consciousness": 0.6,
                    "metaphysical": 0.2,
                },
                "base_valence": -0.7,
                "base_arousal": 0.8,
            }
        }

