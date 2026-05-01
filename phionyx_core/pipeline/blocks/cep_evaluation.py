"""
CEP Evaluation Block
=====================

Block: cep_evaluation
Evaluates CEP (Conscious Echo Proof) for safety and coherence.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class CEPEvaluatorProtocol(Protocol):
    """Protocol for CEP evaluation."""
    def evaluate(
        self,
        frame: Any,
        user_input: str,
        narrative_response: str,
        cognitive_state: Any
    ) -> tuple[Any, Any]:  # Returns (cep_flags, cep_config)
        """Evaluate CEP."""
        ...


class CepEvaluationBlock(PipelineBlock):
    """
    CEP Evaluation Block.

    Evaluates CEP (Conscious Echo Proof) for safety and coherence.
    """

    def __init__(self, evaluator: CEPEvaluatorProtocol | None = None):
        """
        Initialize block.

        Args:
            evaluator: CEP evaluator service
        """
        super().__init__("cep_evaluation")
        self.evaluator = evaluator

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip if no evaluator available."""
        if self.evaluator is None:
            return "cep_evaluator_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute CEP evaluation.

        Args:
            context: Block context with frame and narrative_response

        Returns:
            BlockResult with cep_flags and cep_config
        """
        try:
            # Get frame and narrative_response from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            narrative_response = metadata.get("narrative_text", "")
            cognitive_state = metadata.get("cognitive_state")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"cep_flags": None, "cep_config": None}
                )

            # Evaluate CEP
            if self.evaluator:
                cep_flags, cep_config = self.evaluator.evaluate(
                    frame=frame,
                    user_input=context.user_input,
                    narrative_response=narrative_response,
                    cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                )
            else:
                cep_flags = None
                cep_config = None

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "cep_flags": cep_flags,
                    "cep_config": cep_config
                }
            )
        except Exception as e:
            logger.error(f"CEP evaluation failed: {e}", exc_info=True)
            # Fail-open: continue without CEP
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "cep_flags": None,
                    "cep_config": None,
                    "error": str(e)
                }
            )

