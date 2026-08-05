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
from typing import Any, Optional

from ..base import PipelineBlock, BlockContext, BlockResult
from phionyx_core.services.intent_classifier import IntentClassifier, IntentType

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
)

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
        intent_classifier: Optional[IntentClassifier] = None,
        embedding_cache: Optional[Any] = None,
        llm_provider: Optional[Any] = None
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
                # Empty input is a policy decision, not a classification:
                # there is nothing to classify and CONVERSATION is the
                # documented default. The intent is kept because downstream
                # needs a type; the confidence is not, because
                # `confidence: 0.5` said the classifier was half-sure when it
                # never ran. Nothing reads that field — grep finds no consumer
                # — so the only thing it could ever do is be cited.
                intent_result = {
                    "intent": IntentType.CONVERSATION.value,
                    "method": "policy_default_empty_input",
                    "measurement_status": "NOT_APPLICABLE",
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

            # `.get`, not `[...]`: the empty-input path is a policy default
            # and carries no confidence, and a log line is not a reason to
            # fabricate one. Reading it unconditionally sent that path into
            # the exception handler, where it was recorded as a classifier
            # error it never had.
            _confidence = intent_result.get("confidence")
            logger.debug(
                f"Intent classified: {intent_result.get('intent', 'none')} "
                f"(confidence="
                f"{f'{_confidence:.2f}' if _confidence is not None else 'not_measured'}, "
                f"method={intent_result.get('method')}, "
                f"time={intent_result.get('processing_time_ms', 0.0):.2f}ms)"
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                # Lifted keys are published only when they exist. The empty-
                # input path is a policy default and carries no confidence;
                # reading it unconditionally here threw KeyError into the
                # exception handler, which then recorded a classifier error
                # that never happened — a fabrication replaced by a false
                # failure is not an improvement.
                data={
                    k: v for k, v in {
                        "intent": intent_result,
                        "intent_type": intent_result.get("intent"),
                        "confidence": intent_result.get("confidence"),
                        "method": intent_result.get("method"),
                    }.items() if v is not None
                }
            )
        except Exception as e:
            logger.error(f"Intent classification failed: {e}", exc_info=True)
            # Fallback: default intent
            # Nothing was classified, so no intent is published. Both
            # consumers already handle absence — context_retrieval_rag takes
            # `intent_type = None` and narrative_layer guards with
            # `if intent_data:` — so this is the state they were written for.
            # It used to publish CONVERSATION at confidence 0.5, which made a
            # crashed classifier indistinguishable from one that had read the
            # input and decided.
            fallback_intent = {
                "method": "not_classified",
                "measurement_status": "ERROR",
                "processing_time_ms": 0.0,
                "error": str(e)
            }

            # Store fallback intent in metadata
            if context.metadata is None:
                context.metadata = {}
            context.metadata["intent"] = fallback_intent
            context.metadata["selected_intent"] = fallback_intent

            # Control channel unchanged — this block stays fail-open so the
            # pipeline still completes, and the `return BlockResult(...)`
            # shape is kept so the inventory sweep can still see it. What
            # changes is the record: block_run_status FAILED, measurement
            # ERROR, operating_mode degraded — a crash here can no longer
            # read as a clean measurement.
            _outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    "intent classification raised; the fallback intent is a default, not a classification",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                # `intent_type` and `confidence` are not re-published here.
                # They used to be lifted out of fallback_intent, which is how
                # a fabricated CONVERSATION/0.5 reached three keys instead of
                # one. Nothing classified, so nothing is asserted.
                data={**({
                    "intent": fallback_intent,
                    "method": "not_classified"
                }), "block_outcome": _outcome.to_record_fields()}
            )

