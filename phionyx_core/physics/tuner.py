"""
Profile Tuner - Maps High-Level Profiles to Low-Level Physics Parameters
=========================================================================

Translates user-friendly profiles (reactivity, resilience, safety) into
raw physics parameters (w_c, w_p, gamma, stability_baseline, entropy_sensitivity).
"""

from typing import Dict, Any
from dataclasses import dataclass
from .profiles import PhysicsProfile
from .constants import (
    GAMMA_MIN,
    GAMMA_MAX,
    MIN_STABILITY,
    MAX_STABILITY,
    ENTROPY_MIN,
    ENTROPY_MAX,
)


@dataclass
class PhysicsParams:
    """
    Low-level physics parameters derived from a profile.

    Attributes:
        w_c: Cognitive weight (0-1), higher = more stability-focused
        w_p: Physical weight (0-1), higher = more response-focused (w_p = 1 - w_c)
        gamma: Decay rate (0.05-0.5), higher = faster response decay
        stability_baseline: Base stability value (0-1), higher = more resilient
        entropy_sensitivity: How much entropy affects stability (0-1), higher = more sensitive
        safety_strictness: Policy strictness (0-1), passed to Policy Engine
        max_entropy: Maximum entropy threshold (0-1), hard limit for entropy (ENTERPRISE UPGRADE)
        entropy_threshold: Entropy threshold for penalty calculation (0-1), default 0.5
    """
    w_c: float
    w_p: float
    gamma: float
    stability_baseline: float
    entropy_sensitivity: float
    safety_strictness: float
    max_entropy: float = ENTROPY_MAX  # Default to global max, profile can override
    entropy_threshold: float = 0.5  # Default threshold for entropy penalty calculation

    def __post_init__(self):
        """Clamp all values to valid ranges."""
        self.w_c = max(0.0, min(1.0, self.w_c))
        self.w_p = max(0.0, min(1.0, self.w_p))
        self.gamma = max(GAMMA_MIN, min(GAMMA_MAX, self.gamma))
        self.stability_baseline = max(MIN_STABILITY, min(MAX_STABILITY, self.stability_baseline))
        self.entropy_sensitivity = max(0.0, min(1.0, self.entropy_sensitivity))
        self.safety_strictness = max(0.0, min(1.0, self.safety_strictness))
        self.max_entropy = max(ENTROPY_MIN, min(ENTROPY_MAX, self.max_entropy))
        self.entropy_threshold = max(0.0, min(1.0, self.entropy_threshold))

        # Ensure w_c + w_p = 1.0
        total = self.w_c + self.w_p
        if total > 0:
            self.w_c = self.w_c / total
            self.w_p = self.w_p / total


class ProfileTuner:
    """
    Translates PhysicsProfile to PhysicsParams.

    Mapping Logic:
        - w_c (Cognitive Weight) = 0.3 + (resilience * 0.5)
          → Range: [0.3, 0.8], higher resilience = more cognitive focus

        - w_p (Physical Weight) = 1.0 - w_c
          → Automatically derived, ensures w_c + w_p = 1.0

        - gamma = 0.05 + (reactivity * 0.25)
          → Range: [0.05, 0.3], higher reactivity = faster decay

        - stability_baseline = resilience
          → Direct mapping, higher resilience = higher baseline stability

        - entropy_sensitivity = 1.0 - resilience
          → Inverse mapping, higher resilience = less entropy sensitivity

        - safety_strictness = safety
          → Direct mapping, passed to Policy Engine
    """

    @staticmethod
    def profile_to_parameters(profile: PhysicsProfile) -> PhysicsParams:
        """
        Convert a PhysicsProfile to PhysicsParams.

        Args:
            profile: High-level profile configuration

        Returns:
            PhysicsParams with calculated low-level parameters

        Example:
            >>> from phionyx_core.physics.profiles import ProfileLoader
            >>> loader = ProfileLoader()
            >>> profile = loader.load("SCHOOL_DEFAULT")
            >>> params = ProfileTuner.profile_to_parameters(profile)
            >>> print(f"w_c={params.w_c:.2f}, gamma={params.gamma:.3f}")
        """
        # 1. Calculate Cognitive Weight (w_c)
        # Formula: w_c = 0.3 + (resilience * 0.5)
        # Range: [0.3, 0.8]
        # Higher resilience → more cognitive focus (stability > response)
        w_c = 0.3 + (profile.resilience * 0.5)

        # 2. Calculate Physical Weight (w_p)
        # Formula: w_p = 1.0 - w_c
        # Ensures w_c + w_p = 1.0
        w_p = 1.0 - w_c

        # 3. Calculate Gamma (Decay Rate)
        # Formula: gamma = 0.05 + (reactivity * 0.25)
        # Range: [0.05, 0.3] (within GAMMA_MIN=0.05, GAMMA_MAX=0.5)
        # Higher reactivity → faster decay (more responsive to changes)
        gamma = 0.05 + (profile.reactivity * 0.25)

        # 4. Calculate Stability Baseline
        # Formula: stability_baseline = resilience
        # Direct mapping, higher resilience → higher baseline stability
        stability_baseline = profile.resilience

        # 5. Calculate Entropy Sensitivity
        # Formula: entropy_sensitivity = 1.0 - resilience
        # Inverse mapping, higher resilience → less affected by entropy
        entropy_sensitivity = 1.0 - profile.resilience

        # 6. Safety Strictness (passed to Policy Engine)
        # Direct mapping from profile.safety
        safety_strictness = profile.safety

        # 7. ENTERPRISE UPGRADE: Extract max_entropy from profile (if defined in YAML)
        # Pydantic v2 with extra="allow" stores extra fields - accessible via direct attribute access
        max_entropy = ENTROPY_MAX  # Default to global max
        entropy_threshold = 0.5  # Default threshold

        # Extract max_entropy (direct attribute access works with Pydantic extra="allow")
        if hasattr(profile, 'max_entropy'):
            try:
                max_entropy_val = profile.max_entropy
                if isinstance(max_entropy_val, (int, float)):
                    max_entropy = float(max_entropy_val)
            except (AttributeError, TypeError):
                pass

        # Extract entropy_threshold if defined
        if hasattr(profile, 'entropy_threshold'):
            try:
                threshold_val = profile.entropy_threshold
                if isinstance(threshold_val, (int, float)):
                    entropy_threshold = float(threshold_val)
            except (AttributeError, TypeError):
                pass

        # Clamp values
        max_entropy = max(ENTROPY_MIN, min(ENTROPY_MAX, max_entropy))
        entropy_threshold = max(0.0, min(1.0, entropy_threshold))

        return PhysicsParams(
            w_c=w_c,
            w_p=w_p,
            gamma=gamma,
            stability_baseline=stability_baseline,
            entropy_sensitivity=entropy_sensitivity,
            safety_strictness=safety_strictness,
            max_entropy=max_entropy,
            entropy_threshold=entropy_threshold
        )

    @staticmethod
    def get_context_weights(profile: PhysicsProfile) -> Dict[str, float]:
        """
        Get context weights (w_c, w_p) for use in calculate_phi_v2.

        Args:
            profile: PhysicsProfile instance

        Returns:
            Dict with "wc" and "wp" keys, compatible with CONTEXT_WEIGHTS format

        Example:
            >>> weights = ProfileTuner.get_context_weights(profile)
            >>> result = calculate_phi_v2(..., context_mode="CUSTOM", **weights)
        """
        params = ProfileTuner.profile_to_parameters(profile)
        return {
            "wc": params.w_c,
            "wp": params.w_p
        }

    @staticmethod
    def explain_mapping(profile: PhysicsProfile) -> Dict[str, Any]:
        """
        Explain how a profile maps to parameters (for debugging/UI).

        Args:
            profile: PhysicsProfile instance

        Returns:
            Dict with mapping explanation
        """
        params = ProfileTuner.profile_to_parameters(profile)

        return {
            "profile": {
                "name": profile.name,
                "base_mode": profile.base_mode,
                "reactivity": profile.reactivity,
                "resilience": profile.resilience,
                "safety": profile.safety,
            },
            "mapped_parameters": {
                "w_c": {
                    "value": params.w_c,
                    "formula": "0.3 + (resilience * 0.5)",
                    "interpretation": "Cognitive weight (stability focus)"
                },
                "w_p": {
                    "value": params.w_p,
                    "formula": "1.0 - w_c",
                    "interpretation": "Physical weight (response focus)"
                },
                "gamma": {
                    "value": params.gamma,
                    "formula": "0.05 + (reactivity * 0.25)",
                    "interpretation": "Decay rate (response speed)"
                },
                "stability_baseline": {
                    "value": params.stability_baseline,
                    "formula": "resilience",
                    "interpretation": "Base stability value"
                },
                "entropy_sensitivity": {
                    "value": params.entropy_sensitivity,
                    "formula": "1.0 - resilience",
                    "interpretation": "How much entropy affects stability"
                },
                "safety_strictness": {
                    "value": params.safety_strictness,
                    "formula": "safety",
                    "interpretation": "Policy strictness (0=permissive, 1=strict)"
                }
            }
        }

