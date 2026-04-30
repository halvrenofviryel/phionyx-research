"""
UKF Adaptive Noise - Echoism Core v1.1
=======================================

Per Echoism Core v1.1:
- Dynamic R: Measurement noise adjusted by confidence (low confidence → high R)
- Dynamic Q: Process noise adjusted by emotional volatility (high volatility → high Q)
- Model quality / provider effect: sensor_quality coefficient
"""

from __future__ import annotations

import numpy as np


def calculate_dynamic_measurement_noise(
    base_R: float,
    confidence: float,
    sensor_quality: float = 1.0,
    min_R: float = 0.01,
    max_R: float = 0.5,
    eps: float = 0.01
) -> float:
    """
    Calculate dynamic measurement noise R based on confidence.

    Per Echoism Core v1.1:
    - R = R_base / max(confidence, eps)
    - Low confidence → high R (more measurement noise)
    - High confidence → low R (less measurement noise)
    - Model quality / provider effect: sensor_quality coefficient

    Args:
        base_R: Base measurement noise
        confidence: Measurement confidence (0.0-1.0)
        sensor_quality: Sensor quality coefficient (0.0-1.0, default: 1.0)
        min_R: Minimum R value
        max_R: Maximum R value
        eps: Epsilon to prevent division by zero

    Returns:
        Adjusted measurement noise R
    """
    # Adjust confidence by sensor quality
    effective_confidence = confidence * sensor_quality

    # R = R_base / max(confidence, eps)
    # Low confidence → high R
    R = base_R / max(effective_confidence, eps)

    # Clamp to bounds
    R = max(min_R, min(max_R, R))

    return R


def create_dynamic_measurement_noise_matrix(
    base_R: float,
    confidence: float,
    sensor_quality: float = 1.0,
    state_dim: int = 6,
    min_R: float = 0.01,
    max_R: float = 0.5
) -> np.ndarray:
    """
    Create dynamic measurement noise matrix R for UKF.

    Per Echoism Core v1.1:
    - R matrix is diagonal
    - Each diagonal element = dynamic_R
    - Adjusted by confidence and sensor_quality

    Args:
        base_R: Base measurement noise
        confidence: Measurement confidence (0.0-1.0)
        sensor_quality: Sensor quality coefficient
        state_dim: State dimension (default: 6)
        min_R: Minimum R value
        max_R: Maximum R value

    Returns:
        R matrix (state_dim x state_dim)
    """
    dynamic_R = calculate_dynamic_measurement_noise(
        base_R=base_R,
        confidence=confidence,
        sensor_quality=sensor_quality,
        min_R=min_R,
        max_R=max_R
    )

    # Create diagonal matrix
    R = np.eye(state_dim) * dynamic_R

    return R


def calculate_emotional_volatility(
    dA_history: list[float],
    dV_history: list[float],
    window_size: int = 5
) -> float:
    """
    Calculate emotional volatility from recent dA and dV history.

    Per Echoism Core v1.1:
    - Volatility = average of |dA| and |dV| over last N steps
    - High volatility → high Q (more process noise)
    - Low volatility → low Q (less process noise)

    Args:
        dA_history: History of dA values (last N steps)
        dV_history: History of dV values (last N steps)
        window_size: Window size for volatility calculation

    Returns:
        Volatility score (0.0-1.0)
    """
    if not dA_history or not dV_history:
        return 0.0

    # Take last N values
    dA_recent = dA_history[-window_size:] if len(dA_history) >= window_size else dA_history
    dV_recent = dV_history[-window_size:] if len(dV_history) >= window_size else dV_history

    # Calculate average absolute values
    avg_dA_abs = sum(abs(d) for d in dA_recent) / len(dA_recent) if dA_recent else 0.0
    avg_dV_abs = sum(abs(d) for d in dV_recent) / len(dV_recent) if dV_recent else 0.0

    # Volatility = average of |dA| and |dV|
    # Normalize to [0.0, 1.0] (max possible |dA| or |dV| is 1.0)
    volatility = (avg_dA_abs + avg_dV_abs) / 2.0

    return min(1.0, volatility)


def calculate_dynamic_process_noise(
    base_Q: float,
    volatility: float,
    inertia: float,
    min_Q: float = 0.01,
    max_Q: float = 0.1
) -> float:
    """
    Calculate dynamic process noise Q based on emotional volatility and inertia.

    Per Echoism Core v1.1:
    - High volatility → high Q (more flexible)
    - Low volatility → low Q (more stable)
    - Inertia (I) modulates Q adjustment (I high → Q increase more limited)

    Args:
        base_Q: Base process noise
        volatility: Emotional volatility (0.0-1.0)
        inertia: Inertia value (0.0-1.0)
        min_Q: Minimum Q value
        max_Q: Maximum Q value

    Returns:
        Adjusted process noise Q
    """
    # High volatility → high Q
    # Q = base_Q * (1 + volatility * (1 - inertia))
    # Inertia high → Q increase more limited
    volatility_factor = 1.0 + volatility * (1.0 - inertia)
    Q = base_Q * volatility_factor

    # Clamp to bounds
    Q = max(min_Q, min(max_Q, Q))

    return Q


def create_dynamic_process_noise_matrix(
    base_Q: float,
    volatility: float,
    inertia: float,
    state_dim: int = 6,
    min_Q: float = 0.01,
    max_Q: float = 0.1
) -> np.ndarray:
    """
    Create dynamic process noise matrix Q for UKF.

    Per Echoism Core v1.1:
    - Q matrix is diagonal
    - Each diagonal element = dynamic_Q
    - Adjusted by volatility and inertia

    Args:
        base_Q: Base process noise
        volatility: Emotional volatility (0.0-1.0)
        inertia: Inertia value (0.0-1.0)
        state_dim: State dimension (default: 6)
        min_Q: Minimum Q value
        max_Q: Maximum Q value

    Returns:
        Q matrix (state_dim x state_dim)
    """
    dynamic_Q = calculate_dynamic_process_noise(
        base_Q=base_Q,
        volatility=volatility,
        inertia=inertia,
        min_Q=min_Q,
        max_Q=max_Q
    )

    # Create diagonal matrix
    Q = np.eye(state_dim) * dynamic_Q

    return Q


def get_sensor_quality_from_provider(
    provider: str | None = None,
    model: str | None = None
) -> float:
    """
    Get sensor quality coefficient from LLM provider metadata.

    Per Echoism Core v1.1:
    - Model quality / provider effect on measurement confidence
    - High quality → sensor_quality = 1.0
    - Low quality → sensor_quality < 1.0

    Args:
        provider: LLM provider name (e.g., "openai", "anthropic", "local")
        model: Model name (e.g., "gpt-4", "claude-3", "llama3")

    Returns:
        Sensor quality coefficient (0.0-1.0)
    """
    # Default: assume high quality
    sensor_quality = 1.0

    # Provider-specific adjustments
    if provider:
        provider_lower = provider.lower()
        if "openai" in provider_lower or "anthropic" in provider_lower:
            sensor_quality = 1.0  # High quality
        elif "local" in provider_lower or "ollama" in provider_lower:
            sensor_quality = 0.8  # Slightly lower quality
        elif "test" in provider_lower or "mock" in provider_lower:
            sensor_quality = 0.5  # Test mode

    # Model-specific adjustments
    if model:
        model_lower = model.lower()
        if "gpt-4" in model_lower or "claude-3" in model_lower:
            sensor_quality = min(1.0, sensor_quality * 1.0)  # High quality
        elif "gpt-3.5" in model_lower:
            sensor_quality = min(1.0, sensor_quality * 0.9)  # Slightly lower
        elif "llama" in model_lower:
            sensor_quality = min(1.0, sensor_quality * 0.85)  # Lower quality

    return max(0.1, min(1.0, sensor_quality))

