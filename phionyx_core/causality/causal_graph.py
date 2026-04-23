"""
Causal Graph Builder — v4 §3 (AGI Layer 3)
=============================================

Builds directed acyclic causal graphs from observed co-occurrences
and explicit causal annotations. Integrates with GraphEngine's
EdgeType.CAUSES and EdgeType.INFLUENCES typed relations.

Key concepts:
- CausalNode: A variable in the causal model (e.g., "user_anger", "entropy")
- CausalEdge: Directed causal link A → B with strength and mechanism
- CausalGraph: The full DAG with topological operations

Populates WorldStateSnapshot.causal_graph field.

Integrates with:
- intuition/graph_engine.py (EdgeType.CAUSES, get_causal_subgraph)
- contracts/v4/world_state_snapshot.py (causal_graph field)
"""

import json
import logging
import math
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ── Tunable Parameters (Tier A: Research Engine may modify) ──
default_confidence = 0.75
default_strength = 0.75
pc_alpha = 0.05
pc_min_observations = 20
pc_max_conditioning_size = 3


class NodeType(str, Enum):
    """Type of causal node."""
    STATE = "state"           # Internal state variable (phi, entropy, valence)
    INPUT = "input"           # External input (user message, sensor)
    OUTPUT = "output"         # System output (response, action)
    LATENT = "latent"         # Unobserved/inferred variable
    INTERVENTION = "intervention"  # Externally forced variable


class MechanismType(str, Enum):
    """How the causal effect operates."""
    DIRECT = "direct"         # A directly causes B
    MEDIATED = "mediated"     # A causes B through intermediary
    MODERATED = "moderated"   # A's effect on B depends on C
    OBSERVED = "observed"     # Observed co-occurrence (not yet confirmed causal)


@dataclass
class CausalNode:
    """A variable in the causal graph."""
    node_id: str
    name: str
    node_type: str = NodeType.STATE.value
    observed_values: List[float] = field(default_factory=list)
    current_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def mean_value(self) -> Optional[float]:
        if not self.observed_values:
            return self.current_value
        return sum(self.observed_values) / len(self.observed_values)


@dataclass
class CausalEdge:
    """A directed causal link from cause to effect."""
    source_id: str
    target_id: str
    strength: float = default_strength     # 0.0-1.0: how strong the causal effect
    confidence: float = default_confidence   # 0.0-1.0: how confident we are this is causal
    mechanism: str = MechanismType.OBSERVED.value
    observations: int = 1     # How many times this was observed
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def effective_strength(self) -> float:
        """Strength weighted by confidence."""
        return self.strength * self.confidence


@dataclass
class CausalGraph:
    """A complete causal model as a directed graph."""
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: Dict[str, CausalEdge] = field(default_factory=dict)  # key: "source->target"

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def get_parents(self, node_id: str) -> List[str]:
        """Get direct causes of a node."""
        return [
            e.source_id for e in self.edges.values()
            if e.target_id == node_id
        ]

    def get_children(self, node_id: str) -> List[str]:
        """Get direct effects of a node."""
        return [
            e.target_id for e in self.edges.values()
            if e.source_id == node_id
        ]

    def get_edge(self, source_id: str, target_id: str) -> Optional[CausalEdge]:
        """Get edge between two nodes."""
        key = f"{source_id}->{target_id}"
        return self.edges.get(key)

    def has_cycle(self) -> bool:
        """Check if graph has cycles (should be DAG)."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for child in self.get_children(node_id):
                if child not in visited:
                    if _dfs(child):
                        return True
                elif child in rec_stack:
                    return True
            rec_stack.discard(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if _dfs(node_id):
                    return True
        return False

    def topological_order(self) -> List[str]:
        """Return nodes in topological order (causes before effects)."""
        if self.has_cycle():
            return list(self.nodes.keys())  # Fallback: arbitrary order

        in_degree: Dict[str, int] = dict.fromkeys(self.nodes, 0)
        for e in self.edges.values():
            if e.target_id in in_degree:
                in_degree[e.target_id] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for child in self.get_children(node):
                if child in in_degree:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
        return order

    def get_ancestors(self, node_id: str) -> Set[str]:
        """Get all transitive causes of a node."""
        ancestors: Set[str] = set()
        stack = list(self.get_parents(node_id))
        while stack:
            current = stack.pop()
            if current not in ancestors:
                ancestors.add(current)
                stack.extend(self.get_parents(current))
        return ancestors

    def get_descendants(self, node_id: str) -> Set[str]:
        """Get all transitive effects of a node."""
        descendants: Set[str] = set()
        stack = list(self.get_children(node_id))
        while stack:
            current = stack.pop()
            if current not in descendants:
                descendants.add(current)
                stack.extend(self.get_children(current))
        return descendants

    def to_dict(self) -> Dict[str, Any]:
        """Serialize causal graph (complete, for cross-session persistence)."""
        return {
            "nodes": {
                nid: {
                    "name": n.name,
                    "type": n.node_type,
                    "current_value": n.current_value,
                    "observed_values": list(n.observed_values),
                    "metadata": dict(n.metadata),
                }
                for nid, n in self.nodes.items()
            },
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "strength": e.strength,
                    "confidence": e.confidence,
                    "mechanism": e.mechanism,
                    "observations": e.observations,
                    "metadata": dict(e.metadata),
                }
                for e in self.edges.values()
            ],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalGraph":
        """Restore causal graph from serialized data."""
        graph = cls()
        for nid, ndata in data.get("nodes", {}).items():
            graph.nodes[nid] = CausalNode(
                node_id=nid,
                name=ndata.get("name", nid),
                node_type=ndata.get("type", NodeType.STATE.value),
                current_value=ndata.get("current_value"),
                observed_values=list(ndata.get("observed_values", [])),
                metadata=dict(ndata.get("metadata", {})),
            )
        for edata in data.get("edges", []):
            src = edata["source"]
            tgt = edata["target"]
            key = f"{src}->{tgt}"
            graph.edges[key] = CausalEdge(
                source_id=src,
                target_id=tgt,
                strength=edata.get("strength", default_strength),
                confidence=edata.get("confidence", default_confidence),
                mechanism=edata.get("mechanism", MechanismType.OBSERVED.value),
                observations=edata.get("observations", 1),
                metadata=dict(edata.get("metadata", {})),
            )
        return graph


class CausalGraphBuilder:
    """
    Builds causal graphs from observations and explicit annotations.

    Two modes of operation:
    1. **Explicit**: Add known causal relationships (from domain knowledge)
    2. **Observational**: Track co-occurrence patterns and promote to causal
       when strength exceeds threshold

    Usage:
        builder = CausalGraphBuilder()
        builder.add_node("entropy", node_type="state")
        builder.add_node("coherence", node_type="state")
        builder.add_causal_link("entropy", "coherence", strength=0.8)
        graph = builder.build()

    From GraphEngine:
        builder = CausalGraphBuilder()
        builder.import_from_graph_engine(graph_engine)
        graph = builder.build()
    """

    def __init__(
        self,
        promotion_threshold: float = 0.6,
        min_observations: int = 3,
        max_nodes: int = 500,
    ):
        """
        Args:
            promotion_threshold: Min strength to promote observed→direct
            min_observations: Min observations to promote observed→direct
            max_nodes: Maximum nodes in graph (prevents unbounded growth)
        """
        self.promotion_threshold = promotion_threshold
        self.min_observations = min_observations
        self.max_nodes = max_nodes
        self._graph = CausalGraph()
        self._session_id: str = ""
        self._auto_save_enabled: bool = False
        self._auto_save_path: str = "data/causal_graph"

    def set_session(self, session_id: str) -> None:
        """Set current session context."""
        self._session_id = session_id

    def enable_auto_save(self, base_path: str = "data/causal_graph") -> None:
        """Enable auto-save: mutating methods will persist the graph after each change."""
        self._auto_save_enabled = True
        self._auto_save_path = base_path

    def disable_auto_save(self) -> None:
        """Disable auto-save."""
        self._auto_save_enabled = False

    def _trigger_auto_save(self) -> None:
        """Called after each mutation if auto-save is enabled."""
        if self._auto_save_enabled:
            self.auto_save(self._auto_save_path)

    def auto_save(self, base_path: str = "data/causal_graph") -> Optional[str]:
        """Auto-save causal graph to JSON for cross-session persistence."""
        if not self._session_id:
            logger.warning("Cannot auto-save CausalGraph: no session_id set")
            return None

        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"{self._session_id}.json"

        try:
            data = {
                "session_id": self._session_id,
                "promotion_threshold": self.promotion_threshold,
                "min_observations": self.min_observations,
                "max_nodes": self.max_nodes,
                "graph": self._graph.to_dict(),
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("CausalGraph auto-saved to %s", file_path)
            return str(file_path)
        except (OSError, TypeError) as e:
            logger.error("CausalGraph auto-save failed: %s", e)
            return None

    @classmethod
    def auto_load(cls, session_id: str, base_path: str = "data/causal_graph") -> Optional["CausalGraphBuilder"]:
        """Auto-load causal graph from JSON for session continuity."""
        file_path = Path(base_path) / f"{session_id}.json"

        if not file_path.exists():
            logger.debug("No saved CausalGraph for session %s", session_id)
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            builder = cls(
                promotion_threshold=data.get("promotion_threshold", 0.6),
                min_observations=data.get("min_observations", 3),
                max_nodes=data.get("max_nodes", 500),
            )
            builder._session_id = data.get("session_id", "")
            builder._graph = CausalGraph.from_dict(data.get("graph", {}))
            logger.info("CausalGraph auto-loaded from %s (%d nodes, %d edges)",
                        file_path, builder._graph.node_count, builder._graph.edge_count)
            return builder
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("CausalGraph auto-load failed for %s: %s", file_path, e)
            return None

    def add_node(
        self,
        node_id: str,
        name: Optional[str] = None,
        node_type: str = NodeType.STATE.value,
        current_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CausalNode:
        """Add or update a node in the causal graph."""
        if node_id in self._graph.nodes:
            node = self._graph.nodes[node_id]
            if current_value is not None:
                node.current_value = current_value
                node.observed_values.append(current_value)
            return node

        if len(self._graph.nodes) >= self.max_nodes:
            logger.warning(f"Max nodes ({self.max_nodes}) reached, ignoring {node_id}")
            return CausalNode(node_id=node_id, name=name or node_id)

        node = CausalNode(
            node_id=node_id,
            name=name or node_id,
            node_type=node_type,
            current_value=current_value,
            observed_values=[current_value] if current_value is not None else [],
            metadata=metadata or {},
        )
        self._graph.nodes[node_id] = node
        self._trigger_auto_save()
        return node

    def add_causal_link(
        self,
        source_id: str,
        target_id: str,
        strength: float = default_strength,
        confidence: float = 0.8,
        mechanism: str = MechanismType.DIRECT.value,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CausalEdge]:
        """
        Add a causal link A → B.

        Auto-creates nodes if they don't exist.
        If edge already exists, updates strength using EMA.
        Rejects edges that would create cycles.
        """
        # Auto-create nodes
        if source_id not in self._graph.nodes:
            self.add_node(source_id)
        if target_id not in self._graph.nodes:
            self.add_node(target_id)

        # Reject self-loops
        if source_id == target_id:
            return None

        key = f"{source_id}->{target_id}"

        # Check for cycle: would adding this edge create one?
        if self._would_create_cycle(source_id, target_id):
            logger.debug(f"Rejected {key}: would create cycle")
            return None

        strength = max(0.0, min(1.0, strength))
        confidence = max(0.0, min(1.0, confidence))

        if key in self._graph.edges:
            # Update existing edge with EMA
            edge = self._graph.edges[key]
            alpha = 0.3  # EMA smoothing
            edge.strength = alpha * strength + (1 - alpha) * edge.strength
            edge.confidence = alpha * confidence + (1 - alpha) * edge.confidence
            edge.observations += 1
            # Promote mechanism if enough evidence
            if (
                edge.mechanism == MechanismType.OBSERVED.value
                and edge.observations >= self.min_observations
                and edge.strength >= self.promotion_threshold
            ):
                edge.mechanism = MechanismType.DIRECT.value
            self._trigger_auto_save()
            return edge

        edge = CausalEdge(
            source_id=source_id,
            target_id=target_id,
            strength=strength,
            confidence=confidence,
            mechanism=mechanism,
            observations=1,
            metadata=metadata or {},
        )
        self._graph.edges[key] = edge
        self._trigger_auto_save()
        return edge

    def observe_co_occurrence(
        self,
        variable_a: str,
        variable_b: str,
        value_a: Optional[float] = None,
        value_b: Optional[float] = None,
        direction_hint: Optional[str] = None,
    ) -> Optional[CausalEdge]:
        """
        Record that two variables co-occurred.

        With enough observations and correlation, promotes to causal.

        Args:
            variable_a: First variable
            variable_b: Second variable
            value_a: Observed value of A
            value_b: Observed value of B
            direction_hint: "a->b", "b->a", or None (both directions tracked)
        """
        # Update node values
        if value_a is not None:
            self.add_node(variable_a, current_value=value_a)
        else:
            self.add_node(variable_a)
        if value_b is not None:
            self.add_node(variable_b, current_value=value_b)
        else:
            self.add_node(variable_b)

        # Determine direction
        if direction_hint == "a->b":
            source, target = variable_a, variable_b
        elif direction_hint == "b->a":
            source, target = variable_b, variable_a
        else:
            # Default: alphabetical order for consistency
            source, target = sorted([variable_a, variable_b])

        # Estimate strength from correlation of observed values
        strength = self._estimate_correlation(source, target)

        return self.add_causal_link(
            source_id=source,
            target_id=target,
            strength=strength,
            confidence=0.3,  # Low confidence for observations
            mechanism=MechanismType.OBSERVED.value,
        )

    def import_from_graph_engine_edges(
        self, causal_edges: List[Tuple[str, str, Dict]]
    ) -> int:
        """
        Import causal edges from GraphEngine.get_causal_subgraph().

        Args:
            causal_edges: List of (source_id, target_id, edge_data) tuples

        Returns:
            Number of edges imported
        """
        count = 0
        for source_id, target_id, data in causal_edges:
            weight = data.get("weight", 0.5)
            edge_type = data.get("edge_type", "causes")
            mechanism = (
                MechanismType.DIRECT.value
                if edge_type == "causes"
                else MechanismType.MEDIATED.value
            )
            edge = self.add_causal_link(
                source_id=source_id,
                target_id=target_id,
                strength=weight,
                confidence=0.7,
                mechanism=mechanism,
            )
            if edge:
                count += 1
        return count

    def add_physics_variables(
        self,
        echo_state: Dict[str, Any],
    ) -> None:
        """
        Add Phionyx physics state variables as causal nodes.

        Known causal relationships in Phionyx physics:
        - entropy → coherence (negative: high entropy reduces coherence)
        - phi → resonance (positive: high phi increases resonance)
        - valence → amplitude (positive: emotional valence affects response intensity)
        - arousal → entropy (positive: high arousal increases entropy)
        """
        # Add state variable nodes
        physics_vars = ["phi", "entropy", "coherence", "valence", "arousal",
                        "amplitude", "resonance", "drift"]
        for var in physics_vars:
            val = echo_state.get(var) or echo_state.get(var.upper())
            if val is not None:
                self.add_node(var, node_type=NodeType.STATE.value, current_value=float(val))

        # Add known causal links from Phionyx physics formulas
        known_links = [
            ("entropy", "coherence", 0.85, MechanismType.DIRECT.value),
            ("phi", "resonance", 0.75, MechanismType.DIRECT.value),
            ("valence", "amplitude", 0.6, MechanismType.DIRECT.value),
            ("arousal", "entropy", 0.7, MechanismType.DIRECT.value),
            ("coherence", "drift", 0.65, MechanismType.DIRECT.value),
            ("phi", "amplitude", 0.5, MechanismType.MEDIATED.value),
        ]
        for source, target, strength, mechanism in known_links:
            if source in self._graph.nodes and target in self._graph.nodes:
                self.add_causal_link(
                    source, target,
                    strength=strength,
                    confidence=0.95,  # High confidence — from formulas
                    mechanism=mechanism,
                )

    def discover_structure(
        self,
        min_observations: Optional[int] = None,
        alpha: Optional[float] = None,
        max_conditioning_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run PC algorithm for causal structure discovery on accumulated observations.

        Only triggers when sufficient observations have been collected.
        Discovered edges are merged into the existing graph with 'observed' mechanism.

        Args:
            min_observations: Minimum observations per node before discovery runs.
                              Defaults to module-level pc_min_observations.
            alpha: Significance level for independence tests.
                   Defaults to module-level pc_alpha.
            max_conditioning_size: Maximum conditioning set size for PC algorithm.
                                   Defaults to module-level pc_max_conditioning_size.

        Returns:
            Dict with keys: triggered, edges_added, edges_total, reason
        """
        if min_observations is None:
            min_observations = pc_min_observations
        if alpha is None:
            alpha = pc_alpha
        if max_conditioning_size is None:
            max_conditioning_size = pc_max_conditioning_size

        # Count eligible nodes (those with enough observations)
        eligible_nodes = [
            nid for nid, node in self._graph.nodes.items()
            if len(node.observed_values) >= min_observations
        ]

        if len(eligible_nodes) < 2:
            return {
                "triggered": False,
                "edges_added": 0,
                "edges_total": self._graph.edge_count,
                "reason": f"Need 2+ nodes with {min_observations}+ observations, have {len(eligible_nodes)}",
            }

        # Lazy import to avoid circular dependency
        from phionyx_core.causality.structure_learning import PCAlgorithm

        pc = PCAlgorithm(alpha=alpha, max_conditioning_size=max_conditioning_size)
        result = pc.discover(self._graph)

        edges_added = 0
        conflicts = []
        for edge in result.discovered_edges:
            # Check for conflicting existing edge (reverse direction)
            reverse_key = f"{edge.target_id}->{edge.source_id}"
            if reverse_key in self._graph.edges:
                conflicts.append((edge.source_id, edge.target_id))
                logger.warning(
                    "Discovery conflict: %s->%s discovered but %s->%s exists",
                    edge.source_id, edge.target_id, edge.target_id, edge.source_id,
                )
                continue

            added = self.add_causal_link(
                source_id=edge.source_id,
                target_id=edge.target_id,
                strength=edge.strength,
                confidence=edge.confidence,
                mechanism=edge.mechanism,
            )
            if added:
                edges_added += 1

        return {
            "triggered": True,
            "edges_added": edges_added,
            "edges_total": self._graph.edge_count,
            "conflicts": conflicts,
            "nodes_eligible": len(eligible_nodes),
            "reason": f"PC discovery ran on {len(eligible_nodes)} nodes, added {edges_added} edges",
        }

    def build(self) -> CausalGraph:
        """Return the constructed causal graph."""
        return self._graph

    def to_world_state_dict(self) -> Dict[str, Any]:
        """Serialize for WorldStateSnapshot.causal_graph field."""
        return self._graph.to_dict()

    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding source→target would create a cycle."""
        # If target can reach source, adding source→target creates cycle
        if source_id == target_id:
            return True
        return source_id in self._graph.get_descendants(target_id)

    def _estimate_correlation(self, var_a: str, var_b: str) -> float:
        """Estimate correlation strength from observed values."""
        node_a = self._graph.nodes.get(var_a)
        node_b = self._graph.nodes.get(var_b)
        if not node_a or not node_b:
            return 0.3

        vals_a = node_a.observed_values
        vals_b = node_b.observed_values
        if len(vals_a) < 2 or len(vals_b) < 2:
            return 0.3

        # Use overlapping observations
        n = min(len(vals_a), len(vals_b))
        a = vals_a[-n:]
        b = vals_b[-n:]

        # Pearson correlation (absolute value — direction from hint)
        mean_a = sum(a) / n
        mean_b = sum(b) / n
        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / n
        std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / n)
        std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / n)

        if std_a == 0 or std_b == 0:
            return 0.3

        correlation = abs(cov / (std_a * std_b))
        return min(1.0, correlation)
