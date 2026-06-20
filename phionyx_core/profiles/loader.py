"""
Profile Loader - YAML Loading and Merging Logic
===============================================

Loads profiles from YAML files and merges high-level personas with low-level defaults.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import logging

from .schema import Profile, PhysicsConfig, PedagogyConfig, GovernanceConfig, RoutingConfig

logger = logging.getLogger(__name__)


# Built-in module-configuration profiles. These make the loader work WITHOUT an
# external config/profiles.yaml (which is not shipped in the monorepo), so
# load_profile() actually resolves for the products + legacy personas. An external
# config/profiles.yaml, if present, is merged over (overrides) these.
# These are the module-config LAYER (pedagogy/governance/physics/routing) that sits
# UNDER a deployment runtime_profile (which blocks run) — see runtime_profiles.py.
_BUILTIN_PROFILES: Dict[str, Dict[str, Any]] = {
    # ── Products ──
    "trace_school_rpg": {
        "name": "trace_school_rpg",
        "description": "Trace School RPG — minor-safe, safeguarding-first, GDPR-strict.",
        "physics": {"base_mode": "SCHOOL", "reactivity": 0.4, "resilience": 0.9, "safety_bias": 0.95},
        "pedagogy": {"scaffolding_aggressiveness": 0.7, "intervention_threshold": 0.4},
        "governance": {"policy_id": "edu_safeguarding", "pii_mode": "FULL", "audit_level": "VERBOSE"},
        "routing": {"enable_graph_rag": False, "llm_tier_strategy": "BALANCED"},
        "tags": ["school", "safeguarding", "minor"],
    },
    "npc_studio": {
        "name": "npc_studio",
        "description": "NPC Studio — affect-aware NPC behaviour orchestration, lore-safe.",
        "physics": {"base_mode": "NPC_ENGINE", "reactivity": 0.6, "resilience": 0.7, "safety_bias": 0.6},
        "pedagogy": {"scaffolding_aggressiveness": 0.2, "intervention_threshold": 0.3},
        "governance": {"policy_id": "game_lore", "pii_mode": "PARTIAL", "audit_level": "STANDARD"},
        "routing": {"enable_graph_rag": True, "llm_tier_strategy": "QUALITY_OPTIMIZED"},
        "tags": ["game", "npc", "behaviour"],
    },
    "scenario_generator": {
        "name": "scenario_generator",
        "description": "Scenario Generator — canon/version provenance for AI-assisted writing.",
        "physics": {"base_mode": "GAME", "reactivity": 0.5, "resilience": 0.6, "safety_bias": 0.5},
        "governance": {"policy_id": "content_canon", "pii_mode": "PARTIAL", "audit_level": "STANDARD"},
        "routing": {"enable_graph_rag": True, "llm_tier_strategy": "QUALITY_OPTIMIZED"},
        "tags": ["writing", "canon", "provenance"],
    },
    # ── Legacy personas (kept; map to the same module shape) ──
    "edu": {
        "name": "edu", "description": "Educational profile (legacy alias of trace_school_rpg shape).",
        "physics": {"base_mode": "SCHOOL", "safety_bias": 0.9},
        "governance": {"policy_id": "edu", "pii_mode": "FULL", "audit_level": "VERBOSE"},
        "routing": {"enable_graph_rag": False}, "tags": ["edu", "legacy"],
    },
    "game": {
        "name": "game", "description": "Game profile (legacy).",
        "physics": {"base_mode": "GAME", "safety_bias": 0.5},
        "governance": {"policy_id": "game", "pii_mode": "PARTIAL", "audit_level": "STANDARD"},
        "routing": {"enable_graph_rag": True}, "tags": ["game", "legacy"],
    },
    "clinical": {
        "name": "clinical", "description": "Clinical / therapy profile (legacy).",
        "physics": {"base_mode": "THERAPY", "safety_bias": 0.95, "resilience": 0.9},
        "governance": {"policy_id": "clinical", "pii_mode": "FULL", "audit_level": "VERBOSE"},
        "routing": {"enable_graph_rag": False}, "tags": ["clinical", "legacy"],
    },
    "hearthos": {
        "name": "hearthos",
        "description": "HearthOS — bounded-authority household assistant; system proposes, the responsible adult decides.",
        "physics": {"base_mode": "THERAPY", "reactivity": 0.4, "resilience": 0.9, "safety_bias": 0.95},
        "pedagogy": {"scaffolding_aggressiveness": 0.3, "intervention_threshold": 0.4},
        "governance": {"policy_id": "household_bounded_authority", "pii_mode": "FULL", "audit_level": "VERBOSE"},
        "routing": {"enable_graph_rag": False, "llm_tier_strategy": "BALANCED"},
        "tags": ["household", "bounded_authority", "family"],
    },
    "sdk_default": {
        "name": "sdk_default", "description": "Neutral default profile for SDK examples.",
        "tags": ["default"],
    },
}


class ProfileLoader:
    """
    Loads and merges profiles from YAML files.

    Logic:
    1. Load defaults/*.yaml to get baseline technical values
    2. Load profiles.yaml to get specific persona overrides
    3. Merge persona overrides into defaults
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize profile loader.

        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        if config_dir is None:
            # Default: core-profile/config/
            config_dir = Path(__file__).parent.parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.profiles_file = self.config_dir / "profiles.yaml"
        self.defaults_dir = self.config_dir / "defaults"

        # Cache loaded defaults
        self._defaults_cache: Dict[str, Dict[str, Any]] = {}
        self._profiles_cache: Dict[str, Profile] = {}

    def _load_defaults(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all default YAML files from defaults/ directory.

        Returns:
            Dict mapping module name to default config dict
        """
        if self._defaults_cache:
            return self._defaults_cache

        defaults = {}

        # Load physics defaults
        physics_file = self.defaults_dir / "physics.yaml"
        if physics_file.exists():
            with open(physics_file, 'r', encoding='utf-8') as f:
                defaults['physics'] = yaml.safe_load(f) or {}
        else:
            logger.debug(f"Physics defaults not found: {physics_file}; using schema defaults")
            defaults['physics'] = {}

        # Load pedagogy defaults
        pedagogy_file = self.defaults_dir / "pedagogy.yaml"
        if pedagogy_file.exists():
            with open(pedagogy_file, 'r', encoding='utf-8') as f:
                defaults['pedagogy'] = yaml.safe_load(f) or {}
        else:
            logger.debug(f"Pedagogy defaults not found: {pedagogy_file}; using schema defaults")
            defaults['pedagogy'] = {}

        # Load governance defaults
        governance_file = self.defaults_dir / "governance.yaml"
        if governance_file.exists():
            with open(governance_file, 'r', encoding='utf-8') as f:
                defaults['governance'] = yaml.safe_load(f) or {}
        else:
            logger.debug(f"Governance defaults not found: {governance_file}; using schema defaults")
            defaults['governance'] = {}

        self._defaults_cache = defaults
        return defaults

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge override into base.

        Args:
            base: Base configuration dict
            override: Override configuration dict

        Returns:
            Merged configuration dict
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value

        return result

    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Load profiles.yaml file.

        Returns:
            Dict mapping profile name to profile data
        """
        # Start from the built-in profiles so the loader works without an external
        # config/profiles.yaml. An external file, if present, overrides built-ins.
        profiles: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in _BUILTIN_PROFILES.items()}

        if not self.profiles_file.exists():
            logger.debug(f"No external profiles.yaml at {self.profiles_file}; using built-ins.")
            return profiles

        with open(self.profiles_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or 'profiles' not in data:
            raise ValueError("Invalid profiles.yaml format. Expected 'profiles' key.")

        for profile_data in data['profiles']:
            name = profile_data.get('name')
            if not name:
                logger.warning(f"Skipping profile without name: {profile_data}")
                continue
            profiles[name] = profile_data

        return profiles

    def load_profile(self, profile_name: str) -> Profile:
        """
        Load a profile by name, merging defaults with persona overrides.

        Args:
            profile_name: Profile name (e.g., "SCHOOL_DEFAULT")

        Returns:
            Profile instance with merged configuration

        Raises:
            KeyError: If profile not found
        """
        # Check cache
        if profile_name in self._profiles_cache:
            return self._profiles_cache[profile_name]

        # Load defaults
        defaults = self._load_defaults()

        # Load profiles
        profiles = self._load_profiles()

        if profile_name not in profiles:
            raise KeyError(
                f"Profile '{profile_name}' not found. Available profiles: {list(profiles.keys())}"
            )

        profile_data = profiles[profile_name]

        # Merge defaults with profile overrides
        merged = {
            'physics': self._merge_config(
                defaults.get('physics', {}),
                profile_data.get('physics', {})
            ),
            'pedagogy': self._merge_config(
                defaults.get('pedagogy', {}),
                profile_data.get('pedagogy', {})
            ),
            'governance': self._merge_config(
                defaults.get('governance', {}),
                profile_data.get('governance', {})
            ),
            'routing': self._merge_config(
                defaults.get('routing', {}),
                profile_data.get('routing', {})
            ),
        }

        # Create Profile instance
        profile = Profile(
            name=profile_data.get('name', profile_name),
            description=profile_data.get('description'),
            physics=PhysicsConfig(**merged['physics']),
            pedagogy=PedagogyConfig(**merged['pedagogy']),
            governance=GovernanceConfig(**merged['governance']),
            routing=RoutingConfig(**merged.get('routing', {})),
            version=profile_data.get('version', '1.0.0'),
            tags=profile_data.get('tags', [])
        )

        # Cache it
        self._profiles_cache[profile_name] = profile

        return profile

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        profiles = self._load_profiles()
        return list(profiles.keys())

