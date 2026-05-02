"""
Trust Evaluation Block
=======================

Block: trust_evaluation
Evaluates trust relationships for the current interaction context.
Determines transitive trust levels between entities.

Position in pipeline: After cognitive_layer, before narrative_layer.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class TrustEvaluationBlock(PipelineBlock):
    """
    Trust Evaluation Block (S5 Social & Polish Sprint).

    Evaluates trust levels between the system, user, and relevant entities.
    Uses transitive trust with decay for multi-hop assessment.
    """

    def __init__(self, trust_network=None):
        """
        Args:
            trust_network: TrustNetwork instance (injected via DI)
        """
        super().__init__("trust_evaluation")
        self._network = trust_network

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}

            # Extract confidence metadata (shared between both paths)
            confidence = metadata.get("confidence_result", {})
            t_meta = 1.0
            if isinstance(confidence, dict):
                t_meta = confidence.get("t_meta", 1.0)
            elif hasattr(confidence, "t_meta"):
                t_meta = confidence.t_meta if confidence.t_meta is not None else 1.0

            if self._network is not None:
                # Full TrustNetwork assessment
                system_id = "phionyx_system"
                user_id = context.session_id or "unknown_user"

                self._network.add_trust(
                    source=system_id,
                    target=user_id,
                    trust_level=min(t_meta, 1.0),
                    context=f"turn_{context.envelope_turn_id or 0}",
                )

                assessment = self._network.query_trust(system_id, user_id)
                trusted = self._network.get_trusted_entities(system_id)

                result_data = {
                    "direct_trust": assessment.direct_trust,
                    "transitive_trust": assessment.transitive_trust,
                    "is_trusted": assessment.is_trusted,
                    "trust_path": assessment.trust_path,
                    "trusted_entity_count": len(trusted),
                    "reasoning": assessment.reasoning,
                }
            else:
                # Inline fallback: heuristic trust from confidence + entropy
                entropy = context.current_entropy if context.current_entropy is not None else 0.5
                # Ethics risk lowers trust
                ethics_result = metadata.get("ethics_result", {})
                max_risk: float = 0.0
                if isinstance(ethics_result, dict):
                    max_risk = float(ethics_result.get("risk_level", ethics_result.get("harm_risk", 0.0)) or 0.0)
                elif hasattr(ethics_result, "risk_level"):
                    max_risk = float(getattr(ethics_result, "risk_level", 0.0) or 0.0)

                # Trust = confidence_weight * t_meta - risk - entropy_penalty
                direct_trust = t_meta * 0.6 + (1.0 - max_risk) * 0.3 + (1.0 - entropy) * 0.1
                direct_trust = max(0.0, min(1.0, direct_trust))
                is_trusted = direct_trust >= 0.5

                result_data = {
                    "direct_trust": direct_trust,
                    "transitive_trust": direct_trust,
                    "is_trusted": is_trusted,
                    "trust_path": [],
                    "trusted_entity_count": 1 if is_trusted else 0,
                    "reasoning": f"Inline heuristic: t_meta={t_meta:.2f}, risk={max_risk:.2f}, entropy={entropy:.2f}",
                }

            # Write trust_result to metadata for response_build
            if context.metadata is not None:
                context.metadata["trust_result"] = result_data

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Trust evaluation error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["cognitive_layer"]
