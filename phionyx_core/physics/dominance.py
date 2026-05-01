"""
Dominance (D) - Echoism Core v1.1 (Optional)
============================================

Per Echoism Core v1.1:
- D: Optional dominance score (0.0-1.0, only in Strict profile)
- D is None in Lite/Compat profiles
- If D is None, treat as 0.0 in all calculations
- D provides PAD (Pleasure-Arousal-Dominance) interpretation for A/V modulation
- D production can come from measurement mapper, but None if not available
"""

from __future__ import annotations

from typing import Any


def apply_dominance_to_av_modulation(
    A: float,
    V: float,
    D: float | None,
    modulation_strength: float = 0.1
) -> dict[str, float]:
    """
    Apply Dominance (D) to A/V modulation (PAD interpretation).

    Per Echoism Core v1.1:
    - D None → no modulation (treat as 0.0)
    - D high → secondary modulation to A/V
    - PAD interpretation: Dominance affects how A/V are interpreted

    Args:
        A: Current arousal (0.0-1.0)
        V: Current valence (-1.0 to 1.0)
        D: Dominance value (0.0-1.0 or None)
        modulation_strength: Strength of modulation (default: 0.1)

    Returns:
        Dictionary with modulated A and V
    """
    if D is None:
        # D not available → no modulation
        return {"A": A, "V": V, "D": 0.0}

    # PAD interpretation:
    # High D + High A → more assertive/confident interpretation
    # High D + Low A → more controlled/calm interpretation
    # High D + Positive V → more positive dominance
    # High D + Negative V → more negative dominance (aggression)

    # Modulate A: High D can increase perceived arousal (assertiveness)
    A_modulated = A + (D * modulation_strength * (1.0 - A))
    A_modulated = max(0.0, min(1.0, A_modulated))

    # Modulate V: High D can amplify valence (positive → more positive, negative → more negative)
    V_modulated = V + (D * modulation_strength * V)
    V_modulated = max(-1.0, min(1.0, V_modulated))

    return {
        "A": A_modulated,
        "V": V_modulated,
        "D": D
    }


def extract_dominance_from_measurement(
    measurement: dict[str, Any],
    llm_output: dict[str, Any] | None = None
) -> float | None:
    """
    Extract Dominance (D) from measurement mapper output.

    Per Echoism Core v1.1:
    - D can come from measurement mapper
    - If not available, return None
    - Only used in Strict profile

    Args:
        measurement: Measurement vector (may contain D_meas)
        llm_output: LLM structured output (may contain dominance field)

    Returns:
        Dominance value (0.0-1.0) or None if not available
    """
    # Check measurement vector
    if measurement and "D_meas" in measurement:
        D = measurement["D_meas"]
        return max(0.0, min(1.0, float(D)))

    # Check LLM output
    if llm_output:
        if "dominance" in llm_output:
            D = llm_output["dominance"]
            return max(0.0, min(1.0, float(D)))
        if "D" in llm_output:
            D = llm_output["D"]
            return max(0.0, min(1.0, float(D)))

    # Not available
    return None


def get_dominance_default_for_profile(
    profile_name: str | None = None,
    profile: dict[str, Any] | None = None
) -> float | None:
    """
    Get default Dominance (D) value for profile.

    Per Echoism Core v1.1:
    - Strict profile → D can be active (default: 0.0)
    - Lite/Compat profile → D is None

    Args:
        profile_name: Profile name (e.g., "Echoism-Strict", "Echoism-Lite")
        profile: Profile dictionary

    Returns:
        Default D value (0.0 for Strict, None for Lite/Compat)
    """
    # Check profile name
    if profile_name:
        if "strict" in profile_name.lower():
            return 0.0  # Strict: D can be active (start at 0.0)
        elif "lite" in profile_name.lower() or "compat" in profile_name.lower():
            return None  # Lite/Compat: D is None

    # Check profile dict
    if profile:
        profile_type = profile.get("type", "").lower()
        if "strict" in profile_type:
            return 0.0
        elif "lite" in profile_type or "compat" in profile_type:
            return None

    # Default: None (Lite/Compat behavior)
    return None


def apply_dominance_to_response_amplitude(
    base_amplitude: float,
    D: float | None,
    modulation_factor: float = 0.05
) -> float:
    """
    Apply Dominance (D) to response amplitude (minimal effect).

    Per Echoism Core v1.1:
    - D provides minimal secondary modulation
    - High D → slightly higher amplitude (more assertive)

    Args:
        base_amplitude: Base response amplitude
        D: Dominance value (0.0-1.0 or None)
        modulation_factor: Modulation factor (default: 0.05, minimal)

    Returns:
        Modulated amplitude
    """
    if D is None:
        return base_amplitude

    # Minimal modulation: High D → slightly higher amplitude
    amplitude_modulated = base_amplitude * (1.0 + D * modulation_factor)

    return amplitude_modulated

