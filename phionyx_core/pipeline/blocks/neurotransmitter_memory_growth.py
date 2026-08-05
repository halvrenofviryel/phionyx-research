"""
Neurotransmitter Memory Growth Block
======================================

Block: neurotransmitter_memory_growth
Updates neurotransmitter and memory growth metrics.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
    not_measured,
)

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
                # No updater, so no growth was measured. `{}` used to be
                # published here and echo_orchestrator.py:776 merges block
                # data into metadata, where response_build.py:205 reads it —
                # as growth that was measured and came out empty.
                _outcome = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.COMPLETED,
                    measurement=not_measured(
                        "no growth updater is configured",
                        cause="not_executed"),
                    operating_mode="degraded",
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"block_outcome": _outcome.to_record_fields()},
                )

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
            # Control channel unchanged — this block stays fail-open so the
            # pipeline still completes, and the `return BlockResult(...)`
            # shape is kept so the inventory sweep can still see it. What
            # changes is the record: block_run_status FAILED, measurement
            # ERROR, operating_mode degraded — a crash here can no longer
            # read as a clean measurement.
            _outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    "neurotransmitter/memory growth update raised",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                # No `growth_metrics`. An empty dict merged into metadata and
                # read as growth measured at zero; nothing was measured.
                data={**({
                    "error": str(e)
                }), "block_outcome": _outcome.to_record_fields()}
            )

