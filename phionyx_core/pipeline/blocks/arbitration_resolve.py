"""Arbitration Resolve — canonical block 40.

Resolves conflicts between modules using arbitration math.

**Repair 2 of 3, and the part of it that is safe to do.** The chain from
`confidence_fusion` (39) to `response_revision_gate` (41) is broken in two
places, and only the first is fixed here:

1. This block read `conflict_score` off ``confidence.metadata``, which
   `confidence_fusion` never populates. It therefore read 0.0 on every turn,
   emitted that 0.0, and — because both blocks merge their data into the same
   flat ``conflict_score`` key — **overwrote the value the fusion block had
   actually measured**. Verified 2026-08-02: fusion produced 0.516 for
   conflicting inputs and this block replaced it with 0.0. That is fixed by no
   longer emitting a number this block does not have.
2. The gate reads ``arbitration_result``, which nothing writes. **That wiring is
   deliberately not done**, because the value behind it does not mean what the
   gate's rule assumes — see below.

**Why the conflict signal is not wired into the revision gate.**
``meta/arbitration_math.compute_conflict_score`` computes ``1 - HHI`` over the
modules' normalised confidence shares. That is a *dispersion* index, not a
disagreement measure, and it runs opposite to the gate's rule at the extremes.
Measured:

===============================  ==============  ============================
modules                          conflict_score  gate rule at 0.60 / 0.85
===============================  ==============  ============================
0.9, 0.9, 0.9 (perfect accord)   0.667           would REWRITE
0.9, 0.8, 1.0 (mild spread)      0.664           would REWRITE
0.95, 0.05 (sharp disagreement)  0.095           no trigger
===============================  ==============  ============================

For N equal modules the value is ``1 - 1/N``, so it tracks how many modules
reported far more than whether they disagree, and ``is_conflicted = conflict >
0.5`` is true for any three that agree. The function's own docstring contains
both readings — "high conflict means modules disagree strongly" (not what the
maths does) and "low conflict means one module dominates" (what it does) — and
``tests/compliance_v4/test_arbitration_math.py::test_uniform_distribution``
pins the dispersion behaviour explicitly.

Changing that formula is a founder decision: it carries SF1 C11 / SF2
arbitration claim references and three tests depend on the current values.
Until it is taken, wiring the gate to this signal would make module *agreement*
rewrite responses, so the record says the criterion was not measured rather
than reporting a 0.0 that was never computed.
"""

import logging
from typing import Optional

from ..base import PipelineBlock, BlockContext, BlockResult
from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    Observation,
    RecoveryAction,
    errored,
    measured_pass,
    not_measured,
)

logger = logging.getLogger(__name__)


class ArbitrationResolveBlock(PipelineBlock):
    """
    Resolves inter-module conflicts using arbitration math.

    If conflict score exceeds threshold, applies resolution strategy:
    - Safety-first: defer to ethics engine
    - Confidence-weighted: trust highest-confidence module
    - Consensus: require majority agreement
    """

    def __init__(self, conflict_threshold: float = 0.5):
        super().__init__("arbitration_resolve")
        self.conflict_threshold = conflict_threshold

    def should_skip(self, context: BlockContext) -> Optional[str]:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    def _unmeasured(self, reason: str) -> BlockResult:
        """No conflict score to resolve. Emit no number, so the one measured
        upstream survives in `metadata["conflict_score"]`."""
        outcome = BlockOutcome(
            block_id=self.block_id,
            legacy_control_status="ok",
            block_run_status=BlockRunStatus.COMPLETED,
            measurement=not_measured(reason, cause="input_absent"),
        )
        return BlockResult(
            block_id=self.block_id,
            status="ok",
            data={"arbitration_needed": False,
                  "block_outcome": outcome.to_record_fields()},
        )

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            confidence = context.v4_confidence
            if confidence is None:
                return self._unmeasured("no confidence payload on the context")

            # Check if arbitration is needed
            metadata = context.metadata or {}
            payload_metadata = getattr(confidence, "metadata", None)
            raw = (payload_metadata.get("conflict_score")
                   if isinstance(payload_metadata, dict) else None)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                return self._unmeasured(
                    "the confidence payload carries no conflict score")
            conflict_score = float(raw)

            resolution = "none"
            if conflict_score > self.conflict_threshold:
                # Safety-first resolution: if ethics is enforced, defer to it
                ethics_result = metadata.get("ethics_result", {})
                if isinstance(ethics_result, dict) and ethics_result.get("enforced"):
                    resolution = "safety_override"
                else:
                    resolution = "confidence_weighted"

                logger.info(
                    f"Arbitration resolved: conflict={conflict_score:.2f}, "
                    f"resolution={resolution}"
                )

            needed = conflict_score > self.conflict_threshold
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=measured_pass(1, conflict_score=conflict_score,
                                          resolution_strategy=resolution,
                                          arbitration_needed=needed),
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "arbitration_needed": needed,
                    "conflict_score": conflict_score,
                    "resolution_strategy": resolution,
                    "block_outcome": outcome.to_record_fields(),
                },
            )
        except Exception as e:
            logger.error(f"Arbitration resolve failed: {e}", exc_info=True)
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"arbitration raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"arbitration raised {type(e).__name__}",
                error=e,
                data={"arbitration_needed": False, "error": str(e),
                      "block_outcome": outcome.to_record_fields()},
            )

    def get_dependencies(self) -> list[str]:
        return ["confidence_fusion"]
