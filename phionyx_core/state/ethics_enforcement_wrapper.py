"""
Ethics Enforcement Wrapper
============================

Wrapper class for backward compatibility with tests.
"""

from typing import Any

from .ethics import EthicsVector
from .ethics_enforcement import EthicsEnforcementConfig, apply_ethics_enforcement


class EthicsEnforcement:
    """
    Ethics enforcement class (wrapper for backward compatibility).

    Wraps apply_ethics_enforcement function for class-based API.
    """

    def __init__(self, config: EthicsEnforcementConfig | None = None):
        """Initialize ethics enforcement."""
        self.config = config or EthicsEnforcementConfig()

    def check_risk(
        self,
        ethics_vector: EthicsVector,
        current_entropy: float,
        base_amplitude: float
    ) -> dict[str, Any]:
        """
        Check risk and apply enforcement if needed.

        Args:
            ethics_vector: EthicsVector with risk scores
            current_entropy: Current entropy H
            base_amplitude: Base response amplitude

        Returns:
            Enforcement result dictionary
        """
        return apply_ethics_enforcement(
            ethics_vector=ethics_vector,
            current_entropy=current_entropy,
            base_amplitude=base_amplitude,
            config=self.config
        )

