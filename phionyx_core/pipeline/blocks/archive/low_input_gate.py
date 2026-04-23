"""
Low Input Gate Block
====================

Block: low_input_gate
Gate that checks if user input is too short/low quality and triggers early exit.
"""

import logging

from ...base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class LowInputGateBlock(PipelineBlock):
    """
    Low Input Gate Block.

    Checks if user input is sufficient quality. If not, triggers early exit
    with a clarifying question.
    """

    def __init__(self, min_input_length: int = 3):
        """
        Initialize block.

        Args:
            min_input_length: Minimum input length to pass gate (default: 3)
        """
        super().__init__("low_input_gate")
        self.min_input_length = min_input_length

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute low input gate check.

        Args:
            context: Block context with user_input

        Returns:
            BlockResult with gate status and optional clarifying question
        """
        try:
            user_input = context.user_input or ""
            input_length = len(user_input.strip())

            # Check if input is too short
            if input_length < self.min_input_length:
                clarifying_question = "Could you tell me more about what you're thinking or feeling?"

                logger.debug(
                    f"[LOW_INPUT_GATE] Input too short: length={input_length}, "
                    f"min={self.min_input_length}, triggering early exit"
                )

                return BlockResult(
                    block_id=self.block_id,
                    status="ok",  # Gate passed (triggered early exit, but this is expected behavior)
                    data={
                        "gate_triggered": True,
                        "early_exit": True,
                        "clarifying_question": clarifying_question,
                        "input_length": input_length,
                        "min_length": self.min_input_length
                    }
                )

            # Gate passed - input is sufficient
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "gate_triggered": False,
                    "early_exit": False,
                    "input_length": input_length
                }
            )
        except Exception as e:
            logger.error(f"Low input gate check failed: {e}", exc_info=True)
            # Fail-open: allow input through if gate check fails
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "gate_triggered": False,
                    "early_exit": False,
                    "error": str(e)
                }
            )

