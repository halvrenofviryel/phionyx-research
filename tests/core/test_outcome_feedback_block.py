"""
Tests for OutcomeFeedbackBlock (v3.6.0)
========================================

Validates the outcome feedback pipeline block that bridges turn outcomes
to self-model confidence updates, goal revision proposals, and memory
priority boosts.

Mind-loop stages: Reflect+Revise → UpdateSelfModel, Plan, UpdateMemory
"""

import pytest
from unittest.mock import MagicMock, patch

from phionyx_core.pipeline.base import BlockContext, BlockResult
from phionyx_core.pipeline.blocks.outcome_feedback import OutcomeFeedbackBlock


def _make_context(**overrides) -> BlockContext:
    """Create a minimal BlockContext for testing."""
    defaults = dict(
        user_input="test input",
        card_type="conversation",
        card_title="Test",
        scene_context="test scene",
        card_result="test result",
        metadata={},
    )
    defaults.update(overrides)
    return BlockContext(**defaults)


class TestOutcomeFeedbackBlock:
    """Core tests for OutcomeFeedbackBlock."""

    @pytest.mark.asyncio
    async def test_skip_when_no_self_model(self):
        """Block skips gracefully when no SelfModel is configured."""
        block = OutcomeFeedbackBlock(self_model=None)
        ctx = _make_context()
        result = await block.execute(ctx)
        assert result.status == "skipped"
        assert "No SelfModel" in result.data["reason"]

    @pytest.mark.asyncio
    async def test_skip_when_no_audit_result(self):
        """Block returns ok with no outcomes when audit result is missing."""
        mock_sm = MagicMock()
        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={})
        result = await block.execute(ctx)
        assert result.status == "ok"
        assert "No audit result" in result.data["reason"]
        mock_sm.record_outcome.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_turn_records_outcome_true(self):
        """Successful audit status → record_outcome(cap, True) for each capability."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {"respond": 0.85}
        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={"audit_result": {"status": "ok"}})

        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_sm.record_outcome.assert_called_once_with("respond", True)
        mock_sm.update_confidence_from_outcomes.assert_called_once()
        assert result.data["confidence_updates"] == {"respond": 0.85}
        assert result.data["outcomes_recorded"][0]["success"] is True

    @pytest.mark.asyncio
    async def test_failed_turn_records_outcome_false(self):
        """Failed audit status → record_outcome(cap, False)."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {"respond": 0.60}
        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={"audit_result": {"status": "error"}})

        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_sm.record_outcome.assert_called_once_with("respond", False)
        assert result.data["outcomes_recorded"][0]["success"] is False

    @pytest.mark.asyncio
    async def test_causal_reasoning_capability_inferred(self):
        """Causal graph result in metadata → 'causal_reasoning' capability recorded."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}
        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "ok"},
            "causal_graph_result": {"node_count": 5},
        })

        result = await block.execute(ctx)

        recorded_caps = [o["capability"] for o in result.data["outcomes_recorded"]]
        assert "respond" in recorded_caps
        assert "causal_reasoning" in recorded_caps

    @pytest.mark.asyncio
    async def test_ethical_deliberation_capability_inferred(self):
        """Ethics decision in metadata → 'ethical_deliberation' capability recorded."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}
        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "ok"},
            "ethics_decision": {"blocked": False},
        })

        result = await block.execute(ctx)

        recorded_caps = [o["capability"] for o in result.data["outcomes_recorded"]]
        assert "ethical_deliberation" in recorded_caps

    @pytest.mark.asyncio
    async def test_failed_turn_proposes_goal_revision(self):
        """Failed turn with active goals → propose_revision() called."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        mock_goal = MagicMock()
        mock_goal.goal_id = "goal-1"

        mock_gp = MagicMock()
        mock_gp.get_active_goals.return_value = [mock_goal]
        mock_gp.propose_revision.return_value = {
            "goal_id": "goal-1",
            "revision": "reassess",
        }

        block = OutcomeFeedbackBlock(self_model=mock_sm, goal_persistence=mock_gp)
        ctx = _make_context(metadata={"audit_result": {"status": "failed"}})

        result = await block.execute(ctx)

        mock_gp.propose_revision.assert_called_once()
        assert len(result.data["revisions_proposed"]) == 1
        assert result.data["revisions_proposed"][0]["goal_id"] == "goal-1"

    @pytest.mark.asyncio
    async def test_successful_turn_no_goal_revision(self):
        """Successful turn → no goal revision proposed."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        mock_gp = MagicMock()
        mock_gp.get_active_goals.return_value = []

        block = OutcomeFeedbackBlock(self_model=mock_sm, goal_persistence=mock_gp)
        ctx = _make_context(metadata={"audit_result": {"status": "ok"}})

        result = await block.execute(ctx)

        mock_gp.propose_revision.assert_not_called()
        assert result.data["revisions_proposed"] == []

    @pytest.mark.asyncio
    async def test_goal_persistence_none_partial_operation(self):
        """GoalPersistence=None → self_model part works, no goal revision."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {"respond": 0.70}

        block = OutcomeFeedbackBlock(self_model=mock_sm, goal_persistence=None)
        ctx = _make_context(metadata={"audit_result": {"status": "error"}})

        result = await block.execute(ctx)

        assert result.status == "ok"
        mock_sm.record_outcome.assert_called_once_with("respond", False)
        assert result.data["revisions_proposed"] == []

    @pytest.mark.asyncio
    async def test_memory_boost_ids_written_on_failure(self):
        """Failed turn with retrieved memories → boost IDs in metadata."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        metadata = {
            "audit_result": {"status": "error"},
            "retrieved_memory_ids": ["mem-1", "mem-2"],
        }
        ctx = _make_context(metadata=metadata)

        result = await block.execute(ctx)

        assert ctx.metadata["_feedback_memory_boost_ids"] == ["mem-1", "mem-2"]
        assert result.data["memory_boost_ids"] == ["mem-1", "mem-2"]

    @pytest.mark.asyncio
    async def test_no_memory_boost_on_success(self):
        """Successful turn → no memory boost IDs."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "ok"},
            "retrieved_memory_ids": ["mem-1"],
        })

        result = await block.execute(ctx)

        assert "_feedback_memory_boost_ids" not in ctx.metadata
        assert result.data["memory_boost_ids"] == []

    @pytest.mark.asyncio
    async def test_confidence_updates_written_to_metadata(self):
        """Confidence updates are written to context metadata for downstream blocks."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {
            "respond": 0.82, "causal_reasoning": 0.75,
        }

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "ok"},
            "causal_graph_result": {"node_count": 3},
        })

        await block.execute(ctx)

        assert ctx.metadata["self_model_confidences"]["respond"] == 0.82

    @pytest.mark.asyncio
    async def test_ethics_blocked_is_failure(self):
        """Ethics gate blocked → turn is considered a failure (ambiguous audit status)."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "recorded"},  # ambiguous → fallback checks
            "ethics_decision": {"blocked": True},
        })

        _result = await block.execute(ctx)

        # With ethics blocked, should record failure
        calls = mock_sm.record_outcome.call_args_list
        assert any(c.args == ("respond", False) for c in calls)

    @pytest.mark.asyncio
    async def test_pipeline_errors_is_failure(self):
        """Pipeline errors in metadata → turn is failure (ambiguous audit status)."""
        mock_sm = MagicMock()
        mock_sm.update_confidence_from_outcomes.return_value = {}

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={
            "audit_result": {"status": "recorded"},  # ambiguous → fallback checks
            "pipeline_errors": ["narrative_layer: timeout"],
        })

        _result = await block.execute(ctx)

        calls = mock_sm.record_outcome.call_args_list
        assert any(c.args == ("respond", False) for c in calls)

    def test_dependencies(self):
        """OutcomeFeedbackBlock depends on audit_layer."""
        block = OutcomeFeedbackBlock()
        assert block.get_dependencies() == ["audit_layer"]

    def test_block_id(self):
        """Block ID is 'outcome_feedback'."""
        block = OutcomeFeedbackBlock()
        assert block.block_id == "outcome_feedback"

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Internal errors → status='error', not crash."""
        mock_sm = MagicMock()
        mock_sm.record_outcome.side_effect = RuntimeError("DB down")

        block = OutcomeFeedbackBlock(self_model=mock_sm)
        ctx = _make_context(metadata={"audit_result": {"status": "ok"}})

        result = await block.execute(ctx)

        assert result.status == "error"
        assert "DB down" in result.data["error"]
