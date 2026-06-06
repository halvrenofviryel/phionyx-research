"""
Counterfactual Analysis Block
==============================

Block: counterfactual_analysis
"What if" reasoning — analyzes how different inputs would have changed outcomes.

Position in pipeline: After causal_intervention, optional enrichment.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class CounterfactualAnalysisBlock(PipelineBlock):
    """
    Counterfactual Analysis Block (S4 Causality Advanced Sprint).

    Performs counterfactual reasoning when anomalies are detected.
    Answers: "What would have happened if X were different?"
    """

    def __init__(self, counterfactual_engine=None):
        """
        Args:
            counterfactual_engine: CounterfactualEngine instance (injected via DI)
        """
        super().__init__("counterfactual_analysis")
        self._engine = counterfactual_engine

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._engine is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No CounterfactualEngine instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Only run when anomalies or drift detected
            drift_result = metadata.get("drift_result", {})
            drift_detected = False
            if isinstance(drift_result, dict):
                drift_detected = drift_result.get("drift_detected", False)
            elif hasattr(drift_result, "drift_detected"):
                drift_detected = drift_result.drift_detected

            if not drift_detected:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"counterfactual_run": False, "reason": "No anomaly detected"}
                )

            # Identify the drifting variable
            physics_state = metadata.get("physics_state", {})
            _entropy = physics_state.get("entropy", 0.5)

            # "What if entropy were at baseline?"
            cf_result = self._engine.what_if(
                variable="entropy",
                counterfactual_value=0.3,
                context="drift_correction",
            )

            outcomes = []
            for outcome in cf_result.outcomes:
                outcomes.append({
                    "variable": outcome.variable,
                    "factual": outcome.factual_value,
                    "counterfactual": outcome.counterfactual_value,
                    "delta": outcome.delta,
                })

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "counterfactual_run": True,
                    "query_variable": "entropy",
                    "query_value": 0.3,
                    "outcomes": outcomes,
                    "reasoning": cf_result.reasoning,
                }
            )

        except Exception as e:
            logger.error(f"Counterfactual analysis error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["causal_graph_update"]
