"""
Outcome Feedback Block
=======================

Block: outcome_feedback
Bridges turn outcomes to self-model, goal-revision, and memory feedback channels.

Position in pipeline: After audit_layer, before learning_gate.
Contract: v3.8.0 (46 canonical blocks)

Mind-loop stages: Reflect+Revise → UpdateSelfModel, Plan, UpdateMemory
Cognitive vs. automation: Cognitive — first closed feedback loop in pipeline
"""

import logging
from typing import Any

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class OutcomeFeedbackBlock(PipelineBlock):
    """
    Outcome Feedback Block — Kanal 1 (SelfModel) + Kanal 3 (GoalRevision).

    After audit_layer captures the turn result, this block:
    1. Determines success/failure from audit and pipeline metadata
    2. Records outcome in SelfModel (updates capability confidence)
    3. On failure with active goals, proposes goal revisions
    4. Writes memory boost IDs to metadata for next-turn consolidation
    """

    def __init__(self, self_model=None, goal_persistence=None):
        """
        Args:
            self_model: SelfModel instance (injected via DI)
            goal_persistence: GoalPersistence instance (injected via DI)
        """
        super().__init__("outcome_feedback")
        self._self_model = self_model
        self._goal_persistence = goal_persistence

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._self_model is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No SelfModel instance configured"},
            )

        try:
            metadata = context.metadata or {}
            result_data: dict[str, Any] = {
                "outcomes_recorded": [],
                "confidence_updates": {},
                "revisions_proposed": [],
                "memory_boost_ids": [],
            }

            # --- Determine turn success from audit result ---
            audit_result = metadata.get("audit_result", {})
            if not audit_result:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"reason": "No audit result available", **result_data},
                )

            turn_success = self._determine_turn_success(audit_result, metadata)

            # --- Channel 1: SelfModel outcome recording ---
            capabilities = self._infer_capabilities(metadata)
            for cap in capabilities:
                self._self_model.record_outcome(cap, turn_success)
                result_data["outcomes_recorded"].append(
                    {"capability": cap, "success": turn_success}
                )

            # Update confidence from recent outcomes
            confidence_updates = self._self_model.update_confidence_from_outcomes()
            result_data["confidence_updates"] = confidence_updates

            # Write updated confidences to metadata for downstream blocks
            metadata["self_model_confidences"] = confidence_updates

            # --- Channel 3: Goal revision on failure ---
            if not turn_success and self._goal_persistence is not None:
                active_goals = self._goal_persistence.get_active_goals()
                for goal in active_goals:
                    goal_id = getattr(goal, "goal_id", None) or getattr(goal, "id", None)
                    if goal_id is None:
                        continue
                    revision = self._goal_persistence.propose_revision(
                        goal_id=goal_id,
                        reason="Turn outcome failure detected by outcome_feedback block",
                        evidence=f"audit_status={audit_result.get('status', 'unknown')}",
                    )
                    if revision is not None:
                        result_data["revisions_proposed"].append(revision)

            # --- Memory boost: flag relevant memory IDs for next-turn consolidation ---
            if not turn_success:
                # Boost memories related to the failed turn
                related_memory_ids = metadata.get("retrieved_memory_ids", [])
                if related_memory_ids:
                    metadata["_feedback_memory_boost_ids"] = related_memory_ids
                    result_data["memory_boost_ids"] = related_memory_ids

            logger.info(
                f"[OUTCOME_FEEDBACK] success={turn_success}, "
                f"outcomes={len(result_data['outcomes_recorded'])}, "
                f"revisions={len(result_data['revisions_proposed'])}, "
                f"boosts={len(result_data['memory_boost_ids'])}"
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Outcome feedback error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)},
            )

    def _determine_turn_success(
        self, audit_result: dict[str, Any], metadata: dict[str, Any]
    ) -> bool:
        """Determine turn success from audit result and pipeline metadata."""
        # Explicit audit status
        audit_status = audit_result.get("status", "")
        if audit_status in ("error", "failed", "rejected"):
            return False
        if audit_status in ("ok", "success", "completed"):
            return True

        # Check for pipeline errors
        pipeline_errors = metadata.get("pipeline_errors", [])
        if pipeline_errors:
            return False

        # Check ethics gate
        ethics_decision = metadata.get("ethics_decision", {})
        if isinstance(ethics_decision, dict) and ethics_decision.get("blocked"):
            return False

        # Default: success
        return True

    def _infer_capabilities(self, metadata: dict[str, Any]) -> list[str]:
        """Infer which capabilities were exercised this turn."""
        capabilities = ["respond"]  # Always present — pipeline produced a response

        # Causal reasoning if causal blocks ran
        if metadata.get("causal_graph_result") or metadata.get("causal_intervention_result"):
            capabilities.append("causal_reasoning")

        # Ethical deliberation if ethics gate ran
        if metadata.get("ethics_decision") or metadata.get("deliberative_ethics_result"):
            capabilities.append("ethical_deliberation")

        return capabilities

    def get_dependencies(self) -> list:
        return ["audit_layer"]
