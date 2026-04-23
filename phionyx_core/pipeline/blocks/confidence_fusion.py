"""
Confidence Fusion Block — v3.0.0
===================================

Block: confidence_fusion
Position: After phi_computation
v4 Schema: ConfidencePayload

Fuses confidence estimates from multiple modules using W_final.
"""

import logging
from typing import Optional

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


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

            # Gather confidence signals from various modules
            module_confidences = {}

            # From ConfidenceEstimator
            conf_result = metadata.get("confidence_result")
            if conf_result:
                score = conf_result.get("confidence_score", 0.5) if isinstance(conf_result, dict) else getattr(conf_result, "confidence_score", 0.5)
                module_confidences["confidence_estimator"] = score

            # From physics state (phi-based)
            physics_state = metadata.get("physics_state", {})
            phi = physics_state.get("phi")
            if phi is not None:
                module_confidences["physics_phi"] = min(1.0, phi)

            # From ethics (inverse risk)
            ethics_result = metadata.get("ethics_result", {})
            max_risk = ethics_result.get("max_risk_score", 0.0) if isinstance(ethics_result, dict) else 0.0
            module_confidences["ethics_safety"] = 1.0 - max_risk

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

            context.v4_confidence = payload
            # Propagate w_final to metadata
            context.metadata["w_final"] = arb_result.w_final

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "w_final": arb_result.w_final,
                    "conflict_score": arb_result.conflict_score,
                    "modules_fused": len(module_confidences),
                    "is_conflicted": arb_result.is_conflicted,
                },
            )
        except Exception as e:
            logger.error(f"Confidence fusion v4 failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"w_final": 0.5, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["phi_computation"]
