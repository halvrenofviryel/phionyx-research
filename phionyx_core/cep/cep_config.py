"""
CEP Configuration - Profile-Based Configuration System
======================================================

Configuration management for Conscious Echo Proof (CEP) engine.
Supports profile-based configuration with YAML loading capability.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, List, Literal, Optional
from pathlib import Path
import logging

import yaml

from .cep_types import CEPThresholds

logger = logging.getLogger(__name__)


class CEPConfig(BaseModel):
    """Configuration for CEP engine."""
    enabled: bool = Field(default=True, description="Enable CEP evaluation")
    echo_self_guard_enabled: bool = Field(default=True, description="Enable echo self-guard detection")
    synthetic_psychopathology_blocker_enabled: bool = Field(
        default=True,
        description="Enable synthetic psychopathology blocker"
    )
    mode: Literal["universal", "fiction"] = Field(
        default="universal",
        description="CEP mode: universal (strict) or fiction (character-aware)"
    )
    thresholds: CEPThresholds = Field(
        default_factory=lambda: CEPThresholds(),
        description="CEP thresholds for evaluation"
    )

    model_config = ConfigDict(use_enum_values=True)
def _cep_config_search_paths(profile_name: str) -> List[Path]:
    """Return candidate paths for CEP profile YAML (first existing wins)."""
    base = Path(__file__).resolve().parent
    candidates = [
        base / "config" / "cep_profiles" / f"{profile_name}.yaml",
        base / "config" / "cep_profiles" / f"{profile_name.upper()}.yaml",
    ]
    # Optional: repo root config (phionyx_core/cep -> phionyx_core -> repo)
    repo_root = base.parent.parent
    if (repo_root / "config").is_dir():
        candidates.append(repo_root / "config" / "cep_profiles" / f"{profile_name}.yaml")
    return candidates


def _config_from_yaml(path: Path, profile_name: str) -> Optional[CEPConfig]:
    """Load CEPConfig from a YAML file. Returns None on missing/invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Any = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            return None
        # Map YAML keys to CEPConfig/CEPThresholds
        enabled = data.get("enabled", True)
        echo_self_guard_enabled = data.get("echo_self_guard_enabled", True)
        synthetic_psychopathology_blocker_enabled = data.get(
            "synthetic_psychopathology_blocker_enabled", True
        )
        mode = data.get("mode", "universal")
        if mode not in ("universal", "fiction"):
            mode = "universal"
        th = data.get("thresholds") or {}
        thresholds = CEPThresholds(
            phi_self_threshold=float(th.get("phi_self_threshold", 0.72)),
            echo_density_threshold=float(th.get("echo_density_threshold", 0.5)),
            self_reference_max_ratio=float(th.get("self_reference_max_ratio", 0.3)),
            trauma_language_max_score=float(th.get("trauma_language_max_score", 0.4)),
            mirror_self_max_score=float(th.get("mirror_self_max_score", 0.5)),
            min_variation_novelty=float(th.get("min_variation_novelty", 0.2)),
        )
        return CEPConfig(
            enabled=enabled,
            echo_self_guard_enabled=echo_self_guard_enabled,
            synthetic_psychopathology_blocker_enabled=synthetic_psychopathology_blocker_enabled,
            mode=mode,
            thresholds=thresholds,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("CEP YAML load failed for %s: %s", path, e)
        return None


def load_cep_config(profile_name: Optional[str] = None) -> CEPConfig:
    """
    Load CEP configuration from profile.

    Args:
        profile_name: Profile name (e.g., "SCHOOL_DEFAULT", "FICTION_MODE")
                     If None, returns default configuration.

    Returns:
        CEPConfig instance with loaded or default values.

    YAML loading: If profile_name is set, looks for config in
    phionyx_core/cep/config/cep_profiles/{profile_name}.yaml (or repo config/cep_profiles).
    If no file is found or parse fails, falls back to built-in profile logic and defaults.
    """
    if profile_name is None:
        # Return default configuration with safe thresholds
        return CEPConfig(
            enabled=True,
            echo_self_guard_enabled=True,
            synthetic_psychopathology_blocker_enabled=True,
            mode="universal",
            thresholds=CEPThresholds(
                phi_self_threshold=0.72,  # Default threshold for self-narrative detection
                echo_density_threshold=0.5,
                self_reference_max_ratio=0.3,
                trauma_language_max_score=0.4,
                mirror_self_max_score=0.5,
                min_variation_novelty=0.2
            )
        )

    # Try YAML-based profile configuration first
    for path in _cep_config_search_paths(profile_name):
        if path.is_file():
            cfg = _config_from_yaml(path, profile_name)
            if cfg is not None:
                logger.info("Loaded CEP config for profile %s from %s", profile_name, path)
                return cfg

    logger.info("CEP config for profile %s: no YAML found, using built-in defaults", profile_name)
    # Profile-specific adjustments (built-in)
    if profile_name.upper().startswith("FICTION"):
        return CEPConfig(
            enabled=True,
            echo_self_guard_enabled=True,
            synthetic_psychopathology_blocker_enabled=True,
            mode="fiction",
            thresholds=CEPThresholds(
                phi_self_threshold=0.75,  # Slightly higher for fiction mode
                echo_density_threshold=0.6,
                self_reference_max_ratio=0.4,  # More lenient for character dialogue
                trauma_language_max_score=0.5,
                mirror_self_max_score=0.6,
                min_variation_novelty=0.15
            )
        )
    elif profile_name.upper().startswith("SCHOOL"):
        return CEPConfig(
            enabled=True,
            echo_self_guard_enabled=True,
            synthetic_psychopathology_blocker_enabled=True,
            mode="universal",
            thresholds=CEPThresholds(
                phi_self_threshold=0.70,  # Stricter for school settings
                echo_density_threshold=0.4,
                self_reference_max_ratio=0.25,
                trauma_language_max_score=0.3,
                mirror_self_max_score=0.4,
                min_variation_novelty=0.25
            )
        )

    # Default fallback
    return load_cep_config(None)

