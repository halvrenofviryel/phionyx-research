"""
Deliberative Ethics Gate Block
================================

Block: deliberative_ethics_gate
Multi-framework ethical deliberation for high-risk actions.
Uses 4 ethical frameworks: deontological, consequentialist, virtue, care.

Position in pipeline: After ethics_pre_response, before narrative_layer.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class DeliberativeEthicsGateBlock(PipelineBlock):
    """
    Deliberative Ethics Gate Block (S5 Social & Polish Sprint).

    For high-risk actions, performs multi-framework ethical deliberation.
    If 3+ frameworks DENY, forces pipeline early exit.
    Low consensus triggers DEFER_TO_HUMAN.
    """

    def __init__(self, deliberative_ethics=None):
        """
        Args:
            deliberative_ethics: DeliberativeEthics instance (injected via DI)
        """
        super().__init__("deliberative_ethics_gate")
        self._ethics = deliberative_ethics

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}

            # Get ethics vector from prior ethics block
            ethics_result = metadata.get("ethics_result", {})
            ethics_vector = {}

            if isinstance(ethics_result, dict):
                ethics_vector = {
                    "harm_risk": ethics_result.get("harm_risk", 0.0),
                    "manipulation_risk": ethics_result.get("manipulation_risk", 0.0),
                    "boundary_violation_risk": ethics_result.get("boundary_violation_risk", 0.0),
                    "attachment_risk": ethics_result.get("attachment_risk", 0.0),
                    "child_on_child_risk": ethics_result.get("child_on_child_risk", 0.0),
                }
            elif hasattr(ethics_result, "risk_scores"):
                scores = ethics_result.risk_scores
                if isinstance(scores, dict):
                    ethics_vector = scores

            # Check if any risk is elevated enough to warrant deliberation
            max_risk = max(ethics_vector.values()) if ethics_vector else 0.0
            if max_risk < 0.3:
                low_risk_data = {
                    "deliberation_run": False,
                    "reason": "Risk levels below deliberation threshold",
                    "max_risk": max_risk,
                }
                # Store with prefixed key for downstream AGI context injection
                if context.metadata is not None:
                    context.metadata["_agi_deliberative_ethics"] = low_risk_data
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data=low_risk_data,
                )

            if self._ethics is not None:
                # Full multi-framework deliberation
                result = self._ethics.deliberate(
                    action=context.user_input[:200],
                    ethics_vector=ethics_vector,
                    context={
                        "mode": context.mode,
                        "session_id": context.session_id,
                        "turn_id": context.envelope_turn_id,
                    },
                )
                assessments = []
                for fa in result.framework_assessments:
                    assessments.append({
                        "framework": fa.framework,
                        "verdict": fa.verdict,
                        "confidence": fa.confidence,
                        "reasoning": fa.reasoning,
                    })
                is_denied = result.final_verdict == "DENY"
                is_deferred = result.final_verdict == "DEFER_TO_HUMAN"
                deliberation_data = {
                    "deliberation_run": True,
                    "final_verdict": result.final_verdict,
                    "final_confidence": result.final_confidence,
                    "consensus": result.consensus,
                    "framework_assessments": assessments,
                    "reasoning": result.reasoning,
                    "early_exit": is_denied,
                    "defer_to_human": is_deferred,
                }
            else:
                # Inline fallback: simplified 4-rule deliberation
                harm = ethics_vector.get("harm_risk", 0.0)
                manipulation = ethics_vector.get("manipulation_risk", 0.0)
                boundary = ethics_vector.get("boundary_violation_risk", 0.0)
                # Rule-based verdicts per "framework"
                verdicts = {
                    "consequentialist": "DENY" if harm > 0.7 else "ALLOW",
                    "deontological": "DENY" if boundary > 0.6 else "ALLOW",
                    "virtue": "DENY" if manipulation > 0.6 else "ALLOW",
                    "care": "DENY" if max_risk > 0.8 else "ALLOW",
                }
                deny_count = sum(1 for v in verdicts.values() if v == "DENY")
                if deny_count >= 3:
                    final_verdict = "DENY"
                elif deny_count >= 2:
                    final_verdict = "DEFER_TO_HUMAN"
                else:
                    final_verdict = "ALLOW"
                is_denied = final_verdict == "DENY"
                is_deferred = final_verdict == "DEFER_TO_HUMAN"
                deliberation_data = {
                    "deliberation_run": True,
                    "final_verdict": final_verdict,
                    "final_confidence": 1.0 - (max_risk * 0.5),
                    "consensus": (4 - deny_count) / 4.0,
                    "framework_assessments": [
                        {"framework": k, "verdict": v, "confidence": 0.8, "reasoning": "inline rule"}
                        for k, v in verdicts.items()
                    ],
                    "reasoning": f"Inline 4-rule: {deny_count}/4 deny (max_risk={max_risk:.2f})",
                    "early_exit": is_denied,
                    "defer_to_human": is_deferred,
                }

            if is_denied:
                logger.warning(
                    f"[DELIBERATIVE_ETHICS] DENIED: {deliberation_data.get('reasoning', '')}"
                )

            # Store with prefixed key for downstream AGI context injection
            if context.metadata is not None:
                context.metadata["_agi_deliberative_ethics"] = {
                    "deliberation_run": True,
                    "final_verdict": deliberation_data["final_verdict"],
                    "final_confidence": deliberation_data["final_confidence"],
                    "consensus": deliberation_data["consensus"],
                }

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=deliberation_data,
            )

        except Exception as e:
            logger.error(f"Deliberative ethics error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["ethics_pre_response"]
