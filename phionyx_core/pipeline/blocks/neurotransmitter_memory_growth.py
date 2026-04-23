"""
Neurotransmitter Memory Growth Block
======================================

Block: neurotransmitter_memory_growth
Updates neurotransmitter and memory growth metrics.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class NeurotransmitterMemoryGrowthProtocol(Protocol):
    """Protocol for neurotransmitter/memory growth update."""
    def update_growth(
        self,
        user_input: str,
        narrative_response: str,
        physics_state: Dict[str, Any]
    ) -> Dict[str, Any]:  # Returns growth metrics
        """Update neurotransmitter and memory growth."""
        ...


class NeurotransmitterMemoryGrowthBlock(PipelineBlock):
    """
    Neurotransmitter Memory Growth Block.

    Updates neurotransmitter and memory growth metrics.
    """

    def __init__(self, growth_updater: Optional[NeurotransmitterMemoryGrowthProtocol] = None):
        """
        Initialize block.

        Args:
            growth_updater: Growth updater service
        """
        super().__init__("neurotransmitter_memory_growth")
        self.growth_updater = growth_updater

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no updater available."""
        if self.growth_updater is None:
            return "growth_updater_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute neurotransmitter/memory growth update.

        Args:
            context: Block context with inputs and physics_state

        Returns:
            BlockResult with growth metrics
        """
        try:
            # Get narrative_response and physics_state from metadata
            metadata = context.metadata or {}
            narrative_response = metadata.get("narrative_text", "")
            physics_state = metadata.get("physics_state", {})

            # Update growth
            if self.growth_updater:
                growth_metrics = self.growth_updater.update_growth(
                    user_input=context.user_input,
                    narrative_response=narrative_response,
                    physics_state=physics_state
                )
            else:
                growth_metrics = {}

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "growth_metrics": growth_metrics
                }
            )
        except Exception as e:
            logger.error(f"Neurotransmitter/memory growth update failed: {e}", exc_info=True)
            # Fail-open: continue without growth update
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "growth_metrics": {},
                    "error": str(e)
                }
            )

