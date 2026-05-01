"""
Core Physics Module - Pure Mathematical Formulas
===============================================

Saf matematik modülü. Dışa bağımsız, hiçbir dependency yok.
Sadece Python standard library kullanır.

Exports:
- formulas: All physics calculation functions
- constants: Mathematical constants
- types: Pydantic models for type safety
"""

# Import modules using relative imports (standard package structure)
from . import constants, formulas, types

__all__ = [
    "formulas",
    "constants",
    "types",
    "entropy_modulation",
    "coherence",
    "inertia",
    "dominance",
    "empathy",
]

# Convenience exports
from .coherence import (  # noqa: F401
    calculate_coherence,
    calculate_coherence_with_confidence,
    get_coherence_entropy_boost,
)
from .constants import (  # noqa: F401
    CONTEXT_WEIGHTS,  # v2.0
    DEFAULT_F_SELF,
    DEFAULT_GAMMA,
    GOLDEN_RATIO,
    MAX_ENTROPY,
    MAX_STABILITY,  # v2.0
    MIN_STABILITY,  # v2.0
    PHI_UNIVERSE,
)
from .dominance import (  # noqa: F401
    apply_dominance_to_av_modulation,
    apply_dominance_to_response_amplitude,
    extract_dominance_from_measurement,
    get_dominance_default_for_profile,
)
from .dynamics import (  # noqa: F401
    calculate_complexity,
    calculate_dynamic_entropy,
    update_stability,
)
from .empathy import (  # noqa: F401
    calculate_closeness_language_policy,
    calculate_empathy_v1_1,
    calculate_empathy_with_profile,
    get_tau_from_profile,
)
from .entropy_modulation import (  # noqa: F401
    EntropyModulationConfig,
    calculate_behavior_modulation,
    calculate_entropy_modulated_amplitude,
    modulate_directiveness_level,
    modulate_empathic_intervention_strength,
    modulate_sentence_length_intensity,
)
from .formulas import (  # noqa: F401
    adjust_gamma,
    calculate_consciousness_index,  # Deprecated alias (backward compatibility)
    calculate_echo_energy,
    calculate_entropy_shannon,
    calculate_functional_coherence_score,  # New name (FCS)
    calculate_momentum,
    calculate_phi_cognitive,
    calculate_phi_physical,
    calculate_phi_v2,  # v2.0 (Hybrid Resonance Model, backward compatible)
    calculate_phi_v2_1,  # v2.1 (Circumplex-integrated)
    calculate_resonance_force,
    calculate_temporal_echo,
    classify_resonance,
    compute_phi_components,  # NPC-specific interface (Plutchik → Circumplex → Φ)
    estimate_trace_duration,
    get_context_weights,
)
from .inertia import (  # noqa: F401
    apply_inertia_to_decay_rate,
    apply_inertia_to_derivative_gain,
    apply_inertia_to_ukf_process_noise,
    get_inertia_from_profile,
    update_inertia_slowly,
)

# Configuration & Tuning Layer
from .profiles import (  # noqa: F401
    BaseMode,
    PhysicsProfile,
    ProfileLoader,
)
from .semantic_time_decay import (  # noqa: F401
    SemanticTimeDecayManager,
    apply_semantic_time_decay,
    calculate_decay_factor,
    calculate_decay_rate,
    calculate_semantic_time_decay_metadata,
)
from .tuner import (  # noqa: F401
    PhysicsParams,
    ProfileTuner,
)
from .types import (  # noqa: F401
    NPCPhysicsParams,  # NPC-specific physics parameters
    PhiComponents,  # Φ calculation output components
    PhysicsInput,
    PhysicsOutput,
    PhysicsState,
)

__all__ = [
    "formulas",
    "constants",
    "types",
    "entropy_modulation",
    "coherence",
    "inertia",
    "dominance",
    "empathy",
    # Semantic Time Decay (Patent Aile 4)
    "calculate_decay_rate",
    "calculate_decay_factor",
    "apply_semantic_time_decay",
    "calculate_semantic_time_decay_metadata",
    "SemanticTimeDecayManager",
]

__version__ = "1.0.0"

