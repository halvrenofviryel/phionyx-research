"""
Safety Layer Pre CEP Block
============================

Block: safety_layer_pre_cep
Initial safety assessment before CEP evaluation.
"""

import logging
from typing import Any, Optional, Protocol

from ...base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class SafetyLayerProcessorProtocol(Protocol):
    """Protocol for safety layer processing."""
    async def process_safety(
        self,
        frame: Any,
        user_input: str,
        narrative_response: str,
        cognitive_state: Any,
        context_string: str,
        cep_flags: Optional[Any] = None,
        cep_config: Optional[Any] = None
    ) -> tuple[Any, Any]:  # Returns (frame, safety_result)
        """Process safety layer."""
        ...


class SafetyLayerPreCepBlock(PipelineBlock):
    """
    Safety Layer Pre CEP Block.

    Performs initial safety assessment before CEP evaluation.
    """

    def __init__(self, processor: SafetyLayerProcessorProtocol):
        """
        Initialize block.

        Args:
            processor: Safety layer processor
        """
        super().__init__("safety_layer_pre_cep")
        self.processor = processor

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute safety layer pre CEP.

        Args:
            context: Block context with frame and inputs

        Returns:
            BlockResult with safety_result
        """
        try:
            # Get frame and inputs from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            cognitive_state = metadata.get("cognitive_state")
            context_string = metadata.get("context_string", "")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=ValueError("Frame not found in context")
                )

            # Process safety layer
            updated_frame, safety_result = await self.processor.process_safety(
                frame=frame,
                user_input=context.user_input,
                narrative_response="",  # Not available yet before narrative layer
                cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None),
                context_string=context_string or getattr(frame, 'context_string', ""),
                cep_flags=None,  # Will be updated after CEP evaluation
                cep_config=None  # Will be updated after CEP evaluation
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "frame": updated_frame,
                    "safety_result": safety_result,
                    "is_blocked": getattr(safety_result, 'is_blocked', False) if safety_result else False
                }
            )
        except Exception as e:
            logger.error(f"Safety layer pre CEP failed: {e}", exc_info=True)
            # Fail-open: create no-op safety result
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "safety_result": None,
                    "is_blocked": False,
                    "error": str(e)
                }
            )

