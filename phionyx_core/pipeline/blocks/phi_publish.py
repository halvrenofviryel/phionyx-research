"""
Phi Publish Block
==================

Block: phi_publish
Publishes phi value to unified state.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class PhiPublisherProtocol(Protocol):
    """Protocol for phi publishing."""
    def publish_phi(
        self,
        unified_state: Any,
        phi_value: float,
        phi_components: Optional[Dict[str, Any]] = None
    ) -> Any:  # Returns updated unified_state
        """Publish phi to unified state."""
        ...


class PhiPublishBlock(PipelineBlock):
    """
    Phi Publish Block.

    Publishes phi value to unified state.
    """

    def __init__(self, publisher: Optional[PhiPublisherProtocol] = None):
        """
        Initialize block.

        Args:
            publisher: Phi publisher service
        """
        super().__init__("phi_publish")
        self.publisher = publisher

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no unified_state — output is not consumed downstream."""
        metadata = context.metadata or {}
        if not metadata.get("unified_state"):
            return "v2_5_bypass_no_unified_state"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute phi publish.

        Args:
            context: Block context with unified_state and phi

        Returns:
            BlockResult with updated unified_state
        """
        try:
            # Get unified_state and phi from metadata
            metadata = context.metadata or {}
            unified_state = metadata.get("unified_state")
            phi_value = metadata.get("phi", 0.5)
            phi_components = metadata.get("phi_components", {})

            if not unified_state:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"unified_state": None}
                )

            # Publish phi
            if self.publisher:
                updated_unified_state = self.publisher.publish_phi(
                    unified_state=unified_state,
                    phi_value=phi_value,
                    phi_components=phi_components
                )
            else:
                # Fallback: set phi directly if unified_state has phi attribute
                if hasattr(unified_state, 'phi'):
                    unified_state.phi = phi_value
                updated_unified_state = unified_state

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": updated_unified_state
                }
            )
        except Exception as e:
            logger.error(f"Phi publish failed: {e}", exc_info=True)
            # Fail-open: return original unified_state
            metadata = context.metadata or {}
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": metadata.get("unified_state"),
                    "error": str(e)
                }
            )

