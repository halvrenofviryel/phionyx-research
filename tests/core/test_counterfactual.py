"""
Tests for CounterfactualEngine — v4 §3 (AGI Layer 3)
======================================================
"""

import pytest
from phionyx_core.causality.causal_graph import CausalGraphBuilder, NodeType, MechanismType
from phionyx_core.causality.counterfactual import (
    CounterfactualEngine,
    CounterfactualResult,
    CounterfactualQuery,
    CounterfactualOutcome,
)


# ── Helpers ──


def _build_chain():
    """A(0.5) → B(0.3) → C(0.2)"""
    b = CausalGraphBuilder()
    b.add_node("A", current_value=0.5)
    b.add_node("B", current_value=0.3)
    b.add_node("C", current_value=0.2)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("B", "C", strength=0.6, confidence=1.0)
    return b.build()


def _build_diamond():
    """A → B → D, A → C → D"""
    b = CausalGraphBuilder()
    b.add_node("A", current_value=1.0)
    b.add_node("B", current_value=0.5)
    b.add_node("C", current_value=0.5)
    b.add_node("D", current_value=0.3)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("A", "C", strength=0.6, confidence=1.0)
    b.add_causal_link("B", "D", strength=0.7, confidence=1.0)
    b.add_causal_link("C", "D", strength=0.5, confidence=1.0)
    return b.build()


# ── what_if ──


def test_what_if_basic():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)

    assert result.query.variable == "A"
    assert result.query.counterfactual_value == 1.0
    assert len(result.outcomes) >= 1


def test_what_if_returns_factual_state():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    result = engine.what_if("A", 1.0)
    assert result.factual_state["A"] == 0.5
    assert result.factual_state["B"] == 0.3


def test_what_if_outcome_delta():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)  # delta = 0.5

    b_outcome = result.get_outcome("B")
    assert b_outcome is not None
    assert b_outcome.delta == pytest.approx(0.4)  # 0.5 * 0.8
    assert b_outcome.factual_value == 0.3
    assert b_outcome.counterfactual_value == pytest.approx(0.7)


def test_what_if_nonexistent():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    result = engine.what_if("NONEXISTENT", 1.0)
    assert len(result.outcomes) == 0
    assert "not found" in result.reasoning


def test_what_if_no_change():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    result = engine.what_if("A", 0.5)  # Same as current
    assert len(result.outcomes) == 0


def test_what_if_with_targets():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0, targets=["C"])
    # Should only return outcome for C
    assert all(o.variable == "C" for o in result.outcomes)


def test_what_if_diamond():
    graph = _build_diamond()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 2.0)
    # Should affect B, C, and D
    affected = {o.variable for o in result.outcomes}
    assert "B" in affected
    assert "C" in affected


# ── Necessity & Sufficiency ──


def test_necessity_direct_cause():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    score = engine.necessity("A", "B")
    assert score > 0.5  # A is the sole parent of B → high necessity


def test_necessity_no_relationship():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    score = engine.necessity("C", "A")  # C doesn't cause A
    assert score == pytest.approx(0.0)


def test_necessity_nonexistent():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    assert engine.necessity("X", "Y") == pytest.approx(0.0)


def test_sufficiency():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    score = engine.sufficiency("A", "B")
    assert score == pytest.approx(0.8)  # Direct edge strength


def test_sufficiency_no_path():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    assert engine.sufficiency("C", "A") == pytest.approx(0.0)


# ── Max Impact Variable ──


def test_max_impact_variable():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)
    # B has larger delta than C
    assert result.max_impact_variable == "B"


def test_max_impact_empty():
    graph = _build_chain()
    engine = CounterfactualEngine(graph)
    result = engine.what_if("A", 0.5)  # no change
    assert result.max_impact_variable is None


# ── Serialization ──


def test_to_dict():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)
    d = result.to_dict()
    assert d["query"]["variable"] == "A"
    assert isinstance(d["outcomes"], list)
    assert "reasoning" in d


# ── Reasoning ──


def test_reasoning_has_content():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)
    assert "entropy" not in result.reasoning or len(result.reasoning) > 0
    assert result.reasoning != ""


# ── Causal Path ──


def test_outcome_causal_path():
    graph = _build_chain()
    engine = CounterfactualEngine(graph, attenuation_rate=1.0)
    result = engine.what_if("A", 1.0)
    b_outcome = result.get_outcome("B")
    assert b_outcome is not None
    assert b_outcome.causal_path == ["A", "B"]
