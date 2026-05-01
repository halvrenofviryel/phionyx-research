"""
Participant Reference - Core Abstraction
========================================

Core abstraction for participant references to maintain layer isolation.
This allows phionyx_core to work with participants without depending on bridge.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ParticipantType(str, Enum):
    """Participant type enumeration."""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SYSTEM = "system"


class ParticipantRef(BaseModel):
    """
    Participant reference - core abstraction.

    This is a core-neutral representation of a participant.
    Bridge implementations should map their participant models to this.
    """
    id: str = Field(..., description="Participant identifier")
    type: ParticipantType = Field(..., description="Participant type")
    name: str | None = Field(None, description="Participant name")
    metadata: dict | None = Field(None, description="Additional metadata")

    model_config = ConfigDict(use_enum_values=True)
