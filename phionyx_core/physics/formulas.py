"""
State Scoring Functions - Pure Mathematical Functions
=====================================================

Pure mathematical formulas. No external dependencies.
Uses only Python standard library (math).

Formulas (v2.0 - Hybrid State Model):
- Φ (Phi): Echo Quality (Hybrid: Cognitive + Physical)
- C: Functional Coherence Score
- F: Quality Coupling Score
- E: Echo Energy
- S: Entropy
- M: Momentum
- T: Temporal Echo
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import NPCPhysicsParams, PhiComponents

# Import constants from single source of truth
from .constants import (
    AMPLITUDE_MAX,
    AMPLITUDE_MIN,
    CONSCIOUSNESS_MAX,
    CONSCIOUSNESS_MIN,
    CONTEXT_WEIGHTS,
    DEFAULT_F_SELF,
    ENTROPY_MAX,
    ENTROPY_MIN,
    GAMMA_MAX,
    GAMMA_MIN,
    MAX_STABILITY,
    MIN_STABILITY,
    MIN_TIME_DELTA,
    PHI_MAX,
    PHI_MIN,
)

# ── Tunable Parameters (Tier A: Research Engine may modify) ──
entropy_penalty_k = 0.0
base_resonance = 0.12
recovery_gain = 0.19


def calculate_functional_coherence_score(
    phi_current: float,
    phi_previous: float,
    time_delta: float,
    f_self: float = DEFAULT_F_SELF
) -> float:
    """
    Calculate FCS (Functional Coherence Score).

    Renamed from "Consciousness Index" for better accuracy.
    Measures the functional coherence of the echo system based on phi rate of change.

    Formula: FCS = (dΦ/dt) / f_self

    Args:
        phi_current: Current Φ value
        phi_previous: Previous Φ value
        time_delta: Time difference, seconds
        f_self: Self-frequency (Hz), default 0.5

    Returns:
        Functional coherence score (0.0 - 1.0)
    """
    # Clamp inputs to avoid division by zero
    time_delta = max(MIN_TIME_DELTA, time_delta)
    f_self = max(0.001, f_self)  # Avoid division by zero

    if time_delta < MIN_TIME_DELTA or f_self == 0:
        return 0.0

    # Rate of change: dΦ/dt
    dPhi_dt = (phi_current - phi_previous) / time_delta

    # Functional Coherence Score: FCS = (dΦ/dt) / f_self
    fcs = dPhi_dt / f_self

    # Clamp to valid range
    return max(CONSCIOUSNESS_MIN, min(CONSCIOUSNESS_MAX, abs(fcs)))


# Backward compatibility alias
def calculate_consciousness_index(
    phi_current: float,
    phi_previous: float,
    time_delta: float,
    f_self: float = DEFAULT_F_SELF
) -> float:
    """
    DEPRECATED: Use calculate_functional_coherence_score() instead.

    This is an alias for backward compatibility.
    """
    return calculate_functional_coherence_score(phi_current, phi_previous, time_delta, f_self)


def calculate_resonance_force(
    phi1: float,
    phi2: float,
    delta_f: float,
    t: float
) -> float:
    """
    Calculate F (Resonance Force).

    Formula: F_echo = Φ₁ · Φ₂ · cos(2πΔf·t)

    Args:
        phi1: First echo's Φ value
        phi2: Second echo's Φ value
        delta_f: Frequency difference (Hz)
        t: Time (seconds)

    Returns:
        Resonance force value
    """
    return phi1 * phi2 * math.cos(2 * math.pi * delta_f * t)


def calculate_echo_energy(
    phi: float,
    links: int,
    delta_entropy: float
) -> float:
    """
    Calculate E (Echo Energy).

    Formula: E_echo = Φ · L · ΔS

    Args:
        phi: Echo Quality (Φ)
        links: Number of connections (L)
        delta_entropy: Entropy change (ΔS)

    Returns:
        Echo energy value
    """
    return phi * links * delta_entropy


def calculate_entropy_shannon(probabilities: list[float]) -> float:
    """
    Calculate S (Shannon Entropy).

    Formula: S = -k_B · Σ(p_i · log(p_i))

    Args:
        probabilities: List of probabilities (must sum to ~1.0)

    Returns:
        Entropy value
    """
    k_B = 1.0  # Normalized Boltzmann constant

    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log(p)

    return k_B * entropy


def calculate_momentum(
    energy: float,
    velocity: float,
    time_delta: float
) -> float:
    """
    Calculate M (Momentum).

    Formula: M_echo = (E · v) / t

    Args:
        energy: Echo energy (E)
        velocity: Velocity (v)
        time_delta: Time (t), seconds

    Returns:
        Momentum value
    """
    # Clamp time_delta to avoid division by zero
    time_delta = max(MIN_TIME_DELTA, time_delta)

    return (energy * velocity) / time_delta


def estimate_trace_duration(
    gamma: float,
    threshold: float = 0.1
) -> float:
    """
    Estimate trace duration (how long echo persists).

    Formula: t_trace = -ln(threshold) / γ

    Args:
        gamma: Decay rate (γ)
        threshold: Phi threshold (default 0.1)

    Returns:
        Trace duration in seconds (or inf if gamma=0)
    """
    if gamma == 0:
        return float('inf')

    return -math.log(threshold) / gamma


def calculate_temporal_echo(
    chain_index: int,
    gamma: float
) -> float:
    """
    Calculate T (Temporal Echo).

    Formula: T_echo = chain_index / γ

    Args:
        chain_index: Chain position
        gamma: Decay rate

    Returns:
        Temporal echo value
    """
    if gamma == 0:
        return float('inf')

    return chain_index / gamma


def calculate_c_echo_series(
    phi_values: list[float],
    time_deltas: list[float],
    f_self: float = DEFAULT_F_SELF
) -> float:
    """
    Calculate C Echo from a series of Φ values.

    Args:
        phi_values: List of Φ values over time
        time_deltas: List of time deltas
        f_self: Self-frequency

    Returns:
        Average functional coherence score (FCS)
    """
    if len(phi_values) < 2 or len(time_deltas) < 1:
        return 0.0

    consciousness_values = []
    for i in range(1, len(phi_values)):
        if i <= len(time_deltas):
            c = calculate_functional_coherence_score(
                phi_values[i],
                phi_values[i-1],
                time_deltas[i-1],
                f_self
            )
            consciousness_values.append(c)

    if not consciousness_values:
        return 0.0

    return sum(consciousness_values) / len(consciousness_values)


def classify_resonance(phi: float) -> str:
    """
    Classify resonance level based on Φ value.

    Assumes Φ is in range [PHI_MIN, PHI_MAX] = [0.0, 10.0]

    Thresholds (for 0-10 range):
        - high: >= 8.0
        - medium: >= 5.0
        - low: >= 2.0
        - fractured: < 2.0

    Args:
        phi: Echo Quality (Φ), expected range 0-10

    Returns:
        "high" | "medium" | "low" | "fractured"
    """
    # Clamp phi to valid range first
    phi = max(PHI_MIN, min(PHI_MAX, phi))

    # Thresholds for 0-10 range
    if phi >= 8.0:
        return "high"
    elif phi >= 5.0:
        return "medium"
    elif phi >= 2.0:
        return "low"
    else:
        return "fractured"


def adjust_gamma(
    current_gamma: float,
    intent_multiplier: float,
    severity: float = 0.5
) -> float:
    """
    Adjust gamma based on user intent (PTG feedback loop).

    This is a pure mathematical function. Intent classification
    should be done externally and multiplier passed in.

    Args:
        current_gamma: Current gamma value
        intent_multiplier: Multiplier from intent (1.5 for acceptance, 0.7 for rumination)
        severity: Event severity (0-1), affects adjustment magnitude

    Returns:
        Adjusted gamma (clamped to 0.05-0.3)

    Example:
        >>> # Acceptance: faster recovery
        >>> new_gamma = adjust_gamma(0.15, 1.5, severity=0.8)
        >>> assert new_gamma > 0.15

        >>> # Rumination: slower recovery
        >>> new_gamma = adjust_gamma(0.15, 0.7, severity=0.8)
        >>> assert new_gamma < 0.15
    """
    # Apply multiplier
    new_gamma = current_gamma * intent_multiplier

    # Severity affects the magnitude of adjustment
    severity_factor = 1.0 + (severity * 0.5)
    new_gamma = current_gamma + (new_gamma - current_gamma) * severity_factor

    # Clamp to valid range (0.05 - 0.3)
    return max(0.05, min(0.3, new_gamma))


def calculate_intrinsic_drive(phi: float, entropy: float, risk_level: str) -> float:
    """
    Calculates the internal pressure to explore (Curiosity Force).

    Only active when system is safe and stable.

    Args:
        phi: Current Cognitive Resonance (0.0 - 1.0)
        entropy: Current Entropy (0.0 - 1.0)
        risk_level: 'low', 'medium', 'high'

    Returns:
        drive: 0.0 to 1.0 (Higher means more desire to challenge/explore)
    """
    # Safety Override: Never explore in risky situations
    if risk_level != "low":
        return 0.0

    # Stability Threshold:
    # System must be stable (Phi > 0.2) to consider exploration.
    # Lowered threshold for Phionyx's "calm" nature - allows curiosity when feeling "a bit good"
    # Logic: max(0, phi - 0.2) * 1.25 maps [0.2, 1.0] -> [0.0, 1.0]
    stability_factor = max(0.0, (phi - 0.2) * 1.25)

    # Boredom Factor:
    # Boredom increases as entropy drops. Low entropy = High Boredom.
    # Entropy 0.2 -> Boredom 0.64
    # Entropy 0.8 -> Boredom 0.04
    boredom_factor = (1.0 - entropy) ** 2

    drive = stability_factor * boredom_factor
    return min(1.0, drive)


# ============================================================================
# PHYSICS v2.0 - Hybrid Resonance Model
# ============================================================================

def get_context_weights(context_mode: str) -> dict[str, float]:
    """
    Get cognitive (wc) and physical (wp) weights based on context.

    Args:
        context_mode: Context mode ("SCHOOL", "GAME", "NPC_ENGINE", "THERAPY", "DEFAULT")

    Returns:
        Dict with "wc" (cognitive weight) and "wp" (physical weight)
    """
    return CONTEXT_WEIGHTS.get(context_mode, CONTEXT_WEIGHTS["DEFAULT"])


def calculate_phi_cognitive(
    entropy: float,
    stability: float,
    valence: float = 0.0,
    entropy_penalty_k: float = entropy_penalty_k,
    previous_entropy: float | None = None,
    previous_valence: float | None = None,
    recovery_gain: float = recovery_gain,
    base_resonance: float = base_resonance,
) -> float:
    """
    Calculate Cognitive Resonance (Φ_cognitive).

    v2.0 (Legacy): Φ_c = (1 - Entropy) * Stability
    v2.1 (Circumplex): Φ_c = max{0, (V_eff * Stability) * (1 - Entropy * entropy_penalty_k)}
    v2.2 (Base Life Support): Φ_c = max{0, (V_eff * Stability) * (1 - Entropy * entropy_penalty_k)}
    v2.3 (Regulation Motor): Φ_c = max{phi_min_floor, (V_eff * Stability) * (1 - Nonlinear Entropy Penalty)}

    v2.2 Formula Change - "Base Life Support" Fix:
    - OLD: V_eff = (V + 1) / 2  [Problem: Negative valence → V_eff ≈ 0 → Phi collapses]
    - NEW: V_eff = base_resonance + (|V| * (1 - base_resonance))

    Philosophy: Negative emotions (stress, pain, anger) also create intense resonance.
    A suffering character's Phi should not be zero, only valence should be negative.

    Where:
    - base_resonance = 0.1 (10% minimum survival energy - prevents total collapse)
    - |V| = absolute emotional intensity (both positive and negative emotions create resonance)
    - V_eff range: [0.1, 1.0] (never drops below 10% even in neutral state)

    Examples:
    - Valence = -0.9 (deep stress) → intensity = 0.9 → V_eff = 0.91 (high resonance)
    - Valence = 0.0 (neutral) → intensity = 0.0 → V_eff = 0.1 (base floor)
    - Valence = +0.9 (joy) → intensity = 0.9 → V_eff = 0.91 (high resonance)

    Represents internal balance independent of external stimuli.
    Now includes valence (emotional tone) from Circumplex model.

    The entropy_penalty_k parameter controls how strongly entropy penalizes cognitive resonance:
    - k = 1.0: Standard penalty (backward compatible default)
    - k > 1.0: Stronger penalty (e.g., 1.2 for conservative/regulatory profiles)
    - k < 1.0: Weaker penalty (e.g., 0.9 for game/tolerant profiles)

    Args:
        entropy: Chaos level (0-1)
        stability: Internal resilience metric (0-1)
        valence: Emotional valence from Circumplex model (-1 to +1, default 0.0 for backward compat)
        entropy_penalty_k: Entropy penalty coefficient (default 1.0 for backward compatibility)
        previous_entropy: Previous entropy value (for recovery term calculation, optional)
        previous_valence: Previous valence value (for recovery term calculation, optional)
        recovery_gain: Recovery gain coefficient (default 0.05, range [0, 0.2])

    Returns:
        Cognitive resonance value (0-1, minimum 0.05 due to phi_min_floor)
    """
    # Clamp inputs to valid ranges
    entropy = max(ENTROPY_MIN, min(ENTROPY_MAX, entropy))
    stability = max(MIN_STABILITY, min(MAX_STABILITY, stability))
    valence = max(-1.0, min(1.0, valence))
    entropy_penalty_k = max(0.0, min(2.0, entropy_penalty_k))  # Clamp k to reasonable range [0, 2]

    # ⚠️ v2.2 REFACTORED: "Base Life Support" - Valence Death Trap Fix
    # Problem: Old formula v_eff = (valence + 1) / 2 caused Phi to collapse when valence < 0
    # Example: valence = -0.9 → v_eff = 0.05 → Phi ≈ 0 (character "dies")
    # Philosophy: Negative emotions (stress, pain, anger) also create intense resonance.
    # A suffering character's Phi should not be zero, only valence should be negative.
    #
    # Solution: Use absolute emotional intensity + base resonance floor
    # - High intensity (|valence| ≈ 1.0) → High resonance (both positive and negative)
    # - Neutral (valence ≈ 0.0) → Minimum resonance (base floor)
    # - Base resonance ensures system never fully collapses (survival bias)

    # 1. Absolute Emotional Intensity (both positive and negative emotions create resonance)
    emotional_intensity = abs(valence)  # Range: [0, 1]

    # 2. Base Life Support (minimum resonance floor - prevents total collapse)
    # Even in neutral state (valence=0), character maintains minimum cognitive resonance
    # Uses module-level base_resonance (Tier A tunable)

    # 3. Effective Valence: Base + Intensity-scaled contribution
    # Formula: v_eff = base + (intensity * (1 - base))
    # - intensity=0.0 (neutral) → v_eff = base_resonance (base floor)
    # - intensity=1.0 (extreme emotion) → v_eff = 1.0 (full resonance)
    v_eff = base_resonance + (emotional_intensity * (1.0 - base_resonance))
    v_eff = max(0.0, min(1.0, v_eff))  # Safety clamp

    # ⚠️ v2.3 REFACTORED: "Regulation Motor" - Sedation to Regulation Fix
    # Problem: v2.2 still causes Phi to collapse to 0.0 because entropy penalty is too aggressive
    # Philosophy: System should regulate chaos, not sedate (kill) the character
    #
    # Solution: Three improvements:
    # 1. Nonlinear entropy penalty (quadratic) - soft for low-mid entropy, harsh for extreme
    # 2. Phi minimum floor (0.05) - prevents total collapse unless crisis override
    # 3. Recovery term (future: when entropy decreases, Phi recovers)

    # 1. Nonlinear Entropy Penalty (Quadratic)
    # Formula: penalty = max(0, (entropy - threshold))^2 * entropy_penalty_k
    # This means:
    # - entropy < 0.5: minimal penalty (soft regulation)
    # - entropy > 0.5: quadratic penalty (harsh regulation)
    entropy_threshold = 0.5  # Below this, penalty is minimal
    if entropy <= entropy_threshold:
        # Low entropy: linear penalty (gentle)
        entropy_penalty = entropy * entropy_penalty_k * 0.5  # 50% reduction for low entropy
    else:
        # High entropy: quadratic penalty (harsh)
        excess_entropy = entropy - entropy_threshold
        entropy_penalty = (entropy_threshold * entropy_penalty_k * 0.5) + (excess_entropy ** 2 * entropy_penalty_k)

    # Clamp entropy factor to [0, 1]
    entropy_factor = max(0.0, min(1.0, 1.0 - entropy_penalty))

    # 2. Calculate raw cognitive resonance
    phi_c_raw = v_eff * stability * entropy_factor

    # 3. Apply Phi Minimum Floor (Resonance Floor)
    # Prevents total collapse unless crisis override
    phi_min_floor = 0.05  # 5% minimum survival energy
    phi_c = max(phi_min_floor, phi_c_raw)  # Never drop below floor

    # 4. Recovery Term (v2.3): If entropy decreases and valence improves, add recovery boost
    # Philosophy: System should recover when conditions improve, not just decay
    if previous_entropy is not None and previous_valence is not None:
        entropy_improved = entropy < previous_entropy  # Entropy decreased (chaos reduced)
        valence_improved = valence > previous_valence  # Valence increased (emotional state improved)

        if entropy_improved or valence_improved:
            # Calculate recovery signal strength
            entropy_recovery = max(0.0, previous_entropy - entropy) if entropy_improved else 0.0
            valence_recovery = max(0.0, valence - previous_valence) if valence_improved else 0.0

            # Combined recovery signal (weighted)
            recovery_signal = (entropy_recovery * 0.6) + (valence_recovery * 0.4)

            # Apply recovery gain (scaled by recovery_gain parameter)
            recovery_boost = recovery_gain * recovery_signal

            # Add recovery to Phi (but don't exceed 1.0)
            phi_c = min(1.0, phi_c + recovery_boost)

            # Ensure we still respect minimum floor
            phi_c = max(phi_min_floor, phi_c)

    # Note: Crisis override (phi = 0.0) should be handled at scenario level, not physics level

    return phi_c


def calculate_phi_physical(amplitude: float, time_delta: float, gamma: float, arousal: float = 1.0) -> float:
    """
    Calculate Physical Resonance (Φ_physical).

    v2.0 (Legacy): Φ_p = A * e^(-γt)
    v2.1 (Circumplex): Φ_p = A_eff * e^(-γt)

    Where A_eff = A * A0
        A = arousal from Circumplex model (0-1)
        A0 = amplitude (emotional intensity slider, 0-10)

    Represents transient response to external stimuli.
    Now includes arousal (activation level) from Circumplex model.

    Args:
        amplitude: Emotional intensity slider (A0), 0-10
        time_delta: Time elapsed (t), seconds
        gamma: Decay rate (γ), default 0.15
        arousal: Arousal from Circumplex model (0-1, default 1.0 for backward compat)

    Returns:
        Physical resonance value (0 to AMPLITUDE_MAX)
    """
    # Clamp inputs to valid ranges
    amplitude = max(AMPLITUDE_MIN, min(AMPLITUDE_MAX, amplitude))
    gamma = max(GAMMA_MIN, min(GAMMA_MAX, gamma))
    arousal = max(0.0, min(1.0, arousal))
    if time_delta < 0:
        time_delta = 0.0

    # v2.1: Effective amplitude = arousal * amplitude
    a_eff = arousal * amplitude

    return a_eff * math.exp(-gamma * time_delta)


def calculate_phi_v2_1(
    valence: float,
    arousal: float,
    amplitude: float,
    time_delta: float,
    gamma: float,
    stability: float,
    entropy: float,
    w_c: float,
    w_p: float,
    entropy_penalty_k: float = 1.15  # Default to micro-calibrated value (15% increase)
) -> dict[str, float]:
    """
    Calculate Total Echo Quality (Φ) using Hybrid Resonance Model (Circumplex-integrated with Base Life Support).

    ⚠️ v2.2 UPDATE: Includes "Base Life Support" fix for Valence Death Trap.
    Negative emotions (stress, pain) now create resonance instead of collapsing Phi.

    Formula: Φ_total = (w_c * Φ_c) + (w_p * Φ_p)

    Where:
        - Φ_c = max{0, (V_eff * Stability) * (1 - Entropy)} (Cognitive Resonance)
        - Φ_p = A_eff * e^(-γt) (Physical Resonance)
        - V_eff = (V + 1) / 2 (normalized valence [-1,+1] -> [0,1])
        - A_eff = A * A0 (arousal * amplitude)
        - w_c, w_p = weights (must sum to 1.0)

    Args:
        valence: Emotional valence from Circumplex model (-1 to +1)
        arousal: Arousal from Circumplex model (0 to 1)
        amplitude: Emotional intensity slider (A0), 0-10
        time_delta: Time elapsed (t), seconds
        gamma: Decay rate (γ), 0.05-0.5
        stability: Internal resilience metric (0-1)
        entropy: Chaos level (0-1)
        w_c: Cognitive weight (0-1)
        w_p: Physical weight (0-1, should satisfy w_c + w_p = 1.0)
        entropy_penalty_k: Entropy penalty coefficient (default 1.0, range [0, 2])

    Returns:
        Dict containing:
            - phi: Total echo quality
            - phi_cognitive: Cognitive component
            - phi_physical: Physical component
            - weight_cognitive: Cognitive weight (wc)
            - weight_physical: Physical weight (wp)

    Example:
        >>> result = calculate_phi_v2_1(
        ...     valence=0.5,
        ...     arousal=0.8,
        ...     amplitude=9.0,
        ...     time_delta=2.0,
        ...     gamma=0.2,
        ...     stability=0.9,
        ...     entropy=0.3,
        ...     w_c=0.6,
        ...     w_p=0.4
        ... )
        >>> assert "phi" in result
    """
    # Validate weights sum to 1.0 (allow small floating point errors)
    weight_sum = w_c + w_p
    if abs(weight_sum - 1.0) > 0.01:
        # Normalize weights
        w_c = w_c / weight_sum
        w_p = w_p / weight_sum

    # Calculate components using v2.1 formulas
    # entropy_penalty_k controls how strongly entropy penalizes cognitive resonance
    phi_c = calculate_phi_cognitive(entropy, stability, valence, entropy_penalty_k)
    phi_p = calculate_phi_physical(amplitude, time_delta, gamma, arousal)

    # Weighted Sum
    phi_total = (w_c * phi_c) + (w_p * phi_p)

    # Clamp phi_total to valid range [PHI_MIN, PHI_MAX] (0-10)
    phi_total = max(PHI_MIN, min(PHI_MAX, phi_total))

    return {
        "phi": phi_total,
        "phi_cognitive": phi_c,
        "phi_physical": phi_p,
        "weight_cognitive": w_c,
        "weight_physical": w_p,
    }


def calculate_phi_v2(
    entropy: float,
    stability: float,
    amplitude: float,
    time_delta: float,
    gamma: float,
    context_mode: str = "DEFAULT",
    valence: float = 0.0,
    arousal: float = 1.0,
    entropy_penalty_k: float = entropy_penalty_k,
) -> dict[str, float]:
    """
    Calculate Total Echo Quality (Φ) using Hybrid Resonance Model v2.0 (backward compatible).

    v2.0 (Legacy): Uses context_mode for weights, no Circumplex integration
    v2.1: Use calculate_phi_v2_1() for Circumplex-integrated version

    Formula: Φ_total = (w_c * Φ_c) + (w_p * Φ_p)

    Where:
        - Φ_c = (1 - Entropy) * Stability (v2.0) or with valence (v2.1 if provided)
        - Φ_p = A * e^(-γt) (v2.0) or with arousal (v2.1 if provided)
        - w_c, w_p = Context-dependent weights (or custom if valence/arousal provided)

    Args:
        entropy: Chaos level (0-1)
        stability: Internal resilience metric (0-1)
        amplitude: Emotional intensity (0-10)
        time_delta: Time elapsed (seconds)
        gamma: Decay rate (default 0.15)
        context_mode: Context mode ("SCHOOL", "GAME", "NPC_ENGINE", "THERAPY", "DEFAULT")
        valence: Optional valence from Circumplex (-1 to +1, default 0.0 for v2.0)
        arousal: Optional arousal from Circumplex (0 to 1, default 1.0 for v2.0)
        entropy_penalty_k: Entropy penalty coefficient (default 1.0, range [0, 2])

    Returns:
        Dict containing:
            - phi: Total echo quality
            - phi_cognitive: Cognitive component
            - phi_physical: Physical component
            - weight_cognitive: Cognitive weight (wc)
            - weight_physical: Physical weight (wp)
            - context: Context mode used

    Example:
        >>> result = calculate_phi_v2(
        ...     entropy=0.2,
        ...     stability=0.9,
        ...     amplitude=1.0,
        ...     time_delta=2.0,
        ...     gamma=1.0,
        ...     context_mode="SCHOOL"
        ... )
        >>> assert "phi" in result
        >>> assert result["weight_cognitive"] == 0.75
    """
    # 1. Get weights
    weights = get_context_weights(context_mode)
    wc, wp = weights["wc"], weights["wp"]

    # 2. Calculate components (use v2.1 if valence/arousal provided)
    phi_c = calculate_phi_cognitive(entropy, stability, valence, entropy_penalty_k)
    phi_p = calculate_phi_physical(amplitude, time_delta, gamma, arousal)

    # 3. Weighted Sum
    phi_total = (wc * phi_c) + (wp * phi_p)

    # 4. Clamp phi_total to valid range [PHI_MIN, PHI_MAX] (0-10)
    phi_total = max(PHI_MIN, min(PHI_MAX, phi_total))

    return {
        "phi": phi_total,
        "phi_cognitive": phi_c,
        "phi_physical": phi_p,
        "weight_cognitive": wc,
        "weight_physical": wp,
        "context": context_mode
    }


def compute_phi_components(params: 'NPCPhysicsParams') -> 'PhiComponents':  # type: ignore
    """
    Compute Φ components for Emotional AI NPC using Plutchik → Circumplex → Φ Physics pipeline.

    This function is specifically designed for NPC emotion-to-physics mapping,
    providing a clean interface for NPC emotional state calculations.

    Formula (v2.2 Circumplex-integrated with Base Life Support):
        - Φ_c = max{0, (V_eff * Stability) * (1 - Entropy * entropy_penalty_k)}
        - Φ_p = A_eff * e^(-γt)
        - Φ_total = (w_cognitive * Φ_c) + (w_physical * Φ_p)

    Where:
        - V_eff = base_resonance + (|V| * (1 - base_resonance)) [v2.2: Base Life Support fix]
        - base_resonance = 0.1 (10% minimum survival energy)
        - |V| = absolute emotional intensity (both positive and negative emotions create resonance)
        - A_eff = A * A0 (arousal * amplitude)

    v2.2 Update: Negative emotions (stress, pain) now create resonance instead of collapsing Phi.

    Args:
        params: NPCPhysicsParams containing all physics parameters

    Returns:
        PhiComponents with phi_cognitive, phi_physical, and phi_total

    Example:
        from phionyx_core.physics.types import NPCPhysicsParams
        from phionyx_core.physics.formulas import compute_phi_components

        params = NPCPhysicsParams(
            valence=0.9,
            arousal=0.7,
            amplitude=7.0,
            gamma=0.43,
            stability=0.86,
            entropy=0.66,
            w_cognitive=0.7,
            w_physical=0.3,
            t=1.0
        )
        result = compute_phi_components(params)
        # Note: This is example code in docstring, not production code
        # logger.debug(f"Φ_total: {result.phi_total}, Φ_c: {result.phi_cognitive}, Φ_p: {result.phi_physical}")
    """
    # Import here to avoid circular dependency
    from .types import NPCPhysicsParams, PhiComponents

    # Validate params type
    if not isinstance(params, NPCPhysicsParams):
        # Try to convert if it's a dict or has attributes
        if isinstance(params, dict):
            params = NPCPhysicsParams(**params)
        else:
            raise TypeError(f"params must be NPCPhysicsParams, got {type(params)}")

    # ⚠️ v2.2 REFACTORED: "Base Life Support" - Valence Death Trap Fix
    # Use same formula as calculate_phi_cognitive() for consistency
    # 1. Absolute Emotional Intensity
    emotional_intensity = abs(params.valence)
    # 2. Base Life Support (minimum resonance floor — uses module-level Tier A constant)
    # 3. Effective Valence: Base + Intensity-scaled contribution
    v_eff = base_resonance + (emotional_intensity * (1.0 - base_resonance))
    v_eff = max(0.0, min(1.0, v_eff))

    # Amplitude adjusted by arousal
    a_eff = params.arousal * params.amplitude
    a_eff = max(AMPLITUDE_MIN, min(AMPLITUDE_MAX, a_eff))

    # Calculate Physical Resonance: Φ_p = A_eff * e^(-γt)
    phi_physical = a_eff * math.exp(-params.gamma * params.t)

    # Calculate Cognitive Resonance: Φ_c = max{phi_min_floor, (V_eff * Stability) * (1 - Nonlinear Entropy Penalty)}
    # Use entropy_penalty_k from params if available, otherwise default to 1.0
    # v2.3: Uses Base Life Support (v2.2) + Nonlinear Entropy Penalty + Phi Minimum Floor
    entropy_penalty_k = getattr(params, 'entropy_penalty_k', 1.0)

    # Nonlinear entropy penalty (quadratic for high entropy, linear for low)
    entropy_threshold = 0.5
    if params.entropy <= entropy_threshold:
        entropy_penalty = params.entropy * entropy_penalty_k * 0.5  # 50% reduction for low entropy
    else:
        excess_entropy = params.entropy - entropy_threshold
        entropy_penalty = (entropy_threshold * entropy_penalty_k * 0.5) + (excess_entropy ** 2 * entropy_penalty_k)

    entropy_factor = max(0.0, min(1.0, 1.0 - entropy_penalty))
    phi_cognitive_raw = v_eff * params.stability * entropy_factor

    # Apply Phi Minimum Floor (5% minimum survival energy)
    phi_min_floor = 0.05
    phi_cognitive = max(phi_min_floor, min(1.0, phi_cognitive_raw))

    # Calculate Total: Φ_total = (w_cognitive * Φ_c) + (w_physical * Φ_p)
    phi_total = (
        params.w_cognitive * phi_cognitive +
        params.w_physical * phi_physical
    )

    # Clamp phi_total to valid range [PHI_MIN, PHI_MAX]
    phi_total = max(PHI_MIN, min(PHI_MAX, phi_total))

    return PhiComponents(
        phi_cognitive=phi_cognitive,
        phi_physical=phi_physical,
        phi_total=phi_total
    )

