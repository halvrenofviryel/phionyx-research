"""
Phionyx Profile Module - Enterprise Configuration Layer
=========================================================

Central configuration system that maps high-level personas (Teacher, Gamer)
to low-level technical parameters across all SDK modules.
"""

from .loader import ProfileLoader
from .manager import (
    GovernanceParams,
    PedagogyParams,
    PhysicsParams,
    ProfileManager,
    get_active_profile,
    get_global_manager,
    set_active_profile,
)
from .schema import (
    AuditLevel,
    BaseMode,
    GovernanceConfig,
    LLMTierStrategy,
    PedagogyConfig,
    PhysicsConfig,
    PIIMode,
    Profile,
    RoutingConfig,
)

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

