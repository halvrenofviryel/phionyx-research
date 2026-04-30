"""
Knowledge Boundary Detector — v4 §6 (AGI Layer 6)
====================================================

Detects when the system is operating outside its knowledge boundary.
Combines OOD score with graph relevance to produce "I don't know" signals.

Key insight: A system that doesn't know what it doesn't know is dangerous.
This module provides the "known unknowns" dimension.

Integrates with:
- meta/uncertainty.py (OOD detection)
- meta/novelty.py (novelty scoring)
- intuition/graph_engine.py (graph relevance)
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
boundary_threshold = 0.4
hedge_threshold = 0.6
weight_ood = 0.4
weight_relevance = 0.35
weight_novelty = 0.25


@dataclass
class BoundaryAssessment:
    """Result of knowledge boundary assessment."""
    within_boundary: bool
    boundary_score: float  # 0.0 = completely outside, 1.0 = fully within
    ood_component: float  # OOD score (0.0 = in-distribution, 1.0 = OOD)
    relevance_component: float  # Graph relevance (0.0 = irrelevant, 1.0 = highly relevant)
    novelty_component: float  # Novelty (0.0 = familiar, 1.0 = novel)
    recommendation: str  # "proceed", "hedge", "admit_ignorance", "refuse"
    reasoning: str


class KnowledgeBoundaryDetector:
    """
    Detect when system is outside its knowledge boundary.

    Combines three signals:
    1. OOD score: How far is this from training distribution?
    2. Graph relevance: How much does the knowledge graph cover this topic?
    3. Novelty: How novel is this compared to seen content?

    Boundary score = weighted combination:
        B = w_ood * (1 - OOD) + w_rel * relevance + w_nov * (1 - novelty)

    Usage:
        detector = KnowledgeBoundaryDetector()
        result = detector.assess(
            ood_score=0.7,
            graph_relevance=0.2,
            novelty_score=0.8
        )
        if not result.within_boundary:
            # System should admit ignorance
    """

    def __init__(
        self,
        boundary_threshold: float = boundary_threshold,
        hedge_threshold: float = hedge_threshold,
        weight_ood: float = weight_ood,
        weight_relevance: float = weight_relevance,
        weight_novelty: float = weight_novelty,
    ):
        """
        Args:
            boundary_threshold: Below this score, system is outside boundary
            hedge_threshold: Between boundary and hedge, system should hedge
            weight_ood: Weight for OOD component
            weight_relevance: Weight for graph relevance
            weight_novelty: Weight for novelty component
        """
        self.boundary_threshold = boundary_threshold
        self.hedge_threshold = hedge_threshold
        self.w_ood = weight_ood
        self.w_rel = weight_relevance
        self.w_nov = weight_novelty

        # Normalize weights
        total = self.w_ood + self.w_rel + self.w_nov
        if total > 0:
            self.w_ood /= total
            self.w_rel /= total
            self.w_nov /= total

    def assess(
        self,
        ood_score: float = 0.0,
        graph_relevance: float = 1.0,
        novelty_score: float = 0.0,
    ) -> BoundaryAssessment:
        """
        Assess whether the system is within its knowledge boundary.

        Args:
            ood_score: Out-of-distribution score (0.0=in-dist, 1.0=OOD)
            graph_relevance: Knowledge graph relevance (0.0=irrelevant, 1.0=covered)
            novelty_score: Novelty score (0.0=familiar, 1.0=completely novel)

        Returns:
            BoundaryAssessment with recommendation
        """
        # Clamp inputs
        ood_score = max(0.0, min(1.0, ood_score))
        graph_relevance = max(0.0, min(1.0, graph_relevance))
        novelty_score = max(0.0, min(1.0, novelty_score))

        # Compute boundary score
        # Higher = more within boundary
        ood_contribution = (1.0 - ood_score) * self.w_ood
        rel_contribution = graph_relevance * self.w_rel
        nov_contribution = (1.0 - novelty_score) * self.w_nov

        boundary_score = ood_contribution + rel_contribution + nov_contribution

        # Determine recommendation
        if boundary_score >= self.hedge_threshold:
            recommendation = "proceed"
            within = True
        elif boundary_score >= self.boundary_threshold:
            recommendation = "hedge"
            within = True  # Technically within but uncertain
        elif boundary_score >= 0.2:
            recommendation = "admit_ignorance"
            within = False
        else:
            recommendation = "refuse"
            within = False

        reasoning = self._build_reasoning(
            boundary_score, ood_score, graph_relevance, novelty_score, recommendation
        )

        return BoundaryAssessment(
            within_boundary=within,
            boundary_score=boundary_score,
            ood_component=ood_score,
            relevance_component=graph_relevance,
            novelty_component=novelty_score,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    def assess_from_text(
        self,
        query_embedding: list[float] | None = None,
        reference_embeddings: list[list[float]] | None = None,
        graph_node_count: int = 0,
        graph_relevant_nodes: int = 0,
    ) -> BoundaryAssessment:
        """
        Assess boundary from raw inputs.

        Args:
            query_embedding: Query embedding vector
            reference_embeddings: Reference distribution embeddings
            graph_node_count: Total nodes in graph
            graph_relevant_nodes: Nodes relevant to query
        """
        # Compute OOD
        ood = 0.5  # default: moderate uncertainty
        if query_embedding and reference_embeddings:
            max_sim = 0.0
            for ref in reference_embeddings:
                sim = _cosine_similarity(query_embedding, ref)
                max_sim = max(max_sim, sim)
            ood = max(0.0, 1.0 - max_sim)

        # Compute graph relevance
        relevance = 0.0
        if graph_node_count > 0:
            relevance = min(1.0, graph_relevant_nodes / max(1, graph_node_count) * 10)

        # Novelty = OOD proxy when no separate novelty data
        novelty = ood

        return self.assess(ood_score=ood, graph_relevance=relevance, novelty_score=novelty)

    def _build_reasoning(
        self,
        score: float,
        ood: float,
        relevance: float,
        novelty: float,
        recommendation: str,
    ) -> str:
        """Build human-readable reasoning."""
        parts = []
        if ood > 0.7:
            parts.append(f"high OOD ({ood:.2f})")
        if relevance < 0.3:
            parts.append(f"low graph coverage ({relevance:.2f})")
        if novelty > 0.7:
            parts.append(f"highly novel ({novelty:.2f})")

        if recommendation == "proceed":
            return f"Within knowledge boundary (score={score:.2f})"
        elif recommendation == "hedge":
            caveats = "; ".join(parts) if parts else "moderate uncertainty"
            return f"Near boundary edge (score={score:.2f}): {caveats}"
        elif recommendation == "admit_ignorance":
            reasons = "; ".join(parts) if parts else "low boundary score"
            return f"Outside knowledge boundary (score={score:.2f}): {reasons}"
        else:
            reasons = "; ".join(parts) if parts else "very low boundary score"
            return f"Far outside knowledge boundary (score={score:.2f}): {reasons}"


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
