"""
Action Intent Gate Block — v3.0.0
===================================

Block: action_intent_gate
Position: After ethics_post_response
v4 Schema: ActionIntent

Gates proposed actions through ethics and safety checks.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class ActionIntentGateBlock(PipelineBlock):
    """
    Gates system action intents through safety checks.

    Constructs ActionIntent from cognitive/narrative output and
    verifies ethics clearance before allowing execution.
    """

    def __init__(self):
        super().__init__("action_intent_gate")

    def should_skip(self, context: BlockContext) -> str | None:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            from ...contracts.v4.action_intent import ActionIntent, ActionType, ReversibilityLevel

            metadata = context.metadata or {}
            ethics_result = metadata.get("ethics_result", {})

            # Construct action intent from pipeline state
            intent = ActionIntent(
                action_type=ActionType.RESPOND,
                description="Generate response to user",
                reversibility=ReversibilityLevel.FULLY_REVERSIBLE,
                sandbox_required=False,
                confidence=metadata.get("confidence_score", 0.5),
                ethics_cleared=not ethics_result.get("enforced", False),
            )

            # Check ethics gate
            if not intent.ethics_cleared:
                intent.requires_approval = True
                logger.info("Action intent requires approval — ethics enforcement triggered")

            context.v4_action_intent = intent

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "intent_id": intent.intent_id,
                    "action_type": intent.action_type.value,
                    "ethics_cleared": intent.ethics_cleared,
                },
            )
        except Exception as e:
            logger.error(f"Action intent gate failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"action_intent_created": False, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["ethics_post_response"]
