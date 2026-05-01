"""
Echo Ontology Transformation Block
====================================

Block: echo_ontology_transformation
Transforms trace result into physics state using echo ontology.
"""

import logging
from typing import Any, Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class EchoOntologyTransformerProtocol(Protocol):
    """Protocol for echo ontology transformation."""
    def transform(
        self,
        frame: Any,
        cognitive_state: Any,
        trace_result: Any
    ) -> dict[str, Any]:  # Returns physics_state
        """Transform trace to physics state."""
        ...


class EchoOntologyTransformationBlock(PipelineBlock):
    """
    Echo Ontology Transformation Block.

    Transforms trace result into physics state using echo ontology.
    """

    def __init__(self, transformer: EchoOntologyTransformerProtocol):
        """
        Initialize block.

        Args:
            transformer: Echo ontology transformer
        """
        super().__init__("echo_ontology_transformation")
        self.transformer = transformer

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute echo ontology transformation.

        Args:
            context: Block context with frame and trace_result

        Returns:
            BlockResult with transformed physics_state
        """
        try:
            # Get frame and trace_result from context metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            trace_result = metadata.get("trace_result")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",  # Skip if no frame
                    data={"physics_state": {}}
                )

            # Get cognitive_state from frame
            cognitive_state = getattr(frame, 'cognitive_state', None) or frame.cognitive_state if hasattr(frame, 'cognitive_state') else None

            if not cognitive_state:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",  # Skip if no cognitive_state
                    data={"physics_state": {}}
                )

            # Transform trace to physics state
            physics_state = self.transformer.transform(
                frame=frame,
                cognitive_state=cognitive_state,
                trace_result=trace_result
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": physics_state or {}
                }
            )
        except Exception as e:
            logger.error(f"Echo ontology transformation failed: {e}", exc_info=True)
            # Fail-open: return empty physics_state
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": {},
                    "error": str(e)
                }
            )

