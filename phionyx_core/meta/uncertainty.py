"""
Uncertainty Decomposition — v4 §7
==================================

Epistemic/Aleatoric σ² decomposition using ensemble variance.
Epistemic = reducible with more data (model disagreement).
Aleatoric = irreducible noise (data variance).
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyDecomposition:
    """Result of epistemic/aleatoric decomposition."""
    total_variance: float
    epistemic_variance: float
    aleatoric_variance: float
    dominant_type: str  # "epistemic" or "aleatoric"
    epistemic_ratio: float  # epistemic / total


def decompose_uncertainty(
    ensemble_predictions: list[float],
    ensemble_variances: list[float] | None = None,
) -> UncertaintyDecomposition:
    """
    Decompose total uncertainty into epistemic and aleatoric components.

    Epistemic (model uncertainty):
        σ²_epistemic = Var(mean predictions across ensemble)
        = (1/M) Σ(μ_m - μ̄)²

    Aleatoric (data noise):
        σ²_aleatoric = Mean(per-model variance)
        = (1/M) Σ σ²_m

    Total:
        σ²_total = σ²_epistemic + σ²_aleatoric

    Args:
        ensemble_predictions: Mean predictions from each ensemble member
        ensemble_variances: Per-member variance estimates (optional)

    Returns:
        UncertaintyDecomposition with variance breakdown
    """
    if not ensemble_predictions:
        return UncertaintyDecomposition(
            total_variance=0.0,
            epistemic_variance=0.0,
            aleatoric_variance=0.0,
            dominant_type="epistemic",
            epistemic_ratio=0.5,
        )

    n = len(ensemble_predictions)

    # Epistemic: variance of ensemble means
    mean_pred = sum(ensemble_predictions) / n
    epistemic = sum((p - mean_pred) ** 2 for p in ensemble_predictions) / n

    # Aleatoric: mean of per-member variances
    if ensemble_variances and len(ensemble_variances) == n:
        aleatoric = sum(ensemble_variances) / n
    else:
        # If no per-member variances, estimate from prediction spread
        aleatoric = 0.0

    total = epistemic + aleatoric

    # Determine dominant type
    if total > 0:
        epistemic_ratio = epistemic / total
    else:
        epistemic_ratio = 0.5

    dominant = "epistemic" if epistemic_ratio >= 0.5 else "aleatoric"

    return UncertaintyDecomposition(
        total_variance=total,
        epistemic_variance=epistemic,
        aleatoric_variance=aleatoric,
        dominant_type=dominant,
        epistemic_ratio=epistemic_ratio,
    )


def compute_ece(
    predicted_confidences: list[float],
    actual_outcomes: list[bool],
    n_bins: int = 10,
) -> float:
    """
    Expected Calibration Error (ECE).

    ECE = Σ(|B_m|/N) · |acc(B_m) - conf(B_m)|

    Where B_m are confidence bins, acc is accuracy, conf is mean confidence.

    Args:
        predicted_confidences: Predicted confidence scores (0-1)
        actual_outcomes: Whether prediction was correct (True/False)
        n_bins: Number of calibration bins

    Returns:
        ECE score (0.0 = perfectly calibrated, 1.0 = worst)
    """
    if not predicted_confidences or not actual_outcomes:
        return 0.0

    n = len(predicted_confidences)
    if n != len(actual_outcomes):
        raise ValueError("predicted_confidences and actual_outcomes must have same length")

    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0

    for i in range(n_bins):
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        # Get samples in this bin
        bin_indices = [
            j for j in range(n)
            if low <= predicted_confidences[j] < high
            or (i == n_bins - 1 and predicted_confidences[j] == high)
        ]

        if not bin_indices:
            continue

        bin_size = len(bin_indices)
        bin_acc = sum(1 for j in bin_indices if actual_outcomes[j]) / bin_size
        bin_conf = sum(predicted_confidences[j] for j in bin_indices) / bin_size

        ece += (bin_size / n) * abs(bin_acc - bin_conf)

    return ece


def compute_ood_score(
    embedding: list[float],
    reference_embeddings: list[list[float]],
    threshold: float = 0.5,
) -> float:
    """
    Out-of-Distribution score based on cosine distance from reference set.

    OOD = 1 - max(cosine_similarity with reference set)

    Args:
        embedding: Query embedding vector
        reference_embeddings: Reference distribution embeddings
        threshold: Distance threshold for OOD detection

    Returns:
        OOD score (0.0 = in-distribution, 1.0 = completely OOD)
    """
    if not embedding or not reference_embeddings:
        return 0.5  # Unknown → moderate OOD

    max_sim = 0.0
    for ref in reference_embeddings:
        sim = _cosine_similarity(embedding, ref)
        max_sim = max(max_sim, sim)

    return max(0.0, min(1.0, 1.0 - max_sim))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0

    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)
