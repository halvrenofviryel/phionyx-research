"""
Arbitration Math — v4 §7 Formulas
===================================

Implements 6 core arbitration formulas:
1. W_final (Confidence Fusion)
2. Arbitration Conflict Score (Herfindahl)
3. Goal Legitimacy L(g)
4. Goal Utility U(g)
5. T_meta (Meta-cognitive Trust)
6. Recency Decay d_i

All functions are pure mathematical — no side effects.
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ArbitrationResult:
    """Result of confidence fusion / arbitration."""
    w_final: float
    conflict_score: float
    module_weights: dict[str, float]
    dominant_module: str
    is_conflicted: bool  # conflict_score > threshold


def compute_w_final(
    module_confidences: dict[str, float],
    recency_weights: dict[str, float] | None = None,
    alpha: float = 1.0,
) -> ArbitrationResult:
    """
    Confidence Fusion: W_final = Σ(w_i * c_i) / Σ(w_i)

    Each module provides a confidence score. Optional recency weights
    bias toward more recent assessments.

    Args:
        module_confidences: {module_name: confidence_score}
        recency_weights: {module_name: recency_weight} (default: uniform)
        alpha: Sharpening exponent (1.0 = linear, >1 = sharpen dominant)

    Returns:
        ArbitrationResult with fused confidence and conflict metrics
    """
    if not module_confidences:
        return ArbitrationResult(
            w_final=0.5,
            conflict_score=0.0,
            module_weights={},
            dominant_module="none",
            is_conflicted=False,
        )

    # Default: uniform recency weights
    if recency_weights is None:
        recency_weights = dict.fromkeys(module_confidences, 1.0)

    # Compute weighted fusion
    weighted_sum = 0.0
    weight_total = 0.0
    for module, confidence in module_confidences.items():
        w = recency_weights.get(module, 1.0)
        # Apply sharpening
        w_sharp = w ** alpha
        weighted_sum += w_sharp * confidence
        weight_total += w_sharp

    w_final = weighted_sum / weight_total if weight_total > 0 else 0.5

    # Compute conflict score (Herfindahl-based)
    conflict = compute_conflict_score(list(module_confidences.values()))

    # Find dominant module
    dominant = max(module_confidences, key=lambda k: module_confidences[k])

    return ArbitrationResult(
        w_final=max(0.0, min(1.0, w_final)),
        conflict_score=conflict,
        module_weights=recency_weights,
        dominant_module=dominant,
        is_conflicted=conflict > 0.5,
    )


def compute_conflict_score(confidences: list[float]) -> float:
    """
    Arbitration Conflict Score using Herfindahl index.

    conflict = 1 - HHI, where HHI = Σ(s_i²), s_i = c_i / Σ(c_j)

    High conflict (near 1.0) means modules disagree strongly.
    Low conflict (near 0.0) means one module dominates.

    Args:
        confidences: List of confidence scores from different modules

    Returns:
        Conflict score (0.0 to 1.0)
    """
    if not confidences or len(confidences) < 2:
        return 0.0

    total = sum(abs(c) for c in confidences)
    if total == 0:
        return 0.0

    # Normalized shares
    shares = [abs(c) / total for c in confidences]

    # Herfindahl-Hirschman Index
    hhi = sum(s * s for s in shares)

    # Conflict = 1 - HHI (higher = more disagreement)
    return max(0.0, min(1.0, 1.0 - hhi))


def compute_goal_legitimacy(
    safety_score: float,
    system_score: float,
    user_score: float,
    alpha: float = 0.5,
    beta: float = 0.3,
    gamma: float = 0.2,
) -> float:
    """
    Goal Legitimacy: L(g) = α·safety + β·system + γ·user

    Safety-weighted legitimacy scoring for goal evaluation.

    Args:
        safety_score: Safety alignment (0-1)
        system_score: System alignment (0-1)
        user_score: User alignment (0-1)
        alpha, beta, gamma: Weight coefficients (should sum to 1.0)

    Returns:
        Legitimacy score (0.0 to 1.0)
    """
    legitimacy = alpha * safety_score + beta * system_score + gamma * user_score
    return max(0.0, min(1.0, legitimacy))


def compute_goal_utility(
    legitimacy: float,
    expected_value: float,
    conflict_penalty: float = 0.0,
) -> float:
    """
    Goal Utility: U(g) = L(g) · EV - conflict_penalty

    Args:
        legitimacy: Goal legitimacy L(g)
        expected_value: Expected value of achieving the goal
        conflict_penalty: Penalty for conflicting with other goals

    Returns:
        Goal utility score
    """
    return legitimacy * expected_value - conflict_penalty


def compute_t_meta(
    ece: float,
    ood_score: float,
    self_report_delta: float,
) -> float:
    """
    Meta-cognitive Trust: T_meta = (1 - ECE) · (1 - OOD) · (1 - |self_report_delta|)

    Measures how trustworthy the system's self-assessment is.

    Args:
        ece: Expected Calibration Error (0-1, lower is better)
        ood_score: Out-of-Distribution score (0-1, lower is better)
        self_report_delta: |self_eval - external_eval| / external (0-1)

    Returns:
        T_meta trust score (0.0 to 1.0)
    """
    t_meta = (1.0 - ece) * (1.0 - ood_score) * (1.0 - abs(self_report_delta))
    return max(0.0, min(1.0, t_meta))


def compute_recency_decay(
    time_elapsed: float,
    decay_rate: float = 0.1,
) -> float:
    """
    Recency Decay: d_i = exp(-0.1 · (t - t_i))

    Compatible with SemanticTimeDecay from physics/semantic_time_decay.py.

    Args:
        time_elapsed: Time since event (seconds)
        decay_rate: Decay rate (default 0.1 per second)

    Returns:
        Decay factor (0.0 to 1.0)
    """
    return math.exp(-decay_rate * time_elapsed)


def compute_recency_weights(
    timestamps: dict[str, float],
    current_time: float,
    decay_rate: float = 0.1,
) -> dict[str, float]:
    """
    Compute recency weights for multiple modules.

    Args:
        timestamps: {module_name: last_update_timestamp}
        current_time: Current timestamp
        decay_rate: Decay rate

    Returns:
        {module_name: recency_weight}
    """
    return {
        module: compute_recency_decay(current_time - t, decay_rate)
        for module, t in timestamps.items()
    }
