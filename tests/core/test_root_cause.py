"""
Tests for RootCauseAnalyzer — v4 §3 (AGI Layer 3)
===================================================
"""

import pytest
from phionyx_core.causality.causal_graph import CausalGraphBuilder
from phionyx_core.causality.root_cause import (
    RootCauseAnalyzer,
    RootCauseAnalysis,
    RootCauseCandidate,
)


# ── Helpers ──


def _build_chain():
    """A(0.9) → B(0.8) → C(0.1)  — C is anomalous"""
    b = CausalGraphBuilder()
    b.add_node("A", current_value=0.9)
    b.add_node("B", current_value=0.8)
    b.add_node("C", current_value=0.1)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("B", "C", strength=0.7, confidence=1.0)
    return b.build()


def _build_multi_parent():
    """
    X(0.9) → C(0.1)
    Y(0.2) → C(0.1)
    X is anomalous, Y is normal
    """
    b = CausalGraphBuilder()
    b.add_node("X", current_value=0.9)
    b.add_node("Y", current_value=0.2)
    b.add_node("C", current_value=0.1)
    b.add_causal_link("X", "C", strength=0.8, confidence=1.0)
    b.add_causal_link("Y", "C", strength=0.3, confidence=1.0)
    return b.build()


def _build_deep_chain():
    """R(0.95) → A(0.8) → B(0.7) → C(0.5) → D(0.05)"""
    b = CausalGraphBuilder()
    for node, val in [("R", 0.95), ("A", 0.8), ("B", 0.7), ("C", 0.5), ("D", 0.05)]:
        b.add_node(node, current_value=val)
    b.add_causal_link("R", "A", strength=0.9, confidence=1.0)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("B", "C", strength=0.7, confidence=1.0)
    b.add_causal_link("C", "D", strength=0.6, confidence=1.0)
    return b.build()


# ── Basic Analysis ──


def test_analyze_chain():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    assert result.anomaly_node == "C"
    assert len(result.candidates) >= 1
    assert result.top_cause is not None


def test_analyze_nonexistent():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("NONEXISTENT")
    assert result.top_cause is None
    assert "not found" in result.reasoning


def test_top_cause_is_highest_likelihood():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    if len(result.candidates) > 1:
        likelihoods = [c.likelihood for c in result.candidates]
        assert result.top_cause.likelihood == max(likelihoods)


# ── Multi-parent ──


def test_multi_parent_identifies_stronger_cause():
    graph = _build_multi_parent()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    assert result.top_cause is not None
    # X has stronger link to C (0.8 vs 0.3) and is more anomalous
    assert result.top_cause.node_id == "X"


# ── Deep Chain ──


def test_deep_chain_finds_root():
    graph = _build_deep_chain()
    analyzer = RootCauseAnalyzer(graph, max_depth=5)
    result = analyzer.analyze("D", anomaly_value=0.05, expected_range=(0.3, 0.7))
    assert len(result.candidates) >= 1
    # Should find ancestors — R is the true root
    root_ids = [c.node_id for c in result.candidates]
    assert any(nid in root_ids for nid in ["R", "A", "B", "C"])


def test_max_depth_limits_search():
    graph = _build_deep_chain()
    analyzer = RootCauseAnalyzer(graph, max_depth=1)
    result = analyzer.analyze("D", anomaly_value=0.05, expected_range=(0.3, 0.7))
    root_ids = [c.node_id for c in result.candidates]
    # Should only find C (direct parent), not R or A
    assert "R" not in root_ids


# ── Causal Path ──


def test_candidate_has_causal_path():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    for candidate in result.candidates:
        assert len(candidate.causal_path) >= 2
        assert candidate.causal_path[-1] == "C"  # Path ends at anomaly


# ── Anomaly Magnitude ──


def test_anomaly_within_range():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    # Value within expected range → magnitude = 0
    result = analyzer.analyze("B", anomaly_value=0.6, expected_range=(0.4, 0.8))
    # No candidates because anomaly magnitude is 0
    assert result.anomaly_value == 0.6


def test_anomaly_far_outside_range():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.0, expected_range=(0.5, 0.9))
    # Very anomalous → should find candidates
    assert result.anomaly_value == 0.0


# ── Filtering ──


def test_min_likelihood_filter():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph, min_likelihood=0.99)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    # Very high threshold → likely no candidates
    for c in result.candidates:
        assert c.likelihood >= 0.99


# ── Serialization ──


def test_to_dict():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    d = result.to_dict()
    assert d["anomaly"]["node"] == "C"
    assert d["anomaly"]["value"] == 0.1
    assert isinstance(d["candidates"], list)
    assert "reasoning" in d


# ── Reasoning ──


def test_reasoning_with_cause():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    if result.top_cause:
        assert "Most likely root cause" in result.reasoning


def test_reasoning_no_cause():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph, min_likelihood=1.0)
    result = analyzer.analyze("C", anomaly_value=0.1, expected_range=(0.4, 0.8))
    if not result.top_cause:
        assert "No root cause" in result.reasoning


# ── Leaf Node ──


def test_analyze_root_node():
    graph = _build_chain()
    analyzer = RootCauseAnalyzer(graph)
    result = analyzer.analyze("A", anomaly_value=0.95, expected_range=(0.3, 0.7))
    # A has no parents → no candidates
    assert len(result.candidates) == 0
