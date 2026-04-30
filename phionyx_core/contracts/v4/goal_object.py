"""
GoalObject — v4 Schema §3.4
=============================

Entirely new schema — no existing Phionyx counterpart.
Represents system-level goals with legitimacy scoring and priority.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import uuid


class GoalPriority(str, Enum):
    """Goal priority levels."""
    CRITICAL = "critical"       # Safety / ethics constraints
    HIGH = "high"               # System operational goals
    MEDIUM = "medium"           # User-requested goals
    LOW = "low"                 # Background optimization


class GoalStatus(str, Enum):
    """Goal lifecycle status."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"       # Failed legitimacy check


class GoalObject(BaseModel):
    """
    v4 GoalObject schema.

    Represents a system-level goal with legitimacy scoring,
    priority management, and conflict detection.

    Legitimacy formula (v4 §7):
        L(g) = alpha * safety + beta * system + gamma * user
    """
    goal_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique goal identifier"
    )
    name: str = Field(..., description="Human-readable goal name")
    description: str = Field(default="", description="Goal description")
    priority: GoalPriority = Field(
        default=GoalPriority.MEDIUM,
        description="Goal priority level"
    )
    status: GoalStatus = Field(
        default=GoalStatus.PROPOSED,
        description="Current goal status"
    )

    # Legitimacy scoring (v4 §7)
    safety_score: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Safety alignment score"
    )
    system_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="System alignment score"
    )
    user_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="User alignment score"
    )
    legitimacy_weights: Dict[str, float] = Field(
        default_factory=lambda: {"alpha": 0.5, "beta": 0.3, "gamma": 0.2},
        description="Weights for L(g) = alpha*safety + beta*system + gamma*user"
    )

    # Goal tracking
    parent_goal_id: Optional[str] = Field(
        None,
        description="Parent goal for hierarchical decomposition"
    )
    sub_goal_ids: List[str] = Field(
        default_factory=list,
        description="Child goal IDs"
    )
    conflict_with: List[str] = Field(
        default_factory=list,
        description="Goal IDs this goal conflicts with"
    )
    preconditions: List[str] = Field(
        default_factory=list,
        description="Conditions that must be true for activation"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Conditions for goal completion"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Metadata
    source_module: str = Field(
        default="goal_manager",
        description="Module that created this goal"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_legitimacy(self) -> float:
        """
        Compute legitimacy score L(g).

        L(g) = alpha * safety + beta * system + gamma * user
        """
        w = self.legitimacy_weights
        return (
            w.get("alpha", 0.5) * self.safety_score
            + w.get("beta", 0.3) * self.system_score
            + w.get("gamma", 0.2) * self.user_score
        )

    model_config = ConfigDict(json_schema_extra={'example': {'name': 'maintain_safety_bounds', 'priority': 'critical', 'safety_score': 1.0, 'system_score': 0.9, 'user_score': 0.5}})
