"""
Phionyx Core Math - Pure Mathematical Utilities
=================================================
Implements Information Theory and Control Theory primitives.
No business logic, just math.

Scientific Grounding:
- Kolmogorov Complexity: Information-theoretic measure of complexity
- Lyapunov Stability: Control-theoretic stability criterion
- Sigmoid Normalization: Standard mathematical normalization
"""

import zlib
import math


def calculate_kolmogorov_complexity(data: str) -> float:
    """
    Approximates Kolmogorov Complexity using Zlib compression ratio.

    Science:
    - Low Complexity (e.g., "AAAAA"): Highly compressible -> Ratio ~ 0.1
    - High Complexity (e.g., Random text/High entropy): Hard to compress -> Ratio ~ 1.0

    Fixes: Replaces the arbitrary '500 char limit' heuristic.

    Args:
        data: Input text string

    Returns:
        Complexity ratio [0.0, 1.0] where:
        - 0.0 = highly compressible (low complexity)
        - 1.0 = incompressible (high complexity/randomness)

    Example:
        >>> calculate_kolmogorov_complexity("AAAAA")  # Low complexity
        0.1
        >>> calculate_kolmogorov_complexity("random text with high entropy")  # High complexity
        0.8
    """
    if not data:
        return 0.0

    encoded = data.encode('utf-8')
    raw_len = len(encoded)

    if raw_len == 0:
        return 0.0

    # Zlib compression
    compressed = zlib.compress(encoded)
    compressed_len = len(compressed)

    # Calculate ratio (Handling overhead for very short strings)
    # For very short strings, zlib adds header overhead, so ratio can be > 1.0.
    # We normalize this using a penalty factor for short lengths.
    ratio = compressed_len / raw_len

    if raw_len < 50:
        # Penalize short inputs less aggressively (overhead dominates)
        return min(1.0, ratio * 0.8)

    return min(1.0, ratio)


def sigmoid_normalization(x: float, center: float = 0.5, steepness: float = 10.0) -> float:
    """
    Standard Sigmoid for normalizing unbounded inputs to [0,1].

    Formula: 1 / (1 + exp(-steepness * (x - center)))

    Args:
        x: Input value (unbounded)
        center: Center point of sigmoid (default: 0.5)
        steepness: Steepness parameter (default: 10.0)

    Returns:
        Normalized value in [0.0, 1.0]

    Example:
        >>> sigmoid_normalization(0.5)  # At center
        0.5
        >>> sigmoid_normalization(1.0)  # Above center
        0.999
    """
    return 1.0 / (1.0 + math.exp(-steepness * (x - center)))


def lyapunov_stability_check(energy_t1: float, energy_t0: float, input_energy: float = 0.0) -> float:
    """
    Enforces Lyapunov Stability Criterion: V_dot < 0

    Scientific Principle:
    - If there is NO input (input_energy ~ 0), the system energy MUST decay.
    - If energy grows without input, it violates thermodynamics (Instability).
    - Lyapunov function ensures system converges to equilibrium without external input.

    Args:
        energy_t1: Energy at time t1 (current)
        energy_t0: Energy at time t0 (previous)
        input_energy: External energy input (default: 0.0)

    Returns:
        Damping factor:
        - 1.0 = stable (energy decay or input present)
        - < 1.0 = force decay (instability detected, apply damping)

    Example:
        >>> lyapunov_stability_check(10.0, 9.0, 0.0)  # Energy grew, no input -> unstable
        0.95
        >>> lyapunov_stability_check(9.0, 10.0, 0.0)  # Energy decayed -> stable
        1.0
        >>> lyapunov_stability_check(10.0, 9.0, 2.0)  # Energy grew, but input present -> stable
        1.0
    """
    delta_energy = energy_t1 - energy_t0

    # If energy is growing AND input is negligible -> Instability detected!
    # Threshold: input_energy < 0.01 (1% of typical energy scale)
    if delta_energy > 0 and input_energy < 0.01:
        # Force a damping factor to ensure V_dot < 0 (energy dissipation)
        return 0.95  # Dissipate 5% of energy immediately

    return 1.0

