"""
Intent Classification Block
============================

Block: intent_classification
Classifies user intent early in the pipeline for optimization.

This block:
- Detects user intent (greeting, question, command, conversation, high_risk)
- Provides intent information for downstream blocks
- Enables template-based responses and early exit optimizations
"""

import logging
from typing import Any

from phionyx_core.services.intent_classifier import IntentClassifier, IntentType

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class IntentClassificationBlock(PipelineBlock):
    """
    Intent Classification Block.

    Classifies user intent early in the pipeline.
    Fast path requirement: <200ms processing time.
    """

    determinism = "noisy_sensor"  # rule-based fast path is strict, but fallback tier uses LLM — classify by weakest path

    def __init__(
        self,
        intent_classifier: IntentClassifier | None = None,
        embedding_cache: Any | None = None,
        llm_provider: Any | None = None
    ):
        """
        Initialize block.

        Args:
            intent_classifier: Optional intent classifier (will be created if not provided)
            embedding_cache: Optional embedding cache for fast path
            llm_provider: Optional LLM provider for fallback
        """
        super().__init__("intent_classification")

        if intent_classifier is None:
            self.intent_classifier = IntentClassifier(
                llm_provider=llm_provider,
                embedding_cache=embedding_cache
            )
        else:
            self.intent_classifier = intent_classifier

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute intent classification.

        Args:
            context: Block context with user_input

        Returns:
            BlockResult with intent classification result
        """
        try:
            user_input = context.user_input or ""

            if not user_input.strip():
                # Empty input - default to conversation
                intent_result = {
                    "intent": IntentType.CONVERSATION.value,
                    "confidence": 0.5,
                    "method": "fallback",
                    "processing_time_ms": 0.0
                }
            else:
                # Classify intent (with <200ms requirement)
                result = await self.intent_classifier.classify_intent(
                    user_input,
                    timeout_ms=200.0
                )

                # Check if processing time exceeded requirement
                if result.processing_time_ms > 200.0:
                    logger.warning(
                        f"Intent classification exceeded 200ms requirement: "
                        f"{result.processing_time_ms:.2f}ms"
                    )

                intent_result = {
                    "intent": result.intent.value,
                    "confidence": result.confidence,
                    "method": result.method,
                    "processing_time_ms": result.processing_time_ms
                }

            # Store intent in metadata for downstream blocks
            if context.metadata is None:
                context.metadata = {}
            context.metadata["intent"] = intent_result
            context.metadata["selected_intent"] = intent_result  # Alias for compatibility

            logger.debug(
                f"Intent classified: {intent_result['intent']} "
                f"(confidence={intent_result['confidence']:.2f}, "
                f"method={intent_result['method']}, "
                f"time={intent_result['processing_time_ms']:.2f}ms)"
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "intent": intent_result,
                    "intent_type": intent_result["intent"],
                    "confidence": intent_result["confidence"],
                    "method": intent_result["method"]
                }
            )
        except Exception as e:
            logger.error(f"Intent classification failed: {e}", exc_info=True)
            # Fallback: default intent
            fallback_intent = {
                "intent": IntentType.CONVERSATION.value,
                "confidence": 0.5,
                "method": "fallback",
                "processing_time_ms": 0.0,
                "error": str(e)
            }

            # Store fallback intent in metadata
            if context.metadata is None:
                context.metadata = {}
            context.metadata["intent"] = fallback_intent
            context.metadata["selected_intent"] = fallback_intent

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "intent": fallback_intent,
                    "intent_type": fallback_intent["intent"],
                    "confidence": fallback_intent["confidence"],
                    "method": "fallback"
                }
            )

