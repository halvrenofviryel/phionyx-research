"""
Execution Guard - Comprehensive Infinite Loop Prevention
========================================================

Multiple layers of protection against infinite loops and runaway execution:
1. Iteration limit guard
2. Block execution tracking (duplicate detection)
3. Timeout mechanism
4. Circular dependency detection
5. Early termination on repeated block execution
"""
import logging
import time
from typing import Dict, List, Optional, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from phionyx_core.profiles.schema import ExecutionGuardConfig

logger = logging.getLogger(__name__)


class ExecutionGuard:
    """
    Comprehensive guard against infinite loops and runaway execution.

    Multiple protection layers:
    1. Iteration limit (max iterations per pipeline)
    2. Block execution count tracking (max executions per block)
    3. Timeout mechanism (max execution time)
    4. Circular dependency detection (same block sequence repeated)
    5. Duplicate block execution detection (same block executed multiple times consecutively)
    """

    def __init__(
        self,
        max_iterations: Optional[int] = None,
        max_block_executions: int = 2,  # Same block can execute max 2 times
        max_execution_time: float = 300.0,  # 5 minutes max
        max_repeated_sequence: int = 3  # Same sequence of 3 blocks repeated
    ):
        """
        Initialize execution guard.

        Args:
            max_iterations: Max pipeline iterations (default: 2x block count)
            max_block_executions: Max executions per block (default: 2)
            max_execution_time: Max execution time in seconds (default: 300s = 5min)
            max_repeated_sequence: Max repeated sequence length (default: 3)
        """
        self.max_iterations = max_iterations
        self.max_block_executions = max_block_executions
        self.max_execution_time = max_execution_time
        self.max_repeated_sequence = max_repeated_sequence
        # Captured so reset() can reapply the profile-aware iteration multiplier.
        self._max_iterations_multiplier: int = 3

        # Execution tracking
        self.iteration_count = 0
        self.block_execution_count: Dict[str, int] = defaultdict(int)
        self.execution_sequence: List[str] = []  # Track execution order
        self.start_time: Optional[float] = None
        self.last_block_id: Optional[str] = None
        self.consecutive_repeats: int = 0

        # Violations
        self.violations: List[str] = []
        self.is_safe = True

    @classmethod
    def from_config(
        cls,
        config: Optional["ExecutionGuardConfig"],
        block_order_length: int,
    ) -> "ExecutionGuard":
        """
        Build an ExecutionGuard from a profile-provided config.

        A ``None`` config reproduces the long-standing hard-coded defaults,
        so existing callers (and tests) see no behavioural change.
        """
        if config is None:
            guard = cls(
                max_iterations=block_order_length * 3,
                max_block_executions=2,
                max_execution_time=300.0,
                max_repeated_sequence=3,
            )
            return guard

        guard = cls(
            max_iterations=block_order_length * config.max_iterations_multiplier,
            max_block_executions=config.max_block_executions,
            max_execution_time=config.max_execution_time_sec,
            max_repeated_sequence=config.max_repeated_sequence,
        )
        guard._max_iterations_multiplier = config.max_iterations_multiplier
        return guard

    def reset(self, block_order_length: Optional[int] = None):
        """Reset guard for new pipeline execution."""
        if self.max_iterations is None and block_order_length:
            self.max_iterations = block_order_length * self._max_iterations_multiplier
        self.iteration_count = 0
        self.block_execution_count.clear()
        self.execution_sequence.clear()
        self.start_time = time.time()
        self.last_block_id = None
        self.consecutive_repeats = 0
        self.violations.clear()
        self.is_safe = True

    def check_iteration_limit(self) -> tuple[bool, Optional[str]]:
        """
        Check if iteration limit exceeded.

        Returns:
            (is_safe, violation_message)
        """
        if self.max_iterations and self.iteration_count > self.max_iterations:
            violation = f"Iteration limit exceeded: {self.iteration_count} > {self.max_iterations}"
            self.violations.append(violation)
            self.is_safe = False
            return False, violation
        return True, None

    def check_block_execution_limit(self, block_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if block execution limit exceeded.

        Args:
            block_id: Block ID to check

        Returns:
            (is_safe, violation_message)
        """
        self.block_execution_count[block_id] += 1
        count = self.block_execution_count[block_id]

        if count > self.max_block_executions:
            violation = f"Block '{block_id}' executed {count} times (limit: {self.max_block_executions})"
            self.violations.append(violation)
            self.is_safe = False
            return False, violation

        # Check for consecutive repeats
        if block_id == self.last_block_id:
            self.consecutive_repeats += 1
            if self.consecutive_repeats >= 2:
                violation = f"Block '{block_id}' executed consecutively {self.consecutive_repeats + 1} times"
                self.violations.append(violation)
                self.is_safe = False
                return False, violation
        else:
            self.consecutive_repeats = 0
            self.last_block_id = block_id

        return True, None

    def check_timeout(self) -> tuple[bool, Optional[str]]:
        """
        Check if execution timeout exceeded.

        Returns:
            (is_safe, violation_message)
        """
        if self.start_time is None:
            self.start_time = time.time()
            return True, None

        elapsed = time.time() - self.start_time
        if elapsed > self.max_execution_time:
            violation = f"Execution timeout exceeded: {elapsed:.2f}s > {self.max_execution_time}s"
            self.violations.append(violation)
            self.is_safe = False
            return False, violation

        return True, None

    def check_circular_sequence(self, block_id: str) -> tuple[bool, Optional[str]]:
        """
        Check for circular/repeated block sequences.

        Args:
            block_id: Current block ID

        Returns:
            (is_safe, violation_message)
        """
        # Add current block to sequence
        self.execution_sequence.append(block_id)

        # Keep only last N*2 blocks for pattern detection
        if len(self.execution_sequence) > self.max_repeated_sequence * 2:
            self.execution_sequence = self.execution_sequence[-self.max_repeated_sequence * 2:]

        # Check for repeated sequence
        if len(self.execution_sequence) >= self.max_repeated_sequence * 2:
            # Check if last N blocks repeat
            last_n = self.execution_sequence[-self.max_repeated_sequence:]
            prev_n = self.execution_sequence[-self.max_repeated_sequence * 2:-self.max_repeated_sequence]

            if last_n == prev_n:
                violation = f"Circular sequence detected: {last_n} repeated"
                self.violations.append(violation)
                self.is_safe = False
                return False, violation

        return True, None

    def check_block_index_stall(self, block_index: int, block_order_length: int, iterations_without_progress: int) -> tuple[bool, Optional[str]]:
        """
        Check if block_index is stalled (not incrementing).

        Args:
            block_index: Current block index
            block_order_length: Total block order length
            iterations_without_progress: Number of iterations without index increment

        Returns:
            (is_safe, violation_message)
        """
        # If block_index hasn't changed in many iterations, it's likely stalled
        if iterations_without_progress > block_order_length:
            violation = f"Block index stalled: {block_index} unchanged for {iterations_without_progress} iterations"
            self.violations.append(violation)
            self.is_safe = False
            return False, violation

        return True, None

    def record_iteration(self, block_id: str):
        """Record an iteration."""
        self.iteration_count += 1

    def should_abort(self, block_id: str, block_index: int, block_order_length: int, iterations_without_progress: int = 0) -> tuple[bool, Optional[str]]:
        """
        Comprehensive check: Should execution abort?

        Args:
            block_id: Current block ID
            block_index: Current block index
            block_order_length: Total block order length
            iterations_without_progress: Iterations without index increment

        Returns:
            (should_abort, reason)
        """
        # Check all conditions
        checks = [
            self.check_iteration_limit(),
            self.check_block_execution_limit(block_id),
            self.check_timeout(),
            self.check_circular_sequence(block_id),
            self.check_block_index_stall(block_index, block_order_length, iterations_without_progress)
        ]

        for is_safe, violation in checks:
            if not is_safe:
                logger.error(f"EXECUTION_GUARD: {violation}")
                return True, violation

        return False, None

    def get_statistics(self) -> Dict[str, any]:
        """Get execution statistics."""
        return {
            "iteration_count": self.iteration_count,
            "block_execution_count": dict(self.block_execution_count),
            "execution_sequence": self.execution_sequence[-10:],  # Last 10 blocks
            "execution_time": time.time() - self.start_time if self.start_time else 0.0,
            "violations": self.violations,
            "is_safe": self.is_safe,
            "most_executed_block": max(self.block_execution_count.items(), key=lambda x: x[1]) if self.block_execution_count else None
        }

