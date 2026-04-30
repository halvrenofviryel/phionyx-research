"""
Physics Types - Pydantic Models for Type Safety
===============================================

Type definitions for physics calculations.
"""

from typing import Literal

from pydantic import BaseModel, Field


class PhysicsInput(BaseModel):
    """Input parameters for physics calculations (v2.0/v2.1)."""
    amplitude: float = Field(ge=0.0, le=10.0, description="Emotional intensity slider (A0)")
    time_delta: float = Field(ge=0.0, description="Time elapsed since decision (t)")
    entropy: float = Field(ge=0.0, le=1.0, description="Chaos level (S)")
    kappa: float = Field(default=1.0, ge=0.1, le=2.0, description="Resonance coefficient (κ)")
    gamma: float = Field(default=0.15, ge=0.05, le=0.5, description="Decay rate (γ)")
    entropy_max: float = Field(default=1.0, ge=0.0, description="Maximum entropy (S_max)")
    # v2.1 Circumplex parameters (optional for backward compatibility)
    valence: float = Field(default=0.0, ge=-1.0, le=1.0, description="Emotional valence from Circumplex (-1 to +1)")
    arousal: float = Field(default=1.0, ge=0.0, le=1.0, description="Arousal from Circumplex (0 to 1)")
    stability: float = Field(default=0.8, ge=0.0, le=1.0, description="Internal resilience (0-1)")
    w_c: float = Field(default=0.5, ge=0.0, le=1.0, description="Cognitive weight (0-1)")
    w_p: float = Field(default=0.5, ge=0.0, le=1.0, description="Physical weight (0-1)")
    entropy_penalty_k: float = Field(default=1.0, ge=0.0, le=2.0, description="Entropy penalty coefficient (0-2, default 1.0)")


class PhysicsOutput(BaseModel):
    """Output of physics calculations."""
    phi: float = Field(description="Echo Quality (Φ)")
    consciousness: float = Field(ge=0.0, le=1.0, description="Consciousness Index (C)")
    resonance_force: float = Field(description="Resonance Force (F)")
    echo_energy: float = Field(description="Echo Energy (E)")
    entropy_echo: float = Field(description="Entropy Echo (S)")
    temporal_echo: float = Field(description="Temporal Echo (T)")
    momentum: float = Field(description="Momentum (M)")
    resonance_level: Literal["high", "medium", "low", "fractured"] = Field(
        description="Resonance classification"
    )


class PhysicsState(BaseModel):
    """Complete physics state."""
    phi: float
    consciousness: float
    amplitude: float
    entropy: float
    kappa: float
    gamma: float
    trace_duration: float
    momentum: float
    resonance_force: float
    phi_trend: Literal["increasing", "stable", "decreasing"]
    timestamp: float


class NPCPhysicsParams(BaseModel):
    """
    Physics parameters for Emotional AI NPC calculations.

    This model is specifically designed for NPC emotion-to-physics mapping,
    using Plutchik → Circumplex → Φ Physics pipeline.
    """
    valence: float = Field(ge=-1.0, le=1.0, description="Emotional valence from Circumplex (-1.0 to +1.0)")
    arousal: float = Field(ge=0.0, le=1.0, description="Arousal from Circumplex (0.0 to 1.0)")
    amplitude: float = Field(ge=0.0, le=10.0, description="Emotional intensity slider (0.0 to 10.0)")
    gamma: float = Field(ge=0.0, le=1.0, description="Recovery speed / decay rate")
    stability: float = Field(ge=0.0, le=1.0, description="Internal resilience (0.0 to 1.0)")
    entropy: float = Field(ge=0.0, le=1.0, description="Chaos level (0.0 to 1.0)")
    w_cognitive: float = Field(ge=0.0, le=1.0, description="Cognitive weight (0.0 to 1.0)")
    w_physical: float = Field(ge=0.0, le=1.0, description="Physical weight (0.0 to 1.0)")
    t: float = Field(ge=0.0, description="Time (turn or normalized duration)")
    entropy_penalty_k: float = Field(default=1.0, ge=0.0, le=2.0, description="Entropy penalty coefficient (0-2, default 1.0)")

    def model_post_init(self, __context):
        """Normalize weights after initialization to ensure w_cognitive + w_physical ≈ 1.0."""
        total = self.w_cognitive + self.w_physical
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            # Normalize weights
            if total > 0:
                object.__setattr__(self, 'w_cognitive', self.w_cognitive / total)
                object.__setattr__(self, 'w_physical', self.w_physical / total)
            else:
                object.__setattr__(self, 'w_cognitive', 0.5)
                object.__setattr__(self, 'w_physical', 0.5)


class PhiComponents(BaseModel):
    """Output components of Φ calculation."""
    phi_cognitive: float = Field(ge=0.0, description="Cognitive resonance component (Φ_c)")
    phi_physical: float = Field(ge=0.0, description="Physical resonance component (Φ_p)")
    phi_total: float = Field(ge=0.0, description="Total echo quality (Φ_total)")

