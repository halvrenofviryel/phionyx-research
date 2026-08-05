"""
Confidence Fusion Block — v3.0.0
===================================

Block: confidence_fusion
Position: After phi_computation
v4 Schema: ConfidencePayload

Fuses confidence estimates from multiple modules using W_final.
"""

import logging
from typing import Any, Optional

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


def _number(source: Any, *names: str) -> Optional[float]:
    """The first of `names` carrying a number, or ``None``.

    ``None`` and not a default: this block fuses the signals that reported, and
    a placeholder standing in for a silent module shifts the fused value.
    Booleans are excluded — ``isinstance(True, int)`` is True in Python, and a
    flag where a score belongs is malformed input, not a score of 1.0.
    """
    for name in names:
        value = (source.get(name) if isinstance(source, dict)
                 else getattr(source, name, None))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        return float(value)
    return None


class ConfidenceFusionBlock(PipelineBlock):
    """
    Fuses confidence from multiple sources into a v4 ConfidencePayload.

    Uses arbitration_math.compute_w_final for weighted fusion
    and uncertainty decomposition from meta/uncertainty.py.
    """

    def __init__(self):
        super().__init__("confidence_fusion")

    def should_skip(self, context: BlockContext) -> Optional[str]:
        # No skip — v2.5 uses inline fallback, v3.0+ uses full v4 path
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        metadata = context.metadata or {}

        # --- v3.0+ full path: use arbitration_math + ConfidencePayload ---
        if context.pipeline_version >= "3.0.0":
            return await self._execute_v4(context, metadata)

        # --- v2.5 inline fallback: deterministic w_final from physics ---
        return self._execute_inline(context, metadata)

    def _execute_inline(self, context: BlockContext, metadata: dict) -> BlockResult:
        """Inline confidence fusion: w_final = weighted mean of phi, confidence, safety.

        Formula:
            phi_signal     = physics_state.phi (default 0.5)
            conf_signal    = physics_state.confidence_score (default 0.5)
            safety_signal  = 1.0 - physics_state.risk_level (default 1.0)
            w_final = 0.4 * phi_signal + 0.35 * conf_signal + 0.25 * safety_signal
            clamped to [0.0, 1.0]
        """
        physics_state = metadata.get("physics_state", {})
        if not isinstance(physics_state, dict):
            physics_state = {}

        phi = float(physics_state.get("phi", 0.5))
        confidence_score = float(physics_state.get("confidence_score", 0.5))
        risk_level = float(physics_state.get("risk_level", 0.0))
        safety_signal = 1.0 - min(1.0, max(0.0, risk_level))

        # Weighted fusion
        w_final = 0.4 * min(1.0, max(0.0, phi)) + \
                  0.35 * min(1.0, max(0.0, confidence_score)) + \
                  0.25 * safety_signal
        w_final = max(0.0, min(1.0, w_final))

        # Propagate to metadata for downstream blocks (narrative_layer, response_build)
        if context.metadata is None:
            context.metadata = {}
        context.metadata["w_final"] = w_final

        # Also write to physics_state for chat.py extraction
        if isinstance(context.metadata.get("physics_state"), dict):
            context.metadata["physics_state"]["w_final"] = w_final

        is_uncertain = w_final < 0.5
        recommendation = "proceed" if w_final >= 0.6 else "hedge" if w_final >= 0.4 else "block"

        return BlockResult(
            block_id=self.block_id,
            status="ok",
            data={
                "w_final": w_final,
                "is_uncertain": is_uncertain,
                "recommendation": recommendation,
                "modules_fused": 3,
                "source": "inline_fallback",
                "phi_signal": phi,
                "conf_signal": confidence_score,
                "safety_signal": safety_signal,
            },
        )

    async def _execute_v4(self, context: BlockContext, metadata: dict) -> BlockResult:
        """Full v4 path with arbitration_math and ConfidencePayload."""
        try:
            from ...contracts.v4.confidence_payload import ConfidencePayload, UncertaintyType
            from ...meta.arbitration_math import compute_w_final

            # Gather confidence signals from various modules. A module that did
            # not report is *not* fused: the previous code read a missing
            # ConfidenceEstimator score as 0.5 and a missing ethics risk as 0.0
            # (so `ethics_safety` was 1.0 on every turn, whether or not ethics
            # ran). Those placeholders moved the fused value, and downstream —
            # since `response_revision_gate` now reads `w_final` — they would
            # move a directive.
            module_confidences = {}

            score = _number(metadata.get("confidence_result"), "confidence_score",
                            "confidence")
            if score is not None:
                module_confidences["confidence_estimator"] = score

            # From physics state (phi-based)
            physics_state = metadata.get("physics_state", {})
            phi = _number(physics_state, "phi")
            if phi is not None:
                module_confidences["physics_phi"] = min(1.0, phi)

            # From ethics (inverse risk). The risk field's name depends on the
            # injected ethics processor and is not fixed anywhere in this
            # repository, so the known names are tried and the signal is used
            # only when one of them carries a number.
            risk = _number(metadata.get("ethics_result"),
                           "max_risk_score", "risk_score", "harm_risk")
            if risk is not None:
                module_confidences["ethics_safety"] = 1.0 - risk

            if not module_confidences:
                # `compute_w_final({})` returns 0.5 — a neutral that is
                # indistinguishable from a measured 0.5 and sits exactly on the
                # revision gate's rewrite threshold. Nothing is fused and no
                # `w_final` is written; every consumer already guards on it
                # being absent.
                outcome = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.COMPLETED,
                    measurement=not_measured(
                        "no module reported a confidence signal",
                        cause="input_absent"),
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"modules_fused": 0,
                          "block_outcome": outcome.to_record_fields()},
                )

            # Fuse
            arb_result = compute_w_final(module_confidences)

            # Build payload
            payload = ConfidencePayload(
                confidence_score=arb_result.w_final,
                is_uncertain=arb_result.w_final < 0.6,
                recommendation="proceed" if arb_result.w_final >= 0.6 else "hedge" if arb_result.w_final >= 0.4 else "block",
                reasoning=f"Fused from {len(module_confidences)} modules, conflict={arb_result.conflict_score:.2f}",
                dominant_uncertainty=UncertaintyType.EPISTEMIC,
                source_estimator="confidence_fusion_v4",
            )

            # `arbitration_resolve` reads the conflict score off this payload's
            # metadata. It was never populated, so that block read 0.0 on every
            # turn — the second break in the chain from here to the revision
            # gate. Repair 2, second half; unblocked once
            # `compute_conflict_score` was corrected to measure disagreement.
            payload.metadata["conflict_score"] = arb_result.conflict_score
            payload.metadata["is_conflicted"] = arb_result.is_conflicted
            payload.metadata["modules_fused"] = len(module_confidences)

            context.v4_confidence = payload
            # Propagate w_final to metadata
            context.metadata["w_final"] = arb_result.w_final

            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=measured_pass(len(module_confidences),
                                          w_final=arb_result.w_final,
                                          modules=",".join(sorted(module_confidences))),
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "w_final": arb_result.w_final,
                    "conflict_score": arb_result.conflict_score,
                    "modules_fused": len(module_confidences),
                    "is_conflicted": arb_result.is_conflicted,
                    "block_outcome": outcome.to_record_fields(),
                },
            )
        except Exception as e:
            logger.error(f"Confidence fusion v4 failed: {e}", exc_info=True)
            # `w_final: 0.5` was written here. It is the value `compute_w_final`
            # also returns for "nothing to fuse", it is indistinguishable from a
            # measured 0.5, and it sits exactly on the revision gate's rewrite
            # threshold — so a crash in this block would have prefixed every
            # response once the gate started reading it. No value is written.
            outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="skipped",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    f"confidence fusion raised {type(e).__name__}: {e}"),
                recovery_action=RecoveryAction.FALLBACK,
                observation=Observation.RECORDED,
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                skip_reason=f"confidence fusion raised {type(e).__name__}",
                error=e,
                data={"error": str(e),
                      "block_outcome": outcome.to_record_fields()},
            )

    def get_dependencies(self) -> list[str]:
        return ["phi_computation"]
