"""Entropy Amplitude Post Gate — canonical block 27.

Checks entropy against coherence after narrative generation and flags the turn
when both are bad at once.

**Class (P-5): quality / revision, explicitly non-authorising.** It sets a flag
and returns the physics state unchanged. It cannot block, escalate or release,
which is what makes bounded degradation on failure legitimate here.

**Failure policy (P-4).** Three shapes used to share ``status="ok"`` with
``gate_action="pass"``, and one of them was a fabricated input:

- an absent physics state, and an absent ``entropy`` within it, are
  ``NOT_MEASURED`` / ``input_absent``. The previous code read a missing entropy
  as ``0.5`` and a missing coherence as ``1.0`` — defaults on the passing side
  of both thresholds, so a turn with no measurable inputs was recorded exactly
  like a turn that was measured and found clean.
- the criterion is a conjunction (``entropy > 0.8 AND coherence < 0.7``). With
  entropy above the threshold and coherence unavailable it cannot be settled:
  the evaluator ran and could not decide, which is ``INCONCLUSIVE``. With
  entropy at or below the threshold the conjunction is false whatever coherence
  was, so that path is a real ``PASS``.
- the delegate path is ``NOT_MEASURED`` / ``unknown``: the protocol returns a
  gated physics state and no verdict, so the delegate's result does not cross
  this boundary and this record cannot assert it.

The *gating behaviour* is unchanged by any of this — the flag fires on exactly
the inputs it fired on before. What changed is that the record no longer says a
check passed when there was nothing to check.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Observation,
    RecoveryAction,
    errored,
    inconclusive,
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)

ENTROPY_THRESHOLD = 0.8
COHERENCE_THRESHOLD = 0.7


class EntropyAmplitudeGateProtocol(Protocol):
    """Protocol for entropy/amplitude gating."""
    def apply_gate(
        self,
        physics_state: Dict[str, Any]
    ) -> Dict[str, Any]:  # Returns gated physics_state
        """Apply entropy/amplitude gate."""
        ...


class EntropyAmplitudePostGateBlock(PipelineBlock):
    """
    Entropy Amplitude Post Gate Block.

    Applies entropy/amplitude gate after narrative generation.
    """

    def __init__(self, gate: Optional[EntropyAmplitudeGateProtocol] = None):
        """
        Initialize block.

        Args:
            gate: Entropy/amplitude gate service
        """
        super().__init__("entropy_amplitude_post_gate")
        self.gate = gate

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — inline fallback handles missing gate service."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute entropy/amplitude post gate.

        When the injected gate service is available it is used.  Otherwise an
        inline fallback checks entropy + coherence: if entropy > 0.8 AND
        coherence < 0.7, the response is flagged for downstream awareness.
        """
        try:
            metadata = context.metadata or {}
            physics_state = metadata.get("physics_state", {})

            if not physics_state:
                return self._ok(
                    not_measured("no physics state after narrative generation",
                                 cause="input_absent"),
                    physics_state={},
                    gate_action="not_measured",
                )

            if self.gate:
                gated_physics_state = self.gate.apply_gate(physics_state=physics_state)
                return self._ok(
                    not_measured(
                        "delegated to the injected gate, whose protocol returns "
                        "no verdict — the result is not observable here",
                        cause="unknown"),
                    physics_state=gated_physics_state,
                    gate_action="delegated",
                )

            # Inline fallback: post-narrative entropy + coherence check
            entropy = physics_state.get("entropy")
            if entropy is None:
                return self._ok(
                    not_measured("physics state carries no entropy",
                                 cause="input_absent"),
                    physics_state=physics_state,
                    gate_action="not_measured",
                )

            coherence = self._coherence(metadata)

            if entropy <= ENTROPY_THRESHOLD:
                # The conjunction is false whatever coherence was.
                return self._ok(
                    measured_pass(1, entropy=entropy,
                                  entropy_threshold=ENTROPY_THRESHOLD),
                    physics_state=physics_state,
                    gate_action="pass",
                )

            if coherence is None:
                return self._ok(
                    inconclusive(
                        f"entropy {entropy:.3f} is above the {ENTROPY_THRESHOLD} "
                        "threshold, but no coherence score is available and the "
                        "criterion needs both", items_checked=1, entropy=entropy),
                    physics_state=physics_state,
                    gate_action="inconclusive",
                    entropy=entropy,
                )

            if coherence < COHERENCE_THRESHOLD:
                metadata["entropy_gate_warning"] = True
                return self._ok(
                    measured_fail(
                        f"entropy {entropy:.3f} above {ENTROPY_THRESHOLD} with "
                        f"coherence {coherence:.3f} below {COHERENCE_THRESHOLD}",
                        items_checked=1, entropy=entropy, coherence=coherence),
                    physics_state=physics_state,
                    gate_action="flagged",
                    entropy=entropy,
                    coherence=coherence,
                )

            return self._ok(
                measured_pass(1, entropy=entropy, coherence=coherence),
                physics_state=physics_state,
                gate_action="pass",
            )
        except Exception as e:
            logger.error(f"Entropy amplitude post gate failed: {e}", exc_info=True)
            metadata = context.metadata or {}
            # Fail-open, and `skipped` rather than `error`: this block is outside
            # the orchestrator's always-on set, so `is_error()` would attempt a
            # rollback — turning a non-authorising quality gate into a hard stop.
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"entropy gate raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"entropy gate raised {type(e).__name__}",
                error=e,
                data={
                    "physics_state": metadata.get("physics_state", {}),
                    "error": str(e),
                    "block_outcome": outcome.to_record_fields(),
                },
            )

    @staticmethod
    def _coherence(metadata: Dict[str, Any]) -> Optional[float]:
        """The coherence score, or ``None`` when there is not one.

        ``None`` rather than the previous ``1.0``: a missing score is not a
        perfect score, and defaulting it to the passing side of the threshold is
        the shape this migration exists to remove.
        """
        result = metadata.get("coherence_qa_result")
        if not isinstance(result, dict):
            return None
        score = result.get("coherence_score")
        return float(score) if isinstance(score, (int, float)) else None

    def _ok(self, measurement: Any, **data: Any) -> BlockResult:
        """A completed run, carrying whatever it actually established."""
        outcome = BlockOutcome(
            block_id=self.block_id,
            legacy_control_status="ok",
            block_run_status=BlockRunStatus.COMPLETED,
            measurement=measurement,
        )
        return BlockResult(
            block_id=self.block_id,
            status="ok",
            data={**data, "block_outcome": outcome.to_record_fields()},
        )
