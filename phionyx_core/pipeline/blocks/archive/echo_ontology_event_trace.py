"""
Echo Ontology Event Trace Block
================================

Block: echo_ontology_event_trace
Processes echo ontology event and creates trace.
"""

import logging
from typing import Any, Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class EchoOntologyEventTracerProtocol(Protocol):
    """Protocol for echo ontology event tracing."""
    def process_event_and_trace(
        self,
        user_input: str,
        card_type: str,
        card_title: str,
        scene_context: str,
        t_now: float
    ) -> tuple[Any, Any]:  # Returns (echo_event, trace_result)
        """Process event and create trace."""
        ...


class EchoOntologyEventTraceBlock(PipelineBlock):
    """
    Echo Ontology Event Trace Block.

    Processes echo ontology event and creates trace.
    """

    def __init__(self, tracer: EchoOntologyEventTracerProtocol):
        """
        Initialize block.

        Args:
            tracer: Echo ontology event tracer
        """
        super().__init__("echo_ontology_event_trace")
        self.tracer = tracer

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute echo ontology event tracing.

        Args:
            context: Block context with inputs and t_now

        Returns:
            BlockResult with echo_event and trace_result
        """
        try:
            # Get t_now from context metadata
            metadata = context.metadata or {}
            t_now = metadata.get("t_now", 0.0)

            # Process event and create trace
            echo_event, trace_result = self.tracer.process_event_and_trace(
                user_input=context.user_input,
                card_type=context.card_type,
                card_title=context.card_title,
                scene_context=context.scene_context,
                t_now=t_now
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "echo_event": echo_event,
                    "trace_result": trace_result
                }
            )
        except Exception as e:
            logger.error(f"Echo ontology event trace failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

