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
    evaluator.evaluate = MagicMock(return_value=(
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
