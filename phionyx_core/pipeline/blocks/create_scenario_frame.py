"""
Create Scenario Frame Block
============================

Block: create_scenario_frame
Creates the ScenarioFrame immutable state object for the pipeline.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class ScenarioFrameCreatorProtocol(Protocol):
    """Protocol for scenario frame creation."""
    def create_scenario_frame(
        self,
        user_input: str,
        card_type: str,
        card_title: str,
        scene_context: str,
        card_result: str,
        physics_params: dict[str, Any]
    ) -> Any:  # Returns ScenarioFrame
        """Create scenario frame."""
        ...


class CreateScenarioFrameBlock(PipelineBlock):
    """
    Create Scenario Frame Block.

    Creates the ScenarioFrame immutable state object that flows through the pipeline.
    """

    def __init__(self, frame_creator: ScenarioFrameCreatorProtocol | None = None):
        """
        Initialize block.

        Args:
            frame_creator: Service that creates scenario frames
        """
        super().__init__("create_scenario_frame")
        self.frame_creator = frame_creator

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if frame_creator not available."""
        if self.frame_creator is None:
            return "frame_creator_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute scenario frame creation.

        Args:
            context: Block context

        Returns:
            BlockResult with created frame
        """
        try:
            # Get physics params from context metadata (if available)
            physics_params = context.metadata.get("physics_params", {}) if context.metadata else {}

            if self.frame_creator is None:
                return BlockResult(
                    block_id=self.block_id,
                    status="error",
                    error=RuntimeError("ScenarioFrameCreator not configured")
                )

            # Create scenario frame
            frame = self.frame_creator.create_scenario_frame(
                user_input=context.user_input,
                card_type=context.card_type,
                card_title=context.card_title,
                scene_context=context.scene_context,
                card_result=context.card_result,
                physics_params=physics_params
            )

            # Propagate frame to context metadata for downstream blocks
            if context.metadata is None:
                context.metadata = {}
            context.metadata["frame"] = frame

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "frame": frame
                }
            )
        except Exception as e:
            logger.error(f"Scenario frame creation failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

