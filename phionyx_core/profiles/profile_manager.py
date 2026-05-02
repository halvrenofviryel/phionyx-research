"""
Profile Manager
===============

Manages product profiles and port instantiation.
Creates appropriate port implementations based on profile configuration.
"""

import json
import logging
from pathlib import Path
from typing import Any, cast

from ..ports import (
    IntuitionPort,
    MemoryPort,
    MetaPort,
    NarrativePort,
    PedagogyPort,
    PhysicsPort,
    PolicyPort,
)
from ..ports.null_implementations import (
    NullIntuitionEngine,
    NullMemoryEngine,
    NullMetaEngine,
    NullNarrativeEngine,
    NullPedagogyEngine,
    NullPhysicsEngine,
    NullPolicyEngine,
)
from .profile_configs import get_profile_config

logger = logging.getLogger(__name__)


class ProductProfile:
    """Product profile with port implementations."""

    def __init__(
        self,
        physics: PhysicsPort,
        memory: MemoryPort,
        intuition: IntuitionPort,
        pedagogy: PedagogyPort,
        policy: PolicyPort,
        narrative: NarrativePort,
        meta: MetaPort,
        profile_name: str,
        config: dict[str, Any]
    ):
        self.physics = physics
        self.memory = memory
        self.intuition = intuition
        self.pedagogy = pedagogy
        self.policy = policy
        self.narrative = narrative
        self.meta = meta
        self.profile_name = profile_name
        self.config = config

    def get_module_status(self) -> dict[str, bool]:
        """Get status of each module (enabled/disabled)."""
        return {
            "physics": not isinstance(self.physics, NullPhysicsEngine),
            "memory": not isinstance(self.memory, NullMemoryEngine),
            "intuition": not isinstance(self.intuition, NullIntuitionEngine),
            "pedagogy": not isinstance(self.pedagogy, NullPedagogyEngine),
            "policy": not isinstance(self.policy, NullPolicyEngine),
            "narrative": not isinstance(self.narrative, NullNarrativeEngine),
            "meta": not isinstance(self.meta, NullMetaEngine)
        }


class ProfileManager:
    """Manages product profiles and creates port instances."""

    @staticmethod
    def _create_physics_port(module_config: str) -> PhysicsPort:
        """Create Physics port based on configuration."""
        if module_config == "null":
            return NullPhysicsEngine()

        # Try to import real Physics implementation
        try:
            from phionyx_core.physics.formulas import calculate_phi_v2_1  # noqa: F401

            # Create real Physics port implementation
            # `phionyx_core.implementations.*` is a planned private package not
            # shipped with the public SDK. mypy sees it as Any (per
            # ignore_missing_imports); the cast acknowledges that.
            from ..implementations.physics_impl import RealPhysicsEngine
            return cast(PhysicsPort, RealPhysicsEngine())
        except ImportError:
            logger.warning("Physics SDK not available, using Null implementation")
            return NullPhysicsEngine()

    @staticmethod
    def _create_memory_port(module_config: str) -> MemoryPort:
        """Create Memory port based on configuration."""
        if module_config == "null":
            return NullMemoryEngine()

        try:
            from phionyx_core.memory.vector_store import VectorStore  # noqa: F401

            from ..implementations.memory_impl import RealMemoryEngine
            return cast(MemoryPort, RealMemoryEngine())
        except ImportError:
            logger.warning("Memory SDK not available, using Null implementation")
            return NullMemoryEngine()

    @staticmethod
    def _create_intuition_port(module_config: str) -> IntuitionPort:
        """Create Intuition port based on configuration."""
        if module_config == "null":
            return NullIntuitionEngine()

        try:
            from phionyx_intuition import GraphEngine  # noqa: F401

            from ..implementations.intuition_impl import RealIntuitionEngine
            return cast(IntuitionPort, RealIntuitionEngine())
        except ImportError:
            logger.warning("Intuition SDK not available, using Null implementation")
            return NullIntuitionEngine()

    @staticmethod
    def _create_pedagogy_port(module_config: str) -> PedagogyPort:
        """Create Pedagogy port based on configuration."""
        if module_config == "null" or module_config == "off":
            return NullPedagogyEngine()

        try:
            from phionyx_core.pedagogy.risk_assessment import RiskAssessor  # noqa: F401

            from ..implementations.pedagogy_impl import RealPedagogyEngine
            return cast(PedagogyPort, RealPedagogyEngine(strictness=module_config))
        except ImportError:
            logger.warning("Pedagogy SDK not available, using Null implementation")
            return NullPedagogyEngine()

    @staticmethod
    def _create_policy_port(module_config: str) -> PolicyPort:
        """Create Policy port based on configuration."""
        if module_config == "null":
            return NullPolicyEngine()

        try:
            from ..implementations.policy_impl import RealPolicyEngine
            return cast(PolicyPort, RealPolicyEngine(mode=module_config))
        except ImportError:
            logger.warning("Policy SDK not available, using Null implementation")
            return NullPolicyEngine()

    @staticmethod
    def _create_narrative_port(module_config: str) -> NarrativePort:
        """Create Narrative port based on configuration."""
        if module_config == "null":
            return NullNarrativeEngine()

        try:
            from ..implementations.narrative_impl import RealNarrativeEngine
            return cast(NarrativePort, RealNarrativeEngine(mode=module_config))
        except ImportError:
            logger.warning("Narrative SDK not available, using Null implementation")
            return NullNarrativeEngine()

    @staticmethod
    def _create_meta_port(module_config: str) -> MetaPort:
        """Create Meta port based on configuration."""
        if module_config == "null":
            return NullMetaEngine()

        try:
            from ..implementations.meta_impl import RealMetaEngine
            return cast(MetaPort, RealMetaEngine())
        except ImportError:
            logger.warning("Meta SDK not available, using Null implementation")
            return NullMetaEngine()

    @classmethod
    def create_profile(
        cls,
        profile_name: str,
        config: dict[str, Any] | None = None
    ) -> ProductProfile:
        """
        Create product profile from configuration.

        Args:
            profile_name: Profile name ('edu', 'game', 'clinical')
            config: Optional custom configuration (overrides default)

        Returns:
            ProductProfile with port instances
        """
        if config is None:
            config = get_profile_config(profile_name)

        modules = config.get("modules", {})

        # Create ports based on configuration
        physics = cls._create_physics_port(modules.get("physics", "null"))
        memory = cls._create_memory_port(modules.get("memory", "null"))
        intuition = cls._create_intuition_port(modules.get("intuition", "null"))
        pedagogy = cls._create_pedagogy_port(modules.get("pedagogy", "null"))
        policy = cls._create_policy_port(modules.get("policy", "null"))
        narrative = cls._create_narrative_port(modules.get("narrative", "null"))
        meta = cls._create_meta_port(modules.get("meta", "null"))

        logger.info(f"Created profile '{profile_name}': {cls._get_module_status(modules)}")

        return ProductProfile(
            physics=physics,
            memory=memory,
            intuition=intuition,
            pedagogy=pedagogy,
            policy=policy,
            narrative=narrative,
            meta=meta,
            profile_name=profile_name,
            config=config
        )

    @staticmethod
    def _get_module_status(modules: dict[str, str]) -> str:
        """Get human-readable module status."""
        status = []
        for module, config in modules.items():
            status.append(f"{module}={config}")
        return ", ".join(status)

    @classmethod
    def from_json_file(cls, config_path: str) -> ProductProfile:
        """
        Create profile from JSON configuration file.

        Args:
            config_path: Path to JSON configuration file

        Returns:
            ProductProfile
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Profile config not found: {config_path}")

        with open(path, encoding="utf-8") as f:
            config = json.load(f)

        profile_name = config.get("profile", "edu")
        return cls.create_profile(profile_name, config)

    @classmethod
    def from_versioned_profile(cls, profile_name: str, version: str = "2.1.0") -> ProductProfile:
        """
        Create profile from versioned profile JSON file.

        Looks for profile in: profiles/{profile_name}/{version}.json

        Args:
            profile_name: Profile name ('edu', 'game', 'clinical')
            version: Profile version (default: '2.1.0')

        Returns:
            ProductProfile
        """
        # Get package directory
        package_dir = Path(__file__).parent.parent
        profile_path = package_dir / "profiles" / profile_name / f"{version}.json"

        if not profile_path.exists():
            # Fallback to default config
            logger.warning(f"Versioned profile not found: {profile_path}, using default config")
            return cls.create_profile(profile_name)

        return cls.from_json_file(str(profile_path))

