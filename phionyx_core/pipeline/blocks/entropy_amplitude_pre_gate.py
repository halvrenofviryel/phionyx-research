"""Entropy Amplitude Pre Gate — canonical block 12.

Checks cognitive entropy before CEP evaluation. When entropy is elevated it
appends a high-uncertainty instruction to the context string that
``narrative_layer`` later reads.

**Class (P-5): quality / revision, explicitly non-authorising.** This block
cannot block, escalate or release. Its entire effect is to add a sentence to a
prompt. That is what makes bounded degradation on failure legitimate here and
not in the safety/ethics class — a gate that in fact authorises output belongs
in the second class regardless of what it is named.

**Failure policy (P-4).** Fail-open on the pipeline, honest on the record. The
three things this block used to call ``status="ok"`` are now distinguished:

- entropy above the threshold is a **measured negative** — the check ran and its
  criterion was not met. That is ``FAIL``, not an error and not a
  non-measurement. The injected warning is the block's product, not a recovery.
- entropy absent is ``NOT_MEASURED`` with cause ``input_absent``. Nothing was
  compared, so nothing passed.
- the delegate path is ``NOT_MEASURED`` with cause ``unknown``: the protocol's
  return type carries a context string and a state, **and no verdict**. The
  measurement happens inside the delegate and does not cross this boundary, so
  this record cannot assert its result. That is a gap in the protocol, recorded
  here rather than papered over with a ``PASS`` this block did not establish.
"""

import logging
from typing import Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Observation,
    RecoveryAction,
    errored,
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)

ENTROPY_THRESHOLD = 0.8


class EntropyAmplitudeGateProtocol(Protocol):
    """Protocol for entropy/amplitude gating."""
    def apply_gate(
        self,
        cognitive_state: Any,
        unified_state: Optional[Any],
        enhanced_context_string: str
    ) -> tuple[str, Optional[Any]]:  # Returns (enhanced_context_string, gated_state)
        """Apply entropy/amplitude gate."""
        ...


class EntropyAmplitudePreGateBlock(PipelineBlock):
    """
    Entropy Amplitude Pre Gate Block.

    Applies entropy/amplitude gate before CEP evaluation.
    """

    def __init__(self, gate: Optional[EntropyAmplitudeGateProtocol] = None):
        """
        Initialize block.

        Args:
            gate: Entropy/amplitude gate service
        """
        super().__init__("entropy_amplitude_pre_gate")
        self.gate = gate

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — inline fallback handles missing gate service."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute entropy/amplitude pre gate.

        When the injected gate service is available it is used.  Otherwise an
        inline fallback injects a high-uncertainty warning into the context
        string when entropy exceeds the 0.8 threshold.
        """
        try:
            metadata = context.metadata or {}
            enhanced_context_string = metadata.get("enhanced_context_string", "")
            entropy = context.current_entropy

            if self.gate:
                cognitive_state = metadata.get("cognitive_state")
                unified_state = metadata.get("unified_state")
                enhanced_context_string, gated_state = self.gate.apply_gate(
                    cognitive_state=cognitive_state,
                    unified_state=unified_state,
                    enhanced_context_string=enhanced_context_string,
                )
                return self._ok(
                    not_measured(
                        "delegated to the injected gate, whose protocol returns "
                        "no verdict — the result is not observable here",
                        cause="unknown"),
                    enhanced_context_string=enhanced_context_string,
                    gated_state=gated_state,
                    gate_action="delegated",
                )

            if entropy is None:
                return self._ok(
                    not_measured("no entropy on the context — nothing to compare "
                                 f"against the {ENTROPY_THRESHOLD} threshold",
                                 cause="input_absent"),
                    enhanced_context_string=enhanced_context_string,
                    gate_action="not_measured",
                    entropy=None,
                )

            # Inline fallback gating
            if entropy > ENTROPY_THRESHOLD:
                warning = (
                    "[HIGH UNCERTAINTY] Current cognitive entropy is elevated. "
                    "Prioritize factual, verifiable information."
                )
                enhanced_context_string = enhanced_context_string + "\n\n" + warning
                return self._ok(
                    measured_fail(
                        f"entropy {entropy:.3f} above the {ENTROPY_THRESHOLD} "
                        "threshold; uncertainty instruction injected",
                        items_checked=1, entropy=entropy),
                    enhanced_context_string=enhanced_context_string,
                    gate_action="warning_injected",
                    entropy=entropy,
                )

            return self._ok(
                measured_pass(1, entropy=entropy, threshold=ENTROPY_THRESHOLD),
                enhanced_context_string=enhanced_context_string,
                gate_action="pass",
                entropy=entropy,
            )
        except Exception as e:
            logger.error(f"Entropy amplitude pre gate failed: {e}", exc_info=True)
            metadata = context.metadata or {}
            # Fail-open, and `skipped` rather than `error`: this block is outside
            # the orchestrator's always-on set, so `is_error()` would attempt a
            # rollback — turning a non-authorising quality gate into a hard stop.
            # The decision here is to stop claiming the entropy check ran.
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
                    "enhanced_context_string": metadata.get("enhanced_context_string", ""),
                    "error": str(e),
                    "block_outcome": outcome.to_record_fields(),
                },
            )

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
