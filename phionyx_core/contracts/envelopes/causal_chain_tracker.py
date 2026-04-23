"""
Causal Chain Tracker — Per-Participant Turn ID Monotonicity
===========================================================

Patent SF2-17: Per-participant causal consistency chain validation.
Each participant's turn_id must be strictly monotonically increasing.
Violations are detected and reported for audit trail.
"""

from typing import Optional
from collections import OrderedDict
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CausalConsistencyViolation(BaseModel):
    """Violation report when a participant's turn_id breaks monotonicity."""
    participant_id: str = Field(..., description="Participant that violated causal order")
    expected_min_turn_id: int = Field(..., description="Minimum expected turn_id (last + 1)")
    received_turn_id: int = Field(..., description="Actual turn_id received")
    timestamp_utc: str = Field(..., description="ISO8601 UTC timestamp of violation")


class CausalChainTracker:
    """Per-participant turn_id monotonicity tracker (Patent SF2-17).

    Tracks the last seen turn_id for each participant and validates
    that new messages have strictly increasing turn_ids. Uses an
    OrderedDict with LRU eviction when max_participants is exceeded.
    """

    def __init__(self, max_participants: int = 1000):
        self._chains: OrderedDict[str, int] = OrderedDict()
        self._max_participants = max_participants

    def validate_and_record(
        self, participant_id: str, turn_id: int
    ) -> Optional[CausalConsistencyViolation]:
        """Check turn_id is strictly > last seen for participant, record if valid.

        Args:
            participant_id: The participant sending the message.
            turn_id: The turn_id from the message envelope.

        Returns:
            None if valid, CausalConsistencyViolation if monotonicity broken.
        """
        last_turn_id = self._chains.get(participant_id)

        if last_turn_id is not None and turn_id <= last_turn_id:
            return CausalConsistencyViolation(
                participant_id=participant_id,
                expected_min_turn_id=last_turn_id + 1,
                received_turn_id=turn_id,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )

        # Valid — record and move to end (LRU)
        if participant_id in self._chains:
            self._chains.move_to_end(participant_id)
        self._chains[participant_id] = turn_id

        # Evict oldest if over capacity
        while len(self._chains) > self._max_participants:
            self._chains.popitem(last=False)

        return None

    def get_last_turn_id(self, participant_id: str) -> Optional[int]:
        """Get last recorded turn_id for participant."""
        return self._chains.get(participant_id)

    def reset_participant(self, participant_id: str) -> None:
        """Reset chain for participant (e.g., session restart)."""
        self._chains.pop(participant_id, None)

    def reset_all(self) -> None:
        """Reset all chains."""
        self._chains.clear()

    @property
    def participant_count(self) -> int:
        """Number of tracked participants."""
        return len(self._chains)
