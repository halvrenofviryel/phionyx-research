"""
Unit tests for Early Exit Optimizer
"""
import pytest
from unittest.mock import Mock
from phionyx_core.orchestrator.early_exit_optimizer import (
    EarlyExitOptimizer,
    EarlyExitCondition
)
from phionyx_core.pipeline.base import BlockContext, BlockResult


class TestEarlyExitOptimizer:
    """Test EarlyExitOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create EarlyExitOptimizer instance."""
        return EarlyExitOptimizer()

    @pytest.fixture
    def mock_context(self):
        """Create mock context."""
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )
        context.metadata = {}
        return context

    def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert len(optimizer.conditions) > 0
        assert optimizer.metrics["early_exits"] == 0

    def test_intent_greeting_template_condition(self, optimizer, mock_context):
        """Test intent-based greeting template condition."""
        result = BlockResult(
            block_id="intent_classification",
            status="ok",
            data={
                "intent": {
                    "intent": "greeting",
                    "confidence": 0.8
                }
            }
        )

        mock_context.metadata["template_response_available"] = True

        condition = optimizer.should_short_circuit(
            block_id="intent_classification",
            context=mock_context,
            result=result
        )

        assert condition is not None
        assert condition.condition_type == "intent"
        assert optimizer.metrics["intent_based_exits"] == 1

    def test_safety_gate_blocked_condition(self, optimizer, mock_context):
        """Test safety gate blocked condition."""
        result = BlockResult(
            block_id="input_safety_gate",
            status="ok",
            data={
                "is_blocked": True,
                "gate_triggered": True
            }
        )

        condition = optimizer.should_short_circuit(
            block_id="input_safety_gate",
            context=mock_context,
            result=result
        )

        assert condition is not None
        assert condition.condition_type == "safety"
        assert optimizer.metrics["safety_exits"] == 1

    def test_template_response_condition(self, optimizer, mock_context):
        """Test template response condition."""
        result = BlockResult(
            block_id="narrative_layer",
            status="ok",
            data={
                "narrative_text": "Hello!",
                "narrative_result": {
                    "source": "template"
                }
            }
        )

        condition = optimizer.should_short_circuit(
            block_id="narrative_layer",
            context=mock_context,
            result=result
        )

        assert condition is not None
        assert condition.condition_type == "template"
        assert optimizer.metrics["template_exits"] == 1

    def test_get_blocks_to_skip(self, optimizer):
        """Test getting blocks to skip."""
        condition = optimizer.conditions["intent_greeting_template"]
        blocks_to_skip = optimizer.get_blocks_to_skip(
            condition=condition,
            current_block_id="intent_classification"
        )

        assert len(blocks_to_skip) > 0
        assert "intent_classification" not in blocks_to_skip  # Current block not skipped
        assert "response_build" not in blocks_to_skip  # Always-on block preserved

    def test_get_blocks_to_skip_preserves_always_on(self, optimizer):
        """Test that always-on blocks are preserved."""
        condition = optimizer.conditions["intent_greeting_template"]
        blocks_to_skip = optimizer.get_blocks_to_skip(
            condition=condition,
            current_block_id="intent_classification"
        )

        # Always-on blocks should not be in skip list
        always_on_blocks = {"response_build", "phi_computation", "entropy_computation"}
        assert not (blocks_to_skip & always_on_blocks)

    def test_metrics_collection(self, optimizer, mock_context):
        """Test metrics collection."""
        # Trigger multiple early exits
        result1 = BlockResult(
            block_id="intent_classification",
            status="ok",
            data={"intent": {"intent": "greeting"}}
        )
        mock_context.metadata["template_response_available"] = True
        optimizer.should_short_circuit("intent_classification", mock_context, result1)

        result2 = BlockResult(
            block_id="input_safety_gate",
            status="ok",
            data={"is_blocked": True}
        )
        optimizer.should_short_circuit("input_safety_gate", mock_context, result2)

        metrics = optimizer.get_metrics()

        assert metrics["early_exits"] == 2
        assert metrics["intent_based_exits"] == 1
        assert metrics["safety_exits"] == 1

    def test_reset_metrics(self, optimizer, mock_context):
        """Test metrics reset."""
        result = BlockResult(
            block_id="intent_classification",
            status="ok",
            data={"intent": {"intent": "greeting"}}
        )
        mock_context.metadata["template_response_available"] = True
        optimizer.should_short_circuit("intent_classification", mock_context, result)

        assert optimizer.metrics["early_exits"] > 0

        optimizer.reset_metrics()

        assert optimizer.metrics["early_exits"] == 0
        assert optimizer.metrics["intent_based_exits"] == 0

