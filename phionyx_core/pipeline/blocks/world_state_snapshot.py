"""
World State Snapshot Block — v3.0.0
=====================================

Block: world_state_snapshot
Position: After state_update_physics
v4 Schema: WorldStateSnapshot

Captures full world state snapshot after physics update.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class WorldStateSnapshotBlock(PipelineBlock):
    """
    Captures a v4 WorldStateSnapshot after physics state update.

    Composes EchoState2 with belief vector, arbitration status,
    and causal graph information.
    """

    def __init__(self):
        super().__init__("world_state_snapshot")

    def should_skip(self, context: BlockContext) -> str | None:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            from ...contracts.v4.world_state_snapshot import ArbitrationStatus, WorldStateSnapshot

            metadata = context.metadata or {}
            unified_state = metadata.get("unified_state")
            physics_state = metadata.get("physics_state", {})

            # Get echo_state dict
            echo_state_dict = {}
            if unified_state and hasattr(unified_state, "to_dict"):
                echo_state_dict = unified_state.to_dict()
            elif isinstance(physics_state, dict):
                echo_state_dict = physics_state

            # Build snapshot
            snapshot = WorldStateSnapshot(
                echo_state=echo_state_dict,
                belief_vector=metadata.get("belief_vector", {}),
                arbitration_status=ArbitrationStatus.STABLE,
                active_goals=[
                    g.goal_id for g in (context.v4_active_goals or [])
                    if hasattr(g, "goal_id")
                ],
                turn_index=context.envelope_turn_id or 0,
            )

            context.v4_world_state = snapshot

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"snapshot_captured": True, "turn_index": snapshot.turn_index},
            )
        except Exception as e:
            logger.error(f"World state snapshot failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"snapshot_captured": False, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["state_update_physics"]
