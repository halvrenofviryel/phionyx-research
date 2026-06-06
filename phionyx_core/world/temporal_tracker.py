"""
Temporal Tracker
================

Tracks entity state changes over time, supporting temporal queries
and confidence decay for stale information.

Roadmap Faz 4.2: World Model Hardening — Temporal Tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# Module-level tunable defaults (Tier A — PRE surfaces)
temporal_decay_rate = 0.02
max_history_per_entity = 100


class TemporalResolution(str, Enum):
    TURN = "turn"
    MINUTE = "minute"
    HOUR = "hour"
    SESSION = "session"


@dataclass
class EntityState:
    """A snapshot of an entity's state at a specific time."""
    entity_id: str
    attribute: str
    value: Any
    timestamp: str  # ISO 8601
    turn_index: int
    confidence: float = 1.0  # Decays over time
    source: str = "observation"


@dataclass
class EntityTimeline:
    """Full timeline of an entity's attribute changes."""
    entity_id: str
    attribute: str
    states: List[EntityState] = field(default_factory=list)

    @property
    def current(self) -> Optional[EntityState]:
        return self.states[-1] if self.states else None

    @property
    def history_length(self) -> int:
        return len(self.states)


@dataclass
class TemporalQuery:
    """Result of a temporal query."""
    entity_id: str
    attribute: str
    value: Any
    timestamp: str
    turn_index: int
    confidence: float
    is_current: bool
    decay_applied: float  # How much confidence was reduced
    reasoning: str


@dataclass
class ConflictResolution:
    """Result of resolving conflicting temporal updates."""
    entity_id: str
    attribute: str
    kept_value: Any
    discarded_value: Any
    resolution_method: str  # "latest_wins", "higher_confidence", "source_priority"
    reasoning: str


class TemporalTracker:
    """
    Tracks entity state changes over time.

    Provides:
    - Entity state timeline (what was X at time T?)
    - Confidence decay for stale information
    - Conflict resolution for contradictory updates
    - Turn-indexed temporal queries
    """

    def __init__(
        self,
        decay_rate: float = temporal_decay_rate,
        max_history_per_entity: int = max_history_per_entity,
        conflict_strategy: str = "latest_wins",
    ):
        self.decay_rate = max(0.0, min(1.0, decay_rate))
        self.max_history = max_history_per_entity
        self.conflict_strategy = conflict_strategy
        self._timelines: Dict[str, Dict[str, EntityTimeline]] = {}
        self._current_turn: int = 0
        self._conflicts: List[ConflictResolution] = []

    def advance_turn(self) -> int:
        """Advance the turn counter. Returns new turn index."""
        self._current_turn += 1
        return self._current_turn

    @property
    def current_turn(self) -> int:
        return self._current_turn

    def update(
        self,
        entity_id: str,
        attribute: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "observation",
        timestamp: Optional[str] = None,
    ) -> Optional[ConflictResolution]:
        """
        Record a state change for an entity attribute.

        Returns ConflictResolution if the update conflicts with existing state.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        confidence = max(0.0, min(1.0, confidence))

        # Get or create timeline
        if entity_id not in self._timelines:
            self._timelines[entity_id] = {}
        if attribute not in self._timelines[entity_id]:
            self._timelines[entity_id][attribute] = EntityTimeline(
                entity_id=entity_id, attribute=attribute
            )

        timeline = self._timelines[entity_id][attribute]
        conflict = None

        # Check for conflict with current state
        if timeline.current and timeline.current.value != value:
            conflict = self._resolve_conflict(
                timeline.current, value, confidence, source, ts
            )
            self._conflicts.append(conflict)

        # Record new state
        state = EntityState(
            entity_id=entity_id,
            attribute=attribute,
            value=value,
            timestamp=ts,
            turn_index=self._current_turn,
            confidence=confidence,
            source=source,
        )
        timeline.states.append(state)

        # Cap history
        if len(timeline.states) > self.max_history:
            timeline.states = timeline.states[-self.max_history:]

        return conflict

    def query(
        self,
        entity_id: str,
        attribute: str,
        at_turn: Optional[int] = None,
    ) -> TemporalQuery:
        """
        Query entity state, optionally at a specific turn.

        Applies confidence decay based on staleness.
        """
        timeline = self._get_timeline(entity_id, attribute)
        if not timeline or not timeline.states:
            return TemporalQuery(
                entity_id=entity_id,
                attribute=attribute,
                value=None,
                timestamp="",
                turn_index=-1,
                confidence=0.0,
                is_current=False,
                decay_applied=0.0,
                reasoning=f"No data for {entity_id}.{attribute}",
            )

        if at_turn is not None:
            # Find state at or before the requested turn
            state = None
            for s in reversed(timeline.states):
                if s.turn_index <= at_turn:
                    state = s
                    break
            if not state:
                return TemporalQuery(
                    entity_id=entity_id,
                    attribute=attribute,
                    value=None,
                    timestamp="",
                    turn_index=-1,
                    confidence=0.0,
                    is_current=False,
                    decay_applied=0.0,
                    reasoning=f"No data for {entity_id}.{attribute} at turn {at_turn}",
                )
        else:
            state = timeline.current

        # Apply decay
        turns_elapsed = self._current_turn - state.turn_index
        decay = self.decay_rate * turns_elapsed
        decayed_confidence = max(0.0, state.confidence - decay)
        is_current = (state == timeline.current)

        return TemporalQuery(
            entity_id=entity_id,
            attribute=attribute,
            value=state.value,
            timestamp=state.timestamp,
            turn_index=state.turn_index,
            confidence=decayed_confidence,
            is_current=is_current,
            decay_applied=decay,
            reasoning=f"Value from turn {state.turn_index}, {turns_elapsed} turns ago, decay={decay:.3f}",
        )

    def get_timeline(self, entity_id: str, attribute: str) -> Optional[EntityTimeline]:
        """Get full timeline for an entity attribute."""
        return self._get_timeline(entity_id, attribute)

    def get_entity_attributes(self, entity_id: str) -> List[str]:
        """List all tracked attributes for an entity."""
        return list(self._timelines.get(entity_id, {}).keys())

    def get_all_entities(self) -> List[str]:
        """List all tracked entity IDs."""
        return list(self._timelines.keys())

    def get_conflicts(self) -> List[ConflictResolution]:
        """Return all recorded conflicts."""
        return list(self._conflicts)

    def entity_count(self) -> int:
        """Number of tracked entities."""
        return len(self._timelines)

    def total_states(self) -> int:
        """Total number of recorded state snapshots."""
        return sum(
            len(tl.states)
            for entity_timelines in self._timelines.values()
            for tl in entity_timelines.values()
        )

    def _get_timeline(self, entity_id: str, attribute: str) -> Optional[EntityTimeline]:
        return self._timelines.get(entity_id, {}).get(attribute)

    def _resolve_conflict(
        self,
        existing: EntityState,
        new_value: Any,
        new_confidence: float,
        new_source: str,
        new_timestamp: str,
    ) -> ConflictResolution:
        """Resolve conflicting temporal updates."""
        if self.conflict_strategy == "higher_confidence":
            if new_confidence >= existing.confidence:
                return ConflictResolution(
                    entity_id=existing.entity_id,
                    attribute=existing.attribute,
                    kept_value=new_value,
                    discarded_value=existing.value,
                    resolution_method="higher_confidence",
                    reasoning=f"New confidence {new_confidence:.2f} >= existing {existing.confidence:.2f}",
                )
            else:
                return ConflictResolution(
                    entity_id=existing.entity_id,
                    attribute=existing.attribute,
                    kept_value=existing.value,
                    discarded_value=new_value,
                    resolution_method="higher_confidence",
                    reasoning=f"Existing confidence {existing.confidence:.2f} > new {new_confidence:.2f}",
                )
        # Default: latest_wins
        return ConflictResolution(
            entity_id=existing.entity_id,
            attribute=existing.attribute,
            kept_value=new_value,
            discarded_value=existing.value,
            resolution_method="latest_wins",
            reasoning=f"Latest update wins: {existing.value} → {new_value}",
        )
