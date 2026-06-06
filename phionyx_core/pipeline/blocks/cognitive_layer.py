"""
Cognitive Layer Block
======================

Block: cognitive_layer
Processes cognitive layer (memory, intuition, physics).
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class CognitiveLayerProcessorProtocol(Protocol):
    """Protocol for cognitive layer processing."""
    async def process_cognitive_layer(
        self,
        frame: Any,
        user_input: str,
        card_type: str,
        card_result: str,
        scene_context: str,
        physics_params: Dict[str, Any],
        **kwargs
    ) -> Any:  # Returns updated frame
        """Process cognitive layer."""
        ...


class CognitiveLayerBlock(PipelineBlock):
    """
    Cognitive Layer Block.

    Processes the cognitive layer which includes:
    - Memory retrieval
    - Intuition/GraphRAG
    - Physics integration
    """

    determinism = "noisy_sensor"  # delegates to injected processor; LLM-backed in default wiring

    def __init__(self, processor: Optional[CognitiveLayerProcessorProtocol] = None):
        """
        Initialize block.

        Args:
            processor: Cognitive layer processor
        """
        super().__init__("cognitive_layer")
        self.processor = processor

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if processor not available."""
        if self.processor is None:
            return "processor_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute cognitive layer processing.

        Args:
            context: Block context with frame and inputs

        Returns:
            BlockResult with updated frame and cognitive state
        """
        try:
            # Get frame from context metadata (should be set by previous blocks)
            frame = context.metadata.get("frame") if context.metadata else None
            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=ValueError("Frame not found in context")
                )

            # Get physics params
            physics_params = context.metadata.get("physics_params", {}) if context.metadata else {}

            # Process cognitive layer
            updated_frame = await self.processor.process_cognitive_layer(
                frame=frame,
                user_input=context.user_input,
                card_type=context.card_type,
                card_result=context.card_result,
                scene_context=context.scene_context,
                physics_params=physics_params
            )

            # Extract cognitive state from frame
            cognitive_state = getattr(updated_frame, 'cognitive_state', None) or (
                updated_frame.cognitive_state if hasattr(updated_frame, 'cognitive_state') else None
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "frame": updated_frame,
                    "cognitive_state": cognitive_state
                }
            )
        except Exception as e:
            logger.error(f"Cognitive layer processing failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

