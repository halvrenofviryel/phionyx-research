"""
Empathy Formula - Echoism Core v1.1
====================================

Per Echoism Core v1.1:
- Empathy_t = Base_Response × (1/(1+H)) × tanh(R/τ) × Coherence_factor
- τ (tau): Profile parameter (Strict/Lite different)
- Coherence_factor: C düşükse empati iddiasını düşürsün (daha temkinli dil)
- Affects: response amplitude, closeness language policy
- Does NOT directly manage lore or narrative style
"""

from __future__ import annotations

import math
from typing import Any


def calculate_empathy_v1_1(
    base_response: float,
    entropy: float,
    resonance_score: float,
    coherence: float,
    tau: float = 0.5,
    min_empathy: float = 0.1,
    max_empathy: float = 1.0
) -> float:
    """
    Calculate empathy using v1.1 formula.

    Per Echoism Core v1.1:
    - Empathy_t = Base_Response × (1/(1+H)) × tanh(R/τ) × Coherence_factor
    - τ (tau): Profile parameter (Strict/Lite different)
    - Coherence_factor: C düşükse empati iddiasını düşürsün

    Args:
        base_response: Base response value (0.0-1.0)
        entropy: Entropy H (0.0-1.0)
        resonance_score: ResonanceScore R (0.0-1.0)
        coherence: Coherence C (0.0-1.0)
        tau: Profile parameter τ (default: 0.5)
        min_empathy: Minimum empathy value
        max_empathy: Maximum empathy value

    Returns:
        Empathy value (0.0-1.0)
    """
    # Term 1: (1/(1+H)) - Higher entropy → lower empathy
    entropy_factor = 1.0 / (1.0 + entropy)

    # Term 2: tanh(R/τ) - Resonance saturation
    # Higher R → higher empathy, but saturates
    resonance_factor = math.tanh(resonance_score / tau) if tau > 0 else 0.0

    # Term 3: Coherence_factor - Low C → lower empathy claim (more cautious)
    # C = 0.0 → factor = 0.5 (more cautious)
    # C = 1.0 → factor = 1.0 (full empathy)
    coherence_factor = 0.5 + 0.5 * coherence

    # Combine: Empathy_t = Base_Response × (1/(1+H)) × tanh(R/τ) × Coherence_factor
    empathy = base_response * entropy_factor * resonance_factor * coherence_factor

    # Clamp to bounds
    empathy = max(min_empathy, min(max_empathy, empathy))

    return empathy


def calculate_closeness_language_policy(
    empathy: float,
    resonance_score: float,
    threshold: float = 0.3
) -> str:
    """
    Calculate closeness language policy from empathy.

    Per Echoism Core v1.1:
    - Low empathy + low R → avoid "too close" language
    - High empathy + high R → can use closer language
    - Regression test: New user with low R → "too close" language blocked

    Args:
        empathy: Empathy value (0.0-1.0)
        resonance_score: ResonanceScore R (0.0-1.0)
        threshold: Threshold for closeness policy (default: 0.3)

    Returns:
        Language policy: "distant", "neutral", "close"
    """
    # Low empathy + low R → distant
    if empathy < threshold and resonance_score < threshold:
        return "distant"

    # High empathy + high R → close
    if empathy > 0.7 and resonance_score > 0.7:
        return "close"

    # Default: neutral
    return "neutral"


def get_tau_from_profile(
    profile_name: str | None = None,
    profile: dict[str, Any] | None = None
) -> float:
    """
    Get τ (tau) parameter from profile.

    Per Echoism Core v1.1:
    - Strict profile: τ = 0.3 (lower, more cautious)
    - Lite profile: τ = 0.5 (default)
    - Compat profile: τ = 0.7 (higher, more open)

    Args:
        profile_name: Profile name
        profile: Profile dictionary

    Returns:
        Tau value (0.0-1.0)
    """
    # Check profile name
    if profile_name:
        profile_lower = profile_name.lower()
        if "strict" in profile_lower:
            return 0.3  # Lower tau, more cautious
        elif "lite" in profile_lower:
            return 0.5  # Default
        elif "compat" in profile_lower:
            return 0.7  # Higher tau, more open

    # Check profile dict
    if profile:
        profile_type = profile.get("type", "").lower()
        if "strict" in profile_type:
            return 0.3
        elif "lite" in profile_type:
            return 0.5
        elif "compat" in profile_type:
            return 0.7

    # Default: Lite behavior
    return 0.5


def calculate_empathy_with_profile(
    base_response: float,
    entropy: float,
    resonance_score: float,
    coherence: float,
    profile_name: str | None = None,
    profile: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Calculate empathy with profile-specific parameters.

    Args:
        base_response: Base response value
        entropy: Entropy H
        resonance_score: ResonanceScore R
        coherence: Coherence C
        profile_name: Profile name
        profile: Profile dictionary

    Returns:
        Dictionary with:
        - empathy: float
        - closeness_policy: str
        - tau: float
    """
    tau = get_tau_from_profile(profile_name, profile)

    empathy = calculate_empathy_v1_1(
        base_response=base_response,
        entropy=entropy,
        resonance_score=resonance_score,
        coherence=coherence,
        tau=tau
    )

    closeness_policy = calculate_closeness_language_policy(empathy, resonance_score)

    return {
        "empathy": empathy,
        "closeness_policy": closeness_policy,
        "tau": tau
    }

