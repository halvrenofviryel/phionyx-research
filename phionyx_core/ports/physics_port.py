"""
Physics Port Interface
=====================

Port interface for Physics SDK module.
Enables swapping Physics v2.1 with Null implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict


class PhysicsPort(ABC):
    """Port interface for Physics calculations."""

    @abstractmethod
    async def calculate_phi(
        self,
        amplitude: float,
        entropy: float,
        time_delta: float,
        gamma: float,
        stability: float,
        valence: float = 0.0,
        arousal: float = 1.0,
        w_c: float = 0.5,
        w_p: float = 0.5,
        context_mode: str = "DEFAULT",
        entropy_penalty_k: float = 1.0  # ⚠️ NEW: Entropy penalty coefficient (default 1.0, range [0, 2])
    ) -> Dict[str, float]:
        """
        Calculate Phi (Echo Quality) using Physics v2.1.

        Args:
            entropy_penalty_k: Entropy penalty coefficient (default 1.0, range [0, 2])
                - k = 1.0: Standard penalty (backward compatible)
                - k > 1.0: Stronger penalty (e.g., 1.2 for conservative profiles)
                - k < 1.0: Weaker penalty (e.g., 0.5 for gentler profiles to prevent Phi=0.0)

        Returns:
            Dictionary with phi, phi_cognitive, phi_physical
        """
        pass

    @abstractmethod
    async def calculate_consciousness(
        self,
        phi: float,
        entropy: float
    ) -> float:
        """Calculate consciousness index."""
        pass

    @abstractmethod
    async def calculate_resonance_force(
        self,
        phi: float,
        amplitude: float
    ) -> float:
        """Calculate resonance force."""
        pass

    @abstractmethod
    async def adjust_gamma(
        self,
        current_gamma: float,
        entropy: float,
        stability: float
    ) -> float:
        """Adjust gamma based on entropy and stability."""
        pass

