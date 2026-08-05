"""
CEP Evaluation Block
=====================

Block: cep_evaluation
Evaluates CEP (Conscious Echo Proof) for safety and coherence.
"""

import logging
from typing import Any, Dict, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
    not_measured,
)

logger = logging.getLogger(__name__)


#: The eight CEPMetrics fields, named rather than discovered, so a renamed
#: field shows up as a missing key in the record instead of being silently
#: dropped the way the whole object was.
_METRIC_FIELDS = (
    "phi_echo_quality",
    "phi_echo_density",
    "echo_stability",
    "temporal_delay",
    "self_reference_ratio",
    "trauma_language_score",
    "mirror_self_score",
    "variation_novelty_score",
)


def _metrics_to_record(metrics: Any) -> Optional[Dict[str, float]]:
    """Flatten CEPMetrics into JSON-safe floats, or None if there are none.

    The orchestrator drops non-JSON-safe values from block data, which is how
    these were lost. Only float-able fields are kept: a field that stops being
    numeric should go missing loudly rather than serialise as a repr.
    """
    if metrics is None:
        return None

    record = {}
    for name in _METRIC_FIELDS:
        value = getattr(metrics, name, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            record[name] = float(value)
    return record or None


class CEPEvaluatorProtocol(Protocol):
    """Protocol for CEP evaluation."""
    async def evaluate(
        self,
        frame: Any,
        user_input: str,
        narrative_response: str,
        cognitive_state: Any,
        physics_state: Optional[Dict[str, Any]] = None,
        unified_state: Any = None,
        current_integrity: Optional[float] = None,
        time_delta: Optional[float] = None,
    ) -> tuple[Any, Any]:  # Returns (cep_flags, cep_config)
        """Evaluate CEP.

        Declared async because the only implementation is: the adapter in
        `orchestrator/block_factory.py` awaits `evaluate_cep_and_update_safety`.
        The protocol said sync, so the call site below unpacked a coroutine and
        raised — caught, and recorded as a pass. mypy 1.x did not see it;
        mypy 2.x does.
        """
        ...


class CepEvaluationBlock(PipelineBlock):
    """
    CEP Evaluation Block.

    Evaluates CEP (Conscious Echo Proof) for safety and coherence.
    """

    def __init__(self, evaluator: Optional[CEPEvaluatorProtocol] = None):
        """
        Initialize block.

        Args:
            evaluator: CEP evaluator service
        """
        super().__init__("cep_evaluation")
        self.evaluator = evaluator

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if no evaluator available."""
        if self.evaluator is None:
            return "cep_evaluator_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute CEP evaluation.

        Args:
            context: Block context with frame and narrative_response

        Returns:
            BlockResult with cep_flags and cep_config
        """
        try:
            # Get frame and narrative_response from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            narrative_response = metadata.get("narrative_text", "")
            cognitive_state = metadata.get("cognitive_state")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"cep_flags": None, "cep_config": None}
                )

            # Evaluate CEP
            if self.evaluator:
                # OD-16: the turn's own state is passed through. The adapter
                # used to substitute physics_state={}, unified_state=None,
                # time_delta=1.0 and current_integrity=100.0 — each under a
                # comment saying "Will be set from context", and nothing set
                # them. A safety evaluation was being told the system was at
                # full integrity, unconditionally, against a state that was
                # not this turn's. echo_orchestrator.py:875 does update
                # current_integrity during a turn, so the context carries a
                # real value the adapter was discarding.
                metadata = context.metadata or {}
                # `time_update_sot` is canonical 2 and this block is canonical
                # 19, so the key is normally present. Its absence means the
                # turn reached a safety evaluation without a clock, which is
                # worth recording rather than papering over — see below.
                time_delta = metadata.get("time_delta")
                # The CEP verdict is computed from phi and entropy. When the
                # turn did not measure them the bridge substitutes 0.0, and
                # the entropy substitution is not inert: it drives
                # phi_echo_density to its maximum, which flips
                # is_self_narrative_blocked at 18 measured (self_reference,
                # novelty) points. The evaluation still runs — fail-open is
                # the existing decision — but the record must not report a
                # verdict as though its inputs were measured.
                physics = metadata.get("physics_state") or {}
                unmeasured = [
                    name for name in ("phi", "entropy")
                    if physics.get(name) is None
                ]
                cep_flags, cep_config = await self.evaluator.evaluate(
                    frame=frame,
                    user_input=context.user_input,
                    narrative_response=narrative_response,
                    cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None),
                    physics_state=metadata.get("physics_state") or {},
                    unified_state=metadata.get("unified_state"),
                    current_integrity=context.current_integrity,
                    time_delta=time_delta,
                )
            else:
                cep_flags = None
                cep_config = None
                time_delta = None
                unmeasured = []

            data = {
                "cep_flags": cep_flags,
                "cep_config": cep_config,
            }
            # OD-19. The CEP metrics were computed every turn and then thrown
            # away: CEPMetrics is a plain object, and echo_orchestrator.py:787
            # skips any result value that is not JSON-safe, so nothing about
            # the evaluation reached the record.
            #
            # That is why OD-19 could not be decided. phi_self_threshold is
            # 0.72 against a phi_echo_quality of phi/10, and phi tops out near
            # 3.24 under the declared parameter bounds — so the gate needs a
            # phi the formula cannot produce. Choosing a reachable threshold
            # means knowing the distribution, and the distribution was never
            # recorded. This publishes it as plain floats so it can be.
            metrics = _metrics_to_record(cep_config)
            if metrics is not None:
                data["cep_metrics"] = metrics
            if self.evaluator and (unmeasured or time_delta is None):
                # The evaluation ran and its flags are reported as they stand;
                # what is not claimed is that they were computed from measured
                # inputs. Ordered so the safety-relevant absences lead.
                missing = list(unmeasured)
                if time_delta is None:
                    missing.append("time_delta")
                data["block_outcome"] = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.COMPLETED,
                    measurement=not_measured(
                        "the CEP verdict was computed with "
                        f"{', '.join(missing)} absent from the turn",
                        cause="input_absent",
                    ),
                    operating_mode="degraded",
                ).to_record_fields()

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=data
            )
        except Exception as e:
            logger.error(f"CEP evaluation failed: {e}", exc_info=True)
            # Fail-open on the pipeline, honest on the record.
            #
            # This returned status="ok", so a CEP evaluation that raised was
            # indistinguishable from one that ran and found nothing. "skipped"
            # says what happened and keeps the fail-open behaviour: the
            # orchestrator continues past a skip and attempts a rollback only on
            # "error", so reporting an error here would quietly convert this
            # block from fail-open to fail-closed — a different decision from
            # the one being made, which is to stop claiming a pass.
            # The record was incomplete here and the gate could not see it:
            # `skip_reason` said what happened on the CONTROL channel, and the
            # measurement channel said nothing at all, so a reader of the
            # record could not tell a crashed safety evaluation from one that
            # ran and raised no flags. Found only after
            # test_pipeline_doctrine_alignment was widened to follow
            # `status="skipped"` returns as well as `status="ok"` ones.
            _outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    "the CEP safety evaluation raised; no flags were computed",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"CEP evaluation raised {type(e).__name__}: {e}",
                error=e,
                data={
                    "cep_flags": None,
                    "cep_config": None,
                    "error": str(e),
                    "block_outcome": _outcome.to_record_fields(),
                }
            )

