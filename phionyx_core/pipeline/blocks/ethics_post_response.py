"""Ethics Post Response — canonical block 21.

**This block performs the post-generation content check, of which ethics and
coherence are two criteria.** The name is narrower than the responsibility, and
that is declared here rather than left to be discovered.

Coherence — internal-state leak detection and redaction — was canonical in
v2.4.0 as `coherence_qa`, was dropped in v2.5.0 with no successor mapping and
no recorded rationale, and has been in `blocks/archive/` since 709a0b04. Three
runtime consumers never stopped waiting for its output, so `response_build`'s
redaction path and three of `response_revision_gate`'s seventeen rules could
not fire. Restoring it as a 47th block would make the canonical count cited in
published papers, books and posts inconsistent; it does not need one. It needs
to run after the narrative exists and before block 41, and this block is the
designated post-generation check inside that window. See
`phionyx_core/pipeline/coherence_qa.py`.

**The record names which criterion was measured.** The two are evaluated
independently and reported together the way `response_revision_gate` reports
its own: `items_checked` counts the criteria that had inputs, the verdict is
FAIL if any evaluated criterion failed and PASS only if all of them passed, and
`criteria_measured` / `criteria_absent` say which were which. A block that
measures two things and emits one unqualified verdict is the collapse this
migration exists to remove.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult
from ..coherence_qa import assess_coherence
from ..ethics_measurement import measure_ethics
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Measurement,
    Observation,
    RecoveryAction,
    Verdict,
    errored,
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)


class EthicsProcessorProtocol(Protocol):
    """Protocol for ethics processing."""
    def check_ethics_post_response(
        self,
        frame: Any,
        narrative_response: str,
        cognitive_state: Any
    ) -> Dict[str, Any]:  # Returns ethics_result
        """Check ethics after response."""
        ...


class EthicsPostResponseBlock(PipelineBlock):
    """
    Post-generation content check: ethics and coherence.

    Performs the ethics check after narrative generation, and scans the
    generated text for internal-state leakage. See the module docstring for why
    the second criterion lives here rather than in a block of its own.
    """

    #: The criteria this block evaluates. Named so `items_checked` counts
    #: something that exists rather than a denominator invented at the call
    #: site (MA-3.9).
    CRITERIA = ("ethics", "coherence")

    def __init__(self, processor: Optional[EthicsProcessorProtocol] = None):
        """
        Initialize block.

        Args:
            processor: Ethics processor
        """
        super().__init__("ethics_post_response")
        self.processor = processor

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute ethics post response check.

        Args:
            context: Block context with frame and narrative_response

        Returns:
            BlockResult with ethics_result
        """
        try:
            # Get frame and narrative_response from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            narrative_response = metadata.get("narrative_text", "")
            cognitive_state = metadata.get("cognitive_state")

            # Coherence runs whether or not there is a frame or an ethics
            # evaluator: it needs only the generated text. Keeping it before the
            # early returns is what makes the redaction control reachable on
            # turns where ethics could not run.
            coherence_result = assess_coherence(narrative_response)
            if coherence_result is not None:
                metadata["coherence_qa_result"] = coherence_result
                context.metadata = metadata

            if not frame:
                ethics = not_measured(
                    "no perceptual frame in metadata — ethics was not assessed",
                    cause="input_absent")
            elif not self.processor:
                ethics = not_measured("no ethics processor is injected",
                                      cause="not_executed")
                ethics_result = None
            else:
                ethics_result = self.processor.check_ethics_post_response(
                    frame=frame,
                    narrative_response=narrative_response,
                    cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                )
                ethics = measure_ethics(ethics_result, evaluator=self.block_id)
            if not frame or not self.processor:
                ethics_result = None

            return self._ran(
                self._combine(ethics, coherence_result),
                ethics_result=ethics_result,
                coherence_qa_result=coherence_result)
        except Exception as e:
            logger.error(f"Ethics post response check failed: {e}", exc_info=True)
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

    def _combine(self, ethics: "Measurement",
                 coherence_result: Optional[Dict[str, Any]]) -> "Measurement":
        """One record over two criteria, saying which of them was measured.

        PASS only if every criterion that had an input passed; FAIL if any
        evaluated criterion failed; NOT_MEASURED if neither could be evaluated.
        `items_checked` counts the criteria that ran, never the ones that did
        not — a denominator of 2 on a turn where only coherence was evaluable
        is the fabricated denominator MA-3.9 names.
        """
        measured, failed, reasons = [], [], []

        if ethics.verdict is not Verdict.NOT_MEASURED:
            measured.append("ethics")
            if not ethics.verdict.is_passing:
                failed.append("ethics")
                reasons.append(f"ethics: {ethics.reason}")

        if coherence_result is not None:
            measured.append("coherence")
            if coherence_result["leak_detected"]:
                failed.append("coherence")
                reasons.append(
                    "coherence: internal state leaked into the response — "
                    + ", ".join(coherence_result["violations"]))

        detail = {
            "criteria_measured": ",".join(measured),
            "criteria_absent": ",".join(
                c for c in self.CRITERIA if c not in measured),
        }
        if not measured:
            # Carry the ethics measurement's own cause rather than picking one.
            # "no evaluator was injected" and "there was no input" are different
            # non-measurements and the record should not flatten them.
            return not_measured(
                f"neither criterion could be evaluated — {ethics.reason}, and "
                "there was no narrative text to scan",
                cause=ethics.cause or "unknown",
                # Passed by name rather than by `**detail`: `not_measured`
                # declares `inputs_present: bool | None` ahead of its `**detail`,
                # so a dict expansion is type-checked against that parameter.
                criteria_measured=detail["criteria_measured"],
                criteria_absent=detail["criteria_absent"])
        if failed:
            return measured_fail("; ".join(reasons), items_checked=len(measured),
                                 **detail)
        return measured_pass(len(measured), **detail)
