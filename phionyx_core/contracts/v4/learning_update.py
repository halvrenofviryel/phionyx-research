"""
LearningUpdate — v4 Schema §3.11
====================================

Extends ProfileTuner with boundary gate and approval flow.
Learning updates must pass through a gate before modifying parameters.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class LearningGateDecision(str, Enum):
    """Learning gate verdict."""
    APPROVED = "approved"       # Update can be applied
    REJECTED = "rejected"       # Update violates boundary
    PENDING = "pending"         # Awaiting human approval
    DEFERRED = "deferred"       # Queued for batch review


class LearningUpdate(BaseModel):
    """
    v4 LearningUpdate schema.

    Represents a proposed parameter update that must pass through
    a boundary gate before being applied to the system.
    """
    update_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique update identifier"
    )

    # What is being updated
    target_parameter: str = Field(
        ...,
        description="Parameter path to update (e.g., 'physics.gamma', 'profile.resilience')"
    )
    current_value: Any = Field(
        ...,
        description="Current parameter value"
    )
    proposed_value: Any = Field(
        ...,
        description="Proposed new value"
    )
    delta: Optional[float] = Field(
        None,
        description="Numeric delta (proposed - current) if applicable"
    )

    # Boundary gate
    boundary_zone: str = Field(
        default="adaptive",
        description="Which boundary zone this parameter belongs to"
    )
    gate_decision: LearningGateDecision = Field(
        default=LearningGateDecision.PENDING,
        description="Gate decision for this update"
    )
    gate_reason: str = Field(
        default="",
        description="Reason for gate decision"
    )

    # Impact analysis
    impact_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Estimated impact of this change"
    )
    affected_modules: List[str] = Field(
        default_factory=list,
        description="Modules affected by this update"
    )
    rollback_safe: bool = Field(
        default=True,
        description="Whether this update can be safely rolled back"
    )

    # Provenance
    source_module: str = Field(
        default="learning_engine",
        description="Module proposing this update"
    )
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence supporting this update"
    )
    turn_id: Optional[int] = None

    # Approval flow
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

    # Evidence criteria (Learning Gate Contract v1.0 §4)
    min_experiments: int = Field(
        default=3,
        ge=1,
        description="Minimum consistent experiments required for approval"
    )
    cqs_delta_threshold: float = Field(
        default=0.005,
        ge=0.0,
        description="Minimum |ΔCQS| to consider change significant"
    )
    rollback_procedure: str = Field(
        default="auto",
        description="Rollback strategy: 'auto' (restore original), 'manual' (founder review)"
    )

    # Timestamps
    proposed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rolled_back_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "target_parameter": "physics.gamma",
                "current_value": 0.15,
                "proposed_value": 0.18,
                "delta": 0.03,
                "boundary_zone": "adaptive",
            }
        }
