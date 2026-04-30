"""
AuxState - Optional Control Layer State
========================================

Auxiliary state for trust, regulation, and other control layer metrics.

Per Echoism Core v1.0:
- Trust and regulation are moved to AuxState (optional control layer)
- Core state (EchoState2) remains independent
- AuxState provides backward compatibility
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Any, Optional
from datetime import datetime


class AuxState(BaseModel):
    """
    Auxiliary State - Optional control layer.

    Contains:
    - Trust metrics (trust_score, trust_trend)
    - Regulation metrics (regulation_score, regulation_trend)
    - Risk metrics (risk_score, high_risk_flag)
    - Other control layer metrics

    This is separate from EchoState2 (canonical state) to maintain
    Echoism Core v1.0 compliance while providing backward compatibility.
    """

    # ============================================================
    # Trust Metrics
    # ============================================================

    trust_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Trust score (0.0-1.0), higher = more trusted"
    )

    trust_trend: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Trust trend (Δtrust), positive = increasing trust"
    )

    # ============================================================
    # Regulation Metrics
    # ============================================================

    regulation_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Regulation score (0.0-1.0), higher = better self-regulation"
    )

    regulation_trend: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Regulation trend (Δregulation), positive = improving regulation"
    )

    # ============================================================
    # Risk Metrics
    # ============================================================

    risk_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk score (0.0-1.0), higher = more risk"
    )

    high_risk_flag: bool = Field(
        default=False,
        description="High risk flag, triggers safety interventions"
    )

    # ============================================================
    # Metadata
    # ============================================================

    last_update: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    # ============================================================
    # Helper Methods
    # ============================================================

    def update_trust(self, new_trust: float, previous_trust: Optional[float] = None) -> None:
        """
        Update trust score and compute trend.

        Args:
            new_trust: New trust score (0.0-1.0)
            previous_trust: Previous trust score (for trend computation)
        """
        if previous_trust is None:
            previous_trust = self.trust_score

        self.trust_score = max(0.0, min(1.0, new_trust))
        self.trust_trend = self.trust_score - previous_trust
        self.last_update = datetime.now()

    def update_regulation(self, new_regulation: float, previous_regulation: Optional[float] = None) -> None:
        """
        Update regulation score and compute trend.

        Args:
            new_regulation: New regulation score (0.0-1.0)
            previous_regulation: Previous regulation score (for trend computation)
        """
        if previous_regulation is None:
            previous_regulation = self.regulation_score

        self.regulation_score = max(0.0, min(1.0, new_regulation))
        self.regulation_trend = self.regulation_score - previous_regulation
        self.last_update = datetime.now()

    def update_risk(self, new_risk: float) -> None:
        """
        Update risk score and flag.

        Args:
            new_risk: New risk score (0.0-1.0)
        """
        self.risk_score = max(0.0, min(1.0, new_risk))
        self.high_risk_flag = self.risk_score > 0.7
        self.last_update = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (for serialization).

        Returns:
            Dictionary representation
        """
        return {
            "trust_score": self.trust_score,
            "trust_trend": self.trust_trend,
            "regulation_score": self.regulation_score,
            "regulation_trend": self.regulation_trend,
            "risk_score": self.risk_score,
            "high_risk_flag": self.high_risk_flag,
            "last_update": self.last_update.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuxState:
        """
        Create from dictionary (for deserialization).

        Args:
            data: Dictionary representation

        Returns:
            AuxState instance
        """
        last_update = datetime.fromisoformat(data.get("last_update", datetime.now().isoformat()))

        return cls(
            trust_score=data.get("trust_score", 0.5),
            trust_trend=data.get("trust_trend", 0.0),
            regulation_score=data.get("regulation_score", 0.5),
            regulation_trend=data.get("regulation_trend", 0.0),
            risk_score=data.get("risk_score", 0.0),
            high_risk_flag=data.get("high_risk_flag", False),
            last_update=last_update,
            metadata=data.get("metadata", {})
        )

    model_config = ConfigDict(validate_assignment=True)
