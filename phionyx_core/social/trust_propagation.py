"""
Trust Propagation — v4 §5 (AGI Layer 5)
=========================================

Transitive trust computation. If A trusts B with strength 0.8
and B trusts C with strength 0.7, A's transitive trust in C is
computed via trust propagation with decay.

Trust formula:
    T(A→C) = max over all paths: product(edge_trust * decay^hop)

Properties:
- Trust decays with distance (configurable decay factor)
- Distrust propagates (trust < 0.5 = distrust)
- Trust is asymmetric: T(A→B) ≠ T(B→A)
- Self-trust is always 1.0

Integrates with:
- contracts/v4/confidence_payload.py (T_meta as self-trust)
- governance/rbac.py (role-based trust)
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
decay_factor = 0.9
trust_threshold = 0.5
max_path_length = 5
trust_ema_alpha = 0.3


@dataclass
class TrustEdge:
    """Direct trust relationship between two entities."""
    source: str
    target: str
    trust_level: float  # 0.0 (full distrust) to 1.0 (full trust)
    context: str = ""   # What domain this trust applies to
    observations: int = 1


@dataclass
class TrustAssessment:
    """Result of trust query."""
    source: str
    target: str
    direct_trust: Optional[float]   # Direct edge (None if no direct)
    transitive_trust: float          # Best trust via any path
    trust_path: List[str]            # Path that produced best trust
    is_trusted: bool                 # Above threshold?
    reasoning: str


class TrustNetwork:
    """
    Trust propagation network.

    Usage:
        net = TrustNetwork()
        net.add_trust("system", "user_A", 0.8)
        net.add_trust("user_A", "source_X", 0.7)
        assessment = net.query_trust("system", "source_X")
        # transitive trust ≈ 0.8 * 0.7 * decay
    """

    def __init__(
        self,
        decay_factor: float = decay_factor,
        trust_threshold: float = trust_threshold,
        max_path_length: int = max_path_length,
    ):
        """
        Args:
            decay_factor: Trust decay per hop (0.9 = 10% loss per hop)
            trust_threshold: Above this = trusted
            max_path_length: Maximum hops to search
        """
        self.decay_factor = max(0.0, min(1.0, decay_factor))
        self.trust_threshold = trust_threshold
        self.max_path_length = max_path_length
        self._edges: Dict[str, Dict[str, TrustEdge]] = {}  # source → {target → edge}
        self._entities: Set[str] = set()

    def add_trust(
        self,
        source: str,
        target: str,
        trust_level: float,
        context: str = "",
    ) -> TrustEdge:
        """Add or update a direct trust relationship."""
        trust_level = max(0.0, min(1.0, trust_level))
        self._entities.add(source)
        self._entities.add(target)

        if source not in self._edges:
            self._edges[source] = {}

        if target in self._edges[source]:
            # EMA update
            existing = self._edges[source][target]
            alpha = trust_ema_alpha
            existing.trust_level = alpha * trust_level + (1 - alpha) * existing.trust_level
            existing.observations += 1
            return existing

        edge = TrustEdge(
            source=source,
            target=target,
            trust_level=trust_level,
            context=context,
        )
        self._edges[source][target] = edge
        return edge

    def get_direct_trust(self, source: str, target: str) -> Optional[float]:
        """Get direct trust from source to target (None if no direct edge)."""
        if source == target:
            return 1.0
        edges = self._edges.get(source, {})
        edge = edges.get(target)
        return edge.trust_level if edge else None

    def query_trust(self, source: str, target: str) -> TrustAssessment:
        """
        Query trust from source to target, including transitive.

        Returns:
            TrustAssessment with direct and transitive trust
        """
        if source == target:
            return TrustAssessment(
                source=source,
                target=target,
                direct_trust=1.0,
                transitive_trust=1.0,
                trust_path=[source],
                is_trusted=True,
                reasoning="Self-trust is always 1.0",
            )

        direct = self.get_direct_trust(source, target)

        # Find best transitive trust via all paths
        best_trust, best_path = self._find_best_trust_path(source, target)

        # Direct trust overrides transitive if stronger
        if direct is not None and direct > best_trust:
            best_trust = direct
            best_path = [source, target]

        is_trusted = best_trust >= self.trust_threshold

        reasoning = self._build_reasoning(source, target, direct, best_trust, best_path, is_trusted)

        return TrustAssessment(
            source=source,
            target=target,
            direct_trust=direct,
            transitive_trust=best_trust,
            trust_path=best_path,
            is_trusted=is_trusted,
            reasoning=reasoning,
        )

    def get_trusted_entities(self, source: str) -> List[Tuple[str, float]]:
        """Get all entities trusted by source (above threshold)."""
        results = []
        for entity in self._entities:
            if entity == source:
                continue
            assessment = self.query_trust(source, entity)
            if assessment.is_trusted:
                results.append((entity, assessment.transitive_trust))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_trust_graph(self) -> Dict[str, Any]:
        """Serialize trust network."""
        return {
            "entities": sorted(self._entities),
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "trust": round(e.trust_level, 4),
                    "context": e.context,
                    "observations": e.observations,
                }
                for edges in self._edges.values()
                for e in edges.values()
            ],
            "entity_count": len(self._entities),
        }

    def _find_best_trust_path(
        self, source: str, target: str,
    ) -> Tuple[float, List[str]]:
        """Find path with highest trust from source to target."""
        best_trust = 0.0
        best_path: List[str] = []

        def _dfs(current: str, path: List[str], trust_so_far: float, depth: int):
            nonlocal best_trust, best_path
            if depth > self.max_path_length:
                return
            if current == target:
                if trust_so_far > best_trust:
                    best_trust = trust_so_far
                    best_path = list(path)
                return

            for next_entity, edge in self._edges.get(current, {}).items():
                if next_entity not in path:
                    new_trust = trust_so_far * edge.trust_level * self.decay_factor
                    if new_trust > best_trust:  # Prune: only if potentially better
                        path.append(next_entity)
                        _dfs(next_entity, path, new_trust, depth + 1)
                        path.pop()

        _dfs(source, [source], 1.0, 0)
        return best_trust, best_path

    def _build_reasoning(
        self,
        source: str,
        target: str,
        direct: Optional[float],
        transitive: float,
        path: List[str],
        is_trusted: bool,
    ) -> str:
        if direct is not None and direct >= transitive:
            return f"Direct trust {source}→{target}: {direct:.2f}"
        if path:
            return f"Transitive trust via {' → '.join(path)}: {transitive:.2f}"
        return f"No trust path found from {source} to {target}"
