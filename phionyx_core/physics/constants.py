"""
State Model Constants - Immutable Mathematical Constants
========================================================

Saf matematik sabitleri. Dışa bağımsız, hiçbir dependency yok.
"""

# Golden Ratio (φ) - Used in resonance calculations
GOLDEN_RATIO = 0.618033988749895

# Maximum entropy (S_max)
MAX_ENTROPY = 1.0

# Default decay rate (γ)
DEFAULT_GAMMA = 0.15

# Default self-frequency (f_self) for coherence calculations
DEFAULT_F_SELF = 0.95

# Universe resistance constant (Φ_universe)
PHI_UNIVERSE = 5.0

# Minimum time delta to avoid division by zero
MIN_TIME_DELTA = 0.001

# Phi bounds
PHI_MIN = 0.0
PHI_MAX = 10.0  # Theoretical max, but typically 0-1 range

# Coherence score bounds
CONSCIOUSNESS_MIN = 0.0
CONSCIOUSNESS_MAX = 1.0

# Entropy bounds
ENTROPY_MIN = 0.0
ENTROPY_MAX = 1.0

# Amplitude bounds
AMPLITUDE_MIN = 0.0
AMPLITUDE_MAX = 10.0

# Gamma bounds (decay rate)
GAMMA_MIN = 0.05
GAMMA_MAX = 0.5

# ============================================================================
# PHYSICS v2.0 - Hybrid Resonance Model Constants
# ============================================================================

# Context Weights (w_c: Cognitive, w_p: Physical)
# Determines balance between internal stability and external response
CONTEXT_WEIGHTS = {
    "SCHOOL":     {"wc": 0.75, "wp": 0.25},  # Tutarlılık odaklı (Stability > Response)
    "GAME":       {"wc": 0.40, "wp": 0.60},  # Tepki odaklı (Response > Stability)
    "NPC_ENGINE": {"wc": 0.50, "wp": 0.50},  # Dengeli
    "THERAPY":    {"wc": 0.90, "wp": 0.10},  # Stabilite odaklı (Maximum Stability)
    "DEFAULT":    {"wc": 0.50, "wp": 0.50}   # Balanced default
}

# Valid Ranges for v2.0
MIN_ENTROPY = 0.0
MAX_ENTROPY = 1.0
MIN_STABILITY = 0.0
MAX_STABILITY = 1.0

# ============================================================================
# THRESHOLD CONSTANTS (Centralized from scattered hardcoded values)
# ============================================================================

# Stability thresholds for dynamics calculations
STABILITY_HIGH_THRESHOLD = 0.7  # High resilience = SCHOOL-like
STABILITY_LOW_THRESHOLD = 0.4   # Low resilience = GAME-like

# Entropy thresholds
ENTROPY_THRESHOLD_DEFAULT = 0.5  # Default threshold for penalty calculations

# Coherence constants
COHERENCE_SIGMOID_STEEPNESS = 10.0  # Default sigmoid steepness for coherence calculation
COHERENCE_NORMALIZATION_FACTOR = 2.0  # Normalization factor for residual calculation
COHERENCE_MIDPOINT = 0.5  # Midpoint for sigmoid transformation

# Confidence weighting constants
CONFIDENCE_FACTOR_MIN = 0.5  # Minimum confidence factor
CONFIDENCE_FACTOR_MAX = 1.0  # Maximum confidence factor
CONFIDENCE_FALLBACK_COHERENCE = 0.7  # Fallback coherence for low confidence

# Entropy boost constants
ENTROPY_BOOST_FACTOR = 0.1  # Default entropy boost factor from low coherence
ENTROPY_MIN_INVARIANT = 0.01  # Minimum entropy (invariant: H >= 0.01)

# Temporal echo threshold
TEMPORAL_ECHO_PHI_THRESHOLD = 0.1  # Phi threshold for temporal echo calculation

