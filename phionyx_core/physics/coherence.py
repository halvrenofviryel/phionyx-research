"""
Coherence Calculator - Echoism Core v1.1
=========================================

Per Echoism Core v1.1:
- C_t: Measurement-state consistency score (0.0-1.0, diagnostic)
- Low C → entropy boost signal (diagnostic only, not blocking)
- Calculated after UKF update step

Formula:
- C = normalized residual + sigmoid
- residual = |measurement - state|
- normalized_residual = max(residual_A, residual_V, residual_H) / 2.0
- C = 1 / (1 + exp(10 * (normalized_residual - 0.5)))
"""

from __future__ import annotations

import math

from .constants import (
    COHERENCE_MIDPOINT,
    COHERENCE_NORMALIZATION_FACTOR,
    COHERENCE_SIGMOID_STEEPNESS,
    CONFIDENCE_FACTOR_MAX,
    CONFIDENCE_FACTOR_MIN,
    CONFIDENCE_FALLBACK_COHERENCE,
    ENTROPY_BOOST_FACTOR,
    ENTROPY_MIN_INVARIANT,
)


def calculate_coherence(
    measurement: dict[str, float],
    state: dict[str, float],
    sigmoid_steepness: float = COHERENCE_SIGMOID_STEEPNESS
) -> float:
    """
    Calculate Coherence (C) from measurement-state consistency.

    Per Echoism Core v1.1:
    - C = normalized residual + sigmoid
    - Low C → entropy boost signal (diagnostic only, not blocking)
    - C is bounded to [0.0, 1.0]

    Args:
        measurement: z_t = {A_meas, V_meas, H_meas} from MeasurementMapper
        state: Current state {A, V, H} from EchoState2/EchoState2Plus
        sigmoid_steepness: Sigmoid steepness parameter (default: 10.0)

    Returns:
        Coherence score (0.0-1.0)
    """
    # Extract values
    A_meas = measurement.get("A_meas", state.get("A", 0.5))
    V_meas = measurement.get("V_meas", state.get("V", 0.0))
    H_meas = measurement.get("H_meas", state.get("H", 0.5))

    A_state = state.get("A", 0.5)
    V_state = state.get("V", 0.0)
    H_state = state.get("H", 0.5)

    # Calculate residuals (absolute differences)
    residual_A = abs(A_meas - A_state)
    residual_V = abs(V_meas - V_state)
    residual_H = abs(H_meas - H_state)

    # Normalized residual (0.0-1.0)
    # Max possible difference: A/V: 1.0, H: 1.0
    # Normalize by max possible difference
    max_residual = max(residual_A, residual_V, residual_H)
    normalized_residual = max_residual / COHERENCE_NORMALIZATION_FACTOR

    # Sigmoid transformation: C = 1 / (1 + exp(sigmoid_steepness * (normalized_residual - midpoint)))
    # This maps:
    # - low residual (0.0) → high C (near 1.0)
    # - high residual (1.0) → low C (near 0.0)
    # - medium residual (0.5) → C ≈ 0.5
    sigmoid_input = sigmoid_steepness * (normalized_residual - COHERENCE_MIDPOINT)
    C = 1.0 / (1.0 + math.exp(sigmoid_input))

    # Clamp to [0.0, 1.0]
    C = max(0.0, min(1.0, C))

    return C


def calculate_coherence_with_confidence(
    measurement: dict[str, float],
    state: dict[str, float],
    confidence: float,
    sigmoid_steepness: float = COHERENCE_SIGMOID_STEEPNESS
) -> float:
    """
    Calculate Coherence (C) with measurement confidence weighting.

    Per Echoism Core v1.1:
    - Low confidence → lower weight on measurement
    - Confidence affects residual calculation

    Args:
        measurement: z_t = {A_meas, V_meas, H_meas}
        state: Current state {A, V, H}
        confidence: Measurement confidence (0.0-1.0)
        sigmoid_steepness: Sigmoid steepness parameter

    Returns:
        Coherence score (0.0-1.0)
    """
    # Weight residuals by confidence
    # Low confidence → smaller effective residual (measurement less reliable)
    base_coherence = calculate_coherence(measurement, state, sigmoid_steepness)

    # Adjust coherence by confidence
    # High confidence → use base coherence
    # Low confidence → boost coherence (measurement less reliable, so state is more consistent)
    confidence_factor = CONFIDENCE_FACTOR_MIN + (CONFIDENCE_FACTOR_MAX - CONFIDENCE_FACTOR_MIN) * confidence  # Map [0,1] → [0.5, 1.0]
    adjusted_coherence = base_coherence * confidence_factor + (1.0 - confidence_factor) * CONFIDENCE_FALLBACK_COHERENCE

    return max(0.0, min(1.0, adjusted_coherence))


def get_coherence_entropy_boost(
    coherence: float,
    base_entropy: float,
    boost_factor: float = ENTROPY_BOOST_FACTOR
) -> float:
    """
    Calculate entropy boost from low coherence (diagnostic signal).

    Per Echoism Core v1.1:
    - Low C → entropy boost signal
    - Diagnostic only, not blocking
    - H never goes to 0 (clamp min 0.01)

    Args:
        coherence: Coherence score (0.0-1.0)
        base_entropy: Base entropy value
        boost_factor: Entropy boost factor (default: 0.1)

    Returns:
        Adjusted entropy (with boost if coherence is low)
    """
    # Low coherence → boost entropy
    # C = 0.0 → max boost
    # C = 1.0 → no boost
    coherence_inverse = 1.0 - coherence
    entropy_boost = coherence_inverse * boost_factor

    adjusted_entropy = base_entropy + entropy_boost

    # Clamp to [ENTROPY_MIN_INVARIANT, 1.0] (invariant: H >= ENTROPY_MIN_INVARIANT)
    adjusted_entropy = max(ENTROPY_MIN_INVARIANT, min(1.0, adjusted_entropy))

    return adjusted_entropy

