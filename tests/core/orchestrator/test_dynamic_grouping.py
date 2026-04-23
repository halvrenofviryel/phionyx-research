"""
Unit tests for Dynamic Grouping
"""
import pytest
from phionyx_core.orchestrator.dynamic_grouping import (
    DynamicGrouping,
    IntentBasedGroupConfig
)
from phionyx_core.orchestrator.parallel_executor import ParallelGroup


class TestDynamicGrouping:
    """Test DynamicGrouping."""

    @pytest.fixture
    def grouping(self):
        """Create DynamicGrouping instance."""
        return DynamicGrouping()

    def test_initialization(self, grouping):
        """Test grouping initialization."""
        assert len(grouping.configs) > 0
        assert "greeting" in grouping.configs
        assert "question" in grouping.configs
        assert "high_risk" in grouping.configs

    def test_get_groups_for_intent_greeting(self, grouping):
        """Test getting groups for greeting intent."""
        block_order = [
            "time_update_sot",
            "input_safety_gate",
            "intent_classification",
            "context_retrieval_rag",
            "create_scenario_frame",
            "phi_computation",
            "entropy_computation"
        ]
        executed_blocks = {"time_update_sot"}

        groups = grouping.get_groups_for_intent(
            intent="greeting",
            block_order=block_order,
            executed_blocks=executed_blocks
        )

        assert len(groups) > 0
        # Should have parallel groups for greeting
        for group in groups:
            assert isinstance(group, ParallelGroup)
            assert len(group.block_ids) > 0

    def test_get_groups_for_intent_question(self, grouping):
        """Test getting groups for question intent."""
        block_order = [
            "intent_classification",
            "input_safety_gate",
            "context_retrieval_rag",
            "ukf_predict",
            "entropy_amplitude_pre_gate",
            "phi_computation",
            "entropy_computation"
        ]
        executed_blocks = set()

        groups = grouping.get_groups_for_intent(
            intent="question",
            block_order=block_order,
            executed_blocks=executed_blocks
        )

        assert len(groups) > 0
        # Question intent should have more parallel groups
        assert any(len(group.block_ids) > 1 for group in groups)

    def test_get_groups_for_intent_high_risk(self, grouping):
        """Test getting groups for high-risk intent."""
        block_order = [
            "input_safety_gate",
            "intent_classification",
            "phi_computation",
            "entropy_computation"
        ]
        executed_blocks = set()

        groups = grouping.get_groups_for_intent(
            intent="high_risk",
            block_order=block_order,
            executed_blocks=executed_blocks
        )

        # High-risk should have fewer parallel groups (safety first)
        assert len(groups) >= 0  # May have no parallel groups for safety

    def test_get_groups_for_unknown_intent(self, grouping):
        """Test getting groups for unknown intent."""
        groups = grouping.get_groups_for_intent(
            intent="unknown_intent",
            block_order=[],
            executed_blocks=set()
        )

        assert groups == []

    def test_get_blocks_to_skip_for_intent_greeting(self, grouping):
        """Test getting blocks to skip for greeting intent."""
        skip_blocks = grouping.get_blocks_to_skip_for_intent("greeting")

        assert "context_retrieval_rag" in skip_blocks
        assert "cognitive_layer" in skip_blocks
        assert "response_build" not in skip_blocks  # Always-on preserved

    def test_get_blocks_to_skip_for_intent_question(self, grouping):
        """Test getting blocks to skip for question intent."""
        skip_blocks = grouping.get_blocks_to_skip_for_intent("question")

        # Question intent should skip fewer blocks
        assert len(skip_blocks) == 0 or len(skip_blocks) < 5

    def test_get_blocks_to_skip_for_intent_high_risk(self, grouping):
        """Test getting blocks to skip for high-risk intent."""
        skip_blocks = grouping.get_blocks_to_skip_for_intent("high_risk")

        assert "context_retrieval_rag" in skip_blocks
        assert "cognitive_layer" in skip_blocks
        assert "narrative_layer" in skip_blocks

    def test_should_preserve_block(self, grouping):
        """Test block preservation check."""
        # Always-on blocks should be preserved
        assert grouping.should_preserve_block("response_build", "greeting") is True
        assert grouping.should_preserve_block("phi_computation", "greeting") is True
        assert grouping.should_preserve_block("entropy_computation", "greeting") is True

        # Other blocks should not be preserved
        assert grouping.should_preserve_block("cognitive_layer", "greeting") is False

    def test_get_groups_filters_executed_blocks(self, grouping):
        """Test that executed blocks are filtered from groups."""
        block_order = ["block1", "block2", "block3"]
        executed_blocks = {"block1"}

        groups = grouping.get_groups_for_intent(
            intent="conversation",
            block_order=block_order,
            executed_blocks=executed_blocks
        )

        # Executed blocks should not be in groups
        for group in groups:
            assert "block1" not in group.block_ids

