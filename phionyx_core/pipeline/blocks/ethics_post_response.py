"""
Ethics Post Response Block
===========================

Block: ethics_post_response
Ethics check after narrative generation.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class EthicsProcessorProtocol(Protocol):
    """Protocol for ethics processing."""
    def check_ethics_post_response(
        self,
        frame: Any,
        narrative_response: str,
        cognitive_state: Any
    ) -> dict[str, Any]:  # Returns ethics_result
        """Check ethics after response."""
        ...


class EthicsPostResponseBlock(PipelineBlock):
    """
    Ethics Post Response Block.

    Performs ethics check after narrative generation.
    """

    def __init__(self, processor: EthicsProcessorProtocol | None = None):
        """
        Initialize block.

        Args:
            processor: Ethics processor
        """
        super().__init__("ethics_post_response")
        self.processor = processor

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute ethics post response check.

        Args:
            context: Block context with frame and narrative_response

        Returns:
            BlockResult with ethics_result
        """
        try:
            # Get frame and narrative_response from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            narrative_response = metadata.get("narrative_text", "")
            cognitive_state = metadata.get("cognitive_state")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"ethics_result": None}
                )

            # Check ethics
            if self.processor:
                ethics_result = self.processor.check_ethics_post_response(
                    frame=frame,
                    narrative_response=narrative_response,
                    cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                )
            else:
                ethics_result = None

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "ethics_result": ethics_result
                }
            )
        except Exception as e:
            logger.error(f"Ethics post response check failed: {e}", exc_info=True)
            # Fail-open: continue without ethics check
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "ethics_result": None,
                    "error": str(e)
                }
            )

