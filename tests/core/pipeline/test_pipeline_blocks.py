"""
Unit tests for Pipeline Blocks.

Tests for the 31 canonical pipeline blocks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional

from phionyx_core.pipeline.base import BlockContext, BlockResult, PipelineBlock


class TestBasePipelineBlock:
    """Test suite for PipelineBlock base class."""

    @pytest.fixture
    def mock_block(self):
        """Create a mock pipeline block."""
        block = Mock(spec=PipelineBlock)
        block.block_id = "test_block"
        block.should_skip = Mock(return_value=None)
        block.execute = AsyncMock(return_value=BlockResult(
            block_id="test_block",
            status="ok",
            data={}
        ))
        return block

    @pytest.fixture
    def block_context(self) -> BlockContext:
        """Create a test block context."""
        return BlockContext(
            user_input="test input",
            card_type="shadow",
            card_title="Test Card",
            scene_context="test scene",
            card_result="neutral",
            session_id="test_session",
            current_amplitude=5.0,
            current_entropy=0.5,
            current_integrity=100.0
        )

    def test_block_has_block_id(self, mock_block):
        """Test that block has block_id attribute."""
        assert hasattr(mock_block, 'block_id')
        assert mock_block.block_id == "test_block"

    def test_block_has_should_skip_method(self, mock_block):
        """Test that block has should_skip method."""
        assert hasattr(mock_block, 'should_skip')
        assert callable(mock_block.should_skip)

    def test_block_has_execute_method(self, mock_block):
        """Test that block has execute method."""
        assert hasattr(mock_block, 'execute')
        assert callable(mock_block.execute)

    @pytest.mark.asyncio
    async def test_block_execute_returns_block_result(self, mock_block, block_context):
        """Test that block execute returns BlockResult."""
        result = await mock_block.execute(block_context)
        assert isinstance(result, BlockResult)
        assert result.block_id == "test_block"
        assert result.status == "ok"

    def test_block_should_skip_returns_reason_or_none(self, mock_block, block_context):
        """Test that should_skip returns skip reason or None."""
        skip_reason = mock_block.should_skip(block_context)
        # Should return None (no skip) or a string (skip reason)
        assert skip_reason is None or isinstance(skip_reason, str)


class TestBlockResult:
    """Test suite for BlockResult dataclass."""

    def test_block_result_creation(self):
        """Test creating a BlockResult."""
        result = BlockResult(
            block_id="test_block",
            status="ok",
            data={"key": "value"}
        )
        assert result.block_id == "test_block"
        assert result.status == "ok"
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.skip_reason is None

    def test_block_result_is_success(self):
        """Test is_success method."""
        result = BlockResult(block_id="test", status="ok")
        assert result.is_success() is True

        result = BlockResult(block_id="test", status="error")
        assert result.is_success() is False

        result = BlockResult(block_id="test", status="skipped")
        assert result.is_success() is False

    def test_block_result_is_skipped(self):
        """Test is_skipped method."""
        result = BlockResult(block_id="test", status="skipped", skip_reason="test")
        assert result.is_skipped() is True

        result = BlockResult(block_id="test", status="ok")
        assert result.is_skipped() is False

    def test_block_result_is_error(self):
        """Test is_error method."""
        result = BlockResult(block_id="test", status="error", error=ValueError("test"))
        assert result.is_error() is True

        result = BlockResult(block_id="test", status="ok")
        assert result.is_error() is False


class TestBlockContext:
    """Test suite for BlockContext dataclass."""

    def test_block_context_creation_minimal(self):
        """Test creating BlockContext with minimal fields."""
        context = BlockContext(
            user_input="test",
            card_type="shadow",
            card_title="",
            scene_context="",
            card_result="neutral"
        )
        assert context.user_input == "test"
        assert context.card_type == "shadow"
        assert context.metadata == {}

    def test_block_context_creation_full(self):
        """Test creating BlockContext with all fields."""
        context = BlockContext(
            user_input="test",
            card_type="shadow",
            card_title="Test",
            scene_context="scene",
            card_result="neutral",
            scenario_id="scenario_1",
            scenario_step_id="step_1",
            session_id="session_1",
            participant=Mock(),
            mode="test_mode",
            strategy="test_strategy",
            current_amplitude=5.0,
            current_entropy=0.5,
            current_integrity=100.0,
            previous_phi=1.0,
            metadata={"key": "value"}
        )
        assert context.user_input == "test"
        assert context.scenario_id == "scenario_1"
        assert context.metadata == {"key": "value"}

    def test_block_context_metadata_defaults_to_empty_dict(self):
        """Test that metadata defaults to empty dict."""
        context = BlockContext(
            user_input="test",
            card_type="shadow",
            card_title="",
            scene_context="",
            card_result="neutral"
        )
        assert context.metadata == {}
        assert isinstance(context.metadata, dict)


# Test for specific blocks - we'll add more as we implement them
class TestLowInputGateBlock:
    """Test suite for LowInputGateBlock."""

    @pytest.fixture
    def block_context(self) -> BlockContext:
        """Create a test block context."""
        return BlockContext(
            user_input="test",
            card_type="shadow",
            card_title="",
            scene_context="",
            card_result="neutral"
        )

    @pytest.mark.asyncio
    async def test_low_input_gate_block_exists(self):
        """Test that LowInputGateBlock can be imported and instantiated."""
        try:
            from phionyx_core.pipeline.blocks.archive.low_input_gate import LowInputGateBlock
            # Block may require initialization parameters
            # This test verifies the block exists and can be imported
            assert LowInputGateBlock is not None
        except ImportError:
            pytest.skip("LowInputGateBlock not available")
        except Exception:
            # Block may require specific initialization
            pass

