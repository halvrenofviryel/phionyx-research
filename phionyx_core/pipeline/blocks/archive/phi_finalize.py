"""
Phi Finalize Block
===================

Block: phi_finalize
Finalizes phi computation and updates unified state.
"""

import logging
from typing import Any, Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class PhiFinalizerProtocol(Protocol):
    """Protocol for phi finalization."""
    def finalize_phi(
        self,
        unified_state: Any,
        phi_value: float,
        phi_components: dict[str, Any] | None = None
    ) -> Any:  # Returns finalized unified_state
        """Finalize phi computation."""
        ...


class PhiFinalizeBlock(PipelineBlock):
    """
    Phi Finalize Block.

    Finalizes phi computation and updates unified state.
    """

    def __init__(self, finalizer: PhiFinalizerProtocol | None = None):
        """
        Initialize block.

        Args:
            finalizer: Phi finalizer service
        """
        super().__init__("phi_finalize")
        self.finalizer = finalizer

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if no finalizer or unified_state available."""
        metadata = context.metadata or {}
        if not self.finalizer or not metadata.get("unified_state"):
            return "phi_finalizer_or_unified_state_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute phi finalization.

        Args:
            context: Block context with unified_state and phi

        Returns:
            BlockResult with finalized unified_state
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

            # Finalize phi
            if self.finalizer:
                finalized_unified_state = self.finalizer.finalize_phi(
                    unified_state=unified_state,
                    phi_value=phi_value,
                    phi_components=phi_components
                )
            else:
                # Fallback: set phi directly if unified_state has phi attribute
                if hasattr(unified_state, 'phi'):
                    unified_state.phi = phi_value
                finalized_unified_state = unified_state

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": finalized_unified_state
                }
            )
        except Exception as e:
            logger.error(f"Phi finalization failed: {e}", exc_info=True)
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

