"""
Phionyx Profile Module - Enterprise Configuration Layer
=========================================================

Central configuration system that maps high-level personas (Teacher, Gamer)
to low-level technical parameters across all SDK modules.
"""

from .schema import (
    Profile,
    PhysicsConfig,
    PedagogyConfig,
    GovernanceConfig,
    RoutingConfig,
    BaseMode,
    PIIMode,
    AuditLevel,
    LLMTierStrategy,
)

from .loader import ProfileLoader

from .manager import (
    ProfileManager,
    PhysicsParams,
    PedagogyParams,
    GovernanceParams,
    get_global_manager,
    get_active_profile,
    set_active_profile,
)


def load_profile(profile_name: str) -> Profile:
    """Load a module-configuration profile by name (module-level convenience).

    Resolves via the global :class:`ProfileManager`. Built-in profiles
    (trace_school_rpg, npc_studio, scenario_generator, edu, game, clinical,
    sdk_default) work without any external config; an external config/profiles.yaml,
    if present, overrides them. This is the module-config LAYER (pedagogy /
    governance / physics / routing) that sits under a deployment ``runtime_profile``
    (see ``runtime_profiles``).
    """
    return get_global_manager().load_profile(profile_name)


__all__ = [
    # Schema
    "Profile",
    "PhysicsConfig",
    "PedagogyConfig",
    "GovernanceConfig",
    "RoutingConfig",
    "BaseMode",
    "PIIMode",
    "AuditLevel",
    "LLMTierStrategy",
    # Loader
    "ProfileLoader",
    "load_profile",
    # Manager
    "ProfileManager",
    "PhysicsParams",
    "PedagogyParams",
    "GovernanceParams",
    "get_global_manager",
    "get_active_profile",
    "set_active_profile",
]

__version__ = "1.0.0"

