"""
Profile Compiler
================

Pre-compiles profiles to cache Physics + Meta parameters.
Reduces runtime latency by pre-calculating parameter mappings.
"""

import json
import logging
from pathlib import Path
from typing import Any

from .schema import Profile
from .tuner import ProfileTuner

logger = logging.getLogger(__name__)


class ProfileCompiler:
    """
    Compiles profiles to cache pre-calculated parameters.

    At compile time:
    - Maps high-level profile knobs to low-level physics parameters
    - Pre-calculates meta-cognition thresholds
    - Caches results for fast runtime lookup
    """

    def __init__(self, cache_dir: Path | None = None):
        """
        Initialize profile compiler.

        Args:
            cache_dir: Directory for compiled profile cache (default: ./profile_cache)
        """
        self.cache_dir = cache_dir or Path("./profile_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tuner = ProfileTuner()

    def compile_profile(self, profile: Profile) -> dict[str, Any]:
        """
        Compile a profile to cached parameters.

        Args:
            profile: Profile to compile

        Returns:
            Compiled profile dictionary with pre-calculated parameters
        """
        compiled = {
            "name": profile.name,
            "version": profile.version or "1.0.0",
            "compiled_at": None,  # Will be set by caller
        }

        # Compile Physics parameters
        physics_params = self.tuner.profile_to_parameters(
            profile.physics,
            profile.routing
        )
        compiled["physics"] = {
            "reactivity": profile.physics.reactivity,
            "resilience": profile.physics.resilience,
            "safety_bias": profile.physics.safety_bias,
            "base_mode": profile.physics.base_mode.value,
            "compiled_params": {
                "gamma": physics_params.gamma,
                "w_c": physics_params.w_c,
                "w_p": physics_params.w_p,
                "f_self": physics_params.f_self,
                "kappa": physics_params.kappa if hasattr(physics_params, 'kappa') else None,
            }
        }

        # Compile Meta-Cognition parameters
        compiled["meta"] = {
            "uncertainty_threshold": 0.6,  # Default
            "semantic_anomaly_threshold": 0.5,  # Semantic anomaly detection
            "confidence_penalties": {
                "entropy_penalty": 0.3 if profile.physics.reactivity > 0.7 else 0.2,
                "memory_penalty": 0.4,
                "input_penalty": 0.2,
            }
        }

        # Compile Routing parameters
        compiled["routing"] = {
            "llm_tier_strategy": profile.routing.llm_tier_strategy.value,
            "enable_graph_rag": profile.routing.enable_graph_rag,
            "fallback_model": profile.routing.fallback_model,
        }

        # Compile Governance parameters
        compiled["governance"] = {
            "policy_id": profile.governance.policy_id,
            "pii_mode": profile.governance.pii_mode.value,
            "audit_level": profile.governance.audit_level.value,
        }

        # Compile Pedagogy parameters
        compiled["pedagogy"] = {
            "vygotsky_level": profile.pedagogy.vygotsky_level,
            "scaffolding_aggressiveness": profile.pedagogy.scaffolding_aggressiveness,
            "intervention_threshold": profile.pedagogy.intervention_threshold,
        }

        return compiled

    def save_compiled_profile(self, compiled: dict[str, Any], profile_name: str):
        """
        Save compiled profile to cache.

        Args:
            compiled: Compiled profile dictionary
            profile_name: Profile name (used for filename)
        """
        from datetime import datetime, timezone
        compiled["compiled_at"] = datetime.now(timezone.utc).isoformat()

        cache_file = self.cache_dir / f"{profile_name}_compiled.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(compiled, f, indent=2, ensure_ascii=False)

            logger.info(f"Compiled profile saved: {cache_file}")

        except Exception as e:
            logger.error(f"Failed to save compiled profile: {e}")

    def load_compiled_profile(self, profile_name: str) -> dict[str, Any] | None:
        """
        Load compiled profile from cache.

        Args:
            profile_name: Profile name

        Returns:
            Compiled profile dictionary or None if not found
        """
        cache_file = self.cache_dir / f"{profile_name}_compiled.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                compiled = json.load(f)

            logger.debug(f"Loaded compiled profile: {cache_file}")
            return compiled

        except Exception as e:
            logger.error(f"Failed to load compiled profile: {e}")
            return None

    def compile_all_profiles(self, profiles: list[Profile]):
        """
        Compile all profiles and save to cache.

        Args:
            profiles: List of profiles to compile
        """
        logger.info(f"Compiling {len(profiles)} profiles...")

        for profile in profiles:
            try:
                compiled = self.compile_profile(profile)
                self.save_compiled_profile(compiled, profile.name)
            except Exception as e:
                logger.error(f"Failed to compile profile {profile.name}: {e}")


def compile_profiles(profile_dir: Path | None = None):
    """
    Convenience function to compile all profiles from YAML.

    Args:
        profile_dir: Directory containing profiles.yaml (default: ./config)
    """
    from .loader import ProfileLoader

    loader = ProfileLoader(profile_dir)
    profiles = loader.load_all_profiles()

    compiler = ProfileCompiler()
    compiler.compile_all_profiles(profiles)

    logger.info(f"Profile compilation complete. {len(profiles)} profiles compiled.")


if __name__ == "__main__":
    # CLI entry point
    import sys

    if len(sys.argv) > 1:
        profile_dir = Path(sys.argv[1])
    else:
        profile_dir = None

    compile_profiles(profile_dir)

