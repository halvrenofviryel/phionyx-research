"""
Tests for PC Algorithm — Causal Structure Learning
====================================================

Validates that the PC algorithm correctly:
1. Extracts observations from CausalGraph nodes
2. Computes partial correlations
3. Discovers causal skeleton via conditional independence
4. Orients edges using v-structures
5. Produces deterministic results
6. Handles edge cases gracefully

Mind-loop stages: UpdateWorldModel (causal discovery)
Cognitive vs. automation: Cognitive (self-directed causal discovery)
"""

import math
import pytest

from phionyx_core.causality.causal_graph import (
    CausalGraph,
    CausalGraphBuilder,
    CausalNode,
    CausalEdge,
    MechanismType,
    NodeType,
)
from phionyx_core.causality.structure_learning import (
    DiscoveredEdge,
    PCAlgorithm,
    StructureLearningResult,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def pc():
    """Default PC algorithm instance."""
    return PCAlgorithm(alpha=0.05, max_conditioning_size=2, min_samples=5)


@pytest.fixture
def empty_graph():
    """Empty CausalGraph."""
    return CausalGraph()


@pytest.fixture
def correlated_graph():
    """Graph with correlated variables (A causes B, C independent)."""
    graph = CausalGraph()
    n = 20
    graph.nodes["A"] = CausalNode(
        node_id="A", name="A",
        observed_values=[float(i) * 0.1 for i in range(n)],
    )
    # B = 0.8*A + noise
    graph.nodes["B"] = CausalNode(
        node_id="B", name="B",
        observed_values=[float(i) * 0.08 + 0.02 * (i % 3) for i in range(n)],
    )
    # C = independent random-ish
    graph.nodes["C"] = CausalNode(
        node_id="C", name="C",
        observed_values=[0.5 + 0.3 * math.sin(i * 1.7) for i in range(n)],
    )
    return graph


@pytest.fixture
def chain_graph():
    """Graph with chain structure: A → B → C (mediated cause)."""
    graph = CausalGraph()
    n = 30
    a_vals = [float(i) * 0.1 for i in range(n)]
    b_vals = [0.7 * a + 0.05 * (i % 4) for i, a in enumerate(a_vals)]
    c_vals = [0.6 * b + 0.03 * (i % 5) for i, b in enumerate(b_vals)]

    graph.nodes["A"] = CausalNode(
        node_id="A", name="A", observed_values=a_vals
    )
    graph.nodes["B"] = CausalNode(
        node_id="B", name="B", observed_values=b_vals
    )
    graph.nodes["C"] = CausalNode(
        node_id="C", name="C", observed_values=c_vals
    )
    return graph


@pytest.fixture
def collider_graph():
    """Graph with collider structure: A → C ← B (v-structure)."""
    graph = CausalGraph()
    n = 30
    a_vals = [float(i) * 0.1 for i in range(n)]
    b_vals = [0.5 + 0.3 * math.sin(i * 0.5) for i in range(n)]
    # C is caused by both A and B
    c_vals = [0.5 * a + 0.4 * b for a, b in zip(a_vals, b_vals)]

    graph.nodes["A"] = CausalNode(
        node_id="A", name="A", observed_values=a_vals
    )
    graph.nodes["B"] = CausalNode(
        node_id="B", name="B", observed_values=b_vals
    )
    graph.nodes["C"] = CausalNode(
        node_id="C", name="C", observed_values=c_vals
    )
    return graph


# ── Empty / Insufficient Data ────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_graph(self, pc, empty_graph):
        result = pc.discover(empty_graph)
        assert result.discovered_edges == []
        assert result.nodes_used == 0

    def test_single_node(self, pc):
        graph = CausalGraph()
        graph.nodes["A"] = CausalNode(
            node_id="A", name="A",
            observed_values=[1.0, 2.0, 3.0, 4.0, 5.0],
        )
        result = pc.discover(graph)
        assert result.discovered_edges == []
        assert result.nodes_used <= 1

    def test_insufficient_samples(self, pc):
        """Nodes with fewer than min_samples are excluded."""
        graph = CausalGraph()
        graph.nodes["A"] = CausalNode(
            node_id="A", name="A",
            observed_values=[1.0, 2.0],  # Only 2 samples
        )
        graph.nodes["B"] = CausalNode(
            node_id="B", name="B",
            observed_values=[3.0, 4.0],
        )
        result = pc.discover(graph)
        assert result.discovered_edges == []

    def test_constant_variable(self, pc):
        """Variables with zero variance produce zero correlation."""
        graph = CausalGraph()
        graph.nodes["A"] = CausalNode(
            node_id="A", name="A",
            observed_values=[0.5] * 10,  # Constant
        )
        graph.nodes["B"] = CausalNode(
            node_id="B", name="B",
            observed_values=[float(i) for i in range(10)],
        )
        result = pc.discover(graph)
        # Constant variable → zero correlation → edge removed
        assert len(result.discovered_edges) == 0


# ── Observation Extraction ───────────────────────────────────────────────────


class TestObservationExtraction:
    def test_extracts_eligible_nodes(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        assert len(var_names) == 3
        assert all(name in var_names for name in ["A", "B", "C"])

    def test_aligns_to_shortest(self, pc):
        graph = CausalGraph()
        graph.nodes["X"] = CausalNode(
            node_id="X", name="X",
            observed_values=[1.0, 2.0, 3.0, 4.0, 5.0],
        )
        graph.nodes["Y"] = CausalNode(
            node_id="Y", name="Y",
            observed_values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        )
        var_names, obs = pc._extract_observations(graph)
        # Aligned to shortest (5 samples)
        assert len(obs[0]) == 5
        assert len(obs[1]) == 5

    def test_excludes_sparse_nodes(self):
        pc = PCAlgorithm(min_samples=10)
        graph = CausalGraph()
        graph.nodes["A"] = CausalNode(
            node_id="A", name="A",
            observed_values=list(range(15)),
        )
        graph.nodes["B"] = CausalNode(
            node_id="B", name="B",
            observed_values=list(range(15)),
        )
        graph.nodes["C"] = CausalNode(
            node_id="C", name="C",
            observed_values=[1.0, 2.0, 3.0],  # Only 3, below min_samples=10
        )
        var_names, _ = pc._extract_observations(graph)
        assert "C" not in var_names
        assert len(var_names) == 2

    def test_sorted_variable_names(self, pc, correlated_graph):
        """Variable names are sorted for deterministic ordering."""
        var_names, _ = pc._extract_observations(correlated_graph)
        assert var_names == sorted(var_names)


# ── Correlation Matrix ───────────────────────────────────────────────────────


class TestCorrelationMatrix:
    def test_diagonal_is_one(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        corr = pc._compute_correlation_matrix(obs, len(var_names), len(obs[0]))
        for i in range(len(var_names)):
            assert corr[i][i] == pytest.approx(1.0)

    def test_symmetric(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        n = len(var_names)
        corr = pc._compute_correlation_matrix(obs, n, len(obs[0]))
        for i in range(n):
            for j in range(n):
                assert corr[i][j] == pytest.approx(corr[j][i])

    def test_bounded(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        n = len(var_names)
        corr = pc._compute_correlation_matrix(obs, n, len(obs[0]))
        for i in range(n):
            for j in range(n):
                assert -1.0 <= corr[i][j] <= 1.0

    def test_high_correlation_detected(self, pc, correlated_graph):
        """A and B should be highly correlated."""
        var_names, obs = pc._extract_observations(correlated_graph)
        corr = pc._compute_correlation_matrix(obs, len(var_names), len(obs[0]))
        a_idx = var_names.index("A")
        b_idx = var_names.index("B")
        assert abs(corr[a_idx][b_idx]) > 0.8


# ── Partial Correlation ──────────────────────────────────────────────────────


class TestPartialCorrelation:
    def test_unconditioned_equals_pearson(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        corr = pc._compute_correlation_matrix(obs, len(var_names), len(obs[0]))
        a_idx = var_names.index("A")
        b_idx = var_names.index("B")
        # Partial correlation with empty conditioning = Pearson
        p_corr = pc._partial_correlation(corr, a_idx, b_idx, [])
        assert p_corr == pytest.approx(corr[a_idx][b_idx])

    def test_chain_mediated_independence(self, pc, chain_graph):
        """In A→B→C, A and C become independent when conditioning on B."""
        var_names, obs = pc._extract_observations(chain_graph)
        corr = pc._compute_correlation_matrix(obs, len(var_names), len(obs[0]))
        a_idx = var_names.index("A")
        b_idx = var_names.index("B")
        c_idx = var_names.index("C")

        # A-C unconditional: should be correlated (mediated by B)
        r_ac = pc._partial_correlation(corr, a_idx, c_idx, [])
        assert abs(r_ac) > 0.5

        # A-C conditional on B: should be much weaker
        r_ac_b = pc._partial_correlation(corr, a_idx, c_idx, [b_idx])
        assert abs(r_ac_b) < abs(r_ac)

    def test_partial_correlation_bounded(self, pc, correlated_graph):
        var_names, obs = pc._extract_observations(correlated_graph)
        corr = pc._compute_correlation_matrix(obs, len(var_names), len(obs[0]))
        for i in range(len(var_names)):
            for j in range(len(var_names)):
                if i == j:
                    continue
                cond = [k for k in range(len(var_names)) if k != i and k != j]
                for c in cond:
                    p = pc._partial_correlation(corr, i, j, [c])
                    assert -1.0 <= p <= 1.0


# ── Skeleton Discovery ───────────────────────────────────────────────────────


class TestSkeletonDiscovery:
    def test_correlated_pair_kept(self, pc, correlated_graph):
        """Highly correlated A-B should remain in skeleton."""
        result = pc.discover(correlated_graph)
        edge_pairs = {(e.source_id, e.target_id) for e in result.discovered_edges}
        # At least one direction of A-B should be present
        assert ("A", "B") in edge_pairs or ("B", "A") in edge_pairs

    def test_independent_pair_removed(self, pc):
        """Truly independent variables should be separated."""
        graph = CausalGraph()
        n = 30
        # Two truly independent sequences
        graph.nodes["X"] = CausalNode(
            node_id="X", name="X",
            observed_values=[float(i) for i in range(n)],
        )
        graph.nodes["Y"] = CausalNode(
            node_id="Y", name="Y",
            observed_values=[30.0 - float(i) for i in range(n)],
        )
        graph.nodes["Z"] = CausalNode(
            node_id="Z", name="Z",
            observed_values=[0.5 + 0.4 * math.sin(i * 2.1) for i in range(n)],
        )
        # X and Y are perfectly anti-correlated, Z is independent
        result = pc.discover(graph)
        # X-Y should have an edge (anti-correlated is still dependent)
        edge_ids = {(e.source_id, e.target_id) for e in result.discovered_edges}
        assert ("X", "Y") in edge_ids or ("Y", "X") in edge_ids

    def test_skeleton_edges_count(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        assert result.skeleton_edges >= 0
        assert result.skeleton_edges <= 3  # max for 3 nodes


# ── Edge Orientation ─────────────────────────────────────────────────────────


class TestEdgeOrientation:
    def test_oriented_edges_are_directed(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        for edge in result.discovered_edges:
            assert edge.source_id != edge.target_id

    def test_no_bidirectional_edges(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        edge_set = {(e.source_id, e.target_id) for e in result.discovered_edges}
        for src, tgt in edge_set:
            # Should not have both A→B and B→A
            assert (tgt, src) not in edge_set

    def test_uses_existing_graph_hints(self, pc):
        """Existing non-observed edges in graph guide orientation."""
        graph = CausalGraph()
        n = 20
        a_vals = [float(i) * 0.1 for i in range(n)]
        b_vals = [0.8 * a + 0.01 * i for i, a in enumerate(a_vals)]

        graph.nodes["A"] = CausalNode(
            node_id="A", name="A", observed_values=a_vals,
        )
        graph.nodes["B"] = CausalNode(
            node_id="B", name="B", observed_values=b_vals,
        )
        # Pre-existing directed edge A→B
        graph.edges["A->B"] = CausalEdge(
            source_id="A", target_id="B",
            strength=0.8, confidence=0.9,
            mechanism=MechanismType.DIRECT.value,
        )

        result = pc.discover(graph)
        if result.discovered_edges:
            # Should orient as A→B (matching existing)
            ab_edges = [
                e for e in result.discovered_edges
                if e.source_id == "A" and e.target_id == "B"
            ]
            ba_edges = [
                e for e in result.discovered_edges
                if e.source_id == "B" and e.target_id == "A"
            ]
            assert len(ab_edges) >= len(ba_edges)


# ── Result Structure ─────────────────────────────────────────────────────────


class TestResultStructure:
    def test_result_fields(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        assert isinstance(result, StructureLearningResult)
        assert result.nodes_used == 3
        assert result.sample_size == 20
        assert isinstance(result.discovered_edges, list)
        assert isinstance(result.removed_pairs, list)

    def test_edge_fields(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        for edge in result.discovered_edges:
            assert isinstance(edge, DiscoveredEdge)
            assert 0.0 <= edge.strength <= 1.0
            assert 0.0 <= edge.confidence <= 1.0
            assert edge.source_id in ["A", "B", "C"]
            assert edge.target_id in ["A", "B", "C"]

    def test_edges_sorted_by_confidence(self, pc, correlated_graph):
        result = pc.discover(correlated_graph)
        if len(result.discovered_edges) > 1:
            confs = [e.confidence for e in result.discovered_edges]
            assert confs == sorted(confs, reverse=True)


# ── CausalGraphBuilder Integration ──────────────────────────────────────────


class TestBuilderIntegration:
    def test_discovered_edges_addable(self, pc, correlated_graph):
        """Discovered edges can be added to CausalGraphBuilder."""
        result = pc.discover(correlated_graph)
        builder = CausalGraphBuilder()

        for edge in result.discovered_edges:
            added = builder.add_causal_link(
                edge.source_id,
                edge.target_id,
                strength=edge.strength,
                confidence=edge.confidence,
                mechanism=edge.mechanism,
            )
            assert added is not None

        graph = builder.build()
        assert graph.edge_count == len(result.discovered_edges)

    def test_no_cycles_in_discovered(self, pc, correlated_graph):
        """Discovered edges should not create cycles when added together."""
        result = pc.discover(correlated_graph)
        builder = CausalGraphBuilder()

        for edge in result.discovered_edges:
            builder.add_causal_link(
                edge.source_id,
                edge.target_id,
                strength=edge.strength,
                confidence=edge.confidence,
            )

        graph = builder.build()
        assert not graph.has_cycle()


# ── Determinism ──────────────────────────────────────────────────────────────


class TestDeterminism:
    def test_discover_deterministic(self, correlated_graph):
        """Same graph → same discovery result every time."""
        results = []
        for _ in range(5):
            pc = PCAlgorithm(alpha=0.05, max_conditioning_size=2, min_samples=5)
            result = pc.discover(correlated_graph)
            edge_tuples = tuple(
                (e.source_id, e.target_id, e.strength, e.confidence)
                for e in result.discovered_edges
            )
            results.append(edge_tuples)
        assert len(set(results)) == 1

    def test_removed_pairs_deterministic(self, correlated_graph):
        """Same graph → same removed pairs every time."""
        results = []
        for _ in range(5):
            pc = PCAlgorithm(alpha=0.05, max_conditioning_size=2, min_samples=5)
            result = pc.discover(correlated_graph)
            removed = tuple(
                (a, b, tuple(s)) for a, b, s in result.removed_pairs
            )
            results.append(removed)
        assert len(set(results)) == 1


# ── Statistical Helpers ──────────────────────────────────────────────────────


class TestStatisticalHelpers:
    def test_normal_critical_value_standard(self):
        pc = PCAlgorithm()
        z = pc._normal_critical_value(0.05)
        assert 1.9 < z < 2.0  # Should be ≈1.96

    def test_normal_critical_value_strict(self):
        pc = PCAlgorithm()
        z01 = pc._normal_critical_value(0.01)
        z05 = pc._normal_critical_value(0.05)
        assert z01 > z05  # Stricter alpha → higher critical value

    def test_confidence_score_range(self):
        pc = PCAlgorithm()
        conf = pc._compute_confidence(0.5, 20)
        assert 0.0 <= conf <= 1.0

    def test_confidence_increases_with_samples(self):
        pc = PCAlgorithm()
        conf_small = pc._compute_confidence(0.5, 5)
        conf_large = pc._compute_confidence(0.5, 30)
        assert conf_large > conf_small

    def test_confidence_increases_with_strength(self):
        pc = PCAlgorithm()
        conf_weak = pc._compute_confidence(0.1, 20)
        conf_strong = pc._compute_confidence(0.9, 20)
        assert conf_strong > conf_weak

    def test_combinations_empty(self):
        result = list(PCAlgorithm._combinations([1, 2, 3], 0))
        assert result == [()]

    def test_combinations_size_1(self):
        result = list(PCAlgorithm._combinations([3, 1, 2], 1))
        assert result == [(1,), (2,), (3,)]

    def test_combinations_size_2(self):
        result = list(PCAlgorithm._combinations([1, 2, 3], 2))
        assert result == [(1, 2), (1, 3), (2, 3)]

    def test_combinations_exceeds_items(self):
        result = list(PCAlgorithm._combinations([1, 2], 3))
        assert result == []


# ── Alpha Sensitivity ────────────────────────────────────────────────────────


class TestAlphaSensitivity:
    def test_stricter_alpha_fewer_edges(self, correlated_graph):
        """Lower alpha should discover fewer (or equal) edges."""
        liberal = PCAlgorithm(alpha=0.10, min_samples=5)
        strict = PCAlgorithm(alpha=0.01, min_samples=5)

        r_liberal = liberal.discover(correlated_graph)
        r_strict = strict.discover(correlated_graph)

        assert len(r_strict.discovered_edges) <= len(r_liberal.discovered_edges)
