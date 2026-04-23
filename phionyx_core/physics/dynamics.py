"""
Dynamic Entropy & Stability Calculations
=========================================

Implements dynamic calculation logic for entropy and stability updates
based on runtime conditions (phi variance, negative emotions, complexity).

Scientific Grounding Upgrade (v3):
- Uses Information Theory (Kolmogorov Complexity) for entropy
- Uses Control Theory (Lyapunov Stability) for stability
- Replaces heuristic magic numbers with mathematically grounded approaches
"""

from typing import Optional, Dict
from .constants import (
    ENTROPY_MIN,
    ENTROPY_MAX,
    MIN_STABILITY,
    MAX_STABILITY,
)
from .tuner import PhysicsParams

# Module-level tunable defaults (Tier A — PRE surfaces)
SCHOOL_ALPHA = 0.1
SCHOOL_BETA = 0.2
GAME_ALPHA = 0.3
GAME_BETA = 0.1
DEFAULT_ALPHA = 0.2
DEFAULT_BETA = 0.15

# Scientific Grounding Imports
try:
    from .core_math import lyapunov_stability_check
    from .text_physics import calculate_text_entropy_zlib
    SCIENTIFIC_GROUNDING_AVAILABLE = True
except ImportError:
    # Fallback if modules not available (should not happen in production)
    SCIENTIFIC_GROUNDING_AVAILABLE = False


def calculate_dynamic_entropy(
    phi_variance: float,
    negative_emotion_count: int,
    complexity: float,
    base_entropy: Optional[float] = None
) -> float:
    """
    Calculate dynamic entropy based on runtime conditions.

    Formula: E_dynamic = 0.4 * var + 0.4 * emotion + 0.2 * complexity

    Where:
        - var: Normalized phi variance (0-1)
        - emotion: Normalized negative emotion count (0-1)
        - complexity: Normalized input complexity (0-1)

    Args:
        phi_variance: Variance in phi values over recent turns (raw value)
        negative_emotion_count: Count of negative emotions detected
        complexity: Input complexity score (0-1)
        base_entropy: Optional base entropy to add to dynamic component

    Returns:
        Dynamic entropy value (0-1), clamped to [ENTROPY_MIN, ENTROPY_MAX]

    Example:
        >>> entropy = calculate_dynamic_entropy(
        ...     phi_variance=0.5,
        ...     negative_emotion_count=3,
        ...     complexity=0.7
        ... )
        >>> assert 0.0 <= entropy <= 1.0
    """
    # Normalize phi_variance (assuming max variance ~2.0 for 0-10 phi range)
    # You may need to adjust this based on your actual variance distribution
    var_normalized = min(1.0, phi_variance / 2.0) if phi_variance > 0 else 0.0

    # Normalize negative_emotion_count (assuming max ~10 emotions per turn)
    emotion_normalized = min(1.0, negative_emotion_count / 10.0)

    # Complexity is already 0-1
    complexity_normalized = max(0.0, min(1.0, complexity))

    # Weighted sum: 40% variance + 40% emotion + 20% complexity
    dynamic_component = (0.4 * var_normalized) + (0.4 * emotion_normalized) + (0.2 * complexity_normalized)

    # Add base entropy if provided
    if base_entropy is not None:
        entropy = base_entropy + (dynamic_component * (1.0 - base_entropy))
    else:
        entropy = dynamic_component

    # Clamp to valid range
    return max(ENTROPY_MIN, min(ENTROPY_MAX, entropy))


def update_stability(
    current_stability: float,
    target_phi: float,
    current_phi: float,
    entropy: float,
    params: PhysicsParams,
    alpha: Optional[float] = None,
    beta: Optional[float] = None
) -> float:
    """
    Update stability based on target vs current phi and entropy.

    Formula: stab_new = stab + alpha * (target - current) - beta * entropy

    Where:
        - alpha: Learning rate (derived from base_mode: SCHOOL=0.1, GAME=0.3)
        - beta: Entropy penalty (derived from base_mode: SCHOOL=0.2, GAME=0.1)

    Args:
        current_stability: Current stability value (0-1)
        target_phi: Target phi value (0-10)
        current_phi: Current phi value (0-10)
        entropy: Current entropy (0-1)
        params: PhysicsParams from ProfileTuner
        alpha: Optional learning rate (if None, derived from params)
        beta: Optional entropy penalty (if None, derived from params)

    Returns:
        Updated stability value (0-1), clamped to [MIN_STABILITY, MAX_STABILITY]

    Example:
        >>> from phionyx_core.physics.tuner import ProfileTuner
        >>> params = ProfileTuner.profile_to_parameters(profile)
        >>> new_stability = update_stability(
        ...     current_stability=0.7,
        ...     target_phi=8.0,
        ...     current_phi=6.0,
        ...     entropy=0.3,
        ...     params=params
        ... )
    """
    # Derive alpha and beta from params if not provided
    if alpha is None:
        # SCHOOL mode: slower adaptation (alpha=0.1)
        # GAME mode: faster adaptation (alpha=0.3)
        # Default: 0.2
        from .constants import STABILITY_HIGH_THRESHOLD, STABILITY_LOW_THRESHOLD

        if params.stability_baseline > STABILITY_HIGH_THRESHOLD:  # High resilience = SCHOOL-like
            alpha = SCHOOL_ALPHA
        elif params.stability_baseline < STABILITY_LOW_THRESHOLD:  # Low resilience = GAME-like
            alpha = GAME_ALPHA
        else:
            alpha = DEFAULT_ALPHA

    if beta is None:
        # SCHOOL mode: higher entropy penalty (beta=0.2)
        # GAME mode: lower entropy penalty (beta=0.1)
        # Default: 0.15
        if params.stability_baseline > STABILITY_HIGH_THRESHOLD:  # High resilience = SCHOOL-like
            beta = SCHOOL_BETA
        elif params.stability_baseline < STABILITY_LOW_THRESHOLD:  # Low resilience = GAME-like
            beta = GAME_BETA
        else:
            beta = DEFAULT_BETA

    # Normalize phi difference (target and current are 0-10, difference max ~10)
    phi_diff = (target_phi - current_phi) / 10.0  # Normalize to 0-1

    # Update formula: stab_new = stab + alpha * (target - current) - beta * entropy
    stability_delta = (alpha * phi_diff) - (beta * entropy)
    new_stability = current_stability + stability_delta

    # Clamp to valid range
    return max(MIN_STABILITY, min(MAX_STABILITY, new_stability))


def calculate_complexity(input_text: str, turn_count: int = 1) -> float:
    """
    Calculate input complexity score (0-1).

    Simple heuristic based on:
        - Text length
        - Word count
        - Turn count (longer conversations = more complex)

    Args:
        input_text: User input text
        turn_count: Current turn number in conversation

    Returns:
        Complexity score (0-1)

    Example:
        >>> complexity = calculate_complexity("Hello", turn_count=1)
        >>> assert 0.0 <= complexity <= 1.0
    """
    # Normalize text length (assuming max ~500 chars = 1.0)
    length_score = min(1.0, len(input_text) / 500.0)

    # Normalize word count (assuming max ~100 words = 1.0)
    word_count = len(input_text.split())
    word_score = min(1.0, word_count / 100.0)

    # Normalize turn count (assuming max ~50 turns = 1.0)
    turn_score = min(1.0, turn_count / 50.0)

    # Weighted average: 50% length + 30% words + 20% turns
    complexity = (0.5 * length_score) + (0.3 * word_score) + (0.2 * turn_score)

    return max(0.0, min(1.0, complexity))


# ============================================================================
# SCIENTIFIC GROUNDING UPGRADE (v3) - Information Theory & Control Theory
# ============================================================================

def calculate_dynamic_entropy_v3(
    input_text: str,
    phi_variance: float = 0.0,
    negative_emotion_ratio: float = 0.0,
    base_entropy: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate dynamic entropy using Kolmogorov Complexity (Information Theory).

    Scientific Grounding:
    - Replaces naive "length/500" complexity heuristic with Kolmogorov Complexity
    - Uses Zlib compression ratio to measure actual information density
    - Weighted combination: System Variance + Emotional State + Information Density

    Args:
        input_text: User input text (REQUIRED for entropy calculation)
        phi_variance: Normalized phi variance (0-1), system stability indicator
        negative_emotion_ratio: Ratio of negative emotions (0-1)
        base_entropy: Optional base entropy to blend with dynamic component
        weights: Optional custom weights dict {"w_var": float, "w_emo": float, "w_info": float}

    Returns:
        Dynamic entropy value (0-1), clamped to [ENTROPY_MIN, ENTROPY_MAX]

    Example:
        >>> entropy = calculate_dynamic_entropy_v3(
        ...     input_text="I am very happy and excited!",
        ...     phi_variance=0.3,
        ...     negative_emotion_ratio=0.1
        ... )
        >>> assert ENTROPY_MIN <= entropy <= ENTROPY_MAX
    """
    if not SCIENTIFIC_GROUNDING_AVAILABLE:
        # Fallback to v1 if modules not available (use calculate_complexity)
        complexity = calculate_complexity(input_text, turn_count=1)
        # Use v1 formula with normalized inputs
        var_normalized = max(0.0, min(1.0, phi_variance))
        emo_normalized = max(0.0, min(1.0, negative_emotion_ratio))
        dynamic_component = (0.4 * var_normalized) + (0.4 * emo_normalized) + (0.2 * complexity)
        entropy = base_entropy + (dynamic_component * (1.0 - base_entropy)) if base_entropy is not None else dynamic_component
        return max(ENTROPY_MIN, min(ENTROPY_MAX, entropy))

    # Default weights (Scientific baseline)
    if weights is None:
        weights = {
            "w_var": 0.35,  # System Stability Weight
            "w_emo": 0.35,  # Emotional Valence Weight
            "w_info": 0.30  # Information Density Weight (Kolmogorov Complexity)
        }

    # 1. Information Density (The 'Complexity' fix - Scientific)
    # Measures the 'Surprise' or 'Randomness' of the input text using Kolmogorov Complexity
    info_density = calculate_text_entropy_zlib(input_text)

    # 2. Normalize phi_variance (0-1 range expected)
    var_normalized = max(0.0, min(1.0, phi_variance))

    # 3. Normalize negative_emotion_ratio (0-1 range expected)
    emo_normalized = max(0.0, min(1.0, negative_emotion_ratio))

    # 4. Calculate Weighted Entropy (Scientific Formula)
    # E = w_var * Var + w_emo * Emo + w_info * Info
    raw_entropy = (
        (weights["w_var"] * var_normalized) +
        (weights["w_emo"] * emo_normalized) +
        (weights["w_info"] * info_density)
    )

    # 5. Blend with base_entropy if provided
    if base_entropy is not None:
        entropy = base_entropy + (raw_entropy * (1.0 - base_entropy))
    else:
        entropy = raw_entropy

    # Clamp to valid range
    return max(ENTROPY_MIN, min(ENTROPY_MAX, entropy))


def update_system_stability(
    current_stability: float,
    current_phi: float,
    target_phi: float,
    entropy: float,
    input_energy: float = 0.0,
    params: Optional[PhysicsParams] = None,
    alpha: Optional[float] = None,
    beta: Optional[float] = None
) -> float:
    """
    Update stability ensuring Lyapunov convergence (Control Theory).

    Scientific Grounding:
    - Uses Lyapunov Stability Criterion to prevent energy explosion
    - Enforces V_dot < 0 when input is zero (thermodynamic consistency)
    - Physics-based restoration force (Hooke's Law style)

    Args:
        current_stability: Current stability value (0-1)
        current_phi: Current phi value (0-10)
        target_phi: Target phi value (0-10)
        entropy: Current entropy (0-1)
        input_energy: External energy input (default: 0.0)
        params: Optional PhysicsParams (for backward compatibility)
        alpha: Optional learning rate (if None, uses default 0.1)
        beta: Optional entropy penalty (if None, uses default 0.05)

    Returns:
        Updated stability value (0-1), clamped to [MIN_STABILITY, MAX_STABILITY]

    Example:
        >>> new_stability = update_system_stability(
        ...     current_stability=0.7,
        ...     current_phi=6.0,
        ...     target_phi=8.0,
        ...     entropy=0.3,
        ...     input_energy=0.0
        ... )
        >>> assert MIN_STABILITY <= new_stability <= MAX_STABILITY
    """
    if not SCIENTIFIC_GROUNDING_AVAILABLE:
        # Fallback to v1 if modules not available
        if params is None:
            raise ValueError("params required when scientific grounding unavailable")
        return update_stability(
            current_stability=current_stability,
            target_phi=target_phi,
            current_phi=current_phi,
            entropy=entropy,
            params=params,
            alpha=alpha,
            beta=beta
        )

    # 1. Physics-based Delta (Hooke's Law style restoration force)
    # Restoration Force: F = -k * (current - target)
    # Normalize phi difference (0-10 range -> 0-1)
    phi_diff_normalized = (target_phi - current_phi) / 10.0
    restoration_force = 0.1 * phi_diff_normalized  # k = 0.1 (learning rate)

    # 2. Entropy Friction: High entropy reduces ability to stabilize
    if beta is None:
        beta = 0.05  # Default entropy penalty
    friction = beta * entropy

    # 3. Calculate new stability
    new_stability = current_stability + restoration_force - friction

    # 4. Lyapunov Stability Check (The 'Math Proof' fix)
    # Ensures the system doesn't explode mathematically
    # energy_t1 = new_stability, energy_t0 = current_stability
    damping = lyapunov_stability_check(
        energy_t1=new_stability,
        energy_t0=current_stability,
        input_energy=input_energy
    )

    # Apply damping if instability detected
    final_stability = new_stability * damping

    # Clamp to valid range
    return max(MIN_STABILITY, min(MAX_STABILITY, final_stability))

