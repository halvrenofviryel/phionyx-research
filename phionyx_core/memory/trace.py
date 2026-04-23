"""
Trace - Echo Ontology: Effect → Trace → Echo → Transformation
=============================================================

Trace implementation for Echoism Core v1.0.

Trace: Weighted event influence on state with decay.

Functions:
- trace_weight(event, now): Calculate current weight of event (with decay)
- aggregate_trace(events): Aggregate multiple events into trace vector
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
import math

# Import EchoEvent if available
try:
    from phionyx_core.state.echo_event import EchoEvent
    ECHO_EVENT_AVAILABLE = True
except ImportError:
    ECHO_EVENT_AVAILABLE = False
    EchoEvent = None


def trace_weight(
    event: EchoEvent,
    now: datetime,
    half_life_seconds: float = 300.0,  # Default: 5 minutes
    suppressed: bool = False,
    suppression_factor: float = 0.1
) -> float:
    """
    Calculate current weight of event with exponential decay.

    Per Echoism Core v1.0:
    - Trace: Event's influence on state over time
    - Decay: Exponential decay based on time elapsed
    - Suppression: Reduces weight for suppressed events (trauma recovery)

    Formula: weight = intensity * exp(-λ * t) * suppression_multiplier
    where λ = ln(2) / half_life
    and suppression_multiplier = suppression_factor if suppressed else 1.0

    Args:
        event: EchoEvent instance
        now: Current timestamp
        half_life_seconds: Half-life in seconds (default: 5 minutes)
        suppressed: Whether event is suppressed (default: False)
        suppression_factor: Multiplier for suppressed events (default: 0.1)

    Returns:
        Current weight of event (0.0-1.0)
    """
    if not ECHO_EVENT_AVAILABLE:
        raise ImportError("EchoEvent not available")

    # Calculate time elapsed
    time_elapsed = (now - event.timestamp).total_seconds()

    # If event is in the future, return 0
    if time_elapsed < 0:
        return 0.0

    # Exponential decay: weight = intensity * exp(-λ * t)
    # where λ = ln(2) / half_life
    if half_life_seconds <= 0:
        base_weight = event.intensity  # No decay
    else:
        decay_rate = math.log(2.0) / half_life_seconds
        base_weight = event.intensity * math.exp(-decay_rate * time_elapsed)

    # Apply suppression if event is suppressed
    if suppressed:
        weight = base_weight * suppression_factor
    else:
        weight = base_weight

    return max(0.0, min(1.0, weight))


def aggregate_trace(
    events: List[EchoEvent],
    now: Optional[datetime] = None,
    half_life_seconds: float = 300.0,
    max_events: int = 10
) -> Dict[str, Any]:
    """
    Aggregate multiple events into trace vector.

    Per Echoism Core v1.0:
    - Trace: Weighted sum of event influences
    - Aggregation: Combine multiple events with decay

    Returns:
        Dictionary with:
        - total_weight: Sum of all event weights
        - weighted_intensity: Weighted average intensity
        - active_events: Number of events with weight > 0.01
        - trace_vector: Tag-based trace vector
        - recent_events: List of recent event IDs
    """
    if not ECHO_EVENT_AVAILABLE:
        raise ImportError("EchoEvent not available")

    if now is None:
        now = datetime.now()

    # Sort events by timestamp (most recent first)
    sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)

    # Limit to most recent N events
    if max_events > 0:
        sorted_events = sorted_events[:max_events]

    # Calculate weights and aggregate
    total_weight = 0.0
    weighted_intensity_sum = 0.0
    active_events = 0
    trace_vector: Dict[str, float] = {}  # tag -> weighted sum
    recent_event_ids: List[str] = []

    for event in sorted_events:
        weight = trace_weight(event, now, half_life_seconds)

        # Only consider events with significant weight
        if weight > 0.01:
            total_weight += weight
            weighted_intensity_sum += event.intensity * weight
            active_events += 1
            recent_event_ids.append(event.id)

            # Aggregate by tags
            for tag in event.tags:
                if tag not in trace_vector:
                    trace_vector[tag] = 0.0
                trace_vector[tag] += weight * event.intensity

    # Calculate weighted average intensity
    weighted_intensity = weighted_intensity_sum / total_weight if total_weight > 0 else 0.0

    return {
        "total_weight": total_weight,
        "weighted_intensity": weighted_intensity,
        "active_events": active_events,
        "trace_vector": trace_vector,
        "recent_event_ids": recent_event_ids,
        "timestamp": now.isoformat()
    }


def calculate_trace_decay_rate(
    half_life_seconds: float
) -> float:
    """
    Calculate decay rate from half-life.

    Formula: λ = ln(2) / half_life

    Args:
        half_life_seconds: Half-life in seconds

    Returns:
        Decay rate (λ)
    """
    if half_life_seconds <= 0:
        return 0.0

    return math.log(2.0) / half_life_seconds


def get_active_trace_events(
    events: List[EchoEvent],
    now: Optional[datetime] = None,
    half_life_seconds: float = 300.0,
    min_weight: float = 0.01
) -> List[EchoEvent]:
    """
    Get events with active trace (weight > min_weight).

    Args:
        events: List of EchoEvent instances
        now: Current timestamp
        half_life_seconds: Half-life in seconds
        min_weight: Minimum weight threshold

    Returns:
        List of active events
    """
    if not ECHO_EVENT_AVAILABLE:
        raise ImportError("EchoEvent not available")

    if now is None:
        now = datetime.now()

    active_events = []
    for event in events:
        weight = trace_weight(event, now, half_life_seconds)
        if weight >= min_weight:
            active_events.append(event)

    return active_events

