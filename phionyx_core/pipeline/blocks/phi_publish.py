"""
Phi Publish Block
==================

Block: phi_publish
Publishes phi value to unified state.
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
            # No midpoint. phi_computation (canonical 37) omits `phi` when
            # its engine measured none, and this block WRITES what it reads
            # into unified_state.phi — which twenty-odd call sites then read.
            # Defaulting to 0.5 here put the fabrication back into the state
            # one block after it was removed from the signal, the same shape
            # response_build had.
            phi_value = metadata.get("phi")
            phi_components = metadata.get("phi_components", {})

            if not unified_state:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"unified_state": None}
                )

            if phi_value is None:
                _outcome = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.COMPLETED,
                    measurement=not_measured(
                        "no phi was measured this turn, so none is published "
                        "into unified_state",
                        cause="input_absent"),
                    operating_mode="degraded",
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"block_outcome": _outcome.to_record_fields()},
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
                    "phi publish raised; the state returned is the one that came in",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                # No `unified_state`. It used to republish the state that
                # came in, under this block's own result key, so an updated
                # state and an un-updated one shared a field. Safe to omit,
                # measured not assumed: every consumer reads
                # `metadata["unified_state"]`, not this block's result. The
                # state carries forward because nothing overwrites it.
                data={**({
                    "error": str(e)
                }), "block_outcome": _outcome.to_record_fields()}
            )

