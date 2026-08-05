"""Audit Layer Block — canonical block 44.

**What this block is, and what it is not.** It computes an *integrity
assessment* for the turn: either by delegating to an injected processor, or —
when none is injected — by an inline heuristic over response length, the
presence of a physics state and the coherence result. It returns that
assessment as block data.

It does **not** write an audit record. It contains no signing, no hash chaining
and no ``AuditRecord``. Four public compliance mappings cited this block as an
"Ed25519 hash chain" and rated a control **Full** on that citation; all four
were corrected on 2026-08-02 after the citation was checked against this file.
The signed, hash-chained envelope chain that does exist is written by the MCP
tool boundary, and ``contracts/v4/audit_record.py`` specifies one for the
pipeline that is not yet constructed.

The name is the reason the mistake was easy to make, so the correction belongs
here rather than only in the documents that repeated it.

**Failure policy** (P-4/P-5, oversight class). This block does not gate output:
it observes. A failure is therefore fail-open on the pipeline and an *evidence
gap* on the record — the turn proceeds, and the record says the assessment did
not happen. What it must never do is what it used to do: return ``status="ok"``
after its own processor raised, which telemetry reads through ``is_success()``
as a turn that was audited.
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
    measured_fail,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)


class AuditLayerProcessorProtocol(Protocol):
    """Protocol for audit layer processing."""
    async def process_audit(
        self,
        frame: Any,
        unified_state: Optional[Any],
        narrative_response: str,
        physics_state: Dict[str, Any]
    ) -> Dict[str, Any]:  # Returns audit result
        """Process audit layer."""
        ...


class AuditLayerBlock(PipelineBlock):
    """
    Audit Layer Block.

    Performs audit operations (snapshots, event logging, explainability).
    """

    def __init__(self, processor: Optional[AuditLayerProcessorProtocol] = None):
        """
        Initialize block.

        Args:
            processor: Audit layer processor
        """
        super().__init__("audit_layer")
        self.processor = processor

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — inline fallback computes basic integrity."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """Execute audit layer processing with inline fallback."""
        try:
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            unified_state = metadata.get("unified_state")
            narrative_response = metadata.get("narrative_text", "")
            physics_state = metadata.get("physics_state", {})

            if not frame:
                # No frame is not a clean audit — it is an audit that had
                # nothing to read. `ok` here made "there was no input" and
                # "the integrity check passed" the same record.
                outcome = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="skipped",
                    block_run_status=BlockRunStatus.NOT_STARTED,
                    measurement=not_measured(
                        "no perceptual frame in metadata — nothing to assess",
                        cause="input_absent"),
                    recovery_action=RecoveryAction.SKIP,
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="skipped",
                    skip_reason="no perceptual frame in metadata",
                    data={"audit_result": None,
                          "block_outcome": outcome.to_record_fields()},
                )

            if self.processor:
                audit_result = await self.processor.process_audit(
                    frame=frame,
                    unified_state=unified_state,
                    narrative_response=narrative_response,
                    physics_state=physics_state,
                )
            else:
                # Inline fallback: basic integrity assessment
                integrity = 1.0
                issues = []
                if not narrative_response or len(narrative_response) < 3:
                    integrity -= 0.2
                    issues.append("empty_or_short_response")
                if not physics_state or not isinstance(physics_state, dict):
                    integrity -= 0.1
                    issues.append("missing_physics_state")
                elif physics_state.get("phi") is None:
                    integrity -= 0.1
                    issues.append("missing_phi")
                # Coherence violation lowers integrity
                coherence_qa = metadata.get("coherence_qa_result", {})
                if isinstance(coherence_qa, dict) and coherence_qa.get("leak_detected"):
                    integrity -= 0.2
                    issues.append("state_leak_detected")
                integrity = max(0.0, integrity)
                audit_result = {
                    "status": "ok" if integrity > 0.5 else "degraded",
                    "integrity_score": integrity,
                    "issues": issues,
                    "source": "inline_fallback",
                }

            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=self._measure(audit_result),
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"audit_result": audit_result,
                      "block_outcome": outcome.to_record_fields()},
            )
        except Exception as e:
            logger.error(f"Audit layer processing failed: {e}", exc_info=True)
            # Fail-open on the pipeline, honest on the record. `skipped` and not
            # `error`: the orchestrator attempts a rollback on `is_error()` for
            # any block outside its always-on set, so reporting an error here
            # would convert an oversight block from fail-open to fail-closed —
            # a different decision from the one being made, which is to stop
            # claiming the turn was audited when the assessment raised.
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"integrity assessment raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"integrity assessment raised {type(e).__name__}",
                error=e,
                data={"audit_result": None, "error": str(e),
                      "block_outcome": outcome.to_record_fields()},
            )

    @staticmethod
    def _measure(audit_result: Dict[str, Any]) -> "Any":
        """Read the assessment as a measurement, without overstating it.

        The inline fallback scores three heuristics; the injected processor may
        do more. Either way this is an integrity *assessment* of one turn, so
        `items_checked` is 1 — not a count of audit records written, which is
        zero either way.
        """
        status = (audit_result or {}).get("status")
        if status is None:
            return not_measured(
                "the assessment returned no status", cause="unknown")
        if status == "degraded":
            issues = ", ".join((audit_result or {}).get("issues", [])) or "unspecified"
            return measured_fail(f"integrity below threshold: {issues}",
                                 items_checked=1)
        return measured_pass(1, source=(audit_result or {}).get("source", "processor"))

