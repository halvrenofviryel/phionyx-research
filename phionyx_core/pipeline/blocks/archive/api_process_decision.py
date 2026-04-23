"""
API Process Decision Block
============================

Block: api_process_decision
Top-level API block that wraps the entire pipeline execution.
"""

import logging

from ...base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class ApiProcessDecisionBlock(PipelineBlock):
    """
    API Process Decision Block.

    Top-level block that wraps the entire pipeline execution.
    This is the entry point for the API endpoint.
    """

    def __init__(self):
        """Initialize block."""
        super().__init__("api_process_decision")

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute API process decision.

        This block is primarily a marker/telemetry block.
        Actual processing happens in downstream blocks.

        Args:
            context: Block context

        Returns:
            BlockResult with initial context
        """
        try:
            # This block is primarily for telemetry tracking
            # The actual processing happens in downstream blocks
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "pipeline_started": True,
                    "user_input": context.user_input,
                    "session_id": context.session_id
                }
            )
        except Exception as e:
            logger.error(f"API process decision block failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

