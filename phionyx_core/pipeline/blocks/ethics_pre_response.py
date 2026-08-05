"""
Ethics Pre Response Block
==========================

Block: ethics_pre_response
Ethics check before narrative generation.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ..ethics_measurement import measure_ethics
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Measurement,
    Observation,
    RecoveryAction,
    errored,
    not_measured,
)

logger = logging.getLogger(__name__)


class EthicsProcessorProtocol(Protocol):
    """Protocol for ethics processing."""
    def check_ethics_pre_response(
        self,
        frame: Any,
        user_input: str,
        cognitive_state: Any
    ) -> Dict[str, Any]:  # Returns ethics_result
        """Check ethics before response."""
        ...


class EthicsPreResponseBlock(PipelineBlock):
    """
    Ethics Pre Response Block.

    Performs ethics check before narrative generation.
    """

    def __init__(self, processor: Optional[EthicsProcessorProtocol] = None):
        """
        Initialize block.

        Args:
            processor: Ethics processor
        """
        super().__init__("ethics_pre_response")
        self.processor = processor

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute ethics pre response check.

        Args:
            context: Block context with frame and inputs

        Returns:
            BlockResult with ethics_result
        """
        try:
            # Get frame from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            cognitive_state = metadata.get("cognitive_state")

            if not frame:
                return self._ran(
                    not_measured("no perceptual frame in metadata — the input "
                                 "was not assessed", cause="input_absent"),
                    ethics_result=None)

            # Check ethics
            if self.processor:
                # Check if processor method is async
                import inspect
                if hasattr(self.processor, 'check_ethics_pre_response'):
                    check_method = self.processor.check_ethics_pre_response
                    if inspect.iscoroutinefunction(check_method):
                        # Async method - await it
                        ethics_result = await check_method(
                            frame=frame,
                            user_input=context.user_input,
                            cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                        )
                    else:
                        # Sync method - call directly
                        ethics_result = check_method(
                            frame=frame,
                            user_input=context.user_input,
                            cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                        )
                else:
                    # Fallback: use assess_ethics_pre_response if available
                    if hasattr(self.processor, 'assess_ethics_pre_response'):
                        ethics_result = self.processor.assess_ethics_pre_response(
                            user_input=context.user_input,
                            unified_state=None,
                            current_entropy=0.5,
                            valence_from_emotion=0.0,
                            arousal_from_emotion=0.5
                        )
                        # Convert to expected format
                        # `status` is not defaulted to "ok" here any more: a
                        # processor that returned no status established no
                        # verdict, and measure_ethics reads a missing status as
                        # NOT_MEASURED rather than as a clear result.
                        ethics_result = {
                            "status": ethics_result.get("status"),
                            "risk_level": ethics_result.get("risk_level", 0.0),
                            "reason": ethics_result.get("reason"),
                            "harm_risk": ethics_result.get("risk_level", 0.0)
                        }
                    else:
                        ethics_result = None
            else:
                ethics_result = None

            # Include harm_risk directly in data for test compatibility
            data = {
                "ethics_result": ethics_result
            }
            # Also include harm_risk directly if available
            if ethics_result:
                if isinstance(ethics_result, dict):
                    data["harm_risk"] = ethics_result.get("harm_risk", ethics_result.get("risk_level", 0.0))
                    data["risk_level"] = ethics_result.get("risk_level", 0.0)
                    data["status"] = ethics_result.get("status", "ok")
                elif hasattr(ethics_result, 'harm_risk'):
                    data["harm_risk"] = ethics_result.harm_risk
                elif hasattr(ethics_result, 'risk_level'):
                    data["harm_risk"] = ethics_result.risk_level
                    data["risk_level"] = ethics_result.risk_level

            return self._ran(
                measure_ethics(ethics_result, evaluator=self.block_id), **data)
        except Exception as e:
            logger.error(f"Ethics pre response check failed: {e}", exc_info=True)
            return self._raised(e)

    def _ran(self, measurement: "Measurement", **data) -> BlockResult:
        """The block completed. `legacy_control_status` reports that the block
        did its job, not what it measured — those are the two axes this
        migration exists to separate, and conflating them here is what broke
        the "no blocks skip on v3.0.0" invariant when arbitration_resolve was
        first migrated."""
        outcome = BlockOutcome(
            block_id=self.block_id,
            legacy_control_status="ok",
            block_run_status=BlockRunStatus.COMPLETED,
            measurement=measurement,
        )
        return BlockResult(
            block_id=self.block_id, status="ok",
            data={**data, "block_outcome": outcome.to_record_fields()})

    def _raised(self, exc: Exception, **data) -> BlockResult:
        """Fail-open on the pipeline, ERROR on the record. `skipped` and not
        `error`: this block is outside the orchestrator's always-on set, so
        `is_error()` would attempt a rollback and turn a raised ethics check
        into a hard stop — a separate decision. What changes is that the record
        stops reporting a successful check."""
        outcome = BlockOutcome(
            block_id=self.block_id,
            legacy_control_status="skipped",
            block_run_status=BlockRunStatus.FAILED,
            measurement=errored(f"ethics check raised {type(exc).__name__}: {exc}"),
            recovery_action=RecoveryAction.FALLBACK,
            observation=Observation.RECORDED,
            operating_mode="degraded",
        )
        return BlockResult(
            block_id=self.block_id, status="skipped",
            skip_reason=f"ethics check raised {type(exc).__name__}", error=exc,
            data={**data, "ethics_result": None, "error": str(exc),
                  "block_outcome": outcome.to_record_fields()})
