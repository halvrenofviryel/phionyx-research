"""
Goal Evaluation Block — v3.0.0
================================

Block: goal_evaluation
Position: After initialize_unified_state
v4 Schema: GoalObject

Evaluates active goals, computes legitimacy and utility scores.
"""

import logging
from typing import Optional, Protocol, List, Any

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class GoalRegistryProtocol(Protocol):
    """Protocol for goal registry service."""
    async def get_active_goals(self) -> List[Any]: ...
    async def evaluate_goals(self, context: Any) -> List[Any]: ...


class GoalEvaluationBlock(PipelineBlock):
    """
    Evaluates active goals against current state.

    Computes legitimacy L(g) and utility U(g) for each active goal.
    Updates goal priorities and detects goal drift.
    """

    def __init__(self, goal_registry: Optional[GoalRegistryProtocol] = None):
        super().__init__("goal_evaluation")
        self.goal_registry = goal_registry

    def should_skip(self, context: BlockContext) -> Optional[str]:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        # goal_registry=None → inline fallback in execute() (goals_evaluated: 0)
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            if self.goal_registry is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"goals_evaluated": 0},
                )

            active_goals = await self.goal_registry.get_active_goals()
            evaluated = await self.goal_registry.evaluate_goals(context)

            context.v4_active_goals = evaluated

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "goals_evaluated": len(evaluated),
                    "active_goal_count": len(active_goals),
                },
            )
        except Exception as e:
            logger.error(f"Goal evaluation failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"goals_evaluated": 0, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["initialize_unified_state"]
