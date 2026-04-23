"""
Trace Weight Standard - Echoism Core v1.0
==========================================

Standardized trace weight calculation API.

Per Echoism Core v1.0:
- Trace: Event's influence on state over time
- Standard API: trace_weight(event, state, dt, confidence)
- Used in: Memory retrieval, UKF control input, Echo generation
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import math

# Import EchoEvent and EchoState2 if available
try:
    from phionyx_core.state.echo_event import EchoEvent
    from phionyx_core.state.echo_state_2 import EchoState2
    ECHO_STATE_AVAILABLE = True
except ImportError:
    ECHO_STATE_AVAILABLE = False
    EchoEvent = None
    EchoState2 = None


def trace_weight(
    event: EchoEvent,
    state: Optional[EchoState2] = None,
    dt: Optional[float] = None,
    confidence: Optional[float] = None,
    half_life_seconds: float = 300.0,
    base_decay_rate: Optional[float] = None
) -> float:
    """
    Standard trace weight calculation API.

    Per Echoism Core v1.0:
    - Trace: Event's influence on state over time
    - Weight: Decay-weighted event influence
    - Factors: Time decay, state entropy, measurement confidence

    Formula:
    weight = intensity * exp(-λ * t) * (1 - H) * confidence
    where:
    - λ = decay_rate (from half_life or base_decay_rate)
    - t = time_elapsed (from event.timestamp to state.t_now or now)
    - H = state.entropy (if state available)
    - confidence = measurement confidence (if available)

    Args:
        event: EchoEvent instance
        state: EchoState2 instance (optional, for entropy and time)
        dt: Time delta since last update (optional, for time-aware decay)
        confidence: Measurement confidence (0.0-1.0, optional)
        half_life_seconds: Half-life in seconds (default: 5 minutes)
        base_decay_rate: Base decay rate (optional, overrides half_life)

    Returns:
        Trace weight (0.0-1.0)
    """
    if not ECHO_STATE_AVAILABLE or not EchoEvent:
        raise ImportError("EchoEvent and EchoState2 required for trace_weight")

    # Get current time from state or use event timestamp
    if state and hasattr(state, 't_now'):
        now = state.t_now
    else:
        now = datetime.now()

    # Calculate time elapsed
    time_elapsed = (now - event.timestamp).total_seconds()

    # If event is in the future, return 0
    if time_elapsed < 0:
        return 0.0

    # Calculate decay rate
    if base_decay_rate is not None:
        decay_rate = base_decay_rate
    elif half_life_seconds > 0:
        decay_rate = math.log(2.0) / half_life_seconds
    else:
        decay_rate = 0.0  # No decay

    # Base weight: intensity * exp(-λ * t)
    base_weight = event.intensity * math.exp(-decay_rate * time_elapsed)

    # Apply state entropy modulation (high entropy -> lower trace weight)
    entropy_factor = 1.0
    if state and hasattr(state, 'H'):
        # High entropy means uncertainty, so trace weight should be reduced
        entropy_factor = 1.0 - (state.H * 0.3)  # Max 30% reduction
        entropy_factor = max(0.7, min(1.0, entropy_factor))  # Clamp to [0.7, 1.0]

    # Apply confidence modulation (low confidence -> lower trace weight)
    confidence_factor = 1.0
    if confidence is not None:
        confidence_factor = max(0.5, min(1.0, confidence))  # Clamp to [0.5, 1.0]

    # Apply dt modulation (if dt is very small, weight might be stale)
    dt_factor = 1.0
    if dt is not None and dt > 0:
        # If dt is very large, recent events should have higher weight
        # If dt is very small, weight might be from stale state
        if dt > 10.0:  # Large time gap
            dt_factor = 1.0  # No penalty
        elif dt < 0.1:  # Very small time gap
            dt_factor = 0.9  # Slight penalty for potential staleness
        else:
            dt_factor = 1.0  # Normal

    # Final weight
    weight = base_weight * entropy_factor * confidence_factor * dt_factor

    return max(0.0, min(1.0, weight))


def calculate_trace_strength_from_tags(
    state: EchoState2,
    tags: Optional[list[str]] = None,
    half_life_seconds: float = 300.0,
    confidence: Optional[float] = None
) -> float:
    """
    Calculate trace strength from E_tags in state.

    Per Echoism Core v1.0:
    - E_tags: Event references in state
    - Trace strength: Aggregated weight of matching events
    - Used in: UKF control input, memory retrieval

    Args:
        state: EchoState2 instance
        tags: Optional list of tags to filter (if None, use all tags)
        half_life_seconds: Half-life for decay calculation
        confidence: Measurement confidence (optional)

    Returns:
        Trace strength (0.0-1.0)
    """
    if not ECHO_STATE_AVAILABLE or not EchoState2:
        raise ImportError("EchoState2 required for calculate_trace_strength_from_tags")

    if not state or not hasattr(state, 'E_tags') or not state.E_tags:
        return 0.0

    # Get current time
    now = state.t_now if hasattr(state, 't_now') else datetime.now()

    # Calculate weights for matching events
    total_weight = 0.0
    matching_count = 0

    for event_ref in state.E_tags:
        # Filter by tags if provided
        if tags and event_ref.tag not in tags:
            continue

        # Reconstruct event from reference (simplified)
        # In production, would fetch full event from event_history
        # For now, use reference data
        time_elapsed = (now - event_ref.timestamp).total_seconds() if hasattr(event_ref, 'timestamp') else 0.0

        # Calculate decay
        if half_life_seconds > 0:
            decay_rate = math.log(2.0) / half_life_seconds
            weight = event_ref.intensity * math.exp(-decay_rate * time_elapsed)
        else:
            weight = event_ref.intensity

        # Apply entropy and confidence modulation
        entropy_factor = 1.0 - (state.H * 0.3) if hasattr(state, 'H') else 1.0
        entropy_factor = max(0.7, min(1.0, entropy_factor))

        confidence_factor = max(0.5, min(1.0, confidence)) if confidence is not None else 1.0

        weight = weight * entropy_factor * confidence_factor

        total_weight += weight
        matching_count += 1

    # Normalize by number of matching events (avoid double-counting)
    if matching_count > 0:
        average_weight = total_weight / matching_count
    else:
        average_weight = 0.0

    return max(0.0, min(1.0, average_weight))


def get_trace_tags_for_retrieval(
    state: EchoState2,
    max_tags: int = 5,
    min_weight: float = 0.1
) -> list[str]:
    """
    Get active trace tags for memory retrieval.

    Per Echoism Core v1.0:
    - E_tags: Event references in state
    - Active tags: Tags with significant weight
    - Used in: Memory retrieval filtering

    Args:
        state: EchoState2 instance
        max_tags: Maximum number of tags to return
        min_weight: Minimum weight threshold

    Returns:
        List of active tag strings
    """
    if not ECHO_STATE_AVAILABLE or not EchoState2:
        raise ImportError("EchoState2 required for get_trace_tags_for_retrieval")

    if not state or not hasattr(state, 'E_tags') or not state.E_tags:
        return []

    # Get current time
    now = state.t_now if hasattr(state, 't_now') else datetime.now()

    # Calculate weights for each tag
    tag_weights: Dict[str, float] = {}

    for event_ref in state.E_tags:
        tag = event_ref.tag

        # Calculate weight
        time_elapsed = (now - event_ref.timestamp).total_seconds() if hasattr(event_ref, 'timestamp') else 0.0

        # Decay
        half_life_seconds = 300.0  # Default
        if half_life_seconds > 0:
            decay_rate = math.log(2.0) / half_life_seconds
            weight = event_ref.intensity * math.exp(-decay_rate * time_elapsed)
        else:
            weight = event_ref.intensity

        # Apply entropy modulation
        entropy_factor = 1.0 - (state.H * 0.3) if hasattr(state, 'H') else 1.0
        entropy_factor = max(0.7, min(1.0, entropy_factor))

        weight = weight * entropy_factor

        # Aggregate by tag
        if tag not in tag_weights:
            tag_weights[tag] = 0.0
        tag_weights[tag] += weight

    # Filter by min_weight and sort by weight
    active_tags = [
        tag for tag, weight in tag_weights.items()
        if weight >= min_weight
    ]
    active_tags.sort(key=lambda tag: tag_weights[tag], reverse=True)

    # Return top N tags
    return active_tags[:max_tags]


@dataclass
class RetrievalReductionMetric:
    """Compute resource reduction measurement (Patent SF3-25).

    Measures how much the trace-weight-based filtering reduces
    the number of tags that need to be processed for retrieval.
    """
    tags_before: int
    tags_after: int
    reduction_ratio: float  # 1 - (after/before), 0.0-1.0
    weight_threshold: float
    max_tags: int
    timestamp_utc: str


def get_trace_tags_with_metric(
    state: EchoState2,
    max_tags: int = 5,
    min_weight: float = 0.1,
) -> Tuple[list, RetrievalReductionMetric]:
    """Get trace tags for retrieval with compute resource reduction metric.

    Patent SF3-25: Wraps get_trace_tags_for_retrieval() and measures
    the reduction ratio — how many tags were filtered out by the
    semantic prioritization, quantifying compute resource savings.

    Args:
        state: EchoState2 instance
        max_tags: Maximum number of tags to return
        min_weight: Minimum weight threshold

    Returns:
        Tuple of (filtered_tags, reduction_metric)
    """
    # Count total unique tags before filtering
    tags_before = 0
    if state and hasattr(state, 'E_tags') and state.E_tags:
        seen_tags = set()
        for event_ref in state.E_tags:
            seen_tags.add(event_ref.tag)
        tags_before = len(seen_tags)

    # Run existing filtering
    filtered_tags = get_trace_tags_for_retrieval(state, max_tags, min_weight)
    tags_after = len(filtered_tags)

    # Calculate reduction ratio
    if tags_before > 0:
        reduction_ratio = 1.0 - (tags_after / tags_before)
    else:
        reduction_ratio = 0.0

    metric = RetrievalReductionMetric(
        tags_before=tags_before,
        tags_after=tags_after,
        reduction_ratio=reduction_ratio,
        weight_threshold=min_weight,
        max_tags=max_tags,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )

    return filtered_tags, metric

