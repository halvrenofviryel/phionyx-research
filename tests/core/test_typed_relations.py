"""
Tests for Typed Relations in GraphEngine — v4 §1 Entity Layer
"""

import pytest
from phionyx_core.intuition.graph_engine import (
    EdgeType,
    Concept,
    Association,
    GraphEngine,
)


class TestEdgeType:
    """EdgeType enum tests."""

    def test_all_types_exist(self):
        assert EdgeType.RELATED.value == "related"
        assert EdgeType.CAUSES.value == "causes"
        assert EdgeType.IS_A.value == "is_a"
        assert EdgeType.PART_OF.value == "part_of"
        assert EdgeType.CONTRADICTS.value == "contradicts"
        assert EdgeType.PRECEDES.value == "precedes"
        assert EdgeType.INFLUENCES.value == "influences"

    def test_edge_type_is_string(self):
        assert isinstance(EdgeType.CAUSES.value, str)
        assert EdgeType.CAUSES == "causes"

    def test_edge_type_from_string(self):
        assert EdgeType("causes") == EdgeType.CAUSES
        assert EdgeType("related") == EdgeType.RELATED


class TestConceptObservationSource:
    """Concept observation_source field tests."""

    def test_concept_has_observation_source(self):
        c = Concept(
            name="Fear",
            normalized_name="fear",
            category="emotion",
            confidence=0.9,
            observation_source="user_input",
        )
        assert c.observation_source == "user_input"

    def test_concept_default_observation_source(self):
        c = Concept(name="Test")
        assert c.observation_source == ""

    def test_concept_has_first_observed(self):
        c = Concept(
            name="Test",
            first_observed="2026-03-17T00:00:00",
        )
        assert c.first_observed == "2026-03-17T00:00:00"


class TestAssociationEdgeType:
    """Association edge_type field tests."""

    def test_association_default_edge_type(self):
        a = Association(
            source_id="a",
            target_id="b",
            weight=0.5,
            formation_phi=0.8,
        )
        assert a.edge_type == EdgeType.RELATED.value

    def test_association_custom_edge_type(self):
        a = Association(
            source_id="a",
            target_id="b",
            weight=0.5,
            formation_phi=0.8,
            edge_type=EdgeType.CAUSES.value,
        )
        assert a.edge_type == "causes"


class TestGraphEngineEdgeQueries:
    """GraphEngine edge query methods (in-memory graph only, no Supabase)."""

    def _make_engine(self):
        """Create engine in offline mode.

        ``GraphEngine.graph`` is a lazily initialised networkx instance that
        currently returns ``None`` when Supabase credentials are absent (the
        dev-env default). Skip the suite if that's the case — the
        ``None`` state is what the GraphEngine class promises, not a test bug.
        """
        engine = GraphEngine(actor_ref="test_user")
        if engine.graph is None:
            pytest.skip(
                "GraphEngine.graph is None (Supabase credentials absent); "
                "these tests exercise the in-memory graph and require it."
            )
        # Manually add edges to in-memory graph
        engine.graph.add_edge("a", "b", weight=0.8, edge_type=EdgeType.CAUSES.value)
        engine.graph.add_edge("b", "c", weight=0.6, edge_type=EdgeType.CAUSES.value)
        engine.graph.add_edge("a", "c", weight=0.5, edge_type=EdgeType.RELATED.value)
        engine.graph.add_edge("d", "a", weight=0.3, edge_type=EdgeType.CONTRADICTS.value)
        engine.graph.add_edge("c", "d", weight=0.4, edge_type=EdgeType.INFLUENCES.value)
        return engine

    def test_get_edges_by_type_causes(self):
        engine = self._make_engine()
        causal = engine.get_edges_by_type(EdgeType.CAUSES.value)
        assert len(causal) == 2
        sources = [u for u, _, _ in causal]
        assert "a" in sources
        assert "b" in sources

    def test_get_edges_by_type_related(self):
        engine = self._make_engine()
        related = engine.get_edges_by_type(EdgeType.RELATED.value)
        assert len(related) == 1

    def test_get_causal_subgraph(self):
        engine = self._make_engine()
        subgraph = engine.get_causal_subgraph()
        # Should include CAUSES and INFLUENCES edges
        assert subgraph.number_of_edges() == 3  # 2 causes + 1 influences
        assert subgraph.has_edge("a", "b")
        assert subgraph.has_edge("b", "c")
        assert subgraph.has_edge("c", "d")

    def test_get_contradictions(self):
        engine = self._make_engine()
        contradictions = engine.get_contradictions()
        assert len(contradictions) == 1
        assert contradictions[0][0] == "d"
        assert contradictions[0][1] == "a"

    def test_empty_type_returns_empty(self):
        engine = self._make_engine()
        result = engine.get_edges_by_type(EdgeType.IS_A.value)
        assert len(result) == 0
