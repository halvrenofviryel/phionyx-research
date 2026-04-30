"""
WorkspaceEvent — v4 Schema §3.9
=================================

Extends CEP engine concept toward Global Workspace Theory (GWT).
Represents events broadcast to all modules via salience-based attention.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import uuid


class SalienceLevel(str, Enum):
    """Salience classification for broadcast priority."""
    CRITICAL = "critical"   # Broadcast to all modules immediately
    HIGH = "high"           # Broadcast to subscribed modules
    MEDIUM = "medium"       # Queue for batch processing
    LOW = "low"             # Log only, no broadcast


class WorkspaceEvent(BaseModel):
    """
    v4 WorkspaceEvent schema.

    Implements Global Workspace Theory broadcast mechanism.
    High-salience events are broadcast to all modules; low-salience
    events are queued or logged.
    """
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier"
    )
    event_type: str = Field(
        ...,
        description="Event type (e.g., 'state_change', 'ethics_trigger', 'goal_update')"
    )
    salience: SalienceLevel = Field(
        default=SalienceLevel.MEDIUM,
        description="Event salience level for broadcast routing"
    )
    salience_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Numeric salience score"
    )

    # Event payload
    source_module: str = Field(
        ...,
        description="Module that emitted this event"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload data"
    )

    # Broadcast tracking
    broadcast_targets: List[str] = Field(
        default_factory=list,
        description="Modules that should receive this event"
    )
    acknowledged_by: List[str] = Field(
        default_factory=list,
        description="Modules that acknowledged receipt"
    )

    # CEP compatibility
    cep_correlation_id: Optional[str] = Field(
        None,
        description="CEP engine correlation ID for event chains"
    )

    # Timestamps
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(
        None,
        description="Event expiration (None = no expiry)"
    )

    # Metadata
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={'example': {'event_type': 'ethics_trigger', 'salience': 'high', 'salience_score': 0.9, 'source_module': 'ethics_engine'}})
