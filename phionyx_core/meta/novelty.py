"""
Novelty & Transfer Scoring — v4 §7
=====================================

Novelty Score = 1 - max(cosine_sim) with existing knowledge.
Transfer Potential = avg(relevance across domains).
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NoveltyResult:
    """Result of novelty assessment."""
    novelty_score: float       # 0=familiar, 1=completely novel
    max_similarity: float      # Highest similarity found
    closest_item_id: str | None
    is_novel: bool             # novelty > threshold


@dataclass
class TransferResult:
    """Result of transfer potential assessment."""
    transfer_potential: float  # 0=no transfer, 1=universal
    domain_scores: dict[str, float]
    best_domain: str
    worst_domain: str


def compute_novelty_score(
    candidate_embedding: list[float],
    existing_embeddings: list[list[float]],
    existing_ids: list[str] | None = None,
    threshold: float = 0.7,
) -> NoveltyResult:
    """
    Novelty Score = 1 - max(cosine_similarity).

    Args:
        candidate_embedding: Embedding of discovery candidate
        existing_embeddings: Embeddings of existing knowledge
        existing_ids: Optional IDs for existing items
        threshold: Novelty threshold (score > threshold = novel)

    Returns:
        NoveltyResult
    """
    if not candidate_embedding or not existing_embeddings:
        return NoveltyResult(
            novelty_score=1.0,
            max_similarity=0.0,
            closest_item_id=None,
            is_novel=True,
        )

    max_sim = 0.0
    closest_idx = 0

    for i, ref in enumerate(existing_embeddings):
        sim = _cosine_similarity(candidate_embedding, ref)
        if sim > max_sim:
            max_sim = sim
            closest_idx = i

    novelty = 1.0 - max_sim
    closest_id = existing_ids[closest_idx] if existing_ids and closest_idx < len(existing_ids) else None

    return NoveltyResult(
        novelty_score=max(0.0, min(1.0, novelty)),
        max_similarity=max_sim,
        closest_item_id=closest_id,
        is_novel=novelty > threshold,
    )


def compute_transfer_potential(
    candidate_embedding: list[float],
    domain_embeddings: dict[str, list[list[float]]],
) -> TransferResult:
    """
    Transfer Potential = avg(relevance across domains).

    For each domain, compute average cosine similarity with
    domain exemplars. Transfer potential is the mean across domains.

    Args:
        candidate_embedding: Embedding of discovery candidate
        domain_embeddings: {domain_name: [exemplar_embeddings]}

    Returns:
        TransferResult
    """
    if not candidate_embedding or not domain_embeddings:
        return TransferResult(
            transfer_potential=0.0,
            domain_scores={},
            best_domain="none",
            worst_domain="none",
        )

    domain_scores = {}
    for domain, exemplars in domain_embeddings.items():
        if not exemplars:
            domain_scores[domain] = 0.0
            continue
        sims = [_cosine_similarity(candidate_embedding, ex) for ex in exemplars]
        domain_scores[domain] = sum(sims) / len(sims)

    if not domain_scores:
        return TransferResult(
            transfer_potential=0.0,
            domain_scores={},
            best_domain="none",
            worst_domain="none",
        )

    transfer = sum(domain_scores.values()) / len(domain_scores)
    best = max(domain_scores, key=domain_scores.get)
    worst = min(domain_scores, key=domain_scores.get)

    return TransferResult(
        transfer_potential=max(0.0, min(1.0, transfer)),
        domain_scores=domain_scores,
        best_domain=best,
        worst_domain=worst,
    )


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
