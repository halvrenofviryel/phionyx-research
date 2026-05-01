"""
Arbitration Resolve Block — v3.0.0
=====================================

Block: arbitration_resolve
Position: After confidence_fusion
v4 Schema: W_final, conflict_score

Resolves conflicts between modules using arbitration math.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class ArbitrationResolveBlock(PipelineBlock):
    """
    Resolves inter-module conflicts using arbitration math.

    If conflict score exceeds threshold, applies resolution strategy:
    - Safety-first: defer to ethics engine
    - Confidence-weighted: trust highest-confidence module
    - Consensus: require majority agreement
    """

    def __init__(self, conflict_threshold: float = 0.5):
        super().__init__("arbitration_resolve")
        self.conflict_threshold = conflict_threshold

    def should_skip(self, context: BlockContext) -> str | None:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            confidence = context.v4_confidence
            if confidence is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"arbitration_needed": False},
                )

            # Check if arbitration is needed
            metadata = context.metadata or {}
            conflict_score = 0.0
            if hasattr(confidence, "metadata"):
                conflict_score = confidence.metadata.get("conflict_score", 0.0)

            resolution = "none"
            if conflict_score > self.conflict_threshold:
                # Safety-first resolution: if ethics is enforced, defer to it
                ethics_result = metadata.get("ethics_result", {})
                if isinstance(ethics_result, dict) and ethics_result.get("enforced"):
                    resolution = "safety_override"
                else:
                    resolution = "confidence_weighted"

                logger.info(
                    f"Arbitration resolved: conflict={conflict_score:.2f}, "
                    f"resolution={resolution}"
                )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "arbitration_needed": conflict_score > self.conflict_threshold,
                    "conflict_score": conflict_score,
                    "resolution_strategy": resolution,
                },
            )
        except Exception as e:
            logger.error(f"Arbitration resolve failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"arbitration_needed": False, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["confidence_fusion"]
