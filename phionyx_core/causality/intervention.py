"""
Intervention Model — v4 §3 (AGI Layer 3)
==========================================

Simulates do-calculus style interventions on a causal graph.
Given do(X=x), cuts all incoming edges to X and propagates
the forced value through downstream effects.

Key concepts:
- do(X=x): Force variable X to value x, breaking natural causes
- Propagation: Effects ripple through the causal graph
- Counterfactual seed: "What would happen if X were different?"

Integrates with:
- causality/causal_graph.py (CausalGraph, CausalNode, CausalEdge)
- contracts/v4/world_state_snapshot.py (causal_graph field)
"""

import logging
from dataclasses import dataclass
from typing import Any

from .causal_graph import CausalGraph

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
attenuation_rate = 0.8
min_effect_threshold = 0.01
max_propagation_depth = 10


@dataclass
class InterventionEffect:
    """Effect of an intervention on a single node."""
    node_id: str
    original_value: float | None
    new_value: float
    delta: float
    causal_path: list[str]  # path from intervention to this node
    attenuation: float  # how much the effect was attenuated along the path


@dataclass
class InterventionResult:
    """Full result of a do(X=x) intervention."""
    intervention_variable: str
    intervention_value: float
    original_value: float | None
    effects: list[InterventionEffect]
    total_nodes_affected: int
    max_propagation_depth: int
    graph_snapshot: dict[str, Any]  # post-intervention state

    def get_effect(self, node_id: str) -> InterventionEffect | None:
        """Get effect on a specific node."""
        for e in self.effects:
            if e.node_id == node_id:
                return e
        return None

    @property
    def affected_node_ids(self) -> set[str]:
        return {e.node_id for e in self.effects}

    def to_dict(self) -> dict[str, Any]:
        return {
            "intervention": {
                "variable": self.intervention_variable,
                "value": self.intervention_value,
                "original": self.original_value,
            },
            "effects": [
                {
                    "node": e.node_id,
                    "original": e.original_value,
                    "new": round(e.new_value, 4),
                    "delta": round(e.delta, 4),
                    "path": e.causal_path,
                    "attenuation": round(e.attenuation, 4),
                }
                for e in self.effects
            ],
            "total_affected": self.total_nodes_affected,
            "max_depth": self.max_propagation_depth,
        }


class InterventionModel:
    """
    Simulate do-calculus interventions on a causal graph.

    do(X=x) operation:
    1. Set X to value x
    2. Cut all incoming edges to X (remove natural causes)
    3. Propagate effects to all descendants of X
    4. Return the new state of all affected variables

    Effect propagation formula:
        effect_on_child = parent_delta * edge_strength * attenuation_factor

    Usage:
        model = InterventionModel(causal_graph)
        result = model.do("entropy", 0.9)
        for effect in result.effects:
            print(f"{effect.node_id}: {effect.original_value} → {effect.new_value}")
    """

    def __init__(
        self,
        graph: CausalGraph,
        attenuation_rate: float = attenuation_rate,
        min_effect_threshold: float = min_effect_threshold,
        max_propagation_depth: int = max_propagation_depth,
    ):
        """
        Args:
            graph: The causal graph to simulate on
            attenuation_rate: Effect multiplier per hop (0.8 = 20% loss per hop)
            min_effect_threshold: Minimum delta to continue propagation
            max_propagation_depth: Maximum hops from intervention node
        """
        self.graph = graph
        self.attenuation_rate = max(0.0, min(1.0, attenuation_rate))
        self.min_effect_threshold = min_effect_threshold
        self.max_propagation_depth = max_propagation_depth

    def do(
        self,
        variable: str,
        value: float,
    ) -> InterventionResult:
        """
        Perform do(variable=value) intervention.

        Args:
            variable: Node ID to intervene on
            value: Forced value

        Returns:
            InterventionResult with all downstream effects
        """
        if variable not in self.graph.nodes:
            return InterventionResult(
                intervention_variable=variable,
                intervention_value=value,
                original_value=None,
                effects=[],
                total_nodes_affected=0,
                max_propagation_depth=0,
                graph_snapshot={},
            )

        node = self.graph.nodes[variable]
        original_value = node.current_value
        delta = value - (original_value or 0.0)

        # Propagate effects through descendants
        effects: list[InterventionEffect] = []
        max_depth = 0

        if abs(delta) >= self.min_effect_threshold:
            effects, max_depth = self._propagate(
                source_id=variable,
                source_delta=delta,
                path=[variable],
                depth=0,
                visited=set(),
            )

        # Build post-intervention snapshot
        snapshot = self._build_snapshot(variable, value, effects)

        return InterventionResult(
            intervention_variable=variable,
            intervention_value=value,
            original_value=original_value,
            effects=effects,
            total_nodes_affected=len(effects),
            max_propagation_depth=max_depth,
            graph_snapshot=snapshot,
        )

    def simulate_multiple(
        self,
        interventions: dict[str, float],
    ) -> dict[str, InterventionResult]:
        """
        Simulate multiple simultaneous interventions.

        Args:
            interventions: {variable: value} dict

        Returns:
            Dict of results keyed by variable
        """
        results = {}
        for var, val in interventions.items():
            results[var] = self.do(var, val)
        return results

    def estimate_total_effect(
        self,
        source: str,
        target: str,
    ) -> float:
        """
        Estimate total causal effect of source on target.

        Sums effect through all directed paths, accounting for
        attenuation and edge strengths.

        Args:
            source: Cause variable
            target: Effect variable

        Returns:
            Total effect strength (0.0 = no effect)
        """
        if source not in self.graph.nodes or target not in self.graph.nodes:
            return 0.0

        # Find all directed paths from source to target
        paths = self._find_all_paths(source, target)
        if not paths:
            return 0.0

        # Sum path strengths
        total = 0.0
        for path in paths:
            path_strength = 1.0
            for i in range(len(path) - 1):
                edge = self.graph.get_edge(path[i], path[i + 1])
                if edge:
                    path_strength *= edge.effective_strength
                else:
                    path_strength = 0.0
                    break
            # Apply attenuation per hop
            hops = len(path) - 1
            path_strength *= self.attenuation_rate ** (hops - 1) if hops > 1 else 1.0
            total += path_strength

        return min(1.0, total)

    def identify_confounders(
        self,
        cause: str,
        effect: str,
    ) -> list[str]:
        """
        Identify potential confounding variables between cause and effect.

        A confounder is a common ancestor of both cause and effect.
        """
        if cause not in self.graph.nodes or effect not in self.graph.nodes:
            return []

        ancestors_cause = self.graph.get_ancestors(cause)
        ancestors_effect = self.graph.get_ancestors(effect)
        return sorted(ancestors_cause & ancestors_effect)

    def _propagate(
        self,
        source_id: str,
        source_delta: float,
        path: list[str],
        depth: int,
        visited: set[str],
    ) -> tuple[list[InterventionEffect], int]:
        """Recursively propagate intervention effects."""
        if depth >= self.max_propagation_depth:
            return [], depth

        effects = []
        max_depth = depth
        children = self.graph.get_children(source_id)

        for child_id in children:
            if child_id in visited:
                continue

            edge = self.graph.get_edge(source_id, child_id)
            if not edge:
                continue

            # Calculate effect on child
            child_delta = source_delta * edge.effective_strength * self.attenuation_rate
            if abs(child_delta) < self.min_effect_threshold:
                continue

            child_node = self.graph.nodes.get(child_id)
            original = child_node.current_value if child_node else None
            new_value = (original or 0.0) + child_delta

            effect = InterventionEffect(
                node_id=child_id,
                original_value=original,
                new_value=new_value,
                delta=child_delta,
                causal_path=path + [child_id],
                attenuation=self.attenuation_rate ** (depth + 1),
            )
            effects.append(effect)

            # Recurse into descendants
            visited.add(child_id)
            sub_effects, sub_depth = self._propagate(
                source_id=child_id,
                source_delta=child_delta,
                path=path + [child_id],
                depth=depth + 1,
                visited=visited,
            )
            effects.extend(sub_effects)
            max_depth = max(max_depth, sub_depth)

        return effects, max_depth

    def _find_all_paths(
        self,
        source: str,
        target: str,
        max_length: int = 5,
    ) -> list[list[str]]:
        """Find all directed paths from source to target (bounded)."""
        paths: list[list[str]] = []

        def _dfs(current: str, path: list[str]):
            if len(path) > max_length + 1:
                return
            if current == target:
                paths.append(list(path))
                return
            for child in self.graph.get_children(current):
                if child not in path:  # avoid cycles
                    path.append(child)
                    _dfs(child, path)
                    path.pop()

        _dfs(source, [source])
        return paths

    def _build_snapshot(
        self,
        intervention_var: str,
        intervention_val: float,
        effects: list[InterventionEffect],
    ) -> dict[str, Any]:
        """Build post-intervention state snapshot."""
        snapshot: dict[str, Any] = {}
        for nid, node in self.graph.nodes.items():
            snapshot[nid] = node.current_value
        # Apply intervention
        snapshot[intervention_var] = intervention_val
        # Apply effects
        for e in effects:
            snapshot[e.node_id] = e.new_value
        return snapshot
