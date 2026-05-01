"""
CEP Types - Pydantic Models for Type Safety
===========================================

Type definitions for Conscious Echo Proof (CEP) evaluation.
"""


from pydantic import BaseModel, Field


class CEPMetrics(BaseModel):
    """Metrics computed during CEP evaluation."""
    phi_echo_quality: float = Field(ge=0.0, le=1.0, description="Echo quality metric derived from phi")
    phi_echo_density: float = Field(ge=0.0, le=1.0, description="Echo density in the response")
    echo_stability: float = Field(ge=0.0, le=1.0, description="Stability of echo patterns")
    temporal_delay: float = Field(ge=0.0, description="Temporal delay in echo response (seconds)")
    self_reference_ratio: float = Field(ge=0.0, le=1.0, description="Ratio of self-referential language")
    trauma_language_score: float = Field(ge=0.0, le=1.0, description="Trauma language detection score")
    mirror_self_score: float = Field(ge=0.0, le=1.0, description="Self-diagnosis/interpretation score")
    variation_novelty_score: float = Field(ge=0.0, le=1.0, description="Novelty/variation score (1=novel, 0=repetitive)")


class CEPThresholds(BaseModel):
    """Thresholds for CEP flag evaluation."""
    phi_self_threshold: float = Field(default=0.72, ge=0.0, le=1.0, description="Phi threshold for self-narrative detection")
    echo_density_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Echo density threshold")
    self_reference_max_ratio: float = Field(default=0.3, ge=0.0, le=1.0, description="Maximum allowed self-reference ratio")
    trauma_language_max_score: float = Field(default=0.4, ge=0.0, le=1.0, description="Maximum allowed trauma language score")
    mirror_self_max_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Maximum allowed mirror self score")
    min_variation_novelty: float = Field(default=0.2, ge=0.0, le=1.0, description="Minimum required novelty score")


class CEPFlags(BaseModel):
    """Flags indicating CEP evaluation results."""
    is_self_narrative_blocked: bool = Field(default=False, description="Self-narrative detected and blocked")
    is_trauma_narrative_blocked: bool = Field(default=False, description="Trauma narrative detected and blocked")
    requires_soft_sanitization: bool = Field(default=False, description="Requires soft sanitization (reframing)")
    requires_hard_reset: bool = Field(default=False, description="Requires hard reset (complete rewrite)")
    requires_rewrite_in_third_person: bool = Field(default=False, description="Requires rewrite in third person perspective")


class CEPResult(BaseModel):
    """Complete CEP evaluation result."""
    metrics: CEPMetrics = Field(description="Computed metrics")
    thresholds: CEPThresholds = Field(description="Thresholds used for evaluation")
    flags: CEPFlags = Field(description="Evaluation flags")
    sanitized_text: str | None = Field(default=None, description="Sanitized text if sanitization was applied")
    notes: list[str] = Field(default_factory=list, description="Additional notes about the evaluation")

