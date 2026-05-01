"""
State Adapter - EchoState2 to UnifiedEchoState Adapter
=======================================================

Adapter for using EchoState2 in existing engine code without breaking changes.

This adapter provides backward compatibility by converting EchoState2 to
UnifiedEchoState format when needed.
"""

from __future__ import annotations

from typing import Any

from phionyx_core.state.aux_state import AuxState
from phionyx_core.state.echo_state_2 import EchoState2


class EchoState2Adapter:
    """
    Adapter for EchoState2 to work with existing engine code.

    Provides:
    - Conversion to UnifiedEchoState format (if available)
    - Dictionary format for backward compatibility
    - Property accessors for old state fields
    """

    def __init__(
        self,
        echo_state2: EchoState2,
        aux_state: AuxState | None = None
    ):
        """
        Initialize adapter.

        Args:
            echo_state2: EchoState2 instance
            aux_state: Optional AuxState instance
        """
        self.echo_state2 = echo_state2
        self.aux_state = aux_state or AuxState()

    # ============================================================
    # Property Accessors (Backward Compatibility)
    # ============================================================

    @property
    def phi(self) -> float:
        """Get phi (derived metric)."""
        return self.echo_state2.phi

    @property
    def entropy(self) -> float:
        """Get entropy."""
        return self.echo_state2.H

    @property
    def valence(self) -> float:
        """Get valence."""
        return self.echo_state2.V

    @property
    def arousal(self) -> float:
        """Get arousal."""
        return self.echo_state2.A

    @property
    def trust_score(self) -> float:
        """Get trust score from AuxState."""
        return self.aux_state.trust_score

    @property
    def regulation_score(self) -> float:
        """Get regulation score from AuxState."""
        return self.aux_state.regulation_score

    @property
    def risk_score(self) -> float:
        """Get risk score from AuxState."""
        return self.aux_state.risk_score

    @property
    def stability(self) -> float:
        """Get stability (derived from entropy)."""
        return self.echo_state2.stability

    @property
    def resonance_force(self) -> float:
        """Get resonance force (derived)."""
        return self.echo_state2.resonance

    # ============================================================
    # Dictionary Format (Backward Compatibility)
    # ============================================================

    def to_physics_state(self) -> dict[str, Any]:
        """
        Convert to physics_state dict format (backward compatibility).

        Returns:
            Dictionary in physics_state format
        """
        return {
            "phi": self.phi,
            "entropy": self.entropy,
            "valence": self.valence,
            "arousal": self.arousal,
            "stability": self.stability,
            "amplitude": self.echo_state2.A * 10.0,  # Scale to amplitude range
            "resonance_force": self.resonance_force,
            "trust_score": self.trust_score,
            "regulation_score": self.regulation_score,
            "risk_score": self.risk_score,
            "dA": self.echo_state2.dA,
            "dV": self.echo_state2.dV,
            "t_local": self.echo_state2.t_local,
            "t_global": self.echo_state2.t_global
        }

    def to_unified_echo_state_dict(self) -> dict[str, Any]:
        """
        Convert to UnifiedEchoState dict format (backward compatibility).

        Returns:
            Dictionary in UnifiedEchoState format
        """
        return {
            "phi": self.phi,
            "entropy": self.entropy,
            "resonance_force": self.resonance_force,
            "valence": self.valence,
            "arousal": self.arousal,
            "quadrant": self._compute_quadrant(),
            "trust_score": self.trust_score,
            "trust_trend": self.aux_state.trust_trend,
            "risk_score": self.risk_score,
            "high_risk_flag": self.aux_state.high_risk_flag,
            "memory_tags": [tag.semantic_context for tag in self.echo_state2.E_tags],
            "memory_strength": 0.5,  # Default
            "metadata": {
                **self.aux_state.metadata,
                "dA": self.echo_state2.dA,
                "dV": self.echo_state2.dV,
                "t_local": self.echo_state2.t_local,
                "t_global": self.echo_state2.t_global,
                "regulation_score": self.regulation_score,
                "regulation_trend": self.aux_state.regulation_trend,
                "last_update": self.echo_state2.last_update.isoformat(),
                "relationship_start": self.echo_state2.relationship_start.isoformat()
            }
        }

    def _compute_quadrant(self) -> str:
        """Compute emotional quadrant from valence and arousal."""
        V = self.valence
        A = self.arousal

        if V > 0.2 and A > 0.6:
            return "tense_positive"
        elif V > 0.2 and A <= 0.6:
            return "calm_positive"
        elif V < -0.2 and A > 0.6:
            return "tense_negative"
        elif V < -0.2 and A <= 0.6:
            return "calm_negative"
        else:
            return "calm_neutral"

    # ============================================================
    # Update Methods
    # ============================================================

    def update_from_physics_state(self, physics_state: dict[str, Any]) -> None:
        """
        Update EchoState2 from physics_state dict (backward compatibility).

        Args:
            physics_state: Physics state dictionary
        """
        # Update primary state
        if "arousal" in physics_state:
            A_new = physics_state["arousal"]
        elif "amplitude" in physics_state:
            A_new = physics_state["amplitude"] / 10.0  # Scale from amplitude
        else:
            A_new = None

        V_new = physics_state.get("valence")
        H_new = physics_state.get("entropy")

        self.echo_state2.update_state(A_new, V_new, H_new)

        # Update aux state if available
        if "trust_score" in physics_state:
            self.aux_state.update_trust(physics_state["trust_score"])
        if "regulation_score" in physics_state:
            self.aux_state.update_regulation(physics_state["regulation_score"])
        if "risk_score" in physics_state:
            self.aux_state.update_risk(physics_state["risk_score"])

