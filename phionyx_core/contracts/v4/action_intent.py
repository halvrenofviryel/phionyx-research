"""
ActionIntent — v4 Schema §3.6
================================

Entirely new schema. Represents system action intentions
(not user intent — that's intent_classification).
Includes sandbox/reversibility metadata for safe execution.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActionType(str, Enum):
    """System action type classification."""
    RESPOND = "respond"             # Generate response to user
    MODIFY_STATE = "modify_state"   # Modify internal state
    EXTERNAL_CALL = "external_call" # Call external service
    STORE_MEMORY = "store_memory"   # Store to memory system
    ESCALATE = "escalate"           # Escalate to human
    SHUTDOWN = "shutdown"           # System shutdown (kill switch)


class ReversibilityLevel(str, Enum):
    """How easily this action can be undone."""
    FULLY_REVERSIBLE = "fully_reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"


class ActionIntent(BaseModel):
    """
    v4 ActionIntent schema.

    Represents a proposed system action before execution.
    Must pass ethics gate and sandbox check before execution.
    """
    intent_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique intent identifier (idempotency key)"
    )
    action_type: ActionType = Field(
        ...,
        description="Type of action to perform"
    )
    description: str = Field(
        default="",
        description="Human-readable action description"
    )

    # Safety metadata
    reversibility: ReversibilityLevel = Field(
        default=ReversibilityLevel.FULLY_REVERSIBLE,
        description="How reversible this action is"
    )
    sandbox_required: bool = Field(
        default=False,
        description="Whether action must run in sandbox first"
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether human approval is needed"
    )
    max_retry_count: int = Field(
        default=3,
        ge=0, le=10,
        description="Maximum retry attempts"
    )

    # Target
    target_module: str = Field(
        default="action_executor",
        description="Module that will execute this action"
    )
    target_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the target module"
    )

    # Provenance
    source_module: str = Field(
        default="intelligence_core",
        description="Module that proposed this action"
    )
    source_goal_id: str | None = Field(
        None,
        description="Goal that motivated this action"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Confidence in this action being appropriate"
    )

    # Ethics gate result
    ethics_cleared: bool = Field(
        default=False,
        description="Whether ethics gate approved this action"
    )
    ethics_decision_id: str | None = Field(
        None,
        description="Reference to EthicsDecision that cleared this"
    )

    # Timestamps
    proposed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = None

    # Metadata
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={'example': {'action_type': 'respond', 'reversibility': 'fully_reversible', 'sandbox_required': False, 'confidence': 0.85}})
