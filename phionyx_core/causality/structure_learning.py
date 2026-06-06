"""
Causal Structure Learning — PC Algorithm
==========================================

Constraint-based causal discovery using the PC (Peter-Clark) algorithm.
Discovers causal edges from observational data in CausalGraph nodes.

Algorithm overview:
1. Start with complete undirected skeleton over all nodes with observations
2. Remove edges where conditional independence is detected (via partial correlation)
3. Orient edges using v-structure detection and acyclicity constraints
4. Return discovered directed edges with confidence scores

Mind-loop stages: UpdateWorldModel (causal structure discovery)
AGI component: World-model causal edge enrichment
Cognitive vs. automation: Cognitive (self-directed causal discovery)

Integrates with:
- causality/causal_graph.py (CausalGraph, CausalGraphBuilder)
- contracts/v4/world_state_snapshot.py (enriched causal model)
"""

import math
import logging
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
from dataclasses import dataclass

from phionyx_core.causality.causal_graph import CausalGraph, MechanismType

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredEdge:
    """An edge discovered by the PC algorithm."""
    source_id: str
    target_id: str
    strength: float       # Partial correlation magnitude
    confidence: float     # Based on sample size and statistical significance
    mechanism: str = MechanismType.OBSERVED.value


@dataclass
class StructureLearningResult:
    """Result of running the PC algorithm."""
    discovered_edges: List[DiscoveredEdge]
    removed_pairs: List[Tuple[str, str, List[str]]]  # (var_a, var_b, sep_set)
    nodes_used: int
    sample_size: int
    max_conditioning_size: int
    skeleton_edges: int   # Edges remaining after skeleton phase
    oriented_edges: int   # Edges successfully oriented


class PCAlgorithm:
    """
    PC algorithm for causal structure learning.

    Discovers causal relationships from observational data stored in
    CausalGraph nodes' observed_values. Deterministic — same input
    produces same output.

    Usage:
        pc = PCAlgorithm(alpha=0.05)
        result = pc.discover(causal_graph)
        for edge in result.discovered_edges:
            builder.add_causal_link(edge.source_id, edge.target_id, ...)
    """

    def __init__(
        self,
        alpha: float = 0.05,
        max_conditioning_size: int = 3,
        min_samples: int = 5,
    ):
        """
        Args:
            alpha: Significance level for conditional independence tests.
                   Lower = more conservative (fewer edges).
            max_conditioning_size: Maximum size of conditioning set.
                   Higher = more thorough but slower (O(n^k)).
            min_samples: Minimum observations per node to include in discovery.
        """
        self.alpha = alpha
        self.max_conditioning_size = max_conditioning_size
        self.min_samples = min_samples

    def discover(self, graph: CausalGraph) -> StructureLearningResult:
        """
        Run PC algorithm on a CausalGraph's observational data.

        Args:
            graph: CausalGraph with nodes containing observed_values.

        Returns:
            StructureLearningResult with discovered edges and metadata.
        """
        # Step 1: Extract observation matrix
        var_names, obs_matrix = self._extract_observations(graph)
        n_vars = len(var_names)
        n_samples = len(obs_matrix[0]) if obs_matrix else 0

        if n_vars < 2 or n_samples < self.min_samples:
            return StructureLearningResult(
                discovered_edges=[],
                removed_pairs=[],
                nodes_used=n_vars,
                sample_size=n_samples,
                max_conditioning_size=0,
                skeleton_edges=0,
                oriented_edges=0,
            )

        # Step 2: Compute correlation matrix
        corr_matrix = self._compute_correlation_matrix(obs_matrix, n_vars, n_samples)

        # Step 3: PC skeleton discovery
        adjacency, sep_sets, removed = self._discover_skeleton(
            var_names, corr_matrix, n_samples
        )

        skeleton_count = sum(
            1 for i in range(n_vars) for j in range(i + 1, n_vars) if adjacency[i][j]
        )

        # Step 4: Orient edges
        directed = self._orient_edges(var_names, adjacency, sep_sets, graph)

        # Step 5: Build result
        discovered = []
        for src_idx, tgt_idx in directed:
            src_name = var_names[src_idx]
            tgt_name = var_names[tgt_idx]
            strength = abs(corr_matrix[src_idx][tgt_idx])
            confidence = self._compute_confidence(strength, n_samples)
            discovered.append(DiscoveredEdge(
                source_id=src_name,
                target_id=tgt_name,
                strength=round(strength, 4),
                confidence=round(confidence, 4),
            ))

        # Sort by confidence descending for deterministic output
        discovered.sort(key=lambda e: (-e.confidence, e.source_id, e.target_id))

        return StructureLearningResult(
            discovered_edges=discovered,
            removed_pairs=removed,
            nodes_used=n_vars,
            sample_size=n_samples,
            max_conditioning_size=min(self.max_conditioning_size, n_vars - 2),
            skeleton_edges=skeleton_count,
            oriented_edges=len(directed),
        )

    def _extract_observations(
        self, graph: CausalGraph
    ) -> Tuple[List[str], List[List[float]]]:
        """Extract aligned observation matrix from graph nodes.

        Returns:
            (var_names, obs_matrix) where obs_matrix[var_idx][sample_idx]
            Only includes nodes with >= min_samples observations.
            Aligns to shortest common length.
        """
        # Filter nodes with sufficient observations
        eligible = sorted([
            (nid, node)
            for nid, node in graph.nodes.items()
            if len(node.observed_values) >= self.min_samples
        ])

        if len(eligible) < 2:
            return [], []

        var_names = [nid for nid, _ in eligible]

        # Align to shortest common length
        min_len = min(len(node.observed_values) for _, node in eligible)
        obs_matrix = [
            node.observed_values[-min_len:]  # Use most recent observations
            for _, node in eligible
        ]

        return var_names, obs_matrix

    def _compute_correlation_matrix(
        self, obs_matrix: List[List[float]], n_vars: int, n_samples: int
    ) -> List[List[float]]:
        """Compute Pearson correlation matrix."""
        # Compute means
        means = [sum(obs_matrix[i]) / n_samples for i in range(n_vars)]

        # Compute std devs
        stds = []
        for i in range(n_vars):
            variance = sum(
                (obs_matrix[i][k] - means[i]) ** 2 for k in range(n_samples)
            ) / n_samples
            stds.append(math.sqrt(variance) if variance > 0 else 0.0)

        # Compute correlation matrix
        corr = [[0.0] * n_vars for _ in range(n_vars)]
        for i in range(n_vars):
            corr[i][i] = 1.0
            for j in range(i + 1, n_vars):
                if stds[i] == 0 or stds[j] == 0:
                    corr[i][j] = corr[j][i] = 0.0
                else:
                    cov = sum(
                        (obs_matrix[i][k] - means[i]) * (obs_matrix[j][k] - means[j])
                        for k in range(n_samples)
                    ) / n_samples
                    r = cov / (stds[i] * stds[j])
                    corr[i][j] = corr[j][i] = max(-1.0, min(1.0, r))

        return corr

    def _discover_skeleton(
        self,
        var_names: List[str],
        corr_matrix: List[List[float]],
        n_samples: int,
    ) -> Tuple[
        List[List[bool]],
        Dict[FrozenSet[int], List[int]],
        List[Tuple[str, str, List[str]]],
    ]:
        """PC skeleton discovery: remove edges via conditional independence.

        Returns:
            (adjacency, sep_sets, removed_pairs)
        """
        n = len(var_names)
        adjacency = [[i != j for j in range(n)] for i in range(n)]
        sep_sets: Dict[FrozenSet[int], List[int]] = {}
        removed: List[Tuple[str, str, List[str]]] = []

        for cond_size in range(self.max_conditioning_size + 1):
            for i in range(n):
                for j in range(i + 1, n):
                    if not adjacency[i][j]:
                        continue

                    # Get adjacent nodes (excluding i and j) as conditioning candidates
                    adj_i = [
                        k for k in range(n)
                        if k != i and k != j and adjacency[i][k]
                    ]

                    # Test all conditioning sets of current size
                    if cond_size > len(adj_i):
                        continue

                    found_independent = False
                    for cond_set in self._combinations(adj_i, cond_size):
                        p_corr = self._partial_correlation(
                            corr_matrix, i, j, list(cond_set)
                        )
                        if self._is_independent(p_corr, n_samples, cond_size):
                            # Remove edge
                            adjacency[i][j] = False
                            adjacency[j][i] = False
                            sep_sets[frozenset([i, j])] = list(cond_set)
                            removed.append((
                                var_names[i],
                                var_names[j],
                                [var_names[k] for k in cond_set],
                            ))
                            found_independent = True
                            break

                    if found_independent:
                        continue

        return adjacency, sep_sets, removed

    def _orient_edges(
        self,
        var_names: List[str],
        adjacency: List[List[bool]],
        sep_sets: Dict[FrozenSet[int], List[int]],
        original_graph: CausalGraph,
    ) -> List[Tuple[int, int]]:
        """Orient undirected skeleton edges into directed edges.

        Uses:
        1. V-structure detection (collider orientation)
        2. Existing edge directions from the original graph
        3. Acyclicity enforcement
        """
        n = len(var_names)

        # directed[i][j] = True means i → j is confirmed
        directed: List[List[Optional[bool]]] = [
            [None] * n for _ in range(n)
        ]

        # Rule 1: V-structure detection
        # For each triple i - k - j where i and j are NOT adjacent,
        # if k is NOT in sep_set(i, j), orient as i → k ← j (collider)
        for k in range(n):
            parents_of_k = [
                i for i in range(n) if adjacency[i][k] and i != k
            ]
            for pi in range(len(parents_of_k)):
                for pj in range(pi + 1, len(parents_of_k)):
                    i = parents_of_k[pi]
                    j = parents_of_k[pj]
                    # i and j must NOT be adjacent
                    if adjacency[i][j]:
                        continue
                    # k must NOT be in sep_set(i, j)
                    pair_key = frozenset([i, j])
                    sep = sep_sets.get(pair_key, [])
                    if k not in sep:
                        directed[i][k] = True
                        directed[k][i] = False
                        directed[j][k] = True
                        directed[k][j] = False

        # Rule 2: Use existing graph edges as hints
        for i in range(n):
            for j in range(n):
                if not adjacency[i][j] or i == j:
                    continue
                if directed[i][j] is not None:
                    continue
                # Check if original graph has this edge
                src = var_names[i]
                tgt = var_names[j]
                existing = original_graph.get_edge(src, tgt)
                if existing and existing.mechanism != MechanismType.OBSERVED.value:
                    directed[i][j] = True
                    directed[j][i] = False

        # Rule 3: Orient remaining edges ensuring acyclicity
        # Use topological hints: prefer direction consistent with existing orientation
        for i in range(n):
            for j in range(i + 1, n):
                if not adjacency[i][j]:
                    continue
                if directed[i][j] is not None:
                    continue
                # Default: orient alphabetically (deterministic tie-breaking)
                if not self._would_create_cycle_in_directed(directed, n, j, i):
                    directed[i][j] = True
                    directed[j][i] = False
                elif not self._would_create_cycle_in_directed(directed, n, i, j):
                    directed[j][i] = True
                    directed[i][j] = False
                # else: leave as undirected (don't add to discovered)

        # Collect all directed edges
        result = []
        for i in range(n):
            for j in range(n):
                if directed[i][j] is True and adjacency[i][j]:
                    result.append((i, j))

        return result

    def _partial_correlation(
        self,
        corr_matrix: List[List[float]],
        i: int,
        j: int,
        conditioning: List[int],
    ) -> float:
        """Compute partial correlation between i and j given conditioning set.

        Uses recursive formula:
        ρ(X,Y|Z) = (ρ(X,Y|Z\\{z}) - ρ(X,z|Z\\{z})·ρ(Y,z|Z\\{z}))
                    / √((1-ρ(X,z|Z\\{z})²)·(1-ρ(Y,z|Z\\{z})²))
        """
        if not conditioning:
            return corr_matrix[i][j]

        # Recursive: condition on all but last, then adjust for last
        z = conditioning[-1]
        rest = conditioning[:-1]

        r_ij = self._partial_correlation(corr_matrix, i, j, rest)
        r_iz = self._partial_correlation(corr_matrix, i, z, rest)
        r_jz = self._partial_correlation(corr_matrix, j, z, rest)

        denom_sq = (1.0 - r_iz ** 2) * (1.0 - r_jz ** 2)
        if denom_sq <= 0:
            return 0.0
        denom = math.sqrt(denom_sq)
        if denom < 1e-10:
            return 0.0

        return (r_ij - r_iz * r_jz) / denom

    def _is_independent(
        self, partial_corr: float, n_samples: int, cond_size: int
    ) -> bool:
        """Test conditional independence using Fisher's z-transform.

        H0: partial correlation = 0 (independent)
        Reject if |z| > z_alpha (not independent).
        Returns True if independent (fail to reject H0).
        """
        dof = n_samples - cond_size - 3
        if dof < 1:
            return False  # Not enough data

        r = abs(partial_corr)
        if r >= 1.0:
            return False  # Perfect correlation → not independent

        # Fisher z-transform
        z_stat = 0.5 * math.log((1.0 + r) / (1.0 - r)) * math.sqrt(dof)

        # Critical value from normal distribution
        z_crit = self._normal_critical_value(self.alpha)

        return abs(z_stat) < z_crit

    @staticmethod
    def _normal_critical_value(alpha: float) -> float:
        """Approximate critical value for two-tailed normal test.

        Uses rational approximation (Abramowitz & Stegun 26.2.23).
        Accurate to ~4.5e-4 for standard alpha values.
        """
        p = alpha / 2.0  # Two-tailed
        if p <= 0 or p >= 0.5:
            return 1.96  # Default

        t = math.sqrt(-2.0 * math.log(p))
        # Rational approximation constants
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
        return z

    def _compute_confidence(self, strength: float, n_samples: int) -> float:
        """Compute confidence score for a discovered edge.

        Based on correlation strength and sample size.
        More samples + stronger correlation = higher confidence.
        """
        # Sample size factor: saturates around 30 samples
        size_factor = min(1.0, n_samples / 30.0)
        # Strength factor: stronger correlation = higher confidence
        strength_factor = min(1.0, abs(strength))
        # Combined: geometric mean
        return math.sqrt(size_factor * strength_factor)

    @staticmethod
    def _combinations(items: List[int], size: int):
        """Generate all combinations of given size (deterministic order)."""
        if size == 0:
            yield ()
            return
        items = sorted(items)  # Deterministic order
        n = len(items)
        if size > n:
            return
        indices = list(range(size))
        yield tuple(items[i] for i in indices)
        while True:
            # Find rightmost index that can be incremented
            found = -1
            for i in range(size - 1, -1, -1):
                if indices[i] != i + n - size:
                    found = i
                    break
            if found == -1:
                return
            indices[found] += 1
            for i in range(found + 1, size):
                indices[i] = indices[i - 1] + 1
            yield tuple(items[i] for i in indices)

    @staticmethod
    def _would_create_cycle_in_directed(
        directed: List[List[Optional[bool]]],
        n: int,
        source: int,
        target: int,
    ) -> bool:
        """Check if adding source→target creates a cycle in directed edges."""
        # BFS from target following directed edges to see if we reach source
        visited: Set[int] = set()
        queue = [target]
        while queue:
            current = queue.pop(0)
            if current == source:
                return True
            if current in visited:
                continue
            visited.add(current)
            for next_node in range(n):
                if directed[current][next_node] is True:
                    queue.append(next_node)
        return False
