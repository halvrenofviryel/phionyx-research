"""
Engine Ensure Initialized Block
================================

Block: engine_ensure_initialized
Ensures all engine processors and services are initialized.
"""

import logging

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class EngineEnsureInitializedBlock(PipelineBlock):
    """
    Ensures engine initialization before processing.
    """

    def __init__(self, initialization_checker):
        """
        Initialize block.

        Args:
            initialization_checker: Callable that performs initialization check
        """
        super().__init__("engine_ensure_initialized")
        self.initialization_checker = initialization_checker

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute initialization check.

        Args:
            context: Block context

        Returns:
            BlockResult with initialization status
        """
        try:
            # Call the initialization checker (injected from bridge)
            self.initialization_checker()

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"initialized": True}
            )
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

