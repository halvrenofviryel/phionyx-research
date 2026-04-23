"""
Perceptual Frame Emit Block — v3.0.0
======================================

Block: perceptual_frame_emit
Position: After context_retrieval_rag
v4 Schema: PerceptualFrame

Emits a PerceptualFrame from measurement data and context.
"""

import logging
from typing import Optional

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class PerceptualFrameEmitBlock(PipelineBlock):
    """
    Emits a v4 PerceptualFrame from current measurement data.

    Reads MeasurementVector from metadata and constructs a
    PerceptualFrame with salience and modality information.
    """

    def __init__(self):
        super().__init__("perceptual_frame_emit")

    def should_skip(self, context: BlockContext) -> Optional[str]:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            from ...contracts.v4.perceptual_frame import PerceptualFrame, Modality

            metadata = context.metadata or {}
            measurement = metadata.get("measurement_vector", {})

            frame = PerceptualFrame(
                A_meas=measurement.get("A_meas", 0.5),
                V_meas=measurement.get("V_meas", 0.0),
                H_meas=measurement.get("H_meas", 0.5),
                confidence=measurement.get("confidence", 0.5),
                modality=Modality.TEXT,
                salience=measurement.get("confidence", 0.5),
                semantic_tags=metadata.get("semantic_tags", []),
                intent_vector=metadata.get("intent_vector"),
            )

            # Attach to context
            context.v4_perceptual_frame = frame

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"perceptual_frame_emitted": True, "salience": frame.salience},
            )
        except Exception as e:
            logger.error(f"Perceptual frame emit failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"perceptual_frame_emitted": False, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["context_retrieval_rag"]
