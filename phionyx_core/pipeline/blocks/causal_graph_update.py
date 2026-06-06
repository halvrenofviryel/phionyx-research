"""
Causal Graph Update Block
==========================

Block: causal_graph_update
Updates the causal graph with observations from the current turn.
Adds physics variables and co-occurrences from pipeline state.

Position in pipeline: After state_update_physics, before causal_intervention.
"""

import logging
from typing import Dict, List, Tuple

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)

# ── Observation Pairs (physics variable co-occurrences) ──
# 12 pairs covering all 8 physics variables: phi, entropy, coherence,
# valence, arousal, amplitude, resonance, drift.
# Deterministic: static list, same input → same output.
OBSERVATION_PAIRS: List[Tuple[str, str]] = [
    ("entropy", "coherence"),
    ("phi", "resonance"),
    ("valence", "amplitude"),
    ("arousal", "entropy"),
    ("coherence", "drift"),
    ("phi", "amplitude"),
    ("phi", "coherence"),
    ("entropy", "amplitude"),
    ("arousal", "amplitude"),
    ("valence", "coherence"),
    ("phi", "entropy"),
    ("valence", "arousal"),
]


class CausalGraphUpdateBlock(PipelineBlock):
    """
    Causal Graph Update Block (S3 Causality Foundations Sprint).

    Maintains a running causal DAG by:
    1. Adding physics variables from echo state
    2. Recording co-occurrences between state changes (12 pairs)
    3. Promoting strong correlations to causal links
    """

    def __init__(self, causal_graph_builder=None):
        """
        Args:
            causal_graph_builder: CausalGraphBuilder instance (injected via DI)
        """
        super().__init__("causal_graph_update")
        self._builder = causal_graph_builder

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._builder is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No CausalGraphBuilder instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Extract physics state for causal graph
            physics_state = metadata.get("physics_state", {})
            if physics_state:
                self._builder.add_physics_variables(physics_state)

            # Collect variable values from all sources
            var_values: Dict[str, float] = {}
            for var_name in ["phi", "entropy", "coherence", "valence",
                             "arousal", "amplitude", "resonance", "drift"]:
                val = physics_state.get(var_name)
                if val is not None:
                    var_values[var_name] = float(val)

            # Use precise phi/entropy from dedicated result dicts if available
            phi = metadata.get("phi_result", {})
            entropy = metadata.get("entropy_result", {})
            if isinstance(phi, dict):
                phi_val = phi.get("phi") or phi.get("phi_total")
                if phi_val is not None:
                    var_values["phi"] = float(phi_val)
            if isinstance(entropy, dict):
                entropy_val = entropy.get("entropy") or entropy.get("dynamic_entropy")
                if entropy_val is not None:
                    var_values["entropy"] = float(entropy_val)

            # Record co-occurrences for all pairs where both values are available
            pairs_observed = 0
            for var_a, var_b in OBSERVATION_PAIRS:
                val_a = var_values.get(var_a)
                val_b = var_values.get(var_b)
                if val_a is not None and val_b is not None:
                    self._builder.observe_co_occurrence(
                        var_a, var_b,
                        value_a=val_a, value_b=val_b,
                    )
                    pairs_observed += 1

            # Build current graph snapshot
            graph = self._builder.build()

            # Graph density: edge_count / max_possible_edges
            n = graph.node_count
            max_edges = n * (n - 1) if n > 1 else 1
            graph_density = graph.edge_count / max_edges if max_edges > 0 else 0.0

            result_data = {
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
                "pairs_observed": pairs_observed,
                "graph_density": round(graph_density, 4),
                "causal_graph": self._builder.to_world_state_dict(),
            }

            # Channel 2: Causal structure discovery (PC Algorithm)
            # Uses module-level defaults from causal_graph.py (PRE-tunable)
            try:
                discovery = self._builder.discover_structure()
                if discovery.get("triggered"):
                    logger.info(
                        f"[CAUSAL_DISCOVERY] {discovery.get('edges_added', 0)} new edges"
                    )
                    result_data["discovery"] = discovery
            except Exception as disc_err:
                logger.warning(f"[CAUSAL_DISCOVERY] skipped: {disc_err}")

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Causal graph update error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["state_update_physics"]
