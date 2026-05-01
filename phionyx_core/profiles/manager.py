"""
Profile Manager - Fan-Out Logic for Module Configuration
========================================================

Maps high-level profile knobs to low-level technical parameters across all SDK modules.
This is the "brain" that distributes settings to all modules.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .loader import ProfileLoader
from .schema import Profile, RoutingConfig

logger = logging.getLogger(__name__)


@dataclass
class PhysicsParams:
    """
    Low-level physics parameters derived from profile.

    This is the output of the "fan-out" logic that maps
    high-level knobs (reactivity, resilience) to low-level math (w_c, gamma).
    """
    w_c: float  # Cognitive weight (0-1)
    w_p: float  # Physical weight (0-1)
    gamma: float  # Decay rate (0.05-0.5)
    stability_baseline: float  # Base stability (0-1)
    entropy_sensitivity: float  # Entropy sensitivity (0-1)
    safety_strictness: float  # Safety strictness (0-1)


@dataclass
class PedagogyParams:
    """
    Low-level pedagogy parameters derived from profile.
    """
    intervention_threshold: float  # When to intervene (0-1)
    scaffolding_level: float  # How much to help (0-1)
    vygotsky_zone: float  # ZPD level (0-1)


@dataclass
class GovernanceParams:
    """
    Low-level governance parameters derived from profile.
    """
    policy_id: str  # Policy identifier
    pii_mode: str  # PII scrubbing mode
    audit_level: str  # Audit logging level
    regex_patterns: list[str]  # Custom regex patterns


class ProfileManager:
    """
    Central manager that distributes profile settings to all SDK modules.

    This class implements the "fan-out" logic:
    1. Loads profile from YAML
    2. Maps high-level knobs to low-level parameters
    3. Returns structured params for each module
    """

    def __init__(self, config_dir: str | None = None):
        """
        Initialize profile manager.

        Args:
            config_dir: Optional path to config directory
        """
        self.loader = ProfileLoader(config_dir)
        self._active_profile: Profile | None = None

    def load_profile(self, profile_name: str) -> Profile:
        """
        Load a profile and set it as active.

        Args:
            profile_name: Profile name (e.g., "SCHOOL_DEFAULT")

        Returns:
            Profile instance
        """
        profile = self.loader.load_profile(profile_name)
        self._active_profile = profile
        logger.info(f"Loaded profile: {profile_name}")
        return profile

    def get_active_profile(self) -> Profile | None:
        """Get the currently active profile."""
        return self._active_profile

    # ========================================================================
    # Fan-Out Logic: High-Level → Low-Level Mapping
    # ========================================================================

    def get_physics_params(self, profile: Profile | None = None) -> PhysicsParams:
        """
        Map PhysicsConfig to low-level physics parameters.

        Mapping Logic:
            - w_c = 0.3 + (resilience * 0.5) → [0.3, 0.8]
            - w_p = 1.0 - w_c
            - gamma = 0.05 + (reactivity * 0.25) → [0.05, 0.3]
            - stability_baseline = resilience
            - entropy_sensitivity = 1.0 - resilience
            - safety_strictness = safety_bias

        Args:
            profile: Optional profile. If None, uses active profile.

        Returns:
            PhysicsParams with calculated low-level parameters
        """
        if profile is None:
            profile = self._active_profile

        if profile is None:
            raise ValueError("No active profile. Call load_profile() first.")

        physics = profile.physics

        # Calculate w_c (Cognitive Weight)
        w_c = 0.3 + (physics.resilience * 0.5)
        w_c = max(0.3, min(0.8, w_c))

        # Calculate w_p (Physical Weight)
        w_p = 1.0 - w_c

        # Calculate gamma (Decay Rate)
        gamma = 0.05 + (physics.reactivity * 0.25)
        gamma = max(0.05, min(0.3, gamma))

        # Direct mappings
        stability_baseline = physics.resilience
        entropy_sensitivity = 1.0 - physics.resilience
        safety_strictness = physics.safety_bias

        return PhysicsParams(
            w_c=w_c,
            w_p=w_p,
            gamma=gamma,
            stability_baseline=stability_baseline,
            entropy_sensitivity=entropy_sensitivity,
            safety_strictness=safety_strictness
        )

    def get_pedagogy_params(self, profile: Profile | None = None) -> PedagogyParams:
        """
        Map PedagogyConfig to low-level pedagogy parameters.

        Args:
            profile: Optional profile. If None, uses active profile.

        Returns:
            PedagogyParams with calculated low-level parameters
        """
        if profile is None:
            profile = self._active_profile

        if profile is None:
            raise ValueError("No active profile. Call load_profile() first.")

        pedagogy = profile.pedagogy

        return PedagogyParams(
            intervention_threshold=pedagogy.intervention_threshold,
            scaffolding_level=pedagogy.scaffolding_aggressiveness,
            vygotsky_zone=pedagogy.vygotsky_level
        )

    def get_governance_params(self, profile: Profile | None = None) -> GovernanceParams:
        """
        Map GovernanceConfig to low-level governance parameters.

        Args:
            profile: Optional profile. If None, uses active profile.

        Returns:
            GovernanceParams with calculated low-level parameters
        """
        if profile is None:
            profile = self._active_profile

        if profile is None:
            raise ValueError("No active profile. Call load_profile() first.")

        governance = profile.governance

        return GovernanceParams(
            policy_id=governance.policy_id,
            pii_mode=governance.pii_mode,
            audit_level=governance.audit_level,
            regex_patterns=governance.custom_regex_patterns or []
        )

    def get_routing_config(self, profile: Profile | None = None) -> RoutingConfig:
        """
        Get routing configuration.

        Args:
            profile: Optional profile. If None, uses active profile.

        Returns:
            RoutingConfig instance
        """
        if profile is None:
            profile = self._active_profile

        if profile is None:
            raise ValueError("No active profile. Call load_profile() first.")

        return profile.routing

    def explain_mapping(self, profile: Profile | None = None) -> dict[str, Any]:
        """
        Explain how a profile maps to low-level parameters (for debugging/UI).

        Args:
            profile: Optional profile. If None, uses active profile.

        Returns:
            Dict with mapping explanation
        """
        if profile is None:
            profile = self._active_profile

        if profile is None:
            raise ValueError("No active profile. Call load_profile() first.")

        physics_params = self.get_physics_params(profile)
        pedagogy_params = self.get_pedagogy_params(profile)
        governance_params = self.get_governance_params(profile)

        return {
            "profile": {
                "name": profile.name,
                "description": profile.description,
            },
            "physics": {
                "high_level": {
                    "reactivity": profile.physics.reactivity,
                    "resilience": profile.physics.resilience,
                    "safety_bias": profile.physics.safety_bias,
                },
                "low_level": {
                    "w_c": {
                        "value": physics_params.w_c,
                        "formula": "0.3 + (resilience * 0.5)",
                    },
                    "w_p": {
                        "value": physics_params.w_p,
                        "formula": "1.0 - w_c",
                    },
                    "gamma": {
                        "value": physics_params.gamma,
                        "formula": "0.05 + (reactivity * 0.25)",
                    },
                    "stability_baseline": {
                        "value": physics_params.stability_baseline,
                        "formula": "resilience",
                    },
                }
            },
            "pedagogy": {
                "high_level": {
                    "vygotsky_level": profile.pedagogy.vygotsky_level,
                    "scaffolding_aggressiveness": profile.pedagogy.scaffolding_aggressiveness,
                    "intervention_threshold": profile.pedagogy.intervention_threshold,
                },
                "low_level": {
                    "intervention_threshold": pedagogy_params.intervention_threshold,
                    "scaffolding_level": pedagogy_params.scaffolding_level,
                    "vygotsky_zone": pedagogy_params.vygotsky_zone,
                }
            },
            "governance": {
                "policy_id": governance_params.policy_id,
                "pii_mode": governance_params.pii_mode,
                "audit_level": governance_params.audit_level,
            }
        }


# ============================================================================
# Singleton Helper Function
# ============================================================================

_global_manager: ProfileManager | None = None


def get_global_manager() -> ProfileManager:
    """
    Get or create the global ProfileManager instance.

    Returns:
        Global ProfileManager instance
    """
    global _global_manager

    if _global_manager is None:
        _global_manager = ProfileManager()

    return _global_manager


def get_active_profile() -> Profile | None:
    """
    Get the globally active profile.

    This is a convenience function for UnifiedEchoEngine and other modules
    to access the current profile without managing ProfileManager instances.

    Returns:
        Active Profile instance, or None if no profile loaded
    """
    manager = get_global_manager()
    return manager.get_active_profile()


def set_active_profile(profile_name: str) -> Profile:
    """
    Set the globally active profile.

    Args:
        profile_name: Profile name (e.g., "SCHOOL_DEFAULT")

    Returns:
        Profile instance
    """
    manager = get_global_manager()
    return manager.load_profile(profile_name)

