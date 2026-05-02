"""
Initialize Unified State Block
===============================

Block: initialize_unified_state
Initializes the unified state (EchoState2) for the pipeline.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class UnifiedStateInitializerProtocol(Protocol):
    """Protocol for unified state initialization."""
    def initialize_unified_state(
        self,
        frame: Any,
        time_delta: float,
        physics_params: dict[str, Any]
    ) -> Any:  # Returns UnifiedEchoState
        """Initialize unified state."""
        ...


class InitializeUnifiedStateBlock(PipelineBlock):
    """
    Initialize Unified State Block.

    Initializes the unified state (EchoState2) from frame and physics parameters.
    """

    def __init__(self, initializer: UnifiedStateInitializerProtocol | None = None):
        """
        Initialize block.

        Args:
            initializer: Service that initializes unified state
        """
        super().__init__("initialize_unified_state")
        self.initializer = initializer

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if initializer not available."""
        if self.initializer is None:
            return "initializer_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute unified state initialization.

        Args:
            context: Block context with frame and time_delta

        Returns:
            BlockResult with initialized unified state
        """
        try:
            # Get frame from context metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=ValueError("Frame not found in context")
                )

            # Get time_delta from metadata
            time_delta = metadata.get("time_delta", 1.0)

            # Get physics_params
            physics_params = metadata.get("physics_params", {})

            if self.initializer is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=RuntimeError("UnifiedStateInitializer not configured")
                )

            # Initialize unified state
            unified_state = self.initializer.initialize_unified_state(
                frame=frame,
                time_delta=time_delta,
                physics_params=physics_params
            )

            # Propagate to context metadata for downstream blocks
            if context.metadata is None:
                context.metadata = {}
            context.metadata["unified_state"] = unified_state

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": unified_state
                }
            )
        except Exception as e:
            logger.error(f"Unified state initialization failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

