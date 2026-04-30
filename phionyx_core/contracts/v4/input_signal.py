"""
InputSignal — v4 Schema §3.1
=============================

Wraps TurnEnvelope with v4-required fields: source_module, signal_type.
AD-1: Composition — TurnEnvelope is composed, not replaced.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..envelopes.turn_envelope import TurnEnvelope


class SignalType(str, Enum):
    """Type of input signal."""
    USER_TEXT = "user_text"
    SYSTEM_EVENT = "system_event"
    SENSOR_DATA = "sensor_data"
    AGENT_MESSAGE = "agent_message"
    SCHEDULED_TRIGGER = "scheduled_trigger"


class InputSignal(BaseModel):
    """
    v4 InputSignal schema.

    Composes TurnEnvelope and adds v4 fields for multi-modal,
    multi-source signal routing.
    """
    # Composed existing model
    envelope: TurnEnvelope = Field(..., description="Wrapped TurnEnvelope for delivery guarantee")

    # v4 new fields
    source_module: str = Field(
        default="user_interface",
        description="Module that originated this signal (v4 §3.1)"
    )
    signal_type: SignalType = Field(
        default=SignalType.USER_TEXT,
        description="Signal classification for routing"
    )
    modalities: list[str] = Field(
        default_factory=lambda: ["text"],
        description="Input modalities (text, audio, image, sensor)"
    )
    priority: int = Field(
        default=0,
        ge=0, le=10,
        description="Signal priority (0=normal, 10=critical)"
    )
    trace_id: str | None = Field(
        None,
        description="Distributed trace ID for cross-module tracking"
    )
    correlation_id: str | None = Field(
        None,
        description="Correlation ID for request grouping"
    )
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Signal creation timestamp (UTC)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata"
    )

    model_config = ConfigDict(json_schema_extra={'example': {'source_module': 'user_interface', 'signal_type': 'user_text', 'modalities': ['text'], 'priority': 0}})
