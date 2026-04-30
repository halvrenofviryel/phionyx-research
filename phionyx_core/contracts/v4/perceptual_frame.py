"""
PerceptualFrame — v4 Schema §3.2
==================================

Composes BlockContext + MeasurementVector with v4 perceptual fields.
AD-1: Composition — existing models are referenced, not replaced.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone


class Modality(str, Enum):
    """Perceptual modality type."""
    TEXT = "text"
    AUDIO = "audio"
    VISUAL = "visual"
    SENSOR = "sensor"
    PROPRIOCEPTIVE = "proprioceptive"


class PerceptualFrame(BaseModel):
    """
    v4 PerceptualFrame schema.

    Represents a processed perceptual snapshot after raw input has been
    parsed by the perception engine. Composes MeasurementVector from
    state/measurement_mapper.py.
    """
    # Measurement data (from MeasurementVector)
    A_meas: float = Field(..., ge=0.0, le=1.0, description="Measured arousal")
    V_meas: float = Field(..., ge=-1.0, le=1.0, description="Measured valence")
    H_meas: float = Field(..., ge=0.0, le=1.0, description="Measured entropy")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Measurement confidence")

    # v4 new fields
    modality: Modality = Field(
        default=Modality.TEXT,
        description="Primary modality of this frame"
    )
    salience: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="Salience score — how attention-worthy this frame is"
    )
    semantic_tags: List[str] = Field(
        default_factory=list,
        description="Semantic tags extracted from input"
    )
    intent_vector: Optional[Dict[str, float]] = Field(
        None,
        description="Intent classification distribution"
    )
    entity_mentions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Named entities detected in input"
    )
    source_signal_id: Optional[str] = Field(
        None,
        description="Reference to originating InputSignal"
    )
    frame_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Frame creation timestamp"
    )
    raw_features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw feature vector for downstream processing"
    )

    model_config = ConfigDict(json_schema_extra={'example': {'A_meas': 0.6, 'V_meas': 0.3, 'H_meas': 0.4, 'confidence': 0.85, 'modality': 'text', 'salience': 0.7}})
