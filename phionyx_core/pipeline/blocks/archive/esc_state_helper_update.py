"""
ESC State Helper Update Block
==============================

Block: esc_state_helper_update
Helper update for ESC (Echo State Controller) state.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ...base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class ESCStateHelperProtocol(Protocol):
    """Protocol for ESC state helper update."""
    def update_helper_state(
        self,
        unified_state: Any,
        physics_state: Dict[str, Any]
    ) -> Any:  # Returns updated unified_state
        """Update ESC helper state."""
        ...


class EscStateHelperUpdateBlock(PipelineBlock):
    """
    ESC State Helper Update Block.

    Performs helper updates for ESC state.
    """

    def __init__(self, helper: Optional[ESCStateHelperProtocol] = None):
        """
        Initialize block.

        Args:
            helper: ESC state helper service
        """
        super().__init__("esc_state_helper_update")
        self.helper = helper

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no helper or unified_state available."""
        metadata = context.metadata or {}
        if not self.helper or not metadata.get("unified_state"):
            return "esc_helper_or_unified_state_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute ESC state helper update.

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

            # Update helper state
            if self.helper:
                updated_unified_state = self.helper.update_helper_state(
                    unified_state=unified_state,
                    physics_state=physics_state
                )
            else:
                # No-op: pass through
                updated_unified_state = unified_state

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": updated_unified_state
                }
            )
        except Exception as e:
            logger.error(f"ESC state helper update failed: {e}", exc_info=True)
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

