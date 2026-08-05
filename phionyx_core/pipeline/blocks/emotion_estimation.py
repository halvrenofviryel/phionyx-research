"""
Emotion Estimation Block
========================

Block: emotion_estimation
Estimates emotion (valence, arousal) from user input using EmotionEstimator.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ...memory.emotion_cache import EmotionCache

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
)

logger = logging.getLogger(__name__)


class EmotionEstimatorProtocol(Protocol):
    """Protocol for emotion estimation."""
    async def estimate(self, text: str) -> Dict[str, Any]:
        """Estimate emotion from text."""
        ...


class EmotionEstimationBlock(PipelineBlock):
    """
    Emotion Estimation Block.

    Estimates valence and arousal from user input.
    """

    determinism = "noisy_sensor"  # default estimator is LLM-backed

    def __init__(
        self,
        emotion_estimator: Optional[EmotionEstimatorProtocol] = None,
        emotion_cache: Optional[EmotionCache] = None
    ):
        """
        Initialize emotion estimation block.

        Args:
            emotion_estimator: EmotionEstimator instance (optional)
            emotion_cache: Emotion cache for determinism (optional, will create if None)
        """
        super().__init__("emotion_estimation")
        self.emotion_estimator = emotion_estimator
        # CRITICAL: Cache ensures determinism (same input → same output)
        # This is essential for parallel execution consistency
        self.emotion_cache = emotion_cache or EmotionCache(max_size=10000, enable_metrics=True)

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no estimator available."""
        if self.emotion_estimator is None:
            return "emotion_estimator_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute emotion estimation.

        Args:
            context: Block context with user_input

        Returns:
            BlockResult with valence, arousal estimates
        """
        try:
            # CRITICAL: Check cache FIRST for determinism (same input → same output)
            # This ensures parallel execution produces consistent results
            # Cache check must be FIRST, before any unified_state dependency
            cached_result = self.emotion_cache.get(context.user_input)
            if cached_result is not None:
                cached_valence, cached_arousal = cached_result
                logger.debug(f"Using cached emotion values: valence={cached_valence:.4f}, arousal={cached_arousal:.4f}")
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "valence": cached_valence,
                        "arousal": cached_arousal,
                        "unknown": False,
                        "source": "emotion_cache"
                    }
                )

            # CRITICAL: emotion_estimation must be DETERMINISTIC - only depends on user_input
            # NOT on unified_state (which may differ in sequential vs parallel execution)
            # Use EchoState2 schema defaults: V=0.0, A=0.5 (profil/state-based, not hardcoded)
            # These defaults come from EchoState2 schema, not from unified_state instance
            default_valence = 0.0  # EchoState2 default V (from schema)
            default_arousal = 0.5  # EchoState2 default A (from schema)

            if not self.emotion_estimator:
                # Fallback: Use EchoState2 values (from unified_state or defaults)
                # This ensures we use profile/state-based values, not hardcoded constants
                # CRITICAL: Cache the fallback values for determinism
                self.emotion_cache.set(context.user_input, default_valence, default_arousal)
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "valence": default_valence,
                        "arousal": default_arousal,
                        "unknown": True,
                        "source": "echo_state_defaults"
                    }
                )

            # Estimate emotion from user input
            estimation_result = await self.emotion_estimator.estimate(context.user_input)

            # An estimator that returned no valence or arousal estimated
            # neither. The schema defaults are still used so downstream has a
            # state to work from, but `unknown` is forced True rather than
            # taken from the result — it used to default to False, so a
            # result carrying nothing was reported as a confident neutral
            # reading, and phi_computation reads this valence
            # (phi_computation.py:102) to compute a phi it then publishes.
            valence = estimation_result.get("valence", default_valence)
            arousal = estimation_result.get("arousal", default_arousal)
            values_present = ("valence" in estimation_result
                              and "arousal" in estimation_result)
            unknown = estimation_result.get("unknown", False) or not values_present

            # CRITICAL: Cache the result for determinism (same input → same output)
            # This ensures parallel execution produces consistent results
            self.emotion_cache.set(context.user_input, valence, arousal)
            logger.debug(f"Cached emotion values: valence={valence:.4f}, arousal={arousal:.4f}")

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "valence": valence,
                    "arousal": arousal,
                    "unknown": unknown,
                    "estimation_result": estimation_result,
                    "source": "emotion_estimator"
                }
            )
        except Exception as e:
            logger.error(f"Emotion estimation failed: {e}", exc_info=True)
            # Fallback: Use EchoState2 schema defaults on error (deterministic, not from unified_state)
            # CRITICAL: Use schema defaults, not unified_state values (for determinism)
            fallback_valence = 0.0  # EchoState2 default V (from schema)
            fallback_arousal = 0.5  # EchoState2 default A (from schema)

            # The crash path is deliberately NOT cached. Caching exists so an
            # identical input yields an identical measurement; caching a crash
            # makes a transient fault permanent for that input, and the next
            # turn would read the fabricated pair back without the estimator
            # ever being asked again. Determinism of a path that measured
            # nothing is not a property worth preserving. The cache has no
            # reader outside this block, so nothing downstream depends on the
            # entry existing.

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
                    "emotion estimation raised; valence and arousal are EchoState2 schema defaults, not an estimate",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",  # Don't fail pipeline on emotion estimation error
                data={**({
                    "valence": fallback_valence,
                    "arousal": fallback_arousal,
                    "unknown": True,
                    "error": str(e),
                    "source": "echo_state_schema_defaults"
                }), "block_outcome": _outcome.to_record_fields()}
            )

