"""
Inertia (I) Effects - Echoism Core v1.1
========================================

Per Echoism Core v1.1:
- I: Emotional change resistance (0.0-1.0, mandatory)
- I high → slower change (lower decay rate, lower UKF Q, lower gain)
- I low → faster change (higher decay rate, higher UKF Q, higher gain)
- I is fixed/slowly-updated in v1.1 (not auto-learning)
- Profile-based initial I assignment (age group / persona)
"""

from __future__ import annotations

from typing import Dict, Any, Optional


# Module-level tunable defaults (Tier A — PRE surfaces)
UKF_MIN_Q = 0.01
UKF_MAX_Q = 0.1
DERIVATIVE_MIN_GAIN = 0.1
DERIVATIVE_MAX_GAIN = 1.0


def apply_inertia_to_decay_rate(
    base_decay_rate: float,
    inertia: float
) -> float:
    """
    Apply Inertia (I) to decay rate λ.

    Per Echoism Core v1.1:
    - I high → λ low (slower change)
    - I low → λ high (faster change)

    Formula: λ = base_decay_rate * (1 - I)

    Args:
        base_decay_rate: Base decay rate
        inertia: Inertia value (0.0-1.0)

    Returns:
        Adjusted decay rate (clamped to reasonable bounds)
    """
    # I high → λ low: λ = base_decay_rate * (1 - I)
    adjusted = base_decay_rate * (1.0 - inertia)

    # Clamp to reasonable bounds
    min_decay = 0.001
    max_decay = 1.0
    return max(min_decay, min(max_decay, adjusted))


def apply_inertia_to_ukf_process_noise(
    base_Q: float,
    inertia: float,
    min_Q: float = UKF_MIN_Q,
    max_Q: float = UKF_MAX_Q
) -> float:
    """
    Apply Inertia (I) to UKF process noise Q.

    Per Echoism Core v1.1:
    - I high → Q low (more stable, less process noise)
    - I low → Q high (more flexible, more process noise)

    Args:
        base_Q: Base process noise
        inertia: Inertia value (0.0-1.0)
        min_Q: Minimum Q value
        max_Q: Maximum Q value

    Returns:
        Adjusted process noise Q
    """
    # I high → Q low: Q = base_Q * (1 - I)
    adjusted = base_Q * (1.0 - inertia)

    # Clamp to bounds
    return max(min_Q, min(max_Q, adjusted))


def apply_inertia_to_derivative_gain(
    base_gain: float,
    inertia: float,
    min_gain: float = DERIVATIVE_MIN_GAIN,
    max_gain: float = DERIVATIVE_MAX_GAIN
) -> float:
    """
    Apply Inertia (I) to A/V derivative update gain.

    Per Echoism Core v1.1:
    - I high → lower gain (slower A/V change)
    - I low → higher gain (faster A/V change)

    Args:
        base_gain: Base gain for derivative updates
        inertia: Inertia value (0.0-1.0)
        min_gain: Minimum gain
        max_gain: Maximum gain

    Returns:
        Adjusted gain
    """
    # I high → gain low: gain = base_gain * (1 - I)
    adjusted = base_gain * (1.0 - inertia)

    # Clamp to bounds
    return max(min_gain, min(max_gain, adjusted))


def get_inertia_from_profile(
    profile: Optional[Dict[str, Any]] = None,
    age_group: Optional[str] = None,
    persona: Optional[str] = None
) -> float:
    """
    Get initial Inertia (I) from profile, age group, or persona.

    Per Echoism Core v1.1:
    - Profile-based initial I assignment
    - Age group: younger → lower I, older → higher I
    - Persona: introvert → higher I, extrovert → lower I

    Args:
        profile: Profile dictionary (may contain 'inertia' or 'I' field)
        age_group: Age group string (e.g., "13-15", "16-18", "adult")
        persona: Persona string (e.g., "introvert", "extrovert", "balanced")

    Returns:
        Initial Inertia value (0.0-1.0)
    """
    # Check profile first
    if profile:
        if "inertia" in profile:
            return max(0.0, min(1.0, float(profile["inertia"])))
        if "I" in profile:
            return max(0.0, min(1.0, float(profile["I"])))

    # Age group mapping
    age_inertia = 0.5  # Default
    if age_group:
        if "13" in age_group or "14" in age_group or "15" in age_group:
            age_inertia = 0.4  # Younger: lower I (more changeable)
        elif "16" in age_group or "17" in age_group or "18" in age_group:
            age_inertia = 0.6  # Older: higher I (more stable)
        elif "adult" in age_group.lower():
            age_inertia = 0.7  # Adult: highest I (most stable)

    # Persona mapping
    persona_inertia = 0.0  # Adjustment
    if persona:
        if "introvert" in persona.lower():
            persona_inertia = 0.2  # Introvert: higher I
        elif "extrovert" in persona.lower():
            persona_inertia = -0.2  # Extrovert: lower I

    # Combine: base + persona adjustment
    I = age_inertia + persona_inertia  # noqa: E741

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, I))


def update_inertia_slowly(
    current_I: float,
    target_I: float,
    learning_rate: float = 0.01
) -> float:
    """
    Slowly update Inertia (I) towards target (v1.1: fixed/slowly-updated).

    Per Echoism Core v1.1:
    - I is not auto-learning, but can be slowly updated
    - Used for gradual personality drift or adaptation

    Args:
        current_I: Current Inertia value
        target_I: Target Inertia value
        learning_rate: Learning rate (default: 0.01, very slow)

    Returns:
        Updated Inertia value
    """
    # Simple linear interpolation
    I_new = current_I + (target_I - current_I) * learning_rate

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, I_new))

