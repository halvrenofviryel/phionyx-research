"""
Semantic Time Decay (Patent Aile 4)
====================================

Time decay implementation based on semantic time (t_local, t_global) rather than
wall-clock time. This is a core component of Patent Family 4: Semantic Time & Cognitive Integrity.

Key Concepts:
- Semantic Time: Time measured by cognitive impact, not wall-clock time
- t_local: Time since last emotional effect (seconds)
- t_global: Time since relationship start (seconds)
- Decay Rate (λ): Exponential decay rate based on semantic time
- Half-life: Time for memory/state to decay to half its value

Mathematical Model:
- Decay Factor: decay_factor = exp(-λ * t_semantic)
- λ (decay rate) = ln(2) / half_life_seconds
- Weight after decay: weight(t) = weight(0) * exp(-λ * t)
"""

import math
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def calculate_decay_rate(half_life_seconds: float) -> float:
    """
    Calculate decay rate (λ) from half-life.

    Formula: λ = ln(2) / half_life_seconds

    Args:
        half_life_seconds: Half-life in seconds

    Returns:
        Decay rate (λ)
    """
    if half_life_seconds <= 0:
        return 0.0  # No decay

    return math.log(2.0) / half_life_seconds


def calculate_decay_factor(
    time_elapsed: float,
    decay_rate: Optional[float] = None,
    half_life_seconds: Optional[float] = None
) -> float:
    """
    Calculate decay factor using exponential decay.

    Formula: decay_factor = exp(-λ * t)

    Args:
        time_elapsed: Time elapsed (t_semantic) in seconds
        decay_rate: Decay rate (λ). If None, calculated from half_life_seconds
        half_life_seconds: Half-life in seconds. Used if decay_rate is None

    Returns:
        Decay factor (0.0 to 1.0)
    """
    if time_elapsed < 0:
        time_elapsed = 0.0

    # Calculate decay rate if not provided
    if decay_rate is None:
        if half_life_seconds is None or half_life_seconds <= 0:
            return 1.0  # No decay
        decay_rate = calculate_decay_rate(half_life_seconds)

    if decay_rate <= 0:
        return 1.0  # No decay

    # Exponential decay: decay_factor = exp(-λ * t)
    decay_factor = math.exp(-decay_rate * time_elapsed)

    # Clamp to [0, 1]
    return max(0.0, min(1.0, decay_factor))


def apply_semantic_time_decay(
    initial_value: float,
    t_local: float,
    t_global: float,
    decay_rate: Optional[float] = None,
    half_life_seconds: Optional[float] = None,
    use_local_time: bool = True
) -> float:
    """
    Apply semantic time decay to a value.

    Uses semantic time (t_local or t_global) instead of wall-clock time.
    This is the core implementation of Patent Family 4: Semantic Time.

    Args:
        initial_value: Initial value to decay
        t_local: Semantic time since last update (seconds)
        t_global: Semantic time since relationship start (seconds)
        decay_rate: Decay rate (λ). If None, calculated from half_life_seconds
        half_life_seconds: Half-life in seconds. Used if decay_rate is None
        use_local_time: If True, use t_local. If False, use t_global

    Returns:
        Decayed value
    """
    # Select semantic time
    t_semantic = t_local if use_local_time else t_global

    # Calculate decay factor
    decay_factor = calculate_decay_factor(
        time_elapsed=t_semantic,
        decay_rate=decay_rate,
        half_life_seconds=half_life_seconds
    )

    # Apply decay
    decayed_value = initial_value * decay_factor

    return decayed_value


def calculate_semantic_time_decay_metadata(
    t_local: float,
    t_global: float,
    decay_rate: Optional[float] = None,
    half_life_seconds: Optional[float] = None,
    use_local_time: bool = True
) -> Dict[str, Any]:
    """
    Calculate semantic time decay metadata for reporting and debugging.

    Args:
        t_local: Semantic time since last update (seconds)
        t_global: Semantic time since relationship start (seconds)
        decay_rate: Decay rate (λ). If None, calculated from half_life_seconds
        half_life_seconds: Half-life in seconds. Used if decay_rate is None
        use_local_time: If True, use t_local. If False, use t_global

    Returns:
        Dictionary with decay metadata
    """
    # Calculate decay rate if not provided
    if decay_rate is None:
        if half_life_seconds is None or half_life_seconds <= 0:
            decay_rate = 0.0
        else:
            decay_rate = calculate_decay_rate(half_life_seconds)

    # Select semantic time
    t_semantic = t_local if use_local_time else t_global

    # Calculate decay factor
    decay_factor = calculate_decay_factor(
        time_elapsed=t_semantic,
        decay_rate=decay_rate,
        half_life_seconds=half_life_seconds
    )

    return {
        "t_semantic": t_semantic,
        "t_local": t_local,
        "t_global": t_global,
        "decay_rate": decay_rate,
        "half_life_seconds": half_life_seconds,
        "decay_factor": decay_factor,
        "use_local_time": use_local_time,
        "patent_family": "Aile 4: Semantic Time & Cognitive Integrity"
    }


class SemanticTimeDecayManager:
    """
    Semantic Time Decay Manager (Patent Aile 4).

    Manages time decay based on semantic time (t_local, t_global) rather than
    wall-clock time. This is the core implementation of Patent Family 4.

    Features:
    - Exponential decay based on semantic time
    - Configurable half-life and decay rates
    - Support for both t_local and t_global
    - Decay metadata for reporting
    """

    def __init__(
        self,
        default_half_life_seconds: float = 3600.0,  # 1 hour default
        use_local_time: bool = True
    ):
        """
        Initialize Semantic Time Decay Manager.

        Args:
            default_half_life_seconds: Default half-life in seconds
            use_local_time: If True, use t_local by default. If False, use t_global
        """
        self.default_half_life_seconds = default_half_life_seconds
        self.default_decay_rate = calculate_decay_rate(default_half_life_seconds)
        self.use_local_time = use_local_time

    def decay_value(
        self,
        initial_value: float,
        t_local: float,
        t_global: float,
        decay_rate: Optional[float] = None,
        half_life_seconds: Optional[float] = None,
        use_local_time: Optional[bool] = None
    ) -> float:
        """
        Apply semantic time decay to a value.

        Args:
            initial_value: Initial value to decay
            t_local: Semantic time since last update (seconds)
            t_global: Semantic time since relationship start (seconds)
            decay_rate: Decay rate (λ). If None, uses default
            half_life_seconds: Half-life in seconds. Used if decay_rate is None
            use_local_time: If True, use t_local. If None, uses default

        Returns:
            Decayed value
        """
        if decay_rate is None and half_life_seconds is None:
            decay_rate = self.default_decay_rate

        if use_local_time is None:
            use_local_time = self.use_local_time

        return apply_semantic_time_decay(
            initial_value=initial_value,
            t_local=t_local,
            t_global=t_global,
            decay_rate=decay_rate,
            half_life_seconds=half_life_seconds,
            use_local_time=use_local_time
        )

    def get_decay_metadata(
        self,
        t_local: float,
        t_global: float,
        decay_rate: Optional[float] = None,
        half_life_seconds: Optional[float] = None,
        use_local_time: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get decay metadata.

        Args:
            t_local: Semantic time since last update (seconds)
            t_global: Semantic time since relationship start (seconds)
            decay_rate: Decay rate (λ). If None, uses default
            half_life_seconds: Half-life in seconds. Used if decay_rate is None
            use_local_time: If True, use t_local. If None, uses default

        Returns:
            Dictionary with decay metadata
        """
        if decay_rate is None and half_life_seconds is None:
            decay_rate = self.default_decay_rate

        if use_local_time is None:
            use_local_time = self.use_local_time

        return calculate_semantic_time_decay_metadata(
            t_local=t_local,
            t_global=t_global,
            decay_rate=decay_rate,
            half_life_seconds=half_life_seconds,
            use_local_time=use_local_time
        )

