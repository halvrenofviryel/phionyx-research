"""
UKF Predict Block
=================

Block: ukf_predict
Performs UKF (Unscented Kalman Filter) prediction for state estimation.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class UKFPredictorProtocol(Protocol):
    """Protocol for UKF prediction."""
    def predict(
        self,
        unified_state: Any,
        time_delta: float
    ) -> Any:  # Returns predicted state
        """Perform UKF prediction."""
        ...


class UkfPredictBlock(PipelineBlock):
    """
    UKF Predict Block.

    Performs UKF prediction to estimate next state.
    """

    def __init__(self, predictor: UKFPredictorProtocol | None = None):
        """
        Initialize block.

        Args:
            predictor: UKF predictor service
        """
        super().__init__("ukf_predict")
        self.predictor = predictor

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if no predictor available."""
        if self.predictor is None:
            return "ukf_predictor_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute UKF prediction.

        Args:
            context: Block context with unified_state and time_delta

        Returns:
            BlockResult with predicted state
        """
        try:
            # Get unified_state and time_delta from context metadata
            metadata = context.metadata or {}
            unified_state = metadata.get("unified_state")
            time_delta = metadata.get("time_delta", 1.0)

            if not unified_state or self.predictor is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",  # Skip if no unified state or predictor not configured
                    data={"predicted_state": None}
                )

            # Perform UKF prediction
            predicted_state = self.predictor.predict(
                unified_state=unified_state,
                time_delta=time_delta
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "predicted_state": predicted_state
                }
            )
        except Exception as e:
            logger.error(f"UKF prediction failed: {e}", exc_info=True)
            # Fail-open: continue without prediction
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "predicted_state": None,
                    "error": str(e)
                }
            )

