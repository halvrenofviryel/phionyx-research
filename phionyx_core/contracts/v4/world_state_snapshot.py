"""
WorldStateSnapshot — v4 Schema §3.3
=====================================

Composes EchoState2/EchoState2Plus with v4 world model fields.
AD-1: Composition — EchoState2 is composed as echo_state field.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ArbitrationStatus(str, Enum):
    """Current arbitration state."""
    STABLE = "stable"
    CONFLICT = "conflict"
    RESOLVING = "resolving"
    OVERRIDE = "override"


class WorldStateSnapshot(BaseModel):
    """
    v4 WorldStateSnapshot schema.

    Full world model state at a point in time. Composes EchoState2
    (which carries A, V, H, I, R, C, D, phi, t_local, t_global).

    Usage:
        snapshot = WorldStateSnapshot(
            echo_state=echo_state2_plus.to_dict(),
            belief_vector={...},
        )
    """
    # Composed existing model (serialized EchoState2Plus dict)
    echo_state: Dict[str, Any] = Field(
        ...,
        description="Serialized EchoState2/EchoState2Plus — primary state vector"
    )

    # v4 new fields
    belief_vector: Dict[str, float] = Field(
        default_factory=dict,
        description="Probabilistic belief distribution over world hypotheses"
    )
    arbitration_status: ArbitrationStatus = Field(
        default=ArbitrationStatus.STABLE,
        description="Current arbitration system status"
    )
    causal_graph: Optional[Dict[str, Any]] = Field(
        None,
        description="Causal dependency graph (node→edge structure)"
    )
    active_goals: List[str] = Field(
        default_factory=list,
        description="Currently active goal IDs"
    )
    pending_actions: List[str] = Field(
        default_factory=list,
        description="Action intents awaiting execution"
    )
    snapshot_version: str = Field(
        default="4.0.0",
        description="Schema version of this snapshot"
    )
    snapshot_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this snapshot was captured"
    )
    turn_index: int = Field(
        default=0,
        ge=0,
        description="Turn index at snapshot time"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "echo_state": {"A": 0.5, "V": 0.3, "H": 0.4},
                "belief_vector": {"hypothesis_a": 0.7, "hypothesis_b": 0.3},
                "arbitration_status": "stable",
            }
        }
