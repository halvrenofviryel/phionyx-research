"""
Root Cause Analyzer — v4 §3 (AGI Layer 3)
===========================================

Given an observed anomaly, traces back through the causal graph
to identify the most likely root cause(s).

Algorithm:
1. Start from the anomalous node
2. Walk backwards through parents
3. Score each ancestor by: causal strength * anomaly magnitude * path attenuation
4. Rank by likelihood

Integrates with:
- causality/causal_graph.py (CausalGraph)
- causality/intervention.py (InterventionModel — for verification)
"""

import logging
from dataclasses import dataclass
from typing import Any

from .causal_graph import CausalGraph, CausalNode

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
rca_attenuation_rate = 0.85
rca_max_depth = 8
rca_min_likelihood = 0.05


@dataclass
class RootCauseCandidate:
    """A potential root cause for an observed anomaly."""
    node_id: str
    name: str
    likelihood: float    # 0.0-1.0: how likely this is the root cause
    causal_path: list[str]  # path from root cause to anomaly
    path_strength: float   # product of edge strengths along path
    anomaly_score: float   # how anomalous this node's value is
    current_value: float | None
    expected_value: float | None


@dataclass
class RootCauseAnalysis:
    """Full root cause analysis result."""
    anomaly_node: str
    anomaly_value: float | None
    expected_range: tuple[float, float]
    candidates: list[RootCauseCandidate]
    top_cause: RootCauseCandidate | None
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly": {
                "node": self.anomaly_node,
                "value": self.anomaly_value,
                "expected_range": list(self.expected_range),
            },
            "candidates": [
                {
                    "node": c.node_id,
                    "name": c.name,
                    "likelihood": round(c.likelihood, 4),
                    "path": c.causal_path,
                    "path_strength": round(c.path_strength, 4),
                    "anomaly_score": round(c.anomaly_score, 4),
                    "current": c.current_value,
                    "expected": c.expected_value,
                }
                for c in self.candidates
            ],
            "top_cause": self.top_cause.node_id if self.top_cause else None,
            "reasoning": self.reasoning,
        }


class RootCauseAnalyzer:
    """
    Trace anomalies back to root causes.

    Usage:
        analyzer = RootCauseAnalyzer(causal_graph)
        result = analyzer.analyze(
            anomaly_node="coherence",
            anomaly_value=0.1,
            expected_range=(0.5, 0.9),
        )
        print(f"Root cause: {result.top_cause.name}")
    """

    def __init__(
        self,
        graph: CausalGraph,
        attenuation_rate: float = rca_attenuation_rate,
        max_depth: int = rca_max_depth,
        min_likelihood: float = rca_min_likelihood,
    ):
        """
        Args:
            graph: Causal graph to analyze
            attenuation_rate: Strength decay per hop backwards
            max_depth: Maximum depth to search for causes
            min_likelihood: Minimum likelihood to include as candidate
        """
        self.graph = graph
        self.attenuation_rate = attenuation_rate
        self.max_depth = max_depth
        self.min_likelihood = min_likelihood

    def analyze(
        self,
        anomaly_node: str,
        anomaly_value: float | None = None,
        expected_range: tuple[float, float] = (0.3, 0.7),
    ) -> RootCauseAnalysis:
        """
        Analyze root cause of an anomaly.

        Args:
            anomaly_node: Node where anomaly was observed
            anomaly_value: Observed anomalous value (or use current_value)
            expected_range: Expected normal range (min, max)

        Returns:
            RootCauseAnalysis with ranked candidates
        """
        if anomaly_node not in self.graph.nodes:
            return RootCauseAnalysis(
                anomaly_node=anomaly_node,
                anomaly_value=anomaly_value,
                expected_range=expected_range,
                candidates=[],
                top_cause=None,
                reasoning=f"Node '{anomaly_node}' not found in causal graph",
            )

        node = self.graph.nodes[anomaly_node]
        if anomaly_value is None:
            anomaly_value = node.current_value

        # Calculate anomaly magnitude
        anomaly_magnitude = self._anomaly_magnitude(
            anomaly_value, expected_range
        )

        # Find all ancestor candidates
        candidates = self._find_candidates(
            anomaly_node=anomaly_node,
            anomaly_magnitude=anomaly_magnitude,
            expected_range=expected_range,
        )

        # Sort by likelihood
        candidates.sort(key=lambda c: c.likelihood, reverse=True)

        # Filter below minimum
        candidates = [c for c in candidates if c.likelihood >= self.min_likelihood]

        top_cause = candidates[0] if candidates else None
        reasoning = self._build_reasoning(anomaly_node, anomaly_value, expected_range, top_cause)

        return RootCauseAnalysis(
            anomaly_node=anomaly_node,
            anomaly_value=anomaly_value,
            expected_range=expected_range,
            candidates=candidates,
            top_cause=top_cause,
            reasoning=reasoning,
        )

    def _find_candidates(
        self,
        anomaly_node: str,
        anomaly_magnitude: float,
        expected_range: tuple[float, float],
    ) -> list[RootCauseCandidate]:
        """Walk backward through causal graph to find root cause candidates."""
        candidates: list[RootCauseCandidate] = []
        visited: set[str] = set()

        def _walk_back(
            current: str,
            path: list[str],
            cumulative_strength: float,
            depth: int,
        ):
            if depth > self.max_depth:
                return
            if current in visited:
                return
            visited.add(current)

            parents = self.graph.get_parents(current)

            # If no parents or is root — this is a potential root cause
            if not parents or depth > 0:
                node = self.graph.nodes.get(current)
                if node and depth > 0:
                    # Score this ancestor as potential cause
                    anomaly_score = self._node_anomaly_score(node, expected_range)
                    likelihood = cumulative_strength * max(anomaly_score, 0.1) * anomaly_magnitude
                    likelihood = min(1.0, likelihood)

                    candidates.append(RootCauseCandidate(
                        node_id=current,
                        name=node.name,
                        likelihood=likelihood,
                        causal_path=list(reversed(path)),
                        path_strength=cumulative_strength,
                        anomaly_score=anomaly_score,
                        current_value=node.current_value,
                        expected_value=node.mean_value,
                    ))

            # Walk further back
            for parent in parents:
                edge = self.graph.get_edge(parent, current)
                if edge:
                    new_strength = cumulative_strength * edge.effective_strength * self.attenuation_rate
                    if new_strength >= 0.01:
                        _walk_back(
                            parent,
                            path + [parent],
                            new_strength,
                            depth + 1,
                        )

        _walk_back(anomaly_node, [anomaly_node], 1.0, 0)
        return candidates

    def _anomaly_magnitude(
        self,
        value: float | None,
        expected_range: tuple[float, float],
    ) -> float:
        """How far is the value from the expected range?"""
        if value is None:
            return 0.5  # Unknown — moderate
        low, high = expected_range
        range_size = max(high - low, 0.01)
        deviation = 0.0
        if value < low:
            deviation = (low - value) / range_size
        elif value > high:
            deviation = (value - high) / range_size
        return min(1.0, deviation)

    def _node_anomaly_score(
        self,
        node: CausalNode,
        expected_range: tuple[float, float],
    ) -> float:
        """Score how anomalous this node is."""
        if node.current_value is None:
            return 0.3

        mean = node.mean_value
        if mean is None:
            return 0.3

        # If node has multiple observations, check deviation from own mean
        if len(node.observed_values) >= 2:
            values = node.observed_values
            avg = sum(values) / len(values)
            std = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
            if std > 0:
                z_score = abs(node.current_value - avg) / std
                return min(1.0, z_score / 3.0)  # Normalize: 3σ = 1.0

        # Fallback: check against expected range
        return self._anomaly_magnitude(node.current_value, expected_range)

    def _build_reasoning(
        self,
        anomaly_node: str,
        anomaly_value: float | None,
        expected_range: tuple[float, float],
        top_cause: RootCauseCandidate | None,
    ) -> str:
        if not top_cause:
            return f"No root cause found for anomaly in {anomaly_node}"

        return (
            f"Anomaly in {anomaly_node} (value={anomaly_value}, "
            f"expected={expected_range[0]}-{expected_range[1]}). "
            f"Most likely root cause: {top_cause.name} "
            f"(likelihood={top_cause.likelihood:.2f}, "
            f"path={' → '.join(top_cause.causal_path)})"
        )
