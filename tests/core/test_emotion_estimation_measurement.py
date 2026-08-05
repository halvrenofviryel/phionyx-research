"""emotion_estimation must not cache a crash as this input's answer.

Canonical block 29. Three paths, and one of them was already honest — the
no-estimator path returns `unknown: True` with `source: "echo_state_defaults"`
and says exactly what it did. The other two were not.

**The success path defaulted silently.** `estimation_result.get("valence",
0.0)` with `unknown` taken from the result, which defaults to `False`. So an
estimator that returned an empty dict produced a confident neutral reading.
That matters beyond the record: `phi_computation.py:102` reads this valence
and computes a phi from it, which it then publishes as measured.

**The crash path cached its fabrication.** This is what makes this block
different from the others in the inventory. Elsewhere a fabricated value is
wrong for one turn. Here it was written into the emotion cache, so the next
identical input got the fabricated pair back **without the estimator being
asked again** — a transient fault made permanent for that input.

The cache itself is correct and stays: it exists so an identical input yields
an identical measurement, which is the determinism invariant. What changed is
that a path which measured nothing no longer writes to it. Determinism of a
non-measurement is not a property worth preserving, and the cache has no
reader outside this block, so nothing downstream depends on the entry.

The schema defaults are still returned on both failure paths. Downstream needs
a state to work from; `unknown: True` is what tells it the state was not
estimated.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.emotion_estimation import EmotionEstimationBlock


class _Estimator:
    def __init__(self, result=None, raises: BaseException | None = None):
        self._result = result
        self._raises = raises
        self.calls = 0

    async def estimate(self, user_input):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


def _context(user_input="hello"):
    return BlockContext(
        user_input=user_input,
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={},
    )


@pytest.mark.asyncio
class TestAnEstimateThatDidNotHappenIsMarkedUnknown:
    async def test_an_empty_result_is_unknown(self):
        block = EmotionEstimationBlock(emotion_estimator=_Estimator(result={}))

        result = await block.execute(_context())

        assert result.data["unknown"] is True, (
            "an estimator that returned nothing estimated nothing. This used "
            "to report a confident neutral reading, and phi_computation "
            "computes a phi from it.")

    async def test_a_partial_result_is_unknown(self):
        """Valence without arousal is not an emotional state."""
        block = EmotionEstimationBlock(
            emotion_estimator=_Estimator(result={"valence": 0.7}))

        result = await block.execute(_context())

        assert result.data["unknown"] is True

    async def test_a_full_result_is_not_unknown(self):
        """The control. Without it, a block hardcoding unknown=True would pass
        both assertions above."""
        block = EmotionEstimationBlock(emotion_estimator=_Estimator(
            result={"valence": 0.7, "arousal": 0.3}))

        result = await block.execute(_context())

        assert result.data["unknown"] is False
        assert result.data["valence"] == 0.7
        assert result.data["arousal"] == 0.3


@pytest.mark.asyncio
class TestACrashIsNotCachedAsTheAnswer:
    async def test_the_estimator_is_asked_again_after_a_crash(self):
        """The property that distinguishes this block from the others.

        A cached crash means a transient fault answers for that input
        permanently. The estimator must be reachable on the next turn.
        """
        estimator = _Estimator(raises=RuntimeError("estimator down"))
        block = EmotionEstimationBlock(emotion_estimator=estimator)
        context = _context("the same question")

        first = await block.execute(context)
        assert first.status == "ok", "fail-open: the turn continues"
        assert first.data["unknown"] is True
        assert first.data["block_outcome"]["measurement_status"] == "ERROR"

        await block.execute(_context("the same question"))

        assert estimator.calls == 2, (
            "the second turn read the crash back from the cache instead of "
            "asking again — a transient fault became this input's answer")

    async def test_a_real_estimate_is_still_cached(self):
        """The invariant the cache exists for, and which must survive.

        Identical input, identical measurement, without re-estimating. If this
        broke, removing the crash from the cache would have cost determinism
        to buy honesty, which is not the trade being made.
        """
        estimator = _Estimator(result={"valence": 0.42, "arousal": 0.61})
        block = EmotionEstimationBlock(emotion_estimator=estimator)

        first = await block.execute(_context("stable input"))
        second = await block.execute(_context("stable input"))

        assert estimator.calls == 1, "the second turn should hit the cache"
        assert (second.data["valence"], second.data["arousal"]) == (
            first.data["valence"], first.data["arousal"])


@pytest.mark.asyncio
class TestTheHonestPathStaysHonest:
    """The no-estimator path was already right; this keeps it that way."""

    async def test_no_estimator_reports_unknown_and_names_its_source(self):
        block = EmotionEstimationBlock(emotion_estimator=None)

        result = await block.execute(_context())

        assert result.data["unknown"] is True
        assert result.data["source"] == "echo_state_defaults", (
            "the values are schema defaults and the record says so — this "
            "path did not need fixing and must not be broken by fixing the "
            "others")
