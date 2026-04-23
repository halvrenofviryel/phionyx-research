"""
Self-Model Assessment Block
============================

Block: self_model_assessment
Evaluates system self-awareness — capabilities, limitations, confidence.
Reports what the system can and cannot do for the current turn.

Position in pipeline: After confidence_fusion, before narrative_layer.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class SelfModelAssessmentBlock(PipelineBlock):
    """
    Self-Model Assessment Block (S2 Self-Awareness Sprint).

    Evaluates system capabilities and limitations for the current action.
    Reports confidence levels and available/degraded capabilities.
    """

    def __init__(self, self_model=None):
        """
        Args:
            self_model: SelfModel instance (injected via DI)
        """
        super().__init__("self_model_assessment")
        self._self_model = self_model

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._self_model is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No SelfModel instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Determine current action from intent or mode
            action = metadata.get("intent", {}).get("action", context.mode or "respond")
            confidence = metadata.get("confidence_result", {})
            t_meta = 1.0
            if isinstance(confidence, dict):
                t_meta = confidence.get("t_meta", 1.0)
            elif hasattr(confidence, "t_meta"):
                t_meta = confidence.t_meta if confidence.t_meta is not None else 1.0

            # Assess capability
            assessment = self._self_model.can_i_do(
                action=action,
                context_confidence=t_meta,
                knowledge_score=metadata.get("knowledge_score", 1.0),
            )

            # Get system report
            report = self._self_model.get_report(
                knowledge_coverage=metadata.get("knowledge_coverage", 1.0)
            )

            result_data = {
                "can_do": assessment.can_do,
                "confidence": assessment.confidence,
                "status": assessment.status.value if hasattr(assessment.status, "value") else str(assessment.status),
                "limitations": assessment.limitations,
                "reasoning": assessment.reasoning,
                "capabilities_available": report.capabilities_available,
                "capabilities_degraded": report.capabilities_degraded,
                "capabilities_unavailable": report.capabilities_unavailable,
                "confidence_mean": report.confidence_mean,
            }

            if not assessment.can_do:
                logger.warning(
                    f"[SELF_MODEL] Action '{action}' assessed as NOT capable: "
                    f"{assessment.reasoning}"
                )

            # Store with prefixed key for downstream AGI context injection
            if context.metadata is not None:
                context.metadata["_agi_self_model"] = result_data

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Self-model assessment error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["confidence_fusion"]
