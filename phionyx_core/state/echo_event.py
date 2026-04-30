"""
EchoEvent - Echo Ontology: Effect → Trace → Echo → Transformation
=================================================================

Echoism Core v1.0 ontology implementation.

Chain: Effect → Trace → Echo → Transformation

This module defines:
- EchoEvent: Effect representation
- Trace: Weighted event influence on state
- Echo: Response generated from trace
- Transformation: State change from echo
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EchoEvent(BaseModel):
    """
    EchoEvent - Effect representation in Echo ontology.

    Per Echoism Core v1.0:
    - Effect: External or internal input (text, event, context)
    - Event: Structured representation of effect

    Schema:
    - type: Event type (e.g., "interaction", "memory_recall", "emotional_trigger")
    - timestamp: Event timestamp (from state.t_now)
    - intensity: Event intensity (0.0-1.0)
    - tags: Semantic tags for categorization
    - payload: Additional event data
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event ID"
    )

    type: str = Field(
        ...,
        description="Event type (e.g., 'interaction', 'memory_recall', 'emotional_trigger')"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp (should use state.t_now)"
    )

    intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Event intensity (0.0-1.0)"
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Semantic tags for categorization"
    )

    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event data"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "intensity": self.intensity,
            "tags": self.tags,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EchoEvent:
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data["type"],
            timestamp=timestamp,
            intensity=data.get("intensity", 0.5),
            tags=data.get("tags", []),
            payload=data.get("payload", {})
        )


@dataclass
class EventReference:
    """
    EventReference - Lightweight reference to event in E_tags.

    Stores only essential information for state tracking:
    - id: Event ID
    - tag: Primary semantic tag
    - intensity: Event intensity
    """
    id: str
    tag: str
    intensity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tag": self.tag,
            "intensity": self.intensity
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventReference:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            tag=data["tag"],
            intensity=data["intensity"]
        )

