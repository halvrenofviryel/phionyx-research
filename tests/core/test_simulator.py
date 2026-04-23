"""
Tests for CausalSimulator — v4 §3 (AGI Layer 3)
=================================================
"""

import pytest
from phionyx_core.causality.causal_graph import CausalGraphBuilder
from phionyx_core.causality.simulator import (
    CausalSimulator,
    SimulationResult,
    SimulationStep,
)


# ── Helpers ──


def _build_physics_graph():
    """Phionyx physics causal graph with known values."""
    b = CausalGraphBuilder()
    echo_state = {
        "phi": 0.7, "entropy": 0.3, "coherence": 0.8,
        "valence": 0.5, "arousal": 0.4, "amplitude": 5.0,
        "resonance": 0.6, "drift": 0.1,
    }
    b.add_physics_variables(echo_state)
    return b.build()


def _build_simple_graph():
    """A(0.5) → B(0.3) → C(0.2)"""
    b = CausalGraphBuilder()
    b.add_node("A", current_value=0.5)
    b.add_node("B", current_value=0.3)
    b.add_node("C", current_value=0.2)
    b.add_causal_link("A", "B", strength=0.8, confidence=1.0)
    b.add_causal_link("B", "C", strength=0.6, confidence=1.0)
    return b.build()


# ── Single Step ──


def test_simulate_step_basic():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_step({"A": 1.0})
    assert len(result.steps) == 1
    assert result.steps[0].interventions == {"A": 1.0}
    assert result.total_variables_affected >= 1


def test_simulate_step_final_state():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_step({"A": 1.0})
    assert result.final_state["A"] == 1.0
    assert result.get_final_value("A") == 1.0


def test_simulate_step_delta():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_step({"A": 1.0})
    # A delta = 0.5 (1.0 - 0.5)
    delta_a = result.get_total_delta("A")
    assert delta_a == pytest.approx(0.5)


def test_simulate_step_no_change():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph)
    result = sim.simulate_step({"A": 0.5})  # Same value
    assert result.total_variables_affected == 0


# ── Multi-step Sequence ──


def test_simulate_sequence():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_sequence([
        {"A": 0.8},   # Step 1
        {"A": 1.0},   # Step 2
    ])
    assert len(result.steps) == 2
    assert result.steps[0].step_index == 0
    assert result.steps[1].step_index == 1


def test_sequence_builds_on_previous():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_sequence([
        {"A": 0.8},
        {"A": 1.0},
    ])
    # Final state should reflect cumulative effects
    assert result.final_state["A"] == 1.0


def test_sequence_empty():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph)
    result = sim.simulate_sequence([])
    assert len(result.steps) == 0
    assert result.total_variables_affected == 0


# ── Risk Assessment ──


def test_risk_safe():
    graph = _build_physics_graph()
    sim = CausalSimulator(graph, risk_thresholds={
        "entropy": (0.0, 0.8),
        "drift": (0.0, 0.3),
    })
    result = sim.simulate_step({"phi": 0.75})  # Minor change
    assert result.risk_assessment["safe"] is True
    assert result.risk_assessment["risk_score"] == pytest.approx(0.0)


def test_risk_violation():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, risk_thresholds={
        "A": (0.0, 0.6),
    })
    result = sim.simulate_step({"A": 0.9})  # Exceeds max 0.6
    assert result.risk_assessment["safe"] is False
    assert len(result.risk_assessment["violations"]) >= 1


def test_risk_severity_high():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, risk_thresholds={
        "A": (0.0, 0.5),
    })
    result = sim.simulate_step({"A": 0.9})  # 0.9 > 0.5 + 0.2
    violations = result.risk_assessment["violations"]
    high_severity = [v for v in violations if v["severity"] == "high"]
    assert len(high_severity) >= 1


# ── Preview Risk ──


def test_preview_risk():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, risk_thresholds={"A": (0.0, 0.6)})
    risk = sim.preview_risk({"A": 0.9})
    assert risk["safe"] is False


def test_preview_risk_safe():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, risk_thresholds={"A": (0.0, 1.0)})
    risk = sim.preview_risk({"A": 0.5})
    assert risk["safe"] is True


# ── Compare Actions ──


def test_compare_actions():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0, risk_thresholds={
        "A": (0.0, 0.8),
    })
    comparison = sim.compare_actions(
        action_a={"A": 0.7},
        action_b={"A": 0.9},
    )
    assert "action_a" in comparison
    assert "action_b" in comparison
    assert "recommendation" in comparison
    # action_a is safer (0.7 < 0.8 threshold)
    assert comparison["recommendation"] == "action_a"


def test_compare_actions_differences():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    comparison = sim.compare_actions(
        action_a={"A": 0.6},
        action_b={"A": 0.9},
    )
    assert len(comparison["differences"]) >= 1


# ── Physics Simulation ──


def test_physics_entropy_simulation():
    graph = _build_physics_graph()
    sim = CausalSimulator(graph, attenuation_rate=0.9)
    result = sim.simulate_step({"entropy": 0.9})
    # Entropy increase should affect coherence and drift
    assert "entropy" in result.final_state
    assert result.final_state["entropy"] == 0.9


def test_physics_risk_high_entropy():
    graph = _build_physics_graph()
    sim = CausalSimulator(graph, risk_thresholds={
        "entropy": (0.0, 0.8),
        "drift": (0.0, 0.3),
    })
    risk = sim.preview_risk({"entropy": 0.95})
    # 0.95 > 0.8 threshold
    assert risk["safe"] is False


# ── Serialization ──


def test_to_dict():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_step({"A": 1.0})
    d = result.to_dict()
    assert isinstance(d["steps"], list)
    assert "initial_state" in d
    assert "final_state" in d
    assert "risk" in d


# ── Initial State Preserved ──


def test_initial_state_captured():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph)
    result = sim.simulate_step({"A": 1.0})
    assert result.initial_state["A"] == 0.5  # Original value


# ── Step Delta Summary ──


def test_step_delta_summary():
    graph = _build_simple_graph()
    sim = CausalSimulator(graph, attenuation_rate=1.0)
    result = sim.simulate_step({"A": 1.0})
    step = result.steps[0]
    assert "A" in step.delta_summary
    assert step.delta_summary["A"] == pytest.approx(0.5)
