"""
Tests for InterventionModel — v4 §3 (AGI Layer 3)
===================================================
"""

import pytest
from phionyx_core.causality.causal_graph import (
    CausalGraphBuilder,
    CausalGraph,
    CausalNode,
    CausalEdge,
    NodeType,
    MechanismType,
)
from phionyx_core.causality.intervention import (
    InterventionModel,
    InterventionResult,
    InterventionEffect,
)


# ── Helpers ──


def _build_chain_graph():
    """A → B → C with known values."""
    b = CausalGraphBuilder()
    b.add_node("A", current_value=0.5)
    b.add_node("B", current_value=0.3)
    b.add_node("C", current_value=0.2)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("B", "C", strength=0.6, confidence=1.0)
    return b.build()


def _build_diamond_graph():
    """
    A → B → D
    A → C → D
    """
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


def _build_physics_graph():
    """Phionyx physics causal graph."""
    b = CausalGraphBuilder()
    echo_state = {
        "phi": 0.7, "entropy": 0.3, "coherence": 0.8,
        "valence": 0.5, "arousal": 0.4, "amplitude": 5.0,
        "resonance": 0.6, "drift": 0.1,
    }
    b.add_physics_variables(echo_state)
    return b.build()


# ── Basic Intervention ──


def test_do_nonexistent_variable():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    result = model.do("nonexistent", 1.0)
    assert result.total_nodes_affected == 0
    assert result.effects == []


def test_do_no_delta():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    result = model.do("A", 0.5)  # Same as current value
    assert result.total_nodes_affected == 0


def test_do_chain_propagation():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)  # No attenuation
    result = model.do("A", 1.0)  # delta = 0.5

    assert result.intervention_variable == "A"
    assert result.intervention_value == 1.0
    assert result.original_value == 0.5
    assert result.total_nodes_affected >= 1  # At least B

    # B should be affected: delta_B = 0.5 * 0.8 * 1.0 = 0.4
    b_effect = result.get_effect("B")
    assert b_effect is not None
    assert b_effect.delta == pytest.approx(0.4)
    assert b_effect.new_value == pytest.approx(0.7)  # 0.3 + 0.4


def test_do_chain_with_attenuation():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=0.5)
    result = model.do("A", 1.0)  # delta = 0.5

    b_effect = result.get_effect("B")
    assert b_effect is not None
    # delta_B = 0.5 * 0.8 * 0.5 = 0.2
    assert b_effect.delta == pytest.approx(0.2)

    c_effect = result.get_effect("C")
    if c_effect:
        # delta_C = 0.2 * 0.6 * 0.5 = 0.06
        assert c_effect.delta == pytest.approx(0.06)


def test_do_diamond_multiple_paths():
    graph = _build_diamond_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 2.0)  # delta = 1.0

    assert result.total_nodes_affected >= 2  # At least B and C
    b_effect = result.get_effect("B")
    c_effect = result.get_effect("C")
    assert b_effect is not None
    assert c_effect is not None


def test_intervention_result_affected_ids():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 1.0)
    assert "B" in result.affected_node_ids


def test_max_propagation_depth():
    # Build long chain: A → B → C → D → E → F
    b = CausalGraphBuilder()
    for node in "ABCDEF":
        b.add_node(node, current_value=0.5)
    for i in range(5):
        b.add_causal_link("ABCDEF"[i], "ABCDEF"[i + 1], strength=0.9, confidence=1.0)
    graph = b.build()

    model = InterventionModel(graph, attenuation_rate=1.0, max_propagation_depth=2)
    result = model.do("A", 1.0)
    # Should only propagate 2 hops: B and C
    affected = result.affected_node_ids
    assert "B" in affected
    assert "C" in affected
    assert "D" not in affected


def test_min_effect_threshold():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=0.1, min_effect_threshold=0.05)
    result = model.do("A", 0.6)  # delta = 0.1
    # B: 0.1 * 0.8 * 0.1 = 0.008 — below threshold
    # With attenuation 0.1, effects die fast
    # Actually let's think: delta_B = 0.1 * 0.8 * 0.1 = 0.008 < 0.05
    # So nothing should be affected
    assert result.total_nodes_affected == 0


# ── Causal Path Tracking ──


def test_causal_path_recorded():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 1.0)
    b_effect = result.get_effect("B")
    assert b_effect is not None
    assert b_effect.causal_path == ["A", "B"]

    c_effect = result.get_effect("C")
    if c_effect:
        assert c_effect.causal_path == ["A", "B", "C"]


# ── Snapshot ──


def test_graph_snapshot():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 1.0)
    snap = result.graph_snapshot
    assert snap["A"] == 1.0  # Intervention value
    assert "B" in snap
    assert "C" in snap


# ── Estimate Total Effect ──


def test_estimate_total_effect_direct():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    effect = model.estimate_total_effect("A", "B")
    # Direct: 0.8 * 1.0 = 0.8
    assert effect == pytest.approx(0.8)


def test_estimate_total_effect_indirect():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=0.8)
    effect = model.estimate_total_effect("A", "C")
    # Path A→B→C: 0.8 * 0.6 * 0.8^1 = 0.384
    assert effect == pytest.approx(0.384)


def test_estimate_total_effect_no_path():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    effect = model.estimate_total_effect("C", "A")  # Reverse — no path
    assert effect == pytest.approx(0.0)


def test_estimate_total_effect_nonexistent():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    assert model.estimate_total_effect("X", "Y") == pytest.approx(0.0)


def test_estimate_total_effect_diamond():
    graph = _build_diamond_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    effect = model.estimate_total_effect("A", "D")
    # Path A→B→D: 0.8 * 0.7 = 0.56
    # Path A→C→D: 0.6 * 0.5 = 0.30
    # Total = 0.86
    assert effect == pytest.approx(0.86)


# ── Confounders ──


def test_identify_confounders():
    # X → A, X → B, so X confounds A-B relationship
    b = CausalGraphBuilder()
    b.add_node("X")
    b.add_node("A")
    b.add_node("B")
    b.add_causal_link("X", "A")
    b.add_causal_link("X", "B")
    graph = b.build()
    model = InterventionModel(graph)
    confounders = model.identify_confounders("A", "B")
    assert "X" in confounders


def test_no_confounders():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    confounders = model.identify_confounders("A", "B")
    assert confounders == []  # A has no ancestors


def test_confounders_nonexistent():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    assert model.identify_confounders("X", "Y") == []


# ── Multiple Interventions ──


def test_simulate_multiple():
    graph = _build_diamond_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    results = model.simulate_multiple({"A": 2.0, "B": 1.0})
    assert "A" in results
    assert "B" in results
    assert results["A"].intervention_value == 2.0
    assert results["B"].intervention_value == 1.0


# ── Serialization ──


def test_to_dict():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 1.0)
    d = result.to_dict()
    assert d["intervention"]["variable"] == "A"
    assert d["intervention"]["value"] == 1.0
    assert d["total_affected"] >= 1
    assert isinstance(d["effects"], list)


# ── Physics Graph Intervention ──


def test_physics_entropy_intervention():
    graph = _build_physics_graph()
    model = InterventionModel(graph, attenuation_rate=0.9)
    result = model.do("entropy", 0.9)  # Force high entropy
    # entropy→coherence should be affected
    coh_effect = result.get_effect("coherence")
    if coh_effect:
        assert coh_effect.delta != 0  # Some effect


def test_physics_arousal_chain():
    graph = _build_physics_graph()
    model = InterventionModel(graph, attenuation_rate=0.9)
    # arousal→entropy→coherence→drift
    effect = model.estimate_total_effect("arousal", "drift")
    # Should have some non-zero effect through the chain
    assert effect > 0


# ── Edge Cases ──


def test_intervention_on_leaf_node():
    graph = _build_chain_graph()
    model = InterventionModel(graph)
    result = model.do("C", 1.0)  # Leaf node — no children
    assert result.total_nodes_affected == 0


def test_intervention_on_root_node():
    graph = _build_chain_graph()
    model = InterventionModel(graph, attenuation_rate=1.0)
    result = model.do("A", 1.0)
    assert result.total_nodes_affected >= 1
