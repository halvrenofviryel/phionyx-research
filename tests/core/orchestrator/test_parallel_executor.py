"""
Unit tests for Parallel Executor
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from phionyx_core.orchestrator.parallel_executor import (
    ParallelExecutor,
    ParallelGroup
)
from phionyx_core.orchestrator.dependency_validator import DependencyValidator
from phionyx_core.pipeline.base import BlockContext, BlockResult


class TestParallelGroup:
    """Test ParallelGroup."""

    def test_group_creation(self):
        """Test parallel group creation."""
        group = ParallelGroup(
            block_ids=["block1", "block2"],
            dependencies={"block0"},
            read_only=True
        )

        assert len(group.block_ids) == 2
        assert "block1" in group.block_ids
        assert "block2" in group.block_ids
        assert "block0" in group.dependencies
        assert group.read_only is True

    def test_group_validation_empty(self):
        """Test that empty group raises error."""
        with pytest.raises(ValueError):
            ParallelGroup(block_ids=[])


class TestParallelExecutor:
    """Test ParallelExecutor."""

    @pytest.fixture
    def dependency_validator(self):
        """Create dependency validator."""
        validator = DependencyValidator()
        # Mock dependencies
        validator.dependencies = {
            "block1": {"dependencies": [], "writes": ["key1"], "reads": []},
            "block2": {"dependencies": [], "writes": ["key2"], "reads": []},
            "block3": {"dependencies": ["block1"], "writes": ["key3"], "reads": ["key1"]},
        }
        return validator

    @pytest.fixture
    def executor(self, dependency_validator):
        """Create ParallelExecutor."""
        return ParallelExecutor(
            dependency_validator=dependency_validator,
            enable_parallel=True
        )

    def test_identify_parallel_groups_independent(self, executor):
        """Test identification of independent parallel groups."""
        block_order = ["block1", "block2", "block3"]
        executed_blocks = set()
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        groups = executor.identify_parallel_groups(
            block_order=block_order,
            executed_blocks=executed_blocks,
            context=context
        )

        # block1 and block2 should be in a parallel group
        assert len(groups) > 0
        group = groups[0]
        assert "block1" in group.block_ids or "block2" in group.block_ids

    def test_identify_parallel_groups_with_dependencies(self, executor):
        """Test that blocks with dependencies are not grouped together."""
        block_order = ["block1", "block3"]
        executed_blocks = set()
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        groups = executor.identify_parallel_groups(
            block_order=block_order,
            executed_blocks=executed_blocks,
            context=context
        )

        # block3 depends on block1, so they shouldn't be in the same group
        if groups:
            for group in groups:
                if "block1" in group.block_ids:
                    assert "block3" not in group.block_ids

    def test_has_write_conflict(self, executor):
        """Test write conflict detection."""
        # block1 writes to key1, block2 writes to key2 (no conflict)
        assert executor._has_write_conflict("block1", "block2") is False

        # If both write to same key, there's a conflict
        executor.dependency_validator.dependencies["block2"]["writes"] = ["key1"]
        assert executor._has_write_conflict("block1", "block2") is True

    def test_is_read_only_group(self, executor):
        """Test read-only group detection."""
        # block1 writes, so group is not read-only
        assert executor._is_read_only_group(["block1"]) is False

        # If no blocks write, group is read-only
        executor.dependency_validator.dependencies["read_block"] = {
            "dependencies": [],
            "writes": [],
            "reads": ["key1"]
        }
        assert executor._is_read_only_group(["read_block"]) is True

    @pytest.mark.asyncio
    async def test_execute_parallel_group_single_block(self, executor):
        """Test executing a single block."""
        block = Mock()
        block.execute = AsyncMock(return_value=BlockResult(
            block_id="block1",
            status="ok",
            data={"result": "test"}
        ))

        blocks = {"block1": block}
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        group = ParallelGroup(block_ids=["block1"])
        results = await executor.execute_parallel_group(group, blocks, context)

        assert "block1" in results
        assert results["block1"].status == "ok"
        block.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parallel_group_multiple_blocks(self, executor):
        """Test executing multiple blocks in parallel."""
        block1 = Mock()
        block1.execute = AsyncMock(return_value=BlockResult(
            block_id="block1",
            status="ok",
            data={"result1": "test1"}
        ))

        block2 = Mock()
        block2.execute = AsyncMock(return_value=BlockResult(
            block_id="block2",
            status="ok",
            data={"result2": "test2"}
        ))

        blocks = {"block1": block1, "block2": block2}
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        group = ParallelGroup(block_ids=["block1", "block2"])
        results = await executor.execute_parallel_group(group, blocks, context)

        assert "block1" in results
        assert "block2" in results
        assert results["block1"].status == "ok"
        assert results["block2"].status == "ok"

        # Both blocks should have been called
        block1.execute.assert_called_once()
        block2.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parallel_group_error_handling(self, executor):
        """Test error handling in parallel execution."""
        block = Mock()
        block.execute = AsyncMock(side_effect=Exception("Test error"))

        blocks = {"block1": block}
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        group = ParallelGroup(block_ids=["block1"])
        results = await executor.execute_parallel_group(group, blocks, context)

        assert "block1" in results
        assert results["block1"].status == "error"
        assert results["block1"].error is not None

    def test_copy_context(self, executor):
        """Test context copying for parallel execution."""
        original_context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test",
            metadata={"key": "value"}
        )

        copied_context = executor._copy_context(original_context)

        # Should be a different object
        assert copied_context is not original_context

        # But should have same values
        assert copied_context.user_input == original_context.user_input
        assert copied_context.metadata == original_context.metadata

        # Modifying copied context shouldn't affect original
        copied_context.metadata["new_key"] = "new_value"
        assert "new_key" not in original_context.metadata

    def test_merge_results(self, executor):
        """Test result merging into context."""
        context = BlockContext(
            user_input="test",
            card_type="test",
            card_title="test",
            scene_context="test",
            card_result="test"
        )

        results = {
            "block1": BlockResult(
                block_id="block1",
                status="ok",
                data={"result1": "value1"}
            ),
            "block2": BlockResult(
                block_id="block2",
                status="ok",
                data={"result2": "value2"}
            )
        }

        merged_context = executor.merge_results(results, context)

        assert merged_context.metadata["result1"] == "value1"
        assert merged_context.metadata["result2"] == "value2"
        assert merged_context.metadata["block1_result"]["result1"] == "value1"

