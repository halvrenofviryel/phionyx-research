"""
Time Update Single Source of Truth Block
=========================================

Block: time_update_sot
Updates time semantics using TimeManager (single source of truth per Echoism Core v1.0).
"""

import logging
from typing import Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class TimeManagerProtocol(Protocol):
    """Protocol for TimeManager to avoid direct dependency."""
    def advance_turn(self) -> float:
        """Advance turn and return time_delta in seconds."""
        ...

    def get_turn_index(self) -> int:
        """Get current turn index."""
        ...

    def get_t_now(self) -> float:
        """Get current time."""
        ...


class TimeUpdateSotBlock(PipelineBlock):
    """
    Time Update Block - Single Source of Truth.

    Per Echoism Core v1.0, time semantics (dt, t_local, t_global) must be
    single source of truth from TimeManager.
    """

    def __init__(
        self,
        time_manager: TimeManagerProtocol,
        participant_id: str = "default"
    ):
        """
        Initialize time update block.

        Args:
            time_manager: TimeManager instance for time semantics
            participant_id: Participant ID for participant-scoped time management
        """
        super().__init__("time_update_sot")
        self.time_manager = time_manager
        self.participant_id = participant_id

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Skip if time_manager not available."""
        if self.time_manager is None:
            return "time_manager_not_available"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute time update.

        Args:
            context: Block context

        Returns:
            BlockResult with time_delta, turn_index, t_now
        """
        try:
            # Advance turn and get dt from state (SINGLE SOURCE OF TRUTH)
            time_delta_raw = self.time_manager.advance_turn()
            # Defensive: ensure numeric return (guards against misconfigured DI)
            if not isinstance(time_delta_raw, (int, float)):
                time_delta_raw = 1.0
            original_dt = time_delta_raw

            # Initialize dt_events list for metadata storage
            dt_events_to_store = []

            # Check if this is first tick (no previous timestamp or dt too small)
            is_first_tick = getattr(self.time_manager.state, '_is_first_tick', False)
            if is_first_tick:
                # First tick: TimeManager returned floor (0.1) - this is expected on initialization
                time_delta = 0.1  # Already set by TimeManager
                dt_events_to_store.append({
                    'event': 'dt_invalid',
                    'original_dt': original_dt if original_dt < 0.1 else 0.0,
                    'clamped_dt': time_delta,
                    'reason': 'first_tick_no_previous_timestamp',
                    'severity': 'info'  # This is expected on first turn
                })
                self.time_manager.state._is_first_tick = False
                logger.debug(f"[DT_UPDATE] First tick: using floor {time_delta:.2f} seconds")
            elif time_delta_raw < 0.0:
                # Negative time_delta is invalid (should NEVER happen with monotonic clock)
                logger.error(
                    f"[DT_INVALID] time_delta_raw={time_delta_raw:.2f} is negative (monotonic clock issue). "
                    f"Using floor value 0.1 seconds. This should be RARE."
                )
                time_delta = 0.1
                dt_events_to_store.append({
                    'event': 'dt_invalid',
                    'original_dt': original_dt,
                    'clamped_dt': time_delta,
                    'reason': 'negative_time_delta_monotonic_clock_error',
                    'severity': 'error'
                })
            elif time_delta_raw > 3600.0:
                # Clamp to 3600 seconds (1 hour) instead of resetting to 1.0
                time_delta = min(time_delta_raw, 3600.0)
                logger.warning(
                    f"[DT_CLAMPED] time_delta_raw={time_delta_raw:.2f} is > 1 hour, "
                    f"clamping to {time_delta:.2f} seconds"
                )
                dt_events_to_store.append({
                    'event': 'dt_clamped',
                    'original_dt': original_dt,
                    'clamped_dt': time_delta,
                    'reason': 'exceeds_1_hour'
                })
            else:
                time_delta = time_delta_raw

            # Reject time_delta outside the sensible range (0.1 s .. 3600 s).
            # Explicit ValueError so `python -O` cannot strip the check —
            # `assert` is optimised away under -O which would break this gate
            # silently in production.
            if not (0.1 <= time_delta <= 3600.0):
                raise ValueError(
                    f"time_delta={time_delta:.2f} is outside reasonable range [0.1, 3600] seconds."
                )

            turn_index = self.time_manager.get_turn_index()
            if not isinstance(turn_index, int):
                turn_index = 0
            t_now = self.time_manager.get_t_now()
            if not isinstance(t_now, (int, float)):
                t_now = 0.0

            # Propagate time values to context metadata for downstream blocks
            if context.metadata is None:
                context.metadata = {}
            context.metadata["time_delta"] = time_delta
            context.metadata["turn_index"] = turn_index
            context.metadata["t_now"] = t_now

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "time_delta": time_delta,
                    "turn_index": turn_index,
                    "t_now": t_now,
                    "dt_events": dt_events_to_store,
                    "original_dt": original_dt
                }
            )
        except Exception as e:
            logger.error(f"Time update failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e
            )

