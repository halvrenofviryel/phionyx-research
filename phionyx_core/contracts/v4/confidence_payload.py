"""
ConfidencePayload — v4 Schema §3.8
=====================================

Extends existing ConfidenceResult with epistemic/aleatoric decomposition,
ECE calibration, and OOD detection.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class UncertaintyType(str, Enum):
    """Uncertainty source classification."""
    EPISTEMIC = "epistemic"     # Reducible with more data
    ALEATORIC = "aleatoric"     # Irreducible noise


class ConfidencePayload(BaseModel):
    """
    v4 ConfidencePayload schema.

    Extends ConfidenceResult from meta/estimator.py with v4 fields
    for uncertainty decomposition and calibration metrics.
    """
    # Existing ConfidenceResult fields (composed)
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall confidence score"
    )
    is_uncertain: bool = Field(
        default=False,
        description="Whether system is uncertain"
    )
    recommendation: str = Field(
        default="proceed",
        description="Action recommendation (hedge/clarify/proceed/block)"
    )
    reasoning: str = Field(
        default="",
        description="Confidence score explanation"
    )

    # v4 epistemic/aleatoric decomposition
    epistemic_uncertainty: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Epistemic uncertainty (reducible with more data)"
    )
    aleatoric_uncertainty: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Aleatoric uncertainty (irreducible noise)"
    )
    dominant_uncertainty: UncertaintyType = Field(
        default=UncertaintyType.EPISTEMIC,
        description="Which uncertainty type dominates"
    )

    # Calibration (v4 §7)
    ece_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Expected Calibration Error"
    )
    ood_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Out-of-Distribution score"
    )

    # Meta-cognitive trust (T_meta)
    t_meta: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="T_meta = (1-ECE)*(1-OOD)*(1-|self_report_delta|)"
    )
    self_report_delta: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Discrepancy between self-reported and actual confidence"
    )

    # Ensemble data (for decomposition)
    ensemble_predictions: Optional[List[float]] = Field(
        None,
        description="Predictions from ensemble members"
    )
    ensemble_variance: Optional[float] = Field(
        None, ge=0.0,
        description="Variance across ensemble members"
    )

    # Source tracking
    source_estimator: str = Field(
        default="confidence_estimator",
        description="Which estimator produced this payload"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "confidence_score": 0.82,
                "epistemic_uncertainty": 0.12,
                "aleatoric_uncertainty": 0.06,
                "dominant_uncertainty": "epistemic",
            }
        }
