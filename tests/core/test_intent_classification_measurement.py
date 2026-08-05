"""intent_classification must not report a confidence it never computed.

Canonical block 4. It had two `confidence: 0.5` sites and they were different
kinds of thing, which is the whole reason this block was worth reading rather
than pattern-matching:

- **empty input** is a *policy decision*. There is nothing to classify and
  CONVERSATION is the documented default. That is legitimate — and the
  confidence beside it was not, because no classifier ran to be half-sure.
  Now `NOT_APPLICABLE`, which is what the verdict algebra has for a check that
  did not apply rather than one that failed.
- **the exception path** published the same intent at the same confidence. A
  crashed classifier was indistinguishable from one that had read the input
  and decided CONVERSATION. Now nothing is published, and the record says
  `ERROR`.

Two facts made the second safe, and both were checked before changing it:
`confidence` is read by **no consumer anywhere** — so the number could only
ever be cited, never used — and both readers of `intent` already handle its
absence: `context_retrieval_rag.py:81` takes `intent_type = None` and
`narrative_layer.py:196` guards with `if intent_data:`. Publishing nothing
puts them in the state they were written for.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.intent_classification import (
    IntentClassificationBlock,
)


class _Result:
    """Every attribute the block reads off a classifier result.

    Written from `grep -oE "result\.\w+"` over the block rather than from
    memory — a fixture missing one lands the test in the exception path, where
    it then asserts against a record the block never meant to produce.
    """

    def __init__(self, intent, confidence, ms=1.0, method="classifier"):
        self.intent = intent
        self.confidence = confidence
        self.processing_time_ms = ms
        self.method = method


class _Classifier:
    """Returns what the test chooses, or raises."""

    def __init__(self, result=None, raises: BaseException | None = None):
        self._result = result
        self._raises = raises
        self.calls = 0

    async def classify_intent(self, user_input, timeout_ms=200.0):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


def _context(user_input: str):
    return BlockContext(
        user_input=user_input,
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={},
    )


@pytest.mark.asyncio
class TestAnUncomputedConfidenceIsNotPublished:
    async def test_empty_input_is_a_policy_default_not_a_classification(self):
        classifier = _Classifier()
        block = IntentClassificationBlock(intent_classifier=classifier)

        context = _context("   ")
        await block.execute(context)

        intent = context.metadata["intent"]
        assert classifier.calls == 0, "nothing was classified"
        assert intent["intent"] == "conversation", (
            "the documented default is kept — downstream needs a type")
        assert "confidence" not in intent, (
            "0.5 said the classifier was half-sure and it never ran")
        assert intent["measurement_status"] == "NOT_APPLICABLE"
        assert intent["method"] == "policy_default_empty_input"

    async def test_a_crashed_classifier_publishes_no_intent(self):
        classifier = _Classifier(raises=RuntimeError("classifier down"))
        block = IntentClassificationBlock(intent_classifier=classifier)

        context = _context("what is the weather")
        result = await block.execute(context)

        assert result.status == "ok", "fail-open: the turn continues"
        intent = context.metadata["intent"]
        assert "intent" not in intent, (
            "publishing CONVERSATION here made a crash indistinguishable from "
            "a classifier that read the input and decided")
        assert "confidence" not in intent
        assert intent["measurement_status"] == "ERROR"

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "ERROR"
        assert outcome["operating_mode"] == "degraded"

    async def test_a_real_classification_keeps_its_confidence(self):
        """The control. Without it, a block that dropped confidence entirely
        would pass both assertions above."""
        class _Intent:
            value = "question"

        classifier = _Classifier(result=_Result(_Intent(), 0.91, ms=12.0))
        block = IntentClassificationBlock(intent_classifier=classifier)

        context = _context("what is the weather")
        await block.execute(context)

        intent = context.metadata["intent"]
        assert intent["intent"] == "question"
        assert intent["confidence"] == 0.91, (
            "a confidence the classifier actually computed must survive")


@pytest.mark.asyncio
class TestTheConsumersSurviveAnAbsentIntent:
    """The precondition for not publishing one, asserted rather than assumed.

    If either reader crashed on a missing intent, dropping it would trade a
    fabricated measurement for a broken turn — a worse bargain, and the kind
    that gets discovered in production rather than here.
    """

    async def test_context_retrieval_handles_a_missing_intent(self):
        from phionyx_core.pipeline.blocks.context_retrieval_rag import (
            ContextRetrievalRagBlock,
        )

        block = ContextRetrievalRagBlock(rag_service=None, vector_store=None)
        result = await block.execute(_context("hello"))

        assert result.status in ("ok", "skipped"), (
            "a missing intent must not take the turn down")

    async def test_narrative_layer_guards_on_intent_presence(self):
        """Structural: the guard `if intent_data:` is what makes absence safe."""
        import inspect

        from phionyx_core.pipeline.blocks import narrative_layer

        source = inspect.getsource(narrative_layer)
        assert "if intent_data:" in source, (
            "narrative_layer no longer guards on intent presence; publishing "
            "nothing from intent_classification is only safe while it does")
