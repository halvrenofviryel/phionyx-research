"""
Ethics Enforcement Wrapper
============================

Wrapper class for backward compatibility with tests.
"""

from typing import Dict, Any, Optional
from .ethics_enforcement import (
    apply_ethics_enforcement,
    EthicsEnforcementConfig
)
from .ethics import EthicsVector


class EthicsEnforcement:
    """
    Ethics enforcement class (wrapper for backward compatibility).

    Wraps apply_ethics_enforcement function for class-based API.
    """

    def __init__(self, config: Optional[EthicsEnforcementConfig] = None):
        """Initialize ethics enforcement."""
        self.config = config or EthicsEnforcementConfig()

    def check_risk(
        self,
        ethics_vector: EthicsVector,
        current_entropy: float,
        base_amplitude: float
    ) -> Dict[str, Any]:
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

