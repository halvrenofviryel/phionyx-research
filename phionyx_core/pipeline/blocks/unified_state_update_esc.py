"""
Unified State Update ESC Block
================================

Block: unified_state_update_esc
Updates unified state (EchoState2) from physics state.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class UnifiedStateUpdaterProtocol(Protocol):
    """Protocol for unified state update."""
    def update_from_physics_state(
        self,
        unified_state: Any,
        physics_state: Dict[str, Any]
    ) -> Any:  # Returns updated unified_state
        """Update unified state from physics state."""
        ...


class UnifiedStateUpdateEscBlock(PipelineBlock):
    """
    Unified State Update ESC Block.

    Updates unified state (EchoState2) from physics state.
    """

    def __init__(self, updater: Optional[UnifiedStateUpdaterProtocol] = None):
        """
        Initialize block.

        Args:
            updater: Unified state updater
        """
        super().__init__("unified_state_update_esc")
        self.updater = updater

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no updater or unified_state available."""
        metadata = context.metadata or {}
        if not self.updater or not metadata.get("unified_state"):
            return "unified_state_or_updater_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute unified state update.

        Args:
            context: Block context with unified_state and physics_state

        Returns:
            BlockResult with updated unified_state
        """
        try:
            # Get unified_state and physics_state from metadata
            metadata = context.metadata or {}
            unified_state = metadata.get("unified_state")
            physics_state = metadata.get("physics_state", {})

            if not unified_state:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"unified_state": None}
                )

            # Update unified state from physics state
            if self.updater:
                updated_unified_state = self.updater.update_from_physics_state(
                    unified_state=unified_state,
                    physics_state=physics_state
                )
            else:
                # Fallback: update directly if unified_state has from_physics_state method
                if hasattr(unified_state, 'from_physics_state'):
                    unified_state.from_physics_state(physics_state)
                    updated_unified_state = unified_state
                else:
                    updated_unified_state = unified_state

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": updated_unified_state
                }
            )
        except Exception as e:
            logger.error(f"Unified state update failed: {e}", exc_info=True)
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

