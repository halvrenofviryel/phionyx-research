"""
Parallel Executor
================

Infrastructure for parallel execution of independent pipeline blocks.

Features:
- Dependency analysis
- Read/write conflict detection
- Parallel group formation
- Context copy mechanism
- Result merging
"""

import asyncio
import logging
import time
from copy import deepcopy
from dataclasses import dataclass, field

from ..pipeline.base import BlockContext, BlockResult, PipelineBlock
from .dependency_validator import DependencyValidator

logger = logging.getLogger(__name__)

# OpenTelemetry integration (optional)
try:
    from opentelemetry.trace import Status, StatusCode

    from phionyx_core.telemetry import get_tracer, is_opentelemetry_enabled
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    get_tracer = None
    def is_opentelemetry_enabled() -> bool:
        return False
    Status = None
    StatusCode = None


@dataclass
class ParallelGroup:
    """Group of blocks that can be executed in parallel."""
    block_ids: list[str]
    dependencies: set[str] = field(default_factory=set)
    read_only: bool = True  # If True, blocks only read from context

    def __post_init__(self):
        """Validate group."""
        if not self.block_ids:
            raise ValueError("ParallelGroup must have at least one block_id")


class ParallelExecutor:
    """
    Executes independent blocks in parallel.

    Features:
    - Dependency analysis
    - Read/write conflict detection
    - Context copy for parallel execution
    - Result merging
    """

    def __init__(
        self,
        dependency_validator: DependencyValidator,
        enable_parallel: bool = True
    ):
        """
        Initialize parallel executor.

        Args:
            dependency_validator: Dependency validator for block analysis
            enable_parallel: Enable parallel execution (default: True)
        """
        self.dependency_validator = dependency_validator
        self.enable_parallel = enable_parallel

    def identify_parallel_groups(
        self,
        block_order: list[str],
        executed_blocks: set[str],
        context: BlockContext
    ) -> list[ParallelGroup]:
        """
        Identify groups of blocks that can be executed in parallel.

        Args:
            block_order: Canonical block order
            executed_blocks: Set of already executed block IDs
            context: Current pipeline context

        Returns:
            List of ParallelGroup objects
        """
        if not self.enable_parallel:
            return []

        # Find remaining blocks
        remaining_blocks = [
            block_id for block_id in block_order
            if block_id not in executed_blocks
        ]

        if not remaining_blocks:
            return []

        # Identify independent blocks (no dependencies on each other)
        groups = []
        processed = set()

        for block_id in remaining_blocks:
            if block_id in processed:
                continue

            # Get block dependencies
            deps = self.dependency_validator.get_block_dependencies(block_id)

            # Check if all dependencies are executed
            if not all(dep in executed_blocks for dep in deps):
                continue  # Skip if dependencies not met

            # Find other blocks that can run in parallel
            parallel_blocks = [block_id]
            processed.add(block_id)

            for other_block_id in remaining_blocks:
                if other_block_id in processed:
                    continue

                # Check if other block can run in parallel
                other_deps = self.dependency_validator.get_block_dependencies(other_block_id)

                # Check if dependencies are met
                if not all(dep in executed_blocks for dep in other_deps):
                    continue

                # Check for conflicts (both blocks write to same context keys)
                if self._has_write_conflict(block_id, other_block_id):
                    continue

                # Check if other block depends on current block
                if block_id in other_deps:
                    continue

                # Check if current block depends on other block
                if other_block_id in deps:
                    continue

                # Can run in parallel
                parallel_blocks.append(other_block_id)
                processed.add(other_block_id)

            if len(parallel_blocks) > 1:
                # Create parallel group
                group = ParallelGroup(
                    block_ids=parallel_blocks,
                    dependencies=set(deps),
                    read_only=self._is_read_only_group(parallel_blocks)
                )
                groups.append(group)
            else:
                # Single block, no parallel execution
                processed.add(block_id)

        return groups

    def _has_write_conflict(
        self,
        block_id1: str,
        block_id2: str
    ) -> bool:
        """
        Check if two blocks have write conflicts.

        Args:
            block_id1: First block ID
            block_id2: Second block ID

        Returns:
            True if there's a write conflict, False otherwise
        """
        # Get write keys for each block (from dependency validator)
        writes1 = self.dependency_validator.get_block_writes(block_id1)
        writes2 = self.dependency_validator.get_block_writes(block_id2)

        # Check for overlap
        return bool(writes1 & writes2)

    def _is_read_only_group(self, block_ids: list[str]) -> bool:
        """
        Check if a group of blocks is read-only.

        Args:
            block_ids: List of block IDs

        Returns:
            True if all blocks are read-only, False otherwise
        """
        for block_id in block_ids:
            writes = self.dependency_validator.get_block_writes(block_id)
            if writes:
                return False
        return True

    async def execute_parallel_group(
        self,
        group: ParallelGroup,
        blocks: dict[str, PipelineBlock],
        context: BlockContext
    ) -> dict[str, BlockResult]:
        """
        Execute a group of blocks in parallel.

        Args:
            group: ParallelGroup to execute
            blocks: Dictionary of block_id -> PipelineBlock
            context: Current pipeline context

        Returns:
            Dictionary of block_id -> BlockResult
        """
        if not group.block_ids:
            return {}

        if len(group.block_ids) == 1:
            # Single block, execute sequentially
            block_id = group.block_ids[0]
            block = blocks.get(block_id)
            if not block:
                logger.warning(f"Block {block_id} not found in blocks registry")
                return {}

            try:
                result = await block.execute(context)
                return {block_id: result}
            except Exception as e:
                logger.error(f"Block {block_id} execution failed: {e}", exc_info=True)
                return {
                    block_id: BlockResult(
                        block_id=block_id,
                        status="error",
                        error=e
                    )
                }

        # Multiple blocks - execute in parallel
        logger.debug(f"Executing parallel group: {group.block_ids}")

        # OpenTelemetry: Create group-level span
        group_span = None
        group_start_time = None
        tracer = None
        if OPENTELEMETRY_AVAILABLE and is_opentelemetry_enabled():
            try:
                tracer = get_tracer(__name__)
                if tracer:
                    group_start_time = time.time()
                    group_span = tracer.start_as_current_span("parallel_group")
                    group_span.set_attribute("parallel_group.size", len(group.block_ids))
                    group_span.set_attribute("parallel_group.read_only", group.read_only)
                    group_span.set_attribute("parallel_group.block_ids", ",".join(group.block_ids))
                    if group.dependencies:
                        group_span.set_attribute("parallel_group.dependencies", ",".join(group.dependencies))
            except Exception as e:
                logger.debug(f"OpenTelemetry group span creation failed (non-critical): {e}")

        try:
            # Create context copies for each block (to avoid conflicts)
            contexts = {}
            for block_id in group.block_ids:
                # Deep copy context for parallel execution
                contexts[block_id] = self._copy_context(context)

            # Execute all blocks in parallel
            async def execute_block(block_id: str) -> tuple[str, BlockResult]:
                # OpenTelemetry: Create block-level span within parallel group
                block_span = None
                block_start_time = None
                if OPENTELEMETRY_AVAILABLE and is_opentelemetry_enabled() and tracer:
                    try:
                        block_start_time = time.time()
                        block_span = tracer.start_as_current_span(f"block.{block_id}")
                        block_span.set_attribute("block.name", block_id)
                        block_span.set_attribute("block.parallel", True)
                        # Get block category (simplified)
                        block_category = "core"
                        if "middleware" in block_id:
                            block_category = "middleware"
                        elif block_id in ["entropy_computation", "phi_computation", "emotion_estimation", "state_update_physics"]:
                            block_category = "physics"
                        elif "safety" in block_id or "gate" in block_id or "ethics" in block_id:
                            block_category = "safety"
                        block_span.set_attribute("block.category", block_category)
                    except Exception as e:
                        logger.debug(f"OpenTelemetry block span creation failed (non-critical): {e}")

                block = blocks.get(block_id)
                if not block:
                    logger.warning(f"Block {block_id} not found in blocks registry")
                    result = BlockResult(
                        block_id=block_id,
                        status="error",
                        error=ValueError(f"Block {block_id} not found")
                    )
                    # Update span with error
                    if block_span:
                        try:
                            block_span.set_status(Status(StatusCode.ERROR, f"Block not found: {block_id}"))
                            block_span.end()
                        except Exception:
                            pass
                    return block_id, result

                try:
                    block_context = contexts[block_id]
                    result = await block.execute(block_context)

                    # OpenTelemetry: Update block span with results
                    if block_span:
                        try:
                            if block_start_time:
                                duration_ms = (time.time() - block_start_time) * 1000
                                block_span.set_attribute("block.duration_ms", duration_ms)
                            block_span.set_attribute("block.success", result.is_success())
                            if result.data:
                                if "entropy" in result.data:
                                    block_span.set_attribute("block.entropy", float(result.data["entropy"]))
                                if "phi" in result.data:
                                    block_span.set_attribute("block.phi", float(result.data["phi"]))
                            if result.is_error() and result.error:
                                block_span.set_status(Status(StatusCode.ERROR, str(result.error)))
                                block_span.record_exception(result.error)
                            block_span.end()
                        except Exception as e:
                            logger.debug(f"OpenTelemetry block span update failed (non-critical): {e}")

                    return block_id, result
                except Exception as e:
                    logger.error(f"Block {block_id} execution failed: {e}", exc_info=True)
                    result = BlockResult(
                        block_id=block_id,
                        status="error",
                        error=e
                    )
                    # Update span with error
                    if block_span:
                        try:
                            block_span.set_status(Status(StatusCode.ERROR, str(e)))
                            block_span.record_exception(e)
                            block_span.end()
                        except Exception:
                            pass
                    return block_id, result

            # Execute all blocks concurrently
            tasks = [execute_block(block_id) for block_id in group.block_ids]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert to dictionary
            results = {}
            success_count = 0
            error_count = 0
            for result_item in results_list:
                if isinstance(result_item, Exception):
                    logger.error(f"Parallel execution task failed: {result_item}")
                    error_count += 1
                    continue

                block_id, result = result_item
                results[block_id] = result
                if result.is_success():
                    success_count += 1
                else:
                    error_count += 1

            # OpenTelemetry: Update group span with results
            if group_span:
                try:
                    if group_start_time:
                        duration_ms = (time.time() - group_start_time) * 1000
                        group_span.set_attribute("parallel_group.duration_ms", duration_ms)
                    group_span.set_attribute("parallel_group.success_count", success_count)
                    group_span.set_attribute("parallel_group.error_count", error_count)
                    if error_count > 0:
                        group_span.set_status(Status(StatusCode.ERROR, f"{error_count} blocks failed"))
                    else:
                        group_span.set_status(Status(StatusCode.OK))
                    group_span.end()
                except Exception as e:
                    logger.debug(f"OpenTelemetry group span update failed (non-critical): {e}")

            return results

        except Exception as e:
            logger.error(f"Parallel group execution failed: {e}", exc_info=True)
            # OpenTelemetry: Mark group span as error
            if group_span:
                try:
                    group_span.set_status(Status(StatusCode.ERROR, str(e)))
                    group_span.record_exception(e)
                    group_span.end()
                except Exception:
                    pass
            # Return empty results or error results
            return {}

    def _copy_context(self, context: BlockContext) -> BlockContext:
        """
        Create a deep copy of context for parallel execution.

        Args:
            context: Original context

        Returns:
            Deep copy of context
        """
        # Create new context with copied data
        new_metadata = deepcopy(context.metadata) if context.metadata else {}

        return BlockContext(
            user_input=context.user_input,
            card_type=context.card_type,
            card_title=context.card_title,
            scene_context=context.scene_context,
            card_result=context.card_result,
            scenario_id=context.scenario_id,
            scenario_step_id=context.scenario_step_id,
            session_id=context.session_id,
            current_amplitude=context.current_amplitude,
            current_entropy=context.current_entropy,
            current_integrity=context.current_integrity,
            previous_phi=context.previous_phi,
            participant=context.participant,
            mode=context.mode,
            strategy=context.strategy,
            envelope_message_id=context.envelope_message_id,
            envelope_turn_id=context.envelope_turn_id,
            envelope_user_text_sha256=context.envelope_user_text_sha256,
            capabilities=context.capabilities,
            capability_deriver=context.capability_deriver,
            metadata=new_metadata
        )

    def merge_results(
        self,
        results: dict[str, BlockResult],
        context: BlockContext
    ) -> BlockContext:
        """
        Merge parallel execution results into context.

        Args:
            results: Dictionary of block_id -> BlockResult
            context: Current pipeline context

        Returns:
            Updated context with merged results
        """
        if context.metadata is None:
            context.metadata = {}

        # Merge results into context metadata
        for block_id, result in results.items():
            if result.is_success() and result.data:
                # CRITICAL: Filter out Mock objects - only merge real dictionaries
                if isinstance(result.data, dict):
                    # Merge result data into context metadata
                    # CRITICAL: Only merge actual dictionary values, skip Mock objects
                    filtered_data = {
                        k: v for k, v in result.data.items()
                        if not (hasattr(v, '__class__') and 'Mock' in str(type(v)))
                    }
                    context.metadata.update(filtered_data)

                    # CRITICAL: Special handling for physics_state - ensure it's always a dictionary
                    if "physics_state" in context.metadata:
                        physics_state = context.metadata["physics_state"]
                        if not isinstance(physics_state, dict):
                            logger.warning(f"[Parallel] physics_state is not a dictionary (type: {type(physics_state)}), creating new dictionary")
                            context.metadata["physics_state"] = {}

                    # Store result for reference (only if it's a real dictionary)
                    context.metadata[f"{block_id}_result"] = filtered_data

        return context

