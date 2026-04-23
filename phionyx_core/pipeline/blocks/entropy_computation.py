"""
Entropy Computation Block
============================

Block: entropy_computation
Computes entropy value from user input and response.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class EntropyComputationProtocol(Protocol):
    """Protocol for entropy computation."""
    def compute_entropy(
        self,
        user_input: str,
        response_text: Optional[str] = None,
        previous_entropy: Optional[float] = None
    ) -> Dict[str, Any]:
        """Compute entropy value."""
        ...


class EntropyComputationBlock(PipelineBlock):
    """
    Entropy Computation Block.

    Computes entropy from user input and response using scientific grounding (zlib).
    This is an always-on block.
    """

    def __init__(self, entropy_computer: Optional[EntropyComputationProtocol] = None):
        """
        Initialize block.

        Args:
            entropy_computer: Service that computes entropy
        """
        super().__init__("entropy_computation")
        self.entropy_computer = entropy_computer

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute entropy computation.

        Args:
            context: Block context with user_input and response

        Returns:
            BlockResult with entropy value and components
        """
        try:
            # Get response text from context metadata (if available)
            metadata = context.metadata or {}
            response_text = metadata.get("narrative_text")

            # Get previous entropy from context
            previous_entropy = context.current_entropy

            # Compute entropy
            if self.entropy_computer:
                entropy_result = self.entropy_computer.compute_entropy(
                    user_input=context.user_input,
                    response_text=response_text,
                    previous_entropy=previous_entropy
                )
                # Handle both dict and scalar return values
                if not isinstance(entropy_result, dict):
                    entropy_result = {"entropy": entropy_result, "components": {}}
            else:
                # Fallback: simple entropy computation using zlib
                import zlib
                text = context.user_input or ""
                if response_text:
                    text += " " + response_text

                if text:
                    compressed = zlib.compress(text.encode('utf-8'))
                    entropy = len(compressed) / max(len(text.encode('utf-8')), 1)
                    entropy = min(entropy, 1.0)  # Clamp to [0, 1]
                else:
                    entropy = 0.5  # Default

                entropy_result = {
                    "entropy": entropy,
                    "components": {
                        "message_length": len(context.user_input) if context.user_input else 0,
                        "response_length": len(response_text) if response_text else 0
                    }
                }

            # Update context with computed entropy
            computed_entropy = entropy_result.get("entropy", 0.5)
            context.current_entropy = computed_entropy
            if context.metadata is None:
                context.metadata = {}
            context.metadata["current_entropy"] = computed_entropy

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "entropy": computed_entropy,
                    "entropy_components": entropy_result.get("components", {}),
                    "entropy_result": entropy_result
                }
            )
        except Exception as e:
            logger.error(f"Entropy computation failed: {e}", exc_info=True)
            # Fail-open: return default entropy
            return BlockResult(
                block_id=self.block_id,
                status="ok",  # Don't fail pipeline on entropy computation error
                data={
                    "entropy": context.current_entropy,  # Use current entropy as fallback
                    "entropy_components": {},
                    "error": str(e)
                }
            )

