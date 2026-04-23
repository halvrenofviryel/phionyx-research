"""
Tests for CausalGraphBuilder — v4 §3 (AGI Layer 3)
====================================================
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


# ── Node Operations ──


def test_add_node():
    b = CausalGraphBuilder()
    node = b.add_node("entropy", name="Entropy", node_type=NodeType.STATE.value, current_value=0.5)
    assert node.node_id == "entropy"
    assert node.name == "Entropy"
    assert node.current_value == 0.5


def test_add_node_default_name():
    b = CausalGraphBuilder()
    node = b.add_node("phi")
    assert node.name == "phi"


def test_add_duplicate_node_updates_value():
    b = CausalGraphBuilder()
    b.add_node("x", current_value=0.3)
    b.add_node("x", current_value=0.7)
    graph = b.build()
    assert graph.nodes["x"].current_value == 0.7
    assert graph.nodes["x"].observed_values == [0.3, 0.7]


def test_max_nodes_limit():
    b = CausalGraphBuilder(max_nodes=3)
    b.add_node("a")
    b.add_node("b")
    b.add_node("c")
    b.add_node("d")  # Should be ignored
    assert b.build().node_count == 3


def test_node_mean_value():
    b = CausalGraphBuilder()
    b.add_node("x", current_value=0.2)
    b.add_node("x", current_value=0.4)
    b.add_node("x", current_value=0.6)
    node = b.build().nodes["x"]
    assert node.mean_value == pytest.approx(0.4)


def test_node_mean_value_no_observations():
    node = CausalNode(node_id="x", name="x", current_value=0.5)
    assert node.mean_value == 0.5  # Falls back to current_value


# ── Edge Operations ──


def test_add_causal_link():
    b = CausalGraphBuilder()
    b.add_node("a")
    b.add_node("b")
    edge = b.add_causal_link("a", "b", strength=0.8, confidence=0.9)
    assert edge is not None
    assert edge.strength == pytest.approx(0.8)
    assert edge.effective_strength == pytest.approx(0.72)  # 0.8 * 0.9


def test_add_causal_link_auto_creates_nodes():
    b = CausalGraphBuilder()
    edge = b.add_causal_link("x", "y", strength=0.5)
    assert edge is not None
    graph = b.build()
    assert "x" in graph.nodes
    assert "y" in graph.nodes


def test_reject_self_loop():
    b = CausalGraphBuilder()
    edge = b.add_causal_link("a", "a")
    assert edge is None


def test_reject_cycle():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("b", "c")
    edge = b.add_causal_link("c", "a")  # Would create cycle
    assert edge is None


def test_update_existing_edge_ema():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b", strength=0.5, confidence=0.5)
    b.add_causal_link("a", "b", strength=0.8, confidence=0.8)
    edge = b.build().get_edge("a", "b")
    # EMA: 0.3*0.8 + 0.7*0.5 = 0.59
    assert edge.strength == pytest.approx(0.59)
    assert edge.observations == 2


def test_strength_clamping():
    b = CausalGraphBuilder()
    edge = b.add_causal_link("a", "b", strength=1.5, confidence=2.0)
    assert edge.strength == 1.0
    assert edge.confidence == 1.0


def test_mechanism_promotion():
    b = CausalGraphBuilder(promotion_threshold=0.5, min_observations=3)
    for _ in range(4):
        b.add_causal_link("a", "b", strength=0.7, mechanism=MechanismType.OBSERVED.value)
    edge = b.build().get_edge("a", "b")
    assert edge.mechanism == MechanismType.DIRECT.value


def test_no_promotion_below_threshold():
    b = CausalGraphBuilder(promotion_threshold=0.9, min_observations=3)
    for _ in range(5):
        b.add_causal_link("a", "b", strength=0.3, mechanism=MechanismType.OBSERVED.value)
    edge = b.build().get_edge("a", "b")
    assert edge.mechanism == MechanismType.OBSERVED.value


# ── Graph Structure ──


def test_get_parents():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "c")
    b.add_causal_link("b", "c")
    graph = b.build()
    parents = graph.get_parents("c")
    assert sorted(parents) == ["a", "b"]


def test_get_children():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("a", "c")
    graph = b.build()
    children = graph.get_children("a")
    assert sorted(children) == ["b", "c"]


def test_topological_order():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("b", "c")
    b.add_causal_link("a", "c")
    graph = b.build()
    order = graph.topological_order()
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_ancestors():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("b", "c")
    b.add_causal_link("a", "c")
    graph = b.build()
    assert graph.get_ancestors("c") == {"a", "b"}


def test_descendants():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("b", "c")
    graph = b.build()
    assert graph.get_descendants("a") == {"b", "c"}


def test_no_cycle_in_dag():
    b = CausalGraphBuilder()
    b.add_causal_link("a", "b")
    b.add_causal_link("b", "c")
    assert b.build().has_cycle() is False


# ── Co-occurrence ──


def test_observe_co_occurrence():
    b = CausalGraphBuilder()
    edge = b.observe_co_occurrence("x", "y", value_a=0.5, value_b=0.8, direction_hint="a->b")
    assert edge is not None
    assert edge.mechanism == MechanismType.OBSERVED.value


def test_observe_co_occurrence_alphabetical_default():
    b = CausalGraphBuilder()
    b.observe_co_occurrence("z", "a")
    graph = b.build()
    # Alphabetical: a→z
    assert graph.get_edge("a", "z") is not None


def test_observe_co_occurrence_direction_b_to_a():
    b = CausalGraphBuilder()
    b.observe_co_occurrence("x", "y", direction_hint="b->a")
    graph = b.build()
    assert graph.get_edge("y", "x") is not None


# ── Import from GraphEngine ──


def test_import_from_graph_engine_edges():
    b = CausalGraphBuilder()
    edges = [
        ("fear", "avoidance", {"weight": 0.9, "edge_type": "causes"}),
        ("stress", "anxiety", {"weight": 0.7, "edge_type": "influences"}),
    ]
    count = b.import_from_graph_engine_edges(edges)
    assert count == 2
    graph = b.build()
    assert graph.node_count == 4
    assert graph.edge_count == 2
    fear_edge = graph.get_edge("fear", "avoidance")
    assert fear_edge.mechanism == MechanismType.DIRECT.value
    stress_edge = graph.get_edge("stress", "anxiety")
    assert stress_edge.mechanism == MechanismType.MEDIATED.value


# ── Physics Variables ──


def test_add_physics_variables():
    b = CausalGraphBuilder()
    echo_state = {"phi": 0.7, "entropy": 0.3, "coherence": 0.8, "valence": 0.5,
                  "arousal": 0.4, "amplitude": 5.0, "resonance": 0.6, "drift": 0.1}
    b.add_physics_variables(echo_state)
    graph = b.build()
    assert graph.node_count == 8
    assert graph.edge_count == 6  # 6 known links
    # Check entropy→coherence link
    edge = graph.get_edge("entropy", "coherence")
    assert edge is not None
    assert edge.confidence == pytest.approx(0.95)


def test_add_physics_partial_state():
    b = CausalGraphBuilder()
    echo_state = {"phi": 0.5, "entropy": 0.2}
    b.add_physics_variables(echo_state)
    graph = b.build()
    assert "phi" in graph.nodes
    assert "entropy" in graph.nodes
    # Only links where both endpoints exist
    assert graph.edge_count == 0  # coherence, resonance etc. not present


# ── Serialization ──


def test_to_dict():
    b = CausalGraphBuilder()
    b.add_node("a", current_value=0.5)
    b.add_node("b", current_value=0.3)
    b.add_causal_link("a", "b", strength=0.7, confidence=0.8)
    d = b.to_world_state_dict()
    assert d["node_count"] == 2
    assert d["edge_count"] == 1
    assert "a" in d["nodes"]
    assert len(d["edges"]) == 1
    assert d["edges"][0]["strength"] == pytest.approx(0.7)  # raw strength (confidence stored separately)
    assert d["edges"][0]["confidence"] == pytest.approx(0.8)


def test_empty_graph_to_dict():
    b = CausalGraphBuilder()
    d = b.to_world_state_dict()
    assert d["node_count"] == 0
    assert d["edge_count"] == 0


# ── Correlation Estimation ──


def test_correlation_with_data():
    b = CausalGraphBuilder()
    # Perfect positive correlation
    for i in range(5):
        b.add_node("x", current_value=float(i))
        b.add_node("y", current_value=float(i * 2))
    edge = b.observe_co_occurrence("x", "y", direction_hint="a->b")
    assert edge is not None
    assert edge.strength > 0.8  # Strong correlation


def test_correlation_insufficient_data():
    b = CausalGraphBuilder()
    b.add_node("x", current_value=0.5)
    # Only 1 observation — not enough
    strength = b._estimate_correlation("x", "nonexistent")
    assert strength == pytest.approx(0.3)  # default


# ── CausalGraph from_dict ──


def test_from_dict_roundtrip():
    """CausalGraph serialization roundtrip preserves all state."""
    b = CausalGraphBuilder()
    b.add_node("a", name="NodeA", current_value=0.5)
    b.add_node("b", name="NodeB", current_value=0.3)
    b.add_causal_link("a", "b", strength=0.7, confidence=0.8)
    graph = b.build()

    d = graph.to_dict()
    restored = CausalGraph.from_dict(d)

    assert restored.node_count == 2
    assert restored.edge_count == 1
    assert restored.nodes["a"].name == "NodeA"
    assert restored.nodes["a"].current_value == 0.5
    assert restored.nodes["a"].observed_values == [0.5]
    edge = restored.get_edge("a", "b")
    assert edge is not None
    assert edge.strength == pytest.approx(0.7)
    assert edge.confidence == pytest.approx(0.8)


# ── CausalGraphBuilder Auto-Save ──

import json  # noqa: E402


class TestCausalGraphAutoSave:
    """Tests for CausalGraphBuilder auto-save/load."""

    @pytest.fixture
    def builder(self, tmp_path):
        """CausalGraphBuilder with auto-save enabled."""
        b = CausalGraphBuilder()
        b.set_session("cg-test")
        b.enable_auto_save(base_path=str(tmp_path))
        return b

    def _saved_data(self, tmp_path) -> dict:
        fp = tmp_path / "cg-test.json"
        if not fp.exists():
            return {}
        with open(fp) as f:
            return json.load(f)

    def test_save_load_roundtrip(self, tmp_path):
        """Save and load produce identical builder state."""
        b = CausalGraphBuilder(promotion_threshold=0.7, min_observations=5)
        b.set_session("roundtrip")
        b.add_node("x", name="VarX", current_value=0.5)
        b.add_node("y", name="VarY", current_value=0.3)
        b.add_causal_link("x", "y", strength=0.8, confidence=0.9)
        b.auto_save(base_path=str(tmp_path))

        loaded = CausalGraphBuilder.auto_load("roundtrip", base_path=str(tmp_path))
        assert loaded is not None
        assert loaded._graph.node_count == 2
        assert loaded._graph.edge_count == 1
        assert loaded.promotion_threshold == 0.7
        assert loaded.min_observations == 5
        edge = loaded._graph.get_edge("x", "y")
        assert edge is not None
        assert edge.strength == pytest.approx(0.8)

    def test_add_node_triggers_save(self, builder, tmp_path):
        """add_node persists immediately."""
        builder.add_node("x", current_value=0.5)
        data = self._saved_data(tmp_path)
        assert "x" in data["graph"]["nodes"]

    def test_add_causal_link_triggers_save(self, builder, tmp_path):
        """add_causal_link persists the edge."""
        builder.add_node("a", current_value=0.5)
        builder.add_node("b", current_value=0.3)
        builder.add_causal_link("a", "b", strength=0.7)
        data = self._saved_data(tmp_path)
        assert data["graph"]["edge_count"] == 1

    def test_no_save_when_disabled(self, tmp_path):
        """Mutations do NOT save when auto-save is disabled."""
        b = CausalGraphBuilder()
        b.set_session("quiet")
        b.add_node("x", current_value=0.5)
        fp = tmp_path / "quiet.json"
        assert not fp.exists()

    def test_corrupt_file_returns_none(self, tmp_path):
        """Corrupt JSON returns None."""
        fp = tmp_path / "bad.json"
        fp.write_text("not json{{{")
        result = CausalGraphBuilder.auto_load("bad", base_path=str(tmp_path))
        assert result is None

    def test_missing_session_returns_none(self, tmp_path):
        """Missing file returns None."""
        result = CausalGraphBuilder.auto_load("nonexistent", base_path=str(tmp_path))
        assert result is None

    def test_auto_save_no_session_returns_none(self, tmp_path):
        """auto_save without session_id returns None."""
        b = CausalGraphBuilder()
        result = b.auto_save(base_path=str(tmp_path))
        assert result is None

    def test_observed_values_preserved(self, tmp_path):
        """observed_values history survives roundtrip."""
        b = CausalGraphBuilder()
        b.set_session("history")
        for v in [0.1, 0.3, 0.5, 0.7]:
            b.add_node("x", current_value=v)
        b.auto_save(base_path=str(tmp_path))

        loaded = CausalGraphBuilder.auto_load("history", base_path=str(tmp_path))
        assert loaded is not None
        node = loaded._graph.nodes["x"]
        assert len(node.observed_values) == 4
        assert node.current_value == 0.7
