"""
Emotion From Neurotransmitter Block
====================================

Block: emotion_from_neurotransmitter
Gets emotion (valence, arousal) from neurotransmitter system.
"""

import logging
from typing import Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class NeurotransmitterEmotionProtocol(Protocol):
    """Protocol for neurotransmitter emotion extraction."""
    def get_emotion(
        self,
        user_input: str,
        mode: str | None = None
    ) -> tuple[float, float]:  # Returns (valence, arousal)
        """Get emotion from neurotransmitter."""
        ...


class EmotionFromNeurotransmitterBlock(PipelineBlock):
    """
    Emotion From Neurotransmitter Block.

    Gets emotion (valence, arousal) from neurotransmitter system.
    This is a fallback when emotion estimation is unavailable.
    """

    def __init__(self, neurotransmitter: NeurotransmitterEmotionProtocol | None = None):
        """
        Initialize block.

        Args:
            neurotransmitter: Neurotransmitter service
        """
        super().__init__("emotion_from_neurotransmitter")
        self.neurotransmitter = neurotransmitter

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if no neurotransmitter available."""
        if self.neurotransmitter is None:
            return "neurotransmitter_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute emotion extraction from neurotransmitter.

        Args:
            context: Block context with user_input and mode

        Returns:
            BlockResult with valence and arousal
        """
        try:
            # Get mode from context metadata
            metadata = context.metadata or {}
            mode = metadata.get("mode")

            # Get emotion from neurotransmitter
            if self.neurotransmitter:
                valence, arousal = self.neurotransmitter.get_emotion(
                    user_input=context.user_input,
                    mode=mode
                )
            else:
                # Fallback: neutral values
                valence = 0.0
                arousal = 0.5

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "valence": valence,
                    "arousal": arousal,
                    "source": "neurotransmitter"
                }
            )
        except Exception as e:
            logger.error(f"Emotion from neurotransmitter failed: {e}", exc_info=True)
            # Fallback: neutral values
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "valence": 0.0,
                    "arousal": 0.5,
                    "source": "neurotransmitter_fallback",
                    "error": str(e)
                }
            )

