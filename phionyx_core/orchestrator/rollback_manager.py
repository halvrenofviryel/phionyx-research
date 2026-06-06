"""
Block Rollback Manager
======================

Manages state snapshots and rollback for pipeline blocks.
"""

import logging
import copy
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..pipeline.base import BlockContext

logger = logging.getLogger(__name__)

# Monotonic time keys that must never decrease during rollback (SF3-18 patent claim)
_MONOTONIC_TIME_KEYS = ("t_now", "turn_index", "monotonic_last_update")


@dataclass
class StateSnapshot:
    """Snapshot of block context state."""
    block_id: str
    context_snapshot: Dict[str, Any]
    metadata_snapshot: Dict[str, Any]


class RollbackManager:
    """
    Manages state snapshots and rollback for pipeline blocks.

    Provides checkpoint/rollback functionality to restore state
    when a block fails.

    Invariant (SF3-18): Monotonic time values (t_now, turn_index,
    monotonic_last_update) are never rolled back. This preserves
    one-way impact decay during rollback — once time has advanced,
    decay factors based on semantic time must not reverse.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize rollback manager.

        Args:
            enabled: Whether rollback is enabled (default: True)
        """
        self.enabled = enabled
        self.snapshots: List[StateSnapshot] = []
        self.checkpoint_interval: int = 1  # Create snapshot every N blocks
        self._time_floor: Dict[str, float] = {}  # Monotonic time floor values

    def create_checkpoint(self, block_id: str, context: BlockContext) -> None:
        """
        Create a checkpoint (snapshot) of current state.

        Args:
            block_id: Block ID that just executed successfully
            context: Current block context
        """
        if not self.enabled:
            return

        try:
            # Create deep copy of context state
            context_snapshot = {
                'user_input': context.user_input,
                'card_type': context.card_type,
                'card_title': context.card_title,
                'scene_context': context.scene_context,
                'card_result': context.card_result,
                'scenario_id': context.scenario_id,
                'scenario_step_id': context.scenario_step_id,
                'session_id': context.session_id,
                'current_amplitude': context.current_amplitude,
                'current_entropy': context.current_entropy,
                'current_integrity': context.current_integrity,
                'previous_phi': context.previous_phi,
                'mode': context.mode,
                'strategy': context.strategy,
            }

            # Create deep copy of metadata
            metadata_snapshot = copy.deepcopy(context.metadata) if context.metadata else {}

            snapshot = StateSnapshot(
                block_id=block_id,
                context_snapshot=context_snapshot,
                metadata_snapshot=metadata_snapshot
            )

            self.snapshots.append(snapshot)

            # Update monotonic time floor from current metadata
            self._update_time_floor(metadata_snapshot)

            logger.debug(f"Created checkpoint for block: {block_id}")

        except Exception as e:
            logger.warning(f"Failed to create checkpoint for block {block_id}: {e}")

    def rollback_to_checkpoint(self, block_id: str, context: BlockContext) -> bool:
        """
        Rollback context to the last checkpoint before the failed block.

        Args:
            block_id: Block ID that failed
            context: Current block context (will be restored)

        Returns:
            True if rollback was successful, False otherwise
        """
        if not self.enabled:
            return False

        if not self.snapshots:
            logger.warning(f"No checkpoints available for rollback from block {block_id}")
            return False

        try:
            # Find the last checkpoint before the failed block
            # (Remove checkpoints from failed block onwards)
            while self.snapshots and self.snapshots[-1].block_id != block_id:
                # Find checkpoint before failed block
                for i in range(len(self.snapshots) - 1, -1, -1):
                    if self.snapshots[i].block_id == block_id:
                        # Remove this and all later checkpoints
                        self.snapshots = self.snapshots[:i]
                        break
                else:
                    # No checkpoint found for this block, remove last one
                    if self.snapshots:
                        self.snapshots.pop()
                    break

            if not self.snapshots:
                logger.warning(f"No valid checkpoint found for rollback from block {block_id}")
                return False

            # Restore from last checkpoint
            last_snapshot = self.snapshots[-1]

            # Restore context fields
            for key, value in last_snapshot.context_snapshot.items():
                if hasattr(context, key):
                    setattr(context, key, value)

            # Restore metadata
            context.metadata = copy.deepcopy(last_snapshot.metadata_snapshot)

            # Enforce monotonic time guard (SF3-18):
            # Time values must never decrease during rollback.
            self._enforce_time_floor(context.metadata)

            logger.info(f"Rolled back to checkpoint: {last_snapshot.block_id} (failed block: {block_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback from block {block_id}: {e}", exc_info=True)
            return False

    def get_last_checkpoint(self) -> Optional['StateSnapshot']:
        """
        Get the last checkpoint.

        Returns:
            Last StateSnapshot or None if no checkpoints exist
        """
        return self.snapshots[-1] if self.snapshots else None

    def clear_checkpoints(self) -> None:
        """Clear all checkpoints. Time floor is preserved."""
        self.snapshots.clear()
        logger.debug("All checkpoints cleared")

    def _update_time_floor(self, metadata: Dict[str, Any]) -> None:
        """
        Update monotonic time floor from metadata values.

        The floor tracks the highest time value seen so far.
        Once time advances, it cannot be rolled back.
        """
        for key in _MONOTONIC_TIME_KEYS:
            if key in metadata:
                val = metadata[key]
                if isinstance(val, (int, float)):
                    current_floor = self._time_floor.get(key, float("-inf"))
                    if val > current_floor:
                        self._time_floor[key] = val

    def _enforce_time_floor(self, metadata: Dict[str, Any]) -> None:
        """
        Enforce monotonic time floor on metadata after rollback.

        If a restored snapshot has a time value lower than the floor,
        clamp it to the floor. This preserves one-way impact decay.
        """
        for key, floor_val in self._time_floor.items():
            if key in metadata:
                val = metadata[key]
                if isinstance(val, (int, float)) and val < floor_val:
                    logger.info(
                        f"[MONOTONIC_GUARD] Clamped {key} from {val} to {floor_val} "
                        f"(preventing time reversal during rollback)"
                    )
                    metadata[key] = type(val)(floor_val)  # Preserve int/float type

