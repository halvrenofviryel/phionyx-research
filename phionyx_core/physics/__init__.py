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
from . import formulas
from . import constants
from . import types

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
from .formulas import (  # noqa: F401
    calculate_phi_v2,  # v2.0 (Hybrid Resonance Model, backward compatible)
    calculate_phi_v2_1,  # v2.1 (Circumplex-integrated)
    calculate_phi_cognitive,
    calculate_phi_physical,
    compute_phi_components,  # NPC-specific interface (Plutchik → Circumplex → Φ)
    get_context_weights,
    calculate_functional_coherence_score,  # New name (FCS)
    calculate_consciousness_index,  # Deprecated alias (backward compatibility)
    calculate_resonance_force,
    calculate_echo_energy,
    calculate_entropy_shannon,
    calculate_momentum,
    estimate_trace_duration,
    calculate_temporal_echo,
    classify_resonance,
    adjust_gamma,
)

from .constants import (  # noqa: F401
    GOLDEN_RATIO,
    MAX_ENTROPY,
    DEFAULT_GAMMA,
    DEFAULT_F_SELF,
    PHI_UNIVERSE,
    CONTEXT_WEIGHTS,  # v2.0
    MIN_STABILITY,  # v2.0
    MAX_STABILITY,  # v2.0
)

from .types import (  # noqa: F401
    PhysicsInput,
    PhysicsOutput,
    PhysicsState,
    NPCPhysicsParams,  # NPC-specific physics parameters
    PhiComponents,  # Φ calculation output components
)

# Configuration & Tuning Layer
from .profiles import (  # noqa: F401
    PhysicsProfile,
    ProfileLoader,
    BaseMode,
)

from .tuner import (  # noqa: F401
    ProfileTuner,
    PhysicsParams,
)

from .dynamics import (  # noqa: F401
    calculate_dynamic_entropy,
    update_stability,
    calculate_complexity,
)

from .entropy_modulation import (  # noqa: F401
    EntropyModulationConfig,
    calculate_entropy_modulated_amplitude,
    modulate_empathic_intervention_strength,
    modulate_directiveness_level,
    modulate_sentence_length_intensity,
    calculate_behavior_modulation,
)

from .coherence import (  # noqa: F401
    calculate_coherence,
    calculate_coherence_with_confidence,
    get_coherence_entropy_boost,
)

from .inertia import (  # noqa: F401
    apply_inertia_to_decay_rate,
    apply_inertia_to_ukf_process_noise,
    apply_inertia_to_derivative_gain,
    get_inertia_from_profile,
    update_inertia_slowly,
)

from .semantic_time_decay import (  # noqa: F401
    calculate_decay_rate,
    calculate_decay_factor,
    apply_semantic_time_decay,
    calculate_semantic_time_decay_metadata,
    SemanticTimeDecayManager,
)

from .dominance import (  # noqa: F401
    apply_dominance_to_av_modulation,
    extract_dominance_from_measurement,
    get_dominance_default_for_profile,
    apply_dominance_to_response_amplitude,
)

from .empathy import (  # noqa: F401
    calculate_empathy_v1_1,
    calculate_closeness_language_policy,
    get_tau_from_profile,
    calculate_empathy_with_profile,
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

