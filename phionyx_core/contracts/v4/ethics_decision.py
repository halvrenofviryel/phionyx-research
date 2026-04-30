"""
EthicsDecision — v4 Schema §3.7
=================================

Wraps existing EthicsVector + apply_ethics_enforcement() with v4
verdict enum, deliberation layer, and decision trace.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import uuid


class EthicsVerdict(str, Enum):
    """Ethics decision verdict."""
    ALLOW = "allow"                 # Action is ethically permissible
    ALLOW_WITH_GUARD = "allow_with_guard"  # Allow with safety guardrails
    DENY = "deny"                   # Action is ethically impermissible
    ESCALATE = "escalate"           # Requires human review
    DEFER = "defer"                 # Insufficient information to decide


class DeliberationLayer(str, Enum):
    """Which ethics layer made the decision."""
    RULE_BASED = "rule_based"       # Hard-coded rules (pre_response)
    POLICY_ENGINE = "policy_engine" # PolicyEngine evaluation
    DELIBERATIVE = "deliberative"   # Full deliberation (slow path)
    OVERRIDE = "override"          # Human/admin override


class EthicsDecision(BaseModel):
    """
    v4 EthicsDecision schema.

    Wraps existing ethics enforcement as a policy layer and adds
    structured verdict, deliberation trace, and decision provenance.
    """
    decision_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique decision identifier"
    )
    verdict: EthicsVerdict = Field(
        ...,
        description="Ethics verdict"
    )
    deliberation_layer: DeliberationLayer = Field(
        default=DeliberationLayer.RULE_BASED,
        description="Which layer produced this decision"
    )

    # Existing enforcement data (composed)
    enforced: bool = Field(
        default=False,
        description="Whether enforcement was triggered (from apply_ethics_enforcement)"
    )
    triggered_risks: List[str] = Field(
        default_factory=list,
        description="Risk types that triggered enforcement"
    )
    max_risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Maximum risk score across all dimensions"
    )
    safety_message: Optional[str] = Field(
        None,
        description="Safety message if enforcement triggered"
    )

    # v4 deliberation trace
    deliberation_steps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered deliberation steps with reasoning"
    )
    rules_evaluated: List[str] = Field(
        default_factory=list,
        description="Ethics rules that were evaluated"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Confidence in this decision"
    )

    # Effects
    entropy_adjustment: Optional[float] = Field(
        None,
        description="Entropy adjustment applied (e.g., 0.95 boost)"
    )
    amplitude_damping: Optional[float] = Field(
        None,
        description="Amplitude damping factor applied (e.g., 0.3)"
    )

    # Provenance
    source_action_id: Optional[str] = Field(
        None,
        description="ActionIntent that triggered this evaluation"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={'example': {'verdict': 'allow', 'deliberation_layer': 'rule_based', 'enforced': False, 'max_risk_score': 0.2}})
