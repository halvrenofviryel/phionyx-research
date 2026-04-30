"""
Time Manager - Single Source of Truth for Time Semantics
=========================================================

Centralized time management for EchoState2.

Ensures:
- dt is computed from state, not from external sources
- All time updates go through state.update_time()
- Physics formulas use state.dt
- Events are timestamped with state.t_now
"""

from __future__ import annotations

from datetime import datetime

from phionyx_core.state.echo_state_2 import EchoState2


class TimeManager:
    """
    Time Manager - Single source of truth for time semantics.

    Responsibilities:
    - Update state time fields (t_now, dt, t_local, t_global, turn_index)
    - Provide dt for physics formulas
    - Ensure event timestamps use state.t_now
    - Prevent external dt injection
    """

    def __init__(self, echo_state2: EchoState2):
        """
        Initialize Time Manager.

        Args:
            echo_state2: EchoState2 instance to manage
        """
        self.state = echo_state2

    def advance_turn(
        self,
        current_time: datetime | None = None
    ) -> float:
        """
        Advance turn and update all time fields.

        This is the SINGLE SOURCE OF TRUTH for time updates.
        All dt values MUST come from this method.

        Args:
            current_time: Current timestamp (default: now)

        Returns:
            dt: Time delta in seconds (SINGLE SOURCE OF TRUTH)
        """
        dt = self.state.update_time(current_time, increment_turn=True)
        return dt

    def get_dt(self) -> float:
        """
        Get current dt (time delta).

        This is the SINGLE SOURCE OF TRUTH for time_delta.
        Physics formulas MUST use this value.

        Returns:
            dt: Time delta in seconds
        """
        return self.state.dt

    def get_t_now(self) -> datetime:
        """
        Get current timestamp.

        Events MUST use this timestamp for consistency.

        Returns:
            t_now: Current timestamp
        """
        return self.state.t_now

    def get_turn_index(self) -> int:
        """
        Get current turn index.

        Returns:
            turn_index: Current turn index
        """
        return self.state.turn_index

    def get_t_local(self) -> float:
        """
        Get t_local (time since last update).

        Returns:
            t_local: Time since last update (seconds)
        """
        return self.state.t_local

    def get_t_global(self) -> float:
        """
        Get t_global (time since relationship start).

        Returns:
            t_global: Time since relationship start (seconds)
        """
        return self.state.t_global

    def timestamp_event(self) -> datetime:
        """
        Get timestamp for event.

        Events MUST use this timestamp (state.t_now) for consistency.

        Returns:
            timestamp: Event timestamp (from state.t_now)
        """
        return self.state.t_now

    def validate_dt(self, external_dt: float | None = None) -> float:
        """
        Validate and return dt.

        If external_dt is provided, log warning but use state.dt.
        This ensures dt always comes from state (SINGLE SOURCE OF TRUTH).

        Args:
            external_dt: External dt value (will be ignored)

        Returns:
            dt: Time delta from state (SINGLE SOURCE OF TRUTH)
        """
        if external_dt is not None:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"External dt ({external_dt}) provided but ignored. "
                f"Using state.dt ({self.state.dt}) as SINGLE SOURCE OF TRUTH."
            )

        return self.state.dt

