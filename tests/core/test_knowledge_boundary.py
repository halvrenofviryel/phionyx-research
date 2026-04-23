"""
Tests for KnowledgeBoundaryDetector — v4 §6 (AGI Layer 6)
=========================================================
"""

import pytest
from phionyx_core.meta.knowledge_boundary import (
    KnowledgeBoundaryDetector,
    BoundaryAssessment,
    _cosine_similarity,
)


# ── Basic Assessment ──


def test_fully_within_boundary():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.0, graph_relevance=1.0, novelty_score=0.0)
    assert result.within_boundary is True
    assert result.boundary_score == pytest.approx(1.0)
    assert result.recommendation == "proceed"


def test_fully_outside_boundary():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=1.0, graph_relevance=0.0, novelty_score=1.0)
    assert result.within_boundary is False
    assert result.boundary_score == pytest.approx(0.0)
    assert result.recommendation == "refuse"


def test_hedge_zone():
    detector = KnowledgeBoundaryDetector()
    # Score should land between 0.4 and 0.6
    result = detector.assess(ood_score=0.4, graph_relevance=0.5, novelty_score=0.4)
    assert result.within_boundary is True
    assert result.recommendation == "hedge"


def test_admit_ignorance_zone():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.8, graph_relevance=0.1, novelty_score=0.8)
    assert result.within_boundary is False
    assert result.recommendation in ("admit_ignorance", "refuse")


# ── Score Components ──


def test_components_stored():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.3, graph_relevance=0.7, novelty_score=0.2)
    assert result.ood_component == pytest.approx(0.3)
    assert result.relevance_component == pytest.approx(0.7)
    assert result.novelty_component == pytest.approx(0.2)


def test_score_formula():
    detector = KnowledgeBoundaryDetector(
        weight_ood=0.4, weight_relevance=0.35, weight_novelty=0.25
    )
    # Weights normalized: 0.4, 0.35, 0.25 (sum=1.0, already normalized)
    result = detector.assess(ood_score=0.5, graph_relevance=0.5, novelty_score=0.5)
    # B = 0.4*(1-0.5) + 0.35*0.5 + 0.25*(1-0.5) = 0.2 + 0.175 + 0.125 = 0.5
    assert result.boundary_score == pytest.approx(0.5)


def test_custom_weights():
    detector = KnowledgeBoundaryDetector(
        weight_ood=1.0, weight_relevance=0.0, weight_novelty=0.0
    )
    result = detector.assess(ood_score=0.3, graph_relevance=0.0, novelty_score=1.0)
    # Only OOD matters: B = 1.0*(1-0.3) = 0.7
    assert result.boundary_score == pytest.approx(0.7)


# ── Thresholds ──


def test_custom_thresholds():
    detector = KnowledgeBoundaryDetector(
        boundary_threshold=0.3, hedge_threshold=0.5
    )
    result = detector.assess(ood_score=0.0, graph_relevance=0.4, novelty_score=0.5)
    assert result.within_boundary is True


def test_boundary_edge():
    detector = KnowledgeBoundaryDetector(
        boundary_threshold=0.5, hedge_threshold=0.7
    )
    # Score exactly at boundary_threshold → hedge
    result = detector.assess(ood_score=0.5, graph_relevance=0.5, novelty_score=0.5)
    assert result.recommendation == "hedge"


# ── Input Clamping ──


def test_clamp_high_values():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=2.0, graph_relevance=5.0, novelty_score=3.0)
    # Should clamp to 1.0 each: B = w*(1-1) + w*1 + w*(1-1) = w_rel
    assert result.ood_component == pytest.approx(1.0)
    assert result.relevance_component == pytest.approx(1.0)
    assert result.novelty_component == pytest.approx(1.0)


def test_clamp_negative_values():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=-1.0, graph_relevance=-1.0, novelty_score=-1.0)
    assert result.ood_component == pytest.approx(0.0)
    assert result.relevance_component == pytest.approx(0.0)
    assert result.novelty_component == pytest.approx(0.0)


# ── assess_from_text() ──


def test_assess_from_text_no_embeddings():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess_from_text(graph_node_count=0, graph_relevant_nodes=0)
    # Default OOD=0.5, relevance=0.0, novelty=0.5
    assert result.ood_component == pytest.approx(0.5)
    assert result.relevance_component == pytest.approx(0.0)


def test_assess_from_text_with_embeddings():
    detector = KnowledgeBoundaryDetector()
    query = [1.0, 0.0, 0.0]
    refs = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]  # first is identical
    result = detector.assess_from_text(
        query_embedding=query,
        reference_embeddings=refs,
        graph_node_count=100,
        graph_relevant_nodes=50,
    )
    # max_sim=1.0, OOD=0.0, relevance=min(1.0, 50/100*10)=1.0
    assert result.ood_component == pytest.approx(0.0)
    assert result.relevance_component == pytest.approx(1.0)
    assert result.within_boundary is True


def test_assess_from_text_orthogonal_embeddings():
    detector = KnowledgeBoundaryDetector()
    query = [1.0, 0.0]
    refs = [[0.0, 1.0]]  # orthogonal → similarity=0
    result = detector.assess_from_text(
        query_embedding=query, reference_embeddings=refs
    )
    # max_sim=0.0, OOD=1.0
    assert result.ood_component == pytest.approx(1.0)


# ── Reasoning ──


def test_reasoning_proceed():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.0, graph_relevance=1.0, novelty_score=0.0)
    assert "Within knowledge boundary" in result.reasoning


def test_reasoning_hedge_with_caveats():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.8, graph_relevance=0.7, novelty_score=0.0)
    assert "Near boundary" in result.reasoning or "Within" in result.reasoning


def test_reasoning_outside_with_reasons():
    detector = KnowledgeBoundaryDetector()
    result = detector.assess(ood_score=0.9, graph_relevance=0.1, novelty_score=0.9)
    assert "Outside" in result.reasoning or "Far outside" in result.reasoning


# ── _cosine_similarity ──


def test_cosine_identical():
    assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)


def test_cosine_orthogonal():
    assert _cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_opposite():
    assert _cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_cosine_empty():
    assert _cosine_similarity([], []) == 0.0


def test_cosine_length_mismatch():
    assert _cosine_similarity([1, 0], [1, 0, 0]) == 0.0


def test_cosine_zero_vector():
    assert _cosine_similarity([0, 0], [1, 0]) == 0.0
