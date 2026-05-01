"""
Audit Layer Block
==================

Block: audit_layer
Performs audit operations (snapshots, event logging, explainability).
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class AuditLayerProcessorProtocol(Protocol):
    """Protocol for audit layer processing."""
    async def process_audit(
        self,
        frame: Any,
        unified_state: Any | None,
        narrative_response: str,
        physics_state: dict[str, Any]
    ) -> dict[str, Any]:  # Returns audit result
        """Process audit layer."""
        ...


class AuditLayerBlock(PipelineBlock):
    """
    Audit Layer Block.

    Performs audit operations (snapshots, event logging, explainability).
    """

    def __init__(self, processor: AuditLayerProcessorProtocol | None = None):
        """
        Initialize block.

        Args:
            processor: Audit layer processor
        """
        super().__init__("audit_layer")
        self.processor = processor

    def should_skip(self, context: BlockContext) -> str | None:
        """Never skip — inline fallback computes basic integrity."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """Execute audit layer processing with inline fallback."""
        try:
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            unified_state = metadata.get("unified_state")
            narrative_response = metadata.get("narrative_text", "")
            physics_state = metadata.get("physics_state", {})

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"audit_result": None}
                )

            if self.processor:
                audit_result = await self.processor.process_audit(
                    frame=frame,
                    unified_state=unified_state,
                    narrative_response=narrative_response,
                    physics_state=physics_state,
                )
            else:
                # Inline fallback: basic integrity assessment
                integrity = 1.0
                issues = []
                if not narrative_response or len(narrative_response) < 3:
                    integrity -= 0.2
                    issues.append("empty_or_short_response")
                if not physics_state or not isinstance(physics_state, dict):
                    integrity -= 0.1
                    issues.append("missing_physics_state")
                elif physics_state.get("phi") is None:
                    integrity -= 0.1
                    issues.append("missing_phi")
                # Coherence violation lowers integrity
                coherence_qa = metadata.get("coherence_qa_result", {})
                if isinstance(coherence_qa, dict) and coherence_qa.get("leak_detected"):
                    integrity -= 0.2
                    issues.append("state_leak_detected")
                integrity = max(0.0, integrity)
                audit_result = {
                    "status": "ok" if integrity > 0.5 else "degraded",
                    "integrity_score": integrity,
                    "issues": issues,
                    "source": "inline_fallback",
                }

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"audit_result": audit_result},
            )
        except Exception as e:
            logger.error(f"Audit layer processing failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"audit_result": None, "error": str(e)},
            )

