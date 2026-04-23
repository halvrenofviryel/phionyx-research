"""
Echo Ontology - Effect → Trace → Echo → Transformation
========================================================

Echoism Core v1.0 ontology implementation.

Chain:
1. Effect → Event: External/internal input becomes structured event
2. Event → Trace: Event influence on state (with decay)
3. Trace → Echo: Response generated from trace
4. Echo → Transformation: State change from echo

This module orchestrates the full chain.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime

from phionyx_core.state.echo_event import EchoEvent
from phionyx_core.state.echo_state_2 import EchoState2

# Import trace functions if available
try:
    from phionyx_core.memory.trace import trace_weight, aggregate_trace
    TRACE_AVAILABLE = True
except ImportError:
    TRACE_AVAILABLE = False
    trace_weight = None
    aggregate_trace = None


class EchoOntology:
    """
    Echo Ontology orchestrator.

    Implements: Effect → Trace → Echo → Transformation
    """

    def __init__(
        self,
        echo_state2: EchoState2,
        half_life_seconds: float = 300.0
    ):
        """
        Initialize Echo Ontology.

        Args:
            echo_state2: EchoState2 instance
            half_life_seconds: Trace decay half-life in seconds
        """
        self.state = echo_state2
        self.half_life_seconds = half_life_seconds
        self.event_history: List[EchoEvent] = []

    def effect_to_event(
        self,
        effect_type: str,
        intensity: float,
        tags: List[str],
        payload: Optional[Dict[str, Any]] = None
    ) -> EchoEvent:
        """
        Convert effect to event (Step 1: Effect → Event).

        Args:
            effect_type: Type of effect
            intensity: Effect intensity (0.0-1.0)
            tags: Semantic tags
            payload: Additional data

        Returns:
            EchoEvent instance
        """
        event = EchoEvent(
            type=effect_type,
            timestamp=self.state.t_now,  # Use state.t_now
            intensity=intensity,
            tags=tags,
            payload=payload or {}
        )

        # Add to history
        self.event_history.append(event)

        # Add reference to state.E_tags
        primary_tag = tags[0] if tags else effect_type
        self.state.add_event_tag(
            event_type=effect_type,
            intensity=intensity,
            semantic_context=primary_tag,
            timestamp=self.state.t_now
        )

        return event

    def event_to_trace(
        self,
        event: EchoEvent,
        now: Optional[datetime] = None,
        dt: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate trace weight from event (Step 2: Event → Trace).

        Per Echoism Core v1.0:
        - Uses standard trace_weight API: trace_weight(event, state, dt, confidence)
        - Factors: Time decay, state entropy, measurement confidence

        Args:
            event: EchoEvent instance
            now: Current timestamp (default: state.t_now)
            dt: Time delta since last update (optional)
            confidence: Measurement confidence (optional)

        Returns:
            Trace weight (0.0-1.0)
        """
        if not TRACE_AVAILABLE:
            # Fallback: simple weight
            return event.intensity

        # Use standard trace_weight API
        try:
            from phionyx_core.memory.trace_weight_standard import trace_weight

            # Get dt from state if not provided
            if dt is None and hasattr(self.state, 'dt'):
                dt = self.state.dt

            # Use standard API
            weight = trace_weight(
                event=event,
                state=self.state,
                dt=dt,
                confidence=confidence,
                half_life_seconds=self.half_life_seconds
            )

            return weight
        except ImportError:
            # Fallback to simple trace_weight if standard API not available
            if now is None:
                now = self.state.t_now

            return trace_weight(event, now, self.half_life_seconds)

    def trace_to_echo(
        self,
        events: List[EchoEvent],
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate echo from trace (Step 3: Trace → Echo).

        Args:
            events: List of EchoEvent instances
            now: Current timestamp (default: state.t_now)

        Returns:
            Echo response dictionary with:
            - amplitude: Response amplitude
            - resonance: Echo resonance
            - trace_vector: Tag-based trace vector
        """
        if not TRACE_AVAILABLE:
            # Fallback: simple aggregation
            total_intensity = sum(e.intensity for e in events) / len(events) if events else 0.0
            return {
                "amplitude": total_intensity * 10.0,
                "resonance": total_intensity,
                "trace_vector": {}
            }

        if now is None:
            now = self.state.t_now

        # Aggregate trace
        trace_result = aggregate_trace(events, now, self.half_life_seconds)

        # Generate echo response
        amplitude = trace_result["weighted_intensity"] * 10.0
        resonance = trace_result["weighted_intensity"]

        return {
            "amplitude": amplitude,
            "resonance": resonance,
            "trace_vector": trace_result["trace_vector"],
            "total_weight": trace_result["total_weight"],
            "active_events": trace_result["active_events"]
        }

    def echo_to_transformation(
        self,
        echo: Dict[str, Any],
        state_update: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Apply transformation to state (Step 4: Echo → Transformation).

        Args:
            echo: Echo response dictionary
            state_update: Optional explicit state update (A, V, H)

        Returns:
            State transformation dictionary
        """
        # Use echo to influence state
        if state_update:
            # Explicit update
            self.state.update_state(
                A_new=state_update.get("A"),
                V_new=state_update.get("V"),
                H_new=state_update.get("H")
            )
        else:
            # Implicit update from echo
            # Echo amplitude influences arousal
            amplitude_factor = echo["amplitude"] / 10.0
            new_A = max(0.0, min(1.0, self.state.A * 0.7 + amplitude_factor * 0.3))

            # Echo resonance influences valence
            resonance_factor = echo["resonance"]
            new_V = max(-1.0, min(1.0, self.state.V * 0.8 + resonance_factor * 0.2))

            # Update state
            self.state.update_state(A_new=new_A, V_new=new_V)

        return {
            "A": self.state.A,
            "V": self.state.V,
            "H": self.state.H,
            "phi": self.state.phi
        }

    def process_effect(
        self,
        effect_type: str,
        intensity: float,
        tags: List[str],
        payload: Optional[Dict[str, Any]] = None,
        state_update: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process full chain: Effect → Event → Trace → Echo → Transformation.

        Args:
            effect_type: Type of effect
            intensity: Effect intensity
            tags: Semantic tags
            payload: Additional data
            state_update: Optional explicit state update

        Returns:
            Complete processing result
        """
        # Step 1: Effect → Event
        event = self.effect_to_event(effect_type, intensity, tags, payload)

        # Step 2: Event → Trace
        trace_weight = self.event_to_trace(event)

        # Step 3: Trace → Echo
        # Get recent events for aggregation
        recent_events = self.event_history[-10:] if len(self.event_history) > 10 else self.event_history
        echo = self.trace_to_echo(recent_events)

        # Step 4: Echo → Transformation
        transformation = self.echo_to_transformation(echo, state_update)

        return {
            "event": event.to_dict(),
            "trace_weight": trace_weight,
            "echo": echo,
            "transformation": transformation,
            "state": {
                "A": self.state.A,
                "V": self.state.V,
                "H": self.state.H,
                "phi": self.state.phi
            }
        }

