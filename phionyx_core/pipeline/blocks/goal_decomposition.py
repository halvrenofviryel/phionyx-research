"""
Goal Decomposition Block
=========================

Block: goal_decomposition
Decomposes user goals into ordered sub-goals with dependencies.
Uses causal hints when available for smarter ordering.

Position in pipeline: After intent_classification, before narrative_layer.
"""

import logging

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class GoalDecompositionBlock(PipelineBlock):
    """
    Goal Decomposition Block (S5 Social & Polish Sprint).

    When user intent suggests a multi-step goal, decomposes it into
    ordered sub-goals using topological sort and causal hints.
    """

    def __init__(self, goal_decomposer=None):
        """
        Args:
            goal_decomposer: GoalDecomposer instance (injected via DI)
        """
        super().__init__("goal_decomposition")
        self._decomposer = goal_decomposer

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._decomposer is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No GoalDecomposer instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Check if intent suggests a complex goal
            intent = metadata.get("intent", {})
            if isinstance(intent, dict):
                action = intent.get("action", "")
                requirements = intent.get("requirements", [])
            else:
                action = context.mode or "respond"
                requirements = []

            # Skip if no clear multi-step goal
            if not requirements and action in ("respond", "chat", "greet"):
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"decomposition_run": False, "reason": "Simple action, no decomposition needed"}
                )

            # Generate goal ID
            goal_id = f"goal_{context.envelope_turn_id or 0}"

            # Check for causal hints from causal graph
            causal_data = metadata.get("causal_graph", {})
            causal_deps = []
            if isinstance(causal_data, dict) and causal_data.get("edges"):
                for edge in causal_data.get("edges", {}).values():
                    if isinstance(edge, dict):
                        causal_deps.append((
                            edge.get("source_id", ""),
                            edge.get("target_id", ""),
                        ))

            # Decompose
            if causal_deps:
                plan = self._decomposer.decompose_with_causal_hints(
                    goal_id=goal_id,
                    goal_name=action,
                    requirements=requirements if requirements else [context.user_input],
                    causal_dependencies=causal_deps,
                )
            else:
                plan = self._decomposer.decompose(
                    goal_id=goal_id,
                    goal_name=action,
                    requirements=requirements if requirements else [context.user_input],
                )

            sub_goals = []
            for sg in plan.sub_goals:
                sub_goals.append({
                    "id": sg.sub_goal_id,
                    "name": sg.name,
                    "status": sg.status if isinstance(sg.status, str) else sg.status.value,
                    "priority": sg.priority,
                    "complexity": sg.estimated_complexity,
                })

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "decomposition_run": True,
                    "goal_id": goal_id,
                    "goal_name": action,
                    "sub_goals": sub_goals,
                    "execution_order": plan.execution_order,
                    "total_complexity": plan.total_complexity,
                    "estimated_steps": plan.estimated_steps,
                }
            )

        except Exception as e:
            logger.error(f"Goal decomposition error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["intent_classification"]
