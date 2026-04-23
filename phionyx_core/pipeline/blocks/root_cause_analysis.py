"""
Root Cause Analysis Block
==========================

Block: root_cause_analysis
Backward causal trace to find root causes of anomalies.

Position in pipeline: After counterfactual_analysis, when anomalies detected.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class RootCauseAnalysisBlock(PipelineBlock):
    """
    Root Cause Analysis Block (S4 Causality Advanced Sprint).

    When anomalies are detected (drift, low coherence, high entropy),
    performs backward walk through causal graph to identify root causes.
    """

    def __init__(self, root_cause_analyzer=None):
        """
        Args:
            root_cause_analyzer: RootCauseAnalyzer instance (injected via DI)
        """
        super().__init__("root_cause_analysis")
        self._analyzer = root_cause_analyzer

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._analyzer is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No RootCauseAnalyzer instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Find anomalous variable
            physics_state = metadata.get("physics_state", {})
            anomaly_node = None
            anomaly_value = None

            # Check for high entropy (anomaly)
            entropy = physics_state.get("entropy")
            if entropy is not None and entropy > 0.7:
                anomaly_node = "entropy"
                anomaly_value = entropy

            # Check for low coherence
            coherence = metadata.get("coherence_result", {})
            if isinstance(coherence, dict):
                coh_val = coherence.get("coherence", 1.0)
                if coh_val < 0.3:
                    anomaly_node = "coherence"
                    anomaly_value = coh_val

            if anomaly_node is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"analysis_run": False, "reason": "No anomaly detected"}
                )

            # Run root cause analysis
            analysis = self._analyzer.analyze(
                anomaly_node=anomaly_node,
                anomaly_value=anomaly_value,
            )

            candidates = []
            for candidate in analysis.candidates[:5]:  # Top 5
                candidates.append({
                    "node_id": candidate.node_id,
                    "name": candidate.name,
                    "likelihood": candidate.likelihood,
                    "causal_path": candidate.causal_path,
                    "current_value": candidate.current_value,
                })

            top_cause = None
            if analysis.top_cause:
                top_cause = {
                    "node_id": analysis.top_cause.node_id,
                    "name": analysis.top_cause.name,
                    "likelihood": analysis.top_cause.likelihood,
                }

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "analysis_run": True,
                    "anomaly_node": anomaly_node,
                    "anomaly_value": anomaly_value,
                    "top_cause": top_cause,
                    "candidates": candidates,
                    "reasoning": analysis.reasoning,
                }
            )

        except Exception as e:
            logger.error(f"Root cause analysis error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["causal_graph_update"]
