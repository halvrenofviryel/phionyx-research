"""
Tests for RollbackManager monotonic time guard (SF3-18 patent claim).

Verifies that time values (t_now, turn_index, monotonic_last_update)
never decrease during rollback — preserving one-way impact decay.
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from phionyx_core.orchestrator.rollback_manager import RollbackManager


@dataclass
class MockBlockContext:
    """Minimal BlockContext mock for rollback tests."""
    user_input: str = "test"
    card_type: str = "test"
    card_title: str = "test"
    scene_context: str = "test"
    card_result: str = "result"
    scenario_id: Optional[str] = None
    scenario_step_id: Optional[str] = None
    session_id: Optional[str] = "session_1"
    current_amplitude: float = 5.0
    current_entropy: float = 0.5
    current_integrity: float = 100.0
    previous_phi: Optional[float] = None
    mode: Optional[str] = None
    strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestMonotonicTimeGuard:
    """SF3-18: Monotonic time guard during rollback."""

    def test_rollback_preserves_t_now(self):
        """t_now must not decrease after rollback."""
        rm = RollbackManager()

        # Checkpoint at t_now=10.0
        ctx = MockBlockContext(metadata={"t_now": 10.0, "turn_index": 1})
        rm.create_checkpoint("block_a", ctx)

        # Time advances to t_now=20.0
        ctx.metadata["t_now"] = 20.0
        ctx.metadata["turn_index"] = 2
        rm.create_checkpoint("block_b", ctx)

        # Rollback to block_a's checkpoint
        rm.rollback_to_checkpoint("block_b", ctx)

        # t_now must be clamped to floor (20.0), not restored to 10.0
        assert ctx.metadata["t_now"] >= 20.0

    def test_rollback_preserves_turn_index(self):
        """turn_index must not decrease after rollback."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"turn_index": 5})
        rm.create_checkpoint("block_a", ctx)

        ctx.metadata["turn_index"] = 10
        rm.create_checkpoint("block_b", ctx)

        rm.rollback_to_checkpoint("block_b", ctx)
        assert ctx.metadata["turn_index"] >= 10

    def test_rollback_preserves_monotonic_last_update(self):
        """monotonic_last_update must not decrease after rollback."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"monotonic_last_update": 100.0})
        rm.create_checkpoint("block_a", ctx)

        ctx.metadata["monotonic_last_update"] = 200.0
        rm.create_checkpoint("block_b", ctx)

        rm.rollback_to_checkpoint("block_b", ctx)
        assert ctx.metadata["monotonic_last_update"] >= 200.0

    def test_non_time_metadata_is_restored(self):
        """Non-time metadata restored to earlier checkpoint; time clamped to floor."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"t_now": 5.0, "phi": 0.7, "custom": "old"})
        rm.create_checkpoint("block_a", ctx)

        ctx.metadata["t_now"] = 10.0
        ctx.metadata["phi"] = 0.9
        ctx.metadata["custom"] = "new"
        rm.create_checkpoint("block_b", ctx)

        # Rollback from unknown block_c → pops block_b, restores from block_a
        rm.rollback_to_checkpoint("block_c", ctx)

        # t_now clamped to floor (10.0 from block_b checkpoint)
        assert ctx.metadata["t_now"] >= 10.0
        # Non-time values restored to block_a snapshot
        assert ctx.metadata["phi"] == 0.7
        assert ctx.metadata["custom"] == "old"

    def test_time_floor_survives_clear_checkpoints(self):
        """Time floor is preserved even after clearing checkpoints."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"t_now": 50.0})
        rm.create_checkpoint("block_a", ctx)

        rm.clear_checkpoints()

        # Floor should still be 50.0
        assert rm._time_floor.get("t_now") == 50.0

    def test_multiple_rollbacks_never_decrease_time(self):
        """Repeated rollbacks must never decrease time values."""
        rm = RollbackManager()

        # Build up checkpoints with increasing time
        for i in range(5):
            ctx = MockBlockContext(metadata={"t_now": float(i * 10), "turn_index": i})
            rm.create_checkpoint(f"block_{i}", ctx)

        # Rollback from block_4 → should restore block_3's state
        ctx = MockBlockContext(metadata={"t_now": 40.0, "turn_index": 4})
        rm.rollback_to_checkpoint("block_4", ctx)

        # Time floor was set at 40.0 by block_4 checkpoint
        assert ctx.metadata["t_now"] >= 40.0
        assert ctx.metadata["turn_index"] >= 4

    def test_no_time_in_metadata_no_crash(self):
        """Rollback works fine when metadata has no time keys."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"custom_key": "value"})
        rm.create_checkpoint("block_a", ctx)

        ctx.metadata["custom_key"] = "changed"
        rm.create_checkpoint("block_b", ctx)

        # Rollback from unknown block_c → restores from block_a
        result = rm.rollback_to_checkpoint("block_c", ctx)
        assert result is True
        assert ctx.metadata["custom_key"] == "value"

    def test_guard_clamps_older_snapshot_time(self):
        """Core SF3-18 test: rolling back to older snapshot clamps time to floor."""
        rm = RollbackManager()

        # Block A checkpoint: t_now=10
        ctx = MockBlockContext(metadata={"t_now": 10.0, "turn_index": 1, "data": "a_data"})
        rm.create_checkpoint("block_a", ctx)

        # Block B checkpoint: t_now=20 (floor advances to 20)
        ctx.metadata["t_now"] = 20.0
        ctx.metadata["turn_index"] = 2
        ctx.metadata["data"] = "b_data"
        rm.create_checkpoint("block_b", ctx)

        # Block C fails (no checkpoint) → rollback finds block_a after popping block_b
        ctx.metadata["t_now"] = 30.0  # time advanced further but not checkpointed
        rm.rollback_to_checkpoint("block_c", ctx)

        # Non-time data restored to block_a's values
        assert ctx.metadata["data"] == "a_data"
        # Time clamped to floor (20.0 from block_b), not block_a's 10.0
        assert ctx.metadata["t_now"] == 20.0
        assert ctx.metadata["turn_index"] == 2

    def test_int_type_preserved_for_turn_index(self):
        """turn_index should remain int after time floor enforcement."""
        rm = RollbackManager()

        ctx = MockBlockContext(metadata={"turn_index": 5})
        rm.create_checkpoint("block_a", ctx)

        ctx.metadata["turn_index"] = 10
        rm.create_checkpoint("block_b", ctx)

        rm.rollback_to_checkpoint("block_b", ctx)
        assert isinstance(ctx.metadata["turn_index"], int)
        assert ctx.metadata["turn_index"] >= 10

    def test_disabled_manager_no_guard(self):
        """Disabled manager skips rollback entirely."""
        rm = RollbackManager(enabled=False)

        ctx = MockBlockContext(metadata={"t_now": 10.0})
        rm.create_checkpoint("block_a", ctx)

        result = rm.rollback_to_checkpoint("block_b", ctx)
        assert result is False
