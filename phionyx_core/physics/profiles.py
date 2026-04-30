"""
Physics Profile System - High-Level Configuration Layer
========================================================

Maps user-friendly profiles (Teacher, Parent, Dev) to low-level physics parameters.
Uses Pydantic for validation and YAML for preset storage.
"""

from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
import yaml
from pathlib import Path


class BaseMode(str, Enum):
    """Base context mode for physics calculations."""
    SCHOOL = "SCHOOL"
    GAME = "GAME"
    THERAPY = "THERAPY"
    NPC_ENGINE = "NPC_ENGINE"
    DEFAULT = "DEFAULT"


class PhysicsProfile(BaseModel):
    """
    High-level physics profile configuration.

    Maps intuitive sliders (reactivity, resilience, safety) to low-level
    physics parameters (w_c, gamma, stability).

    Attributes:
        name: Profile name (e.g., "SCHOOL_DEFAULT")
        base_mode: Base context mode (SCHOOL, GAME, THERAPY)
        reactivity: 0.0-1.0, maps to gamma and w_p (higher = more responsive)
        resilience: 0.0-1.0, maps to stability_baseline and w_c (higher = more stable)
        safety: 0.0-1.0, maps to Policy strictness (higher = stricter)
        description: Human-readable description
    """
    name: str = Field(..., description="Profile identifier")
    base_mode: BaseMode = Field(..., description="Base context mode")
    reactivity: float = Field(0.5, ge=0.0, le=1.0, description="Response speed (0=slow, 1=fast)")
    resilience: float = Field(0.5, ge=0.0, le=1.0, description="Stability (0=fragile, 1=robust)")
    safety: float = Field(0.5, ge=0.0, le=1.0, description="Safety strictness (0=permissive, 1=strict)")
    description: Optional[str] = Field(None, description="Human-readable description")

    @field_validator('reactivity', 'resilience', 'safety')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure values are in [0, 1] range."""
        return max(0.0, min(1.0, v))

    model_config = ConfigDict(
        use_enum_values=True,
        extra='allow',
        json_schema_extra={'example': {'name': 'SCHOOL_DEFAULT', 'base_mode': 'SCHOOL', 'reactivity': 0.2, 'resilience': 0.9, 'safety': 0.8, 'description': 'High resilience, low reactivity for educational settings'}},
    )
class ProfileLoader:
    """
    Loads and manages physics profiles from YAML files.

    Usage:
        >>> loader = ProfileLoader()
        >>> profile = loader.load("SCHOOL_DEFAULT")
        >>> print(profile.resilience)  # 0.9
    """

    def __init__(self, profiles_file: Optional[Path] = None):
        """
        Initialize profile loader.

        Args:
            profiles_file: Path to profiles.yaml. If None, uses default location.
        """
        if profiles_file is None:
            # Default: core-physics/src/phionyx_physics/profiles.yaml
            profiles_file = Path(__file__).parent / "profiles.yaml"

        self.profiles_file = profiles_file
        self._profiles: Dict[str, PhysicsProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load all profiles from YAML file."""
        if not self.profiles_file.exists():
            raise FileNotFoundError(
                f"Profiles file not found: {self.profiles_file}\n"
                f"Please create profiles.yaml with default presets."
            )

        with open(self.profiles_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or 'profiles' not in data:
            raise ValueError("Invalid profiles.yaml format. Expected 'profiles' key.")

        for profile_data in data['profiles']:
            profile = PhysicsProfile(**profile_data)
            self._profiles[profile.name] = profile

    def load(self, name: str) -> PhysicsProfile:
        """
        Load a profile by name.

        Args:
            name: Profile name (e.g., "SCHOOL_DEFAULT")

        Returns:
            PhysicsProfile instance

        Raises:
            KeyError: If profile not found
        """
        if name not in self._profiles:
            raise KeyError(
                f"Profile '{name}' not found. Available profiles: {list(self._profiles.keys())}"
            )
        return self._profiles[name]

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        return list(self._profiles.keys())

    def create_custom(
        self,
        name: str,
        base_mode: BaseMode,
        reactivity: float,
        resilience: float,
        safety: float,
        description: Optional[str] = None
    ) -> PhysicsProfile:
        """
        Create a custom profile programmatically.

        Args:
            name: Profile identifier
            base_mode: Base context mode
            reactivity: 0.0-1.0
            resilience: 0.0-1.0
            safety: 0.0-1.0
            description: Optional description

        Returns:
            New PhysicsProfile instance
        """
        profile = PhysicsProfile(
            name=name,
            base_mode=base_mode,
            reactivity=reactivity,
            resilience=resilience,
            safety=safety,
            description=description
        )
        self._profiles[name] = profile
        return profile

