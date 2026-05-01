"""
Profile Loader - YAML Loading and Merging Logic
===============================================

Loads profiles from YAML files and merges high-level personas with low-level defaults.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from .schema import GovernanceConfig, PedagogyConfig, PhysicsConfig, Profile, RoutingConfig

logger = logging.getLogger(__name__)


class ProfileLoader:
    """
    Loads and merges profiles from YAML files.

    Logic:
    1. Load defaults/*.yaml to get baseline technical values
    2. Load profiles.yaml to get specific persona overrides
    3. Merge persona overrides into defaults
    """

    def __init__(self, config_dir: Path | None = None):
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
        self._defaults_cache: dict[str, dict[str, Any]] = {}
        self._profiles_cache: dict[str, Profile] = {}

    def _load_defaults(self) -> dict[str, dict[str, Any]]:
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
            with open(physics_file, encoding='utf-8') as f:
                defaults['physics'] = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Physics defaults not found: {physics_file}")
            defaults['physics'] = {}

        # Load pedagogy defaults
        pedagogy_file = self.defaults_dir / "pedagogy.yaml"
        if pedagogy_file.exists():
            with open(pedagogy_file, encoding='utf-8') as f:
                defaults['pedagogy'] = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Pedagogy defaults not found: {pedagogy_file}")
            defaults['pedagogy'] = {}

        # Load governance defaults
        governance_file = self.defaults_dir / "governance.yaml"
        if governance_file.exists():
            with open(governance_file, encoding='utf-8') as f:
                defaults['governance'] = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Governance defaults not found: {governance_file}")
            defaults['governance'] = {}

        self._defaults_cache = defaults
        return defaults

    def _merge_config(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
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

    def _load_profiles(self) -> dict[str, dict[str, Any]]:
        """
        Load profiles.yaml file.

        Returns:
            Dict mapping profile name to profile data
        """
        if not self.profiles_file.exists():
            raise FileNotFoundError(
                f"Profiles file not found: {self.profiles_file}\n"
                f"Please create profiles.yaml with profile definitions."
            )

        with open(self.profiles_file, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or 'profiles' not in data:
            raise ValueError("Invalid profiles.yaml format. Expected 'profiles' key.")

        profiles = {}
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

