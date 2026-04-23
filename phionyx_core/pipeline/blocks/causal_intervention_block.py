"""
Causal Intervention Block
==========================

Block: causal_intervention
Evaluates potential do-calculus interventions on the causal graph.
Identifies confounders and estimates effects of state changes.

Position in pipeline: After causal_graph_update.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class CausalInterventionBlock(PipelineBlock):
    """
    Causal Intervention Block (S3 Causality Foundations Sprint).

    Applies do-calculus interventions when strategy requires state correction.
    Estimates total effects and identifies confounders.
    """

    def __init__(self, intervention_model=None):
        """
        Args:
            intervention_model: InterventionModel instance (injected via DI)
        """
        super().__init__("causal_intervention")
        self._model = intervention_model

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._model is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No InterventionModel instance configured"}
            )

        try:
            _metadata = context.metadata or {}
            strategy = context.strategy or "normal"

            # Only run interventions when strategy requires correction
            if strategy not in ("stabilize", "comfort", "recovery"):
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"intervention_applied": False, "reason": f"Strategy '{strategy}' doesn't require intervention"}
                )

            # Determine intervention targets based on strategy
            interventions = {}
            if strategy == "stabilize":
                interventions["entropy"] = 0.3  # Lower entropy for stability
            elif strategy == "comfort":
                interventions["valence"] = 0.5  # Neutral valence
            elif strategy == "recovery":
                interventions["phi"] = 0.5  # Reset phi to baseline

            if not interventions:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"intervention_applied": False, "reason": "No interventions needed"}
                )

            # Apply interventions
            results = self._model.simulate_multiple(interventions)

            intervention_data = {}
            total_affected = 0
            for var, result in results.items():
                intervention_data[var] = {
                    "original_value": result.original_value,
                    "new_value": result.intervention_value,
                    "nodes_affected": result.total_nodes_affected,
                }
                total_affected += result.total_nodes_affected

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "intervention_applied": True,
                    "strategy": strategy,
                    "interventions": intervention_data,
                    "total_nodes_affected": total_affected,
                }
            )

        except Exception as e:
            logger.error(f"Causal intervention error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["causal_graph_update"]
