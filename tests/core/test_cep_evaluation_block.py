"""
CEP Evaluation Pipeline Block Tests
====================================

Tests for CepEvaluationBlock — pipeline integration of CEP.

Markers: @pytest.mark.safety, @pytest.mark.unit
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from phionyx_core.pipeline.base import BlockContext, BlockResult
from phionyx_core.pipeline.blocks.cep_evaluation import CepEvaluationBlock


@pytest.fixture
def mock_evaluator():
    """Mock CEP evaluator that returns test flags/config."""
    evaluator = MagicMock()
    # AsyncMock, because the protocol is async and the only real implementation
    # awaits the processor. A sync mock here matched the old declaration and so
    # never exercised the call the block actually makes — which is why the
    # unpack-a-coroutine defect survived in a suite that passed.
    evaluator.evaluate = AsyncMock(return_value=(
        {"is_self_narrative_blocked": False},  # cep_flags
        {"mode": "universal"},  # cep_config
    ))
    return evaluator


@pytest.fixture
def context_with_frame():
    """BlockContext with frame and narrative_text in metadata."""
    frame = MagicMock()
    frame.cognitive_state = {"trust": 0.8}
    return BlockContext(
        user_input="Hello",
        card_type="",
        card_title="",
        scene_context="",
        card_result="",
        metadata={
            "frame": frame,
            "narrative_text": "A safe response about the weather.",
            "cognitive_state": {"trust": 0.8},
        },
    )


@pytest.mark.unit
@pytest.mark.safety
class TestCEPEvaluationBlock:
    """Tests for CepEvaluationBlock pipeline block."""

    def test_skip_when_no_evaluator(self):
        """Block should skip when no evaluator is provided."""
        block = CepEvaluationBlock(evaluator=None)
        reason = block.should_skip(BlockContext(user_input="test", card_type="", card_title="", scene_context="", card_result=""))
        assert reason is not None
        assert "not_available" in reason

    def test_no_skip_when_evaluator_present(self, mock_evaluator):
        """Block should NOT skip when evaluator is present."""
        block = CepEvaluationBlock(evaluator=mock_evaluator)
        reason = block.should_skip(BlockContext(user_input="test", card_type="", card_title="", scene_context="", card_result=""))
        assert reason is None

    @pytest.mark.asyncio
    async def test_execute_calls_evaluator(self, mock_evaluator, context_with_frame):
        """Execute should call evaluator.evaluate and return result."""
        block = CepEvaluationBlock(evaluator=mock_evaluator)
        result = await block.execute(context_with_frame)

        assert isinstance(result, BlockResult)
        assert result.status == "ok"
        assert "cep_flags" in result.data
        mock_evaluator.evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_without_frame_returns_none(self, mock_evaluator):
        """Execute without frame in metadata should return None flags."""
        block = CepEvaluationBlock(evaluator=mock_evaluator)
        context = BlockContext(user_input="test", card_type="", card_title="", scene_context="", card_result="", metadata={})
        result = await block.execute(context)

        assert result.status == "ok"
        assert result.data["cep_flags"] is None


class TestAFailedEvaluationIsNotReportedAsOne:
    """The block returned status="ok" when its evaluator raised.

    A CEP evaluation that never ran was then indistinguishable from one that ran
    and found nothing — the substitution the Measurement Axioms name, inside a
    canonical block of the pipeline they were written about. Found by mypy 2.x,
    which sees that the adapter is async and the call site did not await it.
    """

    @pytest.mark.asyncio
    async def test_a_raising_evaluator_is_recorded_as_skipped(self) -> None:
        evaluator = MagicMock()
        evaluator.evaluate = AsyncMock(side_effect=RuntimeError("evaluator down"))
        block = CepEvaluationBlock(evaluator=evaluator)
        context = BlockContext(user_input="t", card_type="", card_title="",
                               scene_context="", card_result="",
                               metadata={"frame": object()})

        result = await block.execute(context)

        assert result.status == "skipped", (
            "an evaluation that raised must not be reported as one that passed")
        assert result.is_success() is False
        assert "RuntimeError" in (result.skip_reason or "")
        assert result.data["cep_flags"] is None

    @pytest.mark.asyncio
    async def test_it_stays_fail_open(self) -> None:
        """`error` would attempt a rollback in the orchestrator; `skipped` does
        not. The decision being made is to stop claiming a pass, not to convert
        this block from fail-open to fail-closed."""
        evaluator = MagicMock()
        evaluator.evaluate = AsyncMock(side_effect=RuntimeError("down"))
        block = CepEvaluationBlock(evaluator=evaluator)
        context = BlockContext(user_input="t", card_type="", card_title="",
                               scene_context="", card_result="",
                               metadata={"frame": object()})

        result = await block.execute(context)

        assert result.is_error() is False
        assert result.is_skipped() is True

    @pytest.mark.asyncio
    async def test_a_sync_evaluator_no_longer_silently_passes(self) -> None:
        """The shape the old suite used: a sync mock matched the old protocol
        and never exercised the awaited call the block makes."""
        evaluator = MagicMock()
        evaluator.evaluate = MagicMock(return_value=({"a": 1}, {"b": 2}))
        block = CepEvaluationBlock(evaluator=evaluator)
        context = BlockContext(user_input="t", card_type="", card_title="",
                               scene_context="", card_result="",
                               metadata={"frame": object()})

        result = await block.execute(context)

        assert result.status == "skipped"
