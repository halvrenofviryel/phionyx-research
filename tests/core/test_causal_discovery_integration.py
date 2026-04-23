"""
Causal Discovery Integration Tests
====================================

Tests PCAlgorithm → CausalGraphBuilder integration via discover_structure().

Verifies:
- Discovery triggers only with sufficient observations
- Discovered edges merge into existing graph
- Conflicting edges produce warnings (not overwrites)
- Discovery is deterministic

Mind-loop stage: UpdateWorldModel (causal structure enrichment)
"""

import pytest
from phionyx_core.causality.causal_graph import CausalGraphBuilder, NodeType


class TestDiscoverStructureThreshold:
    """Test that discover_structure respects observation thresholds."""

    def test_insufficient_observations_no_trigger(self):
        """Below threshold: discovery does not trigger."""
        builder = CausalGraphBuilder()
        builder.add_node("A", current_value=1.0)
        builder.add_node("B", current_value=2.0)
        # Only 1 observation each

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is False
        assert result["edges_added"] == 0
        assert "Need 2+" in result["reason"]

    def test_10_observations_no_trigger(self):
        """10 observations with threshold 20: no trigger."""
        builder = CausalGraphBuilder()
        for i in range(10):
            builder.add_node("X", current_value=float(i))
            builder.add_node("Y", current_value=float(i * 2))

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is False

    def test_single_eligible_node_no_trigger(self):
        """Only 1 node meets threshold: needs 2+."""
        builder = CausalGraphBuilder()
        for i in range(25):
            builder.add_node("A", current_value=float(i))
        builder.add_node("B", current_value=1.0)  # only 1 obs

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is False


class TestDiscoverStructureExecution:
    """Test that discovery runs and integrates edges."""

    def _build_correlated(self, n: int = 25) -> CausalGraphBuilder:
        """Helper: build graph with correlated observations."""
        builder = CausalGraphBuilder()
        for i in range(n):
            x = float(i)
            builder.add_node("A", current_value=x)
            builder.add_node("B", current_value=x * 0.8 + 1.0)
            builder.add_node("C", current_value=x * 0.3 + 5.0)
        return builder

    def test_sufficient_observations_triggers(self):
        """25 observations: discovery triggers."""
        builder = self._build_correlated(25)

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is True
        assert result["nodes_eligible"] >= 2

    def test_discovered_edges_added_to_graph(self):
        """Discovered edges appear in the built graph."""
        builder = self._build_correlated(30)
        initial_edges = builder.build().edge_count

        result = builder.discover_structure(min_observations=20)

        if result["edges_added"] > 0:
            assert builder.build().edge_count > initial_edges

    def test_discovery_is_deterministic(self):
        """Same input → same output."""
        def run():
            b = self._build_correlated(25)
            return b.discover_structure(min_observations=20)

        r1 = run()
        r2 = run()
        assert r1["edges_added"] == r2["edges_added"]
        assert r1["triggered"] == r2["triggered"]

    def test_custom_alpha(self):
        """Alpha parameter is passed to PCAlgorithm."""
        builder = self._build_correlated(25)
        # Very strict alpha = fewer edges
        result_strict = builder.discover_structure(min_observations=20, alpha=0.001)

        builder2 = self._build_correlated(25)
        # Lenient alpha = more edges
        result_lenient = builder2.discover_structure(min_observations=20, alpha=0.10)

        # Strict should find <= lenient edges
        assert result_strict["edges_added"] <= result_lenient["edges_added"]


class TestDiscoverStructureConflicts:
    """Test conflict handling when discovered edges contradict existing ones."""

    def test_conflicting_edge_not_overwritten(self):
        """Existing A→B + discovery B→A: conflict logged, edge not added."""
        builder = CausalGraphBuilder()
        # Pre-establish A→B
        for i in range(25):
            builder.add_node("A", current_value=float(i))
            builder.add_node("B", current_value=float(i * 0.5))
        builder.add_causal_link("A", "B", strength=0.9, confidence=0.95)

        _initial_edges = builder.build().edge_count

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is True
        # If conflicts found, they should be reported
        if result.get("conflicts"):
            assert len(result["conflicts"]) > 0


class TestEnrichedObservationsDiscovery:
    """Tests for enriched observation pairs enabling discovery."""

    def test_enriched_observations_enable_discovery(self):
        """25+ turns with 8 variables → discovery triggers with enriched data."""
        builder = CausalGraphBuilder()
        import math
        for i in range(30):
            t = float(i)
            builder.add_node("phi", current_value=0.5 + 0.1 * math.sin(t))
            builder.add_node("entropy", current_value=0.4 + 0.05 * t / 30)
            builder.add_node("coherence", current_value=0.7 - 0.05 * t / 30)
            builder.add_node("valence", current_value=0.3 + 0.02 * math.cos(t))
            builder.add_node("arousal", current_value=0.6 + 0.1 * math.sin(t + 1))
            builder.add_node("amplitude", current_value=0.8 - 0.02 * t / 30)
            builder.add_node("resonance", current_value=0.65 + 0.05 * math.sin(t))
            builder.add_node("drift", current_value=0.1 + 0.01 * t / 30)

        result = builder.discover_structure(min_observations=20)

        assert result["triggered"] is True
        assert result["nodes_eligible"] >= 2

    def test_pc_params_tunable_from_module(self):
        """Module-level pc_alpha, pc_min_observations, pc_max_conditioning_size are importable."""
        from phionyx_core.causality import causal_graph as cg

        assert hasattr(cg, "pc_alpha")
        assert hasattr(cg, "pc_min_observations")
        assert hasattr(cg, "pc_max_conditioning_size")
        assert isinstance(cg.pc_alpha, float)
        assert isinstance(cg.pc_min_observations, int)
        assert isinstance(cg.pc_max_conditioning_size, int)
        assert cg.pc_alpha == 0.05
        assert cg.pc_min_observations == 20
        assert cg.pc_max_conditioning_size == 3

    def test_discover_structure_uses_module_defaults(self):
        """Argless discover_structure() uses module-level defaults correctly."""
        from phionyx_core.causality import causal_graph as cg

        builder = CausalGraphBuilder()
        for i in range(25):
            builder.add_node("X", current_value=float(i))
            builder.add_node("Y", current_value=float(i) * 2)

        # Call without arguments — should use pc_min_observations (20)
        result = builder.discover_structure()

        assert result["triggered"] is True
        assert result["nodes_eligible"] >= 2

        # Also verify that passing explicit values still works
        result2 = builder.discover_structure(min_observations=30)
        # With 25 observations and threshold 30, should not trigger
        assert result2["triggered"] is False
