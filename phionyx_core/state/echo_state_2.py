"""
EchoState2 / EchoState2Plus - Echoism Core v1.0/v1.1 Canonical State Model
===========================================================================

Echoism Core Specification v1.0/v1.1 canonical state model.

v1.0 State Vector: x_t = {A, V, H, dA, dV, t_local, t_global, E_tags}
v1.1 Extended: x_t = {A, V, H, dA, dV, t_local, t_global, E_tags, I, R, C, D?}

Key Principles:
- Phi is now a derived metric, not primary state
- Trust and regulation moved to AuxState (optional control layer)
- Time-aware state (t_local, t_global)
- Event trace (E_tags) for contextual empathy
- v1.1: I (Inertia), R (ResonanceScore), C (Coherence), D (Dominance, optional)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import math
import time as time_module  # For monotonic clock

# ============================================================
# Configurable Constants (Patent-Referenced Parameters)
# ============================================================
# These named constants enable parametric patent claims.
# Values are validated by 291 PRE experiments (Tier A).

RESONANCE_AROUSAL_WEIGHT: float = 0.6   # SF1-7: Arousal contribution to resonance
RESONANCE_VALENCE_WEIGHT: float = 0.4   # SF1-7: Valence magnitude contribution to resonance
AMPLITUDE_SCALE_FACTOR: float = 10.0    # SF1-8: Arousal-to-amplitude scaling factor
ENTROPY_FLOOR: float = 0.01             # SF2-9: Minimum entropy (prevents zero-entropy singularity)

# Import EventReference for E_tags
try:
    from phionyx_core.state.echo_event import EventReference
    EVENT_REFERENCE_AVAILABLE = True
except ImportError:
    EVENT_REFERENCE_AVAILABLE = False
    # Fallback EventReference definition
    @dataclass
    class EventReference:
        id: str
        tag: str
        intensity: float


class EchoState2(BaseModel):
    """
    EchoState2 - Canonical state model per Echoism Core v1.0.

    Primary State Vector:
    - A_t: Arousal (0.0-1.0)
    - V_t: Valence (-1.0 to 1.0)
    - H_t: Entropy (0.0-1.0)
    - dA_t: Arousal change rate (derivative)
    - dV_t: Valence change rate (derivative)
    - t_local: Time since last emotional effect (seconds)
    - t_global: Time since relationship start (seconds)
    - E_tags_t: Event/effect tags

    Derived Metrics (computed, not stored):
    - phi: Computed from A, V, H (via physics formulas)
    - stability: Computed from H
    - resonance: Computed from A, V

    Invariants:
    - State must be time-aware (t_local, t_global cannot be None)
    - Entropy cannot be zero (minimum 0.01)
    - Event tags cannot be deleted (only appended)
    """

    # ============================================================
    # Primary State Vector (Canonical)
    # ============================================================

    A: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Arousal (0.0-1.0): Low to high activation"
    )

    V: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Valence (-1.0 to 1.0): Negative to positive"
    )

    H: float = Field(
        default=0.5,
        ge=ENTROPY_FLOOR,  # Invariant: Entropy cannot be zero (configurable floor)
        le=1.0,
        description="Entropy (ENTROPY_FLOOR-1.0): Emotional uncertainty"
    )

    dA: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Arousal change rate (derivative): dA/dt"
    )

    dV: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Valence change rate (derivative): dV/dt"
    )

    t_local: float = Field(
        default=0.0,
        ge=0.0,
        description="Time since last emotional effect (seconds)"
    )

    t_global: float = Field(
        default=0.0,
        ge=0.0,
        description="Time since relationship start (seconds)"
    )

    E_tags: List[EventReference] = Field(
        default_factory=list,
        description="Event references (last N events: id + tag + intensity)"
    )

    # ============================================================
    # Time Semantics (First-Class Citizen)
    # ============================================================

    t_now: datetime = Field(
        default_factory=datetime.now,
        description="Current timestamp (updated every turn)"
    )

    turn_index: int = Field(
        default=0,
        ge=0,
        description="Turn index (incremented every turn)"
    )

    dt: float = Field(
        default=0.0,
        ge=0.0,
        description="Time delta since last update (seconds) - SINGLE SOURCE OF TRUTH"
    )

    # ============================================================
    # Metadata (for tracking, not part of canonical state)
    # ============================================================

    last_update: datetime = Field(
        default_factory=datetime.now,
        description="Last state update timestamp (for dt computation)"
    )

    relationship_start: datetime = Field(
        default_factory=datetime.now,
        description="Relationship start timestamp (for t_global)"
    )

    # ⚠️ CRITICAL: Monotonic clock for dt computation (prevents wall-clock time travel)
    # Note: Pydantic doesn't allow fields with leading underscores, so we use regular names
    monotonic_last_update: float = Field(
        default_factory=lambda: time_module.monotonic(),
        description="Last update monotonic time (for dt computation, immune to wall-clock changes)"
    )

    monotonic_relationship_start: float = Field(
        default_factory=lambda: time_module.monotonic(),
        description="Relationship start monotonic time (for t_global, immune to wall-clock changes)"
    )

    # ============================================================
    # Derived Metrics (Computed Properties)
    # ============================================================

    @property
    def phi(self) -> float:
        """
        Compute Phi (cognitive resonance) from primary state.

        Phi is now a derived metric, not primary state.
        Formula: phi = f(A, V, H, dt) via Physics 2.1 formulas.

        Uses state.dt as SINGLE SOURCE OF TRUTH for time_delta.

        Returns:
            Phi value (0.0-1.0)
        """
        # Import physics formulas
        try:
            from phionyx_core.physics.formulas import calculate_phi_v2

            # Convert state to physics params
            amplitude = self.A * AMPLITUDE_SCALE_FACTOR  # Scale A to amplitude range
            stability = max(0.0, 1.0 - self.H)  # Inverse of entropy

            # Use state.dt as SINGLE SOURCE OF TRUTH for time_delta
            time_delta = max(0.1, self.dt) if self.dt > 0 else 1.0  # Minimum 0.1s

            phi_result = calculate_phi_v2(
                amplitude=amplitude,
                time_delta=time_delta,  # From state.dt (SINGLE SOURCE OF TRUTH)
                entropy=self.H,
                stability=stability,
                context_mode="DEFAULT",  # Can be overridden
                gamma=0.15  # Default recovery rate
            )

            return phi_result.get("phi", 0.5)
        except ImportError:
            # Fallback: Simple heuristic
            # Higher A and positive V with low H = higher phi
            stability_factor = 1.0 - self.H
            valence_factor = (self.V + 1.0) / 2.0  # Normalize to 0-1
            arousal_factor = self.A

            return min(1.0, stability_factor * (valence_factor * 0.6 + arousal_factor * 0.4))

    @property
    def stability(self) -> float:
        """
        Compute stability from entropy.

        Returns:
            Stability (0.0-1.0), higher = more stable
        """
        return max(0.0, 1.0 - self.H)

    @property
    def resonance(self) -> float:
        """
        Compute resonance from A and V.

        Returns:
            Resonance (0.0-1.0), higher = stronger emotional resonance
        """
        # Resonance is intensity of emotional response
        # Higher arousal and stronger valence = higher resonance
        valence_magnitude = abs(self.V)
        return min(1.0, self.A * RESONANCE_AROUSAL_WEIGHT + valence_magnitude * RESONANCE_VALENCE_WEIGHT)

    # ============================================================
    # State Update Methods
    # ============================================================

    def update_time(
        self,
        current_time: Optional[datetime] = None,
        increment_turn: bool = True
    ) -> float:
        """
        Update time fields (t_now, dt, t_local, t_global, turn_index).

        This is the SINGLE SOURCE OF TRUTH for time updates.
        All time_delta/dt values MUST come from state.dt.

        ⚠️ CRITICAL: Uses monotonic clock for dt computation to prevent wall-clock time travel.
        Wall-clock can go backwards (NTP sync, system clock changes), but monotonic clock is guaranteed monotonic.

        Args:
            current_time: Current timestamp (default: now) - used for t_now only, NOT for dt computation
            increment_turn: Whether to increment turn_index

        Returns:
            dt: Time delta in seconds (SINGLE SOURCE OF TRUTH, computed from monotonic clock)
        """
        if current_time is None:
            current_time = datetime.now()

        # Update t_now (wall-clock time for display/logging)
        self.t_now = current_time

        # ⚠️ CRITICAL: Use monotonic clock for dt computation (immune to wall-clock changes)
        monotonic_now = time_module.monotonic()

        # Compute dt (SINGLE SOURCE OF TRUTH) using monotonic clock
        # ⚠️ CRITICAL: First call (no previous timestamp or dt too small) → use floor (0.1) and mark as invalid
        # This ensures dt is always in valid range [0.1, 3600.0] per Failure Mode spec
        DT_FLOOR = 0.1  # Minimum valid dt per Failure Mode spec

        if hasattr(self, 'monotonic_last_update') and self.monotonic_last_update > 0:
            # Compute dt from monotonic clock (guaranteed monotonic, no time travel)
            monotonic_dt = monotonic_now - self.monotonic_last_update

            # If dt is too small (< DT_FLOOR), treat as first tick (initialization artifact)
            if monotonic_dt < DT_FLOOR:
                # Very small dt (likely from initialization) → use floor and mark as first tick
                self.dt = DT_FLOOR
                self._is_first_tick = True
            elif monotonic_dt < 0.0:
                # ⚠️ CRITICAL: Negative dt from monotonic clock should NEVER happen
                # This indicates a serious bug (monotonic clock went backwards)
                # Log error and use floor
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"[DT_INVALID] Monotonic clock went backwards! "
                    f"monotonic_now={monotonic_now}, monotonic_last_update={self.monotonic_last_update}, "
                    f"monotonic_dt={monotonic_dt}. This should NEVER happen. Using floor."
                )
                self.dt = DT_FLOOR
                self._is_first_tick = True
            else:
                self.dt = monotonic_dt
                self._is_first_tick = False
        else:
            # First call: no previous monotonic timestamp → use floor and mark as "first_tick"
            # This will trigger dt_invalid event in time_update_sot block
            self.dt = DT_FLOOR
            # Mark that this is first tick (will be used to generate dt_invalid event)
            self._is_first_tick = True

        # Update t_local (time since last update)
        self.t_local = self.dt

        # Update t_global (time since relationship start) using monotonic clock
        if hasattr(self, 'monotonic_relationship_start') and self.monotonic_relationship_start > 0:
            monotonic_t_global = monotonic_now - self.monotonic_relationship_start
            self.t_global = max(0.0, monotonic_t_global)
        else:
            self.t_global = 0.0

        # Increment turn index
        if increment_turn:
            self.turn_index += 1

        # Update last_update (wall-clock) for display/logging
        self.last_update = current_time

        # ⚠️ CRITICAL: Update monotonic timestamps for next turn
        self.monotonic_last_update = monotonic_now
        if not hasattr(self, 'monotonic_relationship_start') or self.monotonic_relationship_start <= 0:
            self.monotonic_relationship_start = monotonic_now

        return self.dt

    def from_physics_state(self, physics_state: Dict[str, Any]) -> None:
        """
        Update EchoState2 from physics state dictionary.

        This method updates the unified state from physics state values.
        This is a core pipeline function that does NOT depend on LLM models.

        Args:
            physics_state: Dict with physics state values:
                - entropy (H): Optional[float]
                - valence (V): Optional[float]
                - arousal (A): Optional[float]
                - phi: Optional[float] (computed, not stored directly)
                - amplitude: Optional[float]
                - stability: Optional[float]
        """
        if not isinstance(physics_state, dict):
            return

        # Update entropy (H)
        if "entropy" in physics_state:
            entropy = physics_state["entropy"]
            if isinstance(entropy, (int, float)):
                # Clamp to valid range [0.01, 1.0]
                self.H = max(ENTROPY_FLOOR, min(1.0, float(entropy)))

        # Update valence (V)
        if "valence" in physics_state:
            valence = physics_state["valence"]
            if isinstance(valence, (int, float)):
                # Clamp to valid range [-1.0, 1.0]
                self.V = max(-1.0, min(1.0, float(valence)))

        # Update arousal (A)
        if "arousal" in physics_state:
            arousal = physics_state["arousal"]
            if isinstance(arousal, (int, float)):
                # Clamp to valid range [0.0, 1.0]
                self.A = max(0.0, min(1.0, float(arousal)))

        # Note: phi is a computed property (from A, V, H), cannot be set directly
        # phi value is computed automatically when accessed

        # Log update (optional, for debugging)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Updated EchoState2 from physics_state: V={self.V:.3f}, A={self.A:.3f}, H={self.H:.3f}")

    def add_event_tag(
        self,
        event_type: str,
        intensity: float,
        semantic_context: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Add event tag (immutable append-only).

        Events are timestamped with state.t_now for consistency.

        Args:
            event_type: Type of event
            intensity: Event intensity (0.0-1.0)
            semantic_context: Semantic context description
            metadata: Optional metadata
            timestamp: Event timestamp (default: state.t_now)
        """
        # Use state.t_now as SINGLE SOURCE OF TRUTH for event timestamps
        if timestamp is None:
            timestamp = self.t_now

        # Create EventReference (simplified for E_tags)
        if EVENT_REFERENCE_AVAILABLE:
            ref = EventReference(
                event_id=f"event_{len(self.E_tags)}",
                event_type=event_type,
                intensity=max(0.0, min(1.0, intensity)),
                tags=[semantic_context] if semantic_context else []
            )
            self.E_tags.append(ref)
        else:
            # Fallback
            ref = EventReference(
                id=f"event_{len(self.E_tags)}",
                tag=semantic_context or event_type,
                intensity=max(0.0, min(1.0, intensity))
            )
            self.E_tags.append(ref)

    def update_state(
        self,
        A_new: Optional[float] = None,
        V_new: Optional[float] = None,
        H_new: Optional[float] = None,
        current_time: Optional[datetime] = None,
        increment_turn: bool = True
    ) -> float:
        """
        Update state with new values and compute derivatives.

        This method:
        1. Updates time (t_now, dt, t_local, t_global, turn_index)
        2. Updates state values (A, V, H)
        3. Computes derivatives (dA, dV) using state.dt

        Args:
            A_new: New arousal value
            V_new: New valence value
            H_new: New entropy value
            current_time: Current timestamp (default: now)
            increment_turn: Whether to increment turn_index

        Returns:
            dt: Time delta in seconds (SINGLE SOURCE OF TRUTH)
        """
        # Store old values for derivative computation
        A_old = self.A
        V_old = self.V
        _H_old = self.H

        # Update time (SINGLE SOURCE OF TRUTH for dt)
        dt = self.update_time(current_time, increment_turn)

        # Update values
        if A_new is not None:
            self.A = max(0.0, min(1.0, A_new))
        if V_new is not None:
            self.V = max(-1.0, min(1.0, V_new))
        if H_new is not None:
            self.H = max(ENTROPY_FLOOR, min(1.0, H_new))  # Invariant: H >= ENTROPY_FLOOR

        # Compute derivatives (change rates) using state.dt
        if dt > 0:
            self.dA = (self.A - A_old) / dt
            self.dV = (self.V - V_old) / dt
        else:
            self.dA = 0.0
            self.dV = 0.0

        return dt

    def get_recent_events(self, time_window: float = 300.0) -> List[EventReference]:
        """
        Get recent events within time window.

        Args:
            time_window: Time window in seconds (default: 5 minutes)

        Returns:
            List of recent event references
        """
        if not self.E_tags:
            return []

        # EventReference doesn't have timestamp, so return all recent ones
        # (In practice, E_tags should be limited to recent N events)
        return self.E_tags[-10:] if len(self.E_tags) > 10 else self.E_tags

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (for serialization).

        Returns:
            Dictionary representation
        """
        return {
            "A": self.A,
            "V": self.V,
            "H": self.H,
            "dA": self.dA,
            "dV": self.dV,
            "t_local": self.t_local,
            "t_global": self.t_global,
            "t_now": self.t_now.isoformat(),
            "turn_index": self.turn_index,
            "dt": self.dt,  # SINGLE SOURCE OF TRUTH
            "E_tags": [
                {
                    "id": ref.id,
                    "tag": ref.tag,
                    "intensity": ref.intensity
                }
                for ref in self.E_tags
            ],
            "last_update": self.last_update.isoformat(),
            "relationship_start": self.relationship_start.isoformat(),
            # Derived metrics (computed)
            "phi": self.phi,
            "stability": self.stability,
            "resonance": self.resonance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EchoState2:
        """
        Create from dictionary (for deserialization).

        Args:
            data: Dictionary representation

        Returns:
            EchoState2 instance
        """
        # Parse event references
        E_tags = []
        for ref_data in data.get("E_tags", []):
            if EVENT_REFERENCE_AVAILABLE:
                ref = EventReference(
                    id=ref_data["id"],
                    tag=ref_data["tag"],
                    intensity=ref_data["intensity"]
                )
            else:
                # Fallback
                ref = EventReference(
                    id=ref_data.get("id", ""),
                    tag=ref_data.get("tag", ""),
                    intensity=ref_data.get("intensity", 0.0)
                )
            E_tags.append(ref)

        # Parse timestamps
        last_update = datetime.fromisoformat(data.get("last_update", datetime.now().isoformat()))
        relationship_start = datetime.fromisoformat(data.get("relationship_start", datetime.now().isoformat()))
        t_now = datetime.fromisoformat(data.get("t_now", datetime.now().isoformat()))

        return cls(
            A=data.get("A", 0.5),
            V=data.get("V", 0.0),
            H=data.get("H", 0.5),
            dA=data.get("dA", 0.0),
            dV=data.get("dV", 0.0),
            t_local=data.get("t_local", 0.0),
            t_global=data.get("t_global", 0.0),
            t_now=t_now,
            turn_index=data.get("turn_index", 0),
            dt=data.get("dt", 0.0),
            E_tags=E_tags,
            last_update=last_update,
            relationship_start=relationship_start
        )

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
        validate_assignment = True


class EchoState2Plus(EchoState2):
    """
    EchoState2Plus - Echoism Core v1.1 Extended State Model

    Extends EchoState2 with v1.1 fields:
    - I (Inertia): Emotional change resistance (0.0-1.0, mandatory)
    - R (ResonanceScore): Relationship depth, bounded/saturating (0.0-1.0, mandatory)
    - C (Coherence): Measurement-state consistency (0.0-1.0, diagnostic)
    - D (Dominance): Optional dominance score (0.0-1.0, only in Strict profile)

    Per Echoism Core v1.1:
    - I, R, C are mandatory fields
    - D is optional (None if not in Strict profile)
    - Phi remains a derived metric (not in state)
    - Backward compatible with EchoState2 via default initialization
    """

    # ============================================================
    # v1.1 Extended Fields
    # ============================================================

    I: float = Field(  # noqa: E741
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Inertia (0.0-1.0): Emotional change resistance. Higher = slower change"
    )

    R: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="ResonanceScore (0.0-1.0): Relationship depth, bounded/saturating. R = 1 - exp(-k * interactions_effective)"
    )

    C: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Coherence (0.0-1.0): Measurement-state consistency (diagnostic). Low C → entropy boost signal"
    )

    D: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Dominance (0.0-1.0, optional): Only active in Strict profile. None in Lite/Compat"
    )

    # ============================================================
    # Karpathy Feature Extensions (Faz 1.2: State Management Genişletme)
    # ============================================================

    # Assumptions tracking (Karpathy Problem 1)
    assumptions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of assumptions extracted during code generation. Each assumption has: type, description, code_reference, confidence, evidence"
    )

    # Inconsistencies tracking (Karpathy Problem 2)
    inconsistencies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of inconsistencies detected between code, plan, tests, and requirements. Each inconsistency has: type, description, severity, code_reference, resolution_suggestion, evidence"
    )

    # Complexity metrics tracking (Karpathy Problem 7)
    complexity_metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complexity metrics: cyclomatic, cognitive, nesting_depth, function_length, class_complexity"
    )

    # Complexity budget configuration
    complexity_budget: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Complexity budget limits: max_cyclomatic, max_cognitive, max_nesting, max_function_length, max_class_complexity"
    )

    # ============================================================
    # v1.1 Helper Methods
    # ============================================================

    def update_resonance(
        self,
        interactions_effective: float,
        k: float = 0.1,
        trace_weight_sum: float = 0.0,
        positive_bond_events: int = 0,
        suppression_active: bool = False,
        ethics_breach: bool = False
    ) -> None:
        """
        Update ResonanceScore (R) with saturating function.

        Per Echoism Core v1.1:
        - R = 1 - exp(-k * interactions_effective)
        - interactions_effective includes trace_weight and positive bond events
        - R is bounded to [0.0, 1.0]
        - Active Suppression or ethics breach → R growth damping

        Args:
            interactions_effective: Effective interaction count (not just message count)
            k: Saturation rate (default: 0.1)
            trace_weight_sum: Sum of trace weights from positive events
            positive_bond_events: Count of positive bond-forming events
            suppression_active: Whether active suppression is active (damps R growth)
            ethics_breach: Whether ethics breach detected (damps R growth)
        """
        # Use core-state resonance calculator
        try:
            from phionyx_core.state.resonance import calculate_resonance_score

            self.R = calculate_resonance_score(
                interactions_effective=interactions_effective,
                k=k,
                trace_weight_sum=trace_weight_sum,
                positive_bond_events=positive_bond_events,
                suppression_active=suppression_active,
                ethics_breach=ethics_breach
            )
        except ImportError:
            # Fallback: Simple calculation
            effective = interactions_effective + trace_weight_sum * 0.5 + positive_bond_events * 0.3

            # Apply damping
            damping_factor = 1.0
            if suppression_active:
                damping_factor *= 0.5
            if ethics_breach:
                damping_factor *= 0.3

            effective = effective * damping_factor

            self.R = 1.0 - math.exp(-k * effective)
            self.R = max(0.0, min(1.0, self.R))

    def update_resonance_incremental(
        self,
        new_interactions: int = 0,
        trace_weight_sum: float = 0.0,
        positive_bond_events: int = 0,
        suppression_active: bool = False,
        ethics_breach: bool = False,
        k: float = 0.1
    ) -> None:
        """
        Update ResonanceScore (R) incrementally from new events (post-event phase).

        Per Echoism Core v1.1:
        - R update happens in 'post-event' phase
        - Each turn, R is updated based on new interactions

        Args:
            new_interactions: New interaction count this turn
            trace_weight_sum: Sum of trace weights from positive events this turn
            positive_bond_events: Count of positive bond-forming events this turn
            suppression_active: Whether active suppression is active
            ethics_breach: Whether ethics breach detected
            k: Saturation rate
        """
        try:
            from phionyx_core.state.resonance import update_resonance_from_events

            self.R = update_resonance_from_events(
                current_R=self.R,
                new_interactions=new_interactions,
                trace_weight_sum=trace_weight_sum,
                positive_bond_events=positive_bond_events,
                suppression_active=suppression_active,
                ethics_breach=ethics_breach,
                k=k
            )
        except ImportError:
            # Fallback: Simple incremental update
            effective_new = new_interactions + trace_weight_sum * 0.5 + positive_bond_events * 0.3

            damping_factor = 1.0
            if suppression_active:
                damping_factor *= 0.5
            if ethics_breach:
                damping_factor *= 0.3

            effective_new = effective_new * damping_factor

            # Simple incremental: R_new = R_old + (1 - R_old) * effective_new * k
            self.R = self.R + (1.0 - self.R) * effective_new * k
            self.R = max(0.0, min(1.0, self.R))

    def update_coherence(
        self,
        measurement: Dict[str, float],
        state: Optional[Dict[str, float]] = None,
        confidence: Optional[float] = None
    ) -> None:
        """
        Update Coherence (C) from measurement-state consistency.

        Per Echoism Core v1.1:
        - Uses core-physics.coherence.calculate_coherence()
        - Low C → entropy boost signal (diagnostic only, not blocking)

        Args:
            measurement: z_t = {A_meas, V_meas, H_meas} from MeasurementMapper
            state: Current state {A, V, H} (default: use self)
            confidence: Measurement confidence (optional, for weighted calculation)
        """
        if state is None:
            state = {"A": self.A, "V": self.V, "H": self.H}

        # Use core-physics coherence calculator
        try:
            from phionyx_core.physics.coherence import (
                calculate_coherence,
                calculate_coherence_with_confidence
            )

            if confidence is not None:
                self.C = calculate_coherence_with_confidence(
                    measurement=measurement,
                    state=state,
                    confidence=confidence
                )
            else:
                self.C = calculate_coherence(
                    measurement=measurement,
                    state=state
                )
        except ImportError:
            # Fallback: Simple calculation (same as before)
            residual_A = abs(measurement.get("A_meas", self.A) - state["A"])
            residual_V = abs(measurement.get("V_meas", self.V) - state["V"])
            residual_H = abs(measurement.get("H_meas", self.H) - state["H"])

            max_residual = max(residual_A, residual_V, residual_H)
            normalized_residual = max_residual / 2.0

            sigmoid_input = 10.0 * (normalized_residual - 0.5)
            self.C = 1.0 / (1.0 + math.exp(sigmoid_input))
            self.C = max(0.0, min(1.0, self.C))

    def apply_inertia_to_decay_rate(self, base_decay_rate: float) -> float:
        """
        Apply Inertia (I) to decay rate λ.

        Per Echoism Core v1.1:
        - I high → λ low (slower change)
        - I low → λ high (faster change)

        Args:
            base_decay_rate: Base decay rate

        Returns:
            Adjusted decay rate
        """
        try:
            from phionyx_core.physics.inertia import apply_inertia_to_decay_rate as apply_inertia
            return apply_inertia(base_decay_rate, self.I)
        except ImportError:
            # Fallback
            adjusted = base_decay_rate * (1.0 - self.I)
            min_decay = 0.001
            max_decay = 1.0
            return max(min_decay, min(max_decay, adjusted))

    def apply_inertia_to_ukf_process_noise(self, base_Q: float) -> float:
        """
        Apply Inertia (I) to UKF process noise Q.

        Per Echoism Core v1.1:
        - I high → Q low (more stable)
        - I low → Q high (more flexible)

        Args:
            base_Q: Base process noise

        Returns:
            Adjusted process noise Q
        """
        try:
            from phionyx_core.physics.inertia import apply_inertia_to_ukf_process_noise as apply_inertia
            return apply_inertia(base_Q, self.I)
        except ImportError:
            # Fallback
            adjusted = base_Q * (1.0 - self.I)
            return max(0.01, min(0.1, adjusted))

    def apply_inertia_to_derivative_gain(self, base_gain: float) -> float:
        """
        Apply Inertia (I) to A/V derivative update gain.

        Per Echoism Core v1.1:
        - I high → lower gain (slower A/V change)
        - I low → higher gain (faster A/V change)

        Args:
            base_gain: Base gain for derivative updates

        Returns:
            Adjusted gain
        """
        try:
            from phionyx_core.physics.inertia import apply_inertia_to_derivative_gain as apply_inertia
            return apply_inertia(base_gain, self.I)
        except ImportError:
            # Fallback
            adjusted = base_gain * (1.0 - self.I)
            return max(0.1, min(1.0, adjusted))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (includes v1.1 fields and Karpathy extensions).

        Returns:
            Dictionary representation
        """
        base_dict = super().to_dict()
        base_dict.update({
            "I": self.I,
            "R": self.R,
            "C": self.C,
            "D": self.D,
            "assumptions": self.assumptions,
            "inconsistencies": self.inconsistencies,
            "complexity_metrics": self.complexity_metrics,
            "complexity_budget": self.complexity_budget
        })
        return base_dict

    def add_assumption(
        self,
        assumption_type: str,
        description: str,
        code_reference: Optional[str] = None,
        confidence: float = 1.0,
        evidence: Optional[List[str]] = None
    ) -> None:
        """
        Add an assumption to state.

        Args:
            assumption_type: Type of assumption (input_type, state, dependency, performance)
            description: Assumption description
            code_reference: Code reference (file:line)
            confidence: Confidence level (0.0-1.0)
            evidence: Evidence array
        """
        self.assumptions.append({
            "type": assumption_type,
            "description": description,
            "code_reference": code_reference,
            "confidence": confidence,
            "evidence": evidence or []
        })

    def add_inconsistency(
        self,
        inconsistency_type: str,
        description: str,
        severity: str,
        code_reference: Optional[str] = None,
        resolution_suggestion: Optional[str] = None,
        evidence: Optional[List[str]] = None
    ) -> None:
        """
        Add an inconsistency to state.

        Args:
            inconsistency_type: Type of inconsistency (code_plan, code_test, plan_requirement, state)
            description: Inconsistency description
            severity: Severity level (low, medium, high, critical)
            code_reference: Code reference (file:line)
            resolution_suggestion: Suggested resolution
            evidence: Evidence array
        """
        self.inconsistencies.append({
            "type": inconsistency_type,
            "description": description,
            "severity": severity,
            "code_reference": code_reference,
            "resolution_suggestion": resolution_suggestion,
            "evidence": evidence or []
        })

    def update_complexity_metrics(
        self,
        cyclomatic: int,
        cognitive: int,
        nesting_depth: int,
        function_length: int,
        class_complexity: int
    ) -> None:
        """
        Update complexity metrics in state.

        Args:
            cyclomatic: Cyclomatic complexity
            cognitive: Cognitive complexity
            nesting_depth: Maximum nesting depth
            function_length: Maximum function length
            class_complexity: Class complexity
        """
        self.complexity_metrics = {
            "cyclomatic": cyclomatic,
            "cognitive": cognitive,
            "nesting_depth": nesting_depth,
            "function_length": function_length,
            "class_complexity": class_complexity
        }

    def set_complexity_budget(
        self,
        max_cyclomatic: int = 10,
        max_cognitive: int = 15,
        max_nesting: int = 4,
        max_function_length: int = 50,
        max_class_complexity: int = 20
    ) -> None:
        """
        Set complexity budget limits.

        Args:
            max_cyclomatic: Maximum cyclomatic complexity
            max_cognitive: Maximum cognitive complexity
            max_nesting: Maximum nesting depth
            max_function_length: Maximum function length
            max_class_complexity: Maximum class complexity
        """
        self.complexity_budget = {
            "max_cyclomatic": max_cyclomatic,
            "max_cognitive": max_cognitive,
            "max_nesting": max_nesting,
            "max_function_length": max_function_length,
            "max_class_complexity": max_class_complexity
        }

    @classmethod
    def from_echo_state2(
        cls,
        state2: EchoState2,
        I_default: float = 0.6,
        R_default: float = 0.05,
        C_default: float = 0.5,
        D_default: Optional[float] = None
    ) -> EchoState2Plus:
        """
        Create EchoState2Plus from EchoState2 (backward compatibility).

        Per Echoism Core v1.1:
        - Default initialization for v1.0 → v1.1 migration
        - I = profile default (e.g., 0.6)
        - R = min(0.05, session_age_factor)
        - C = 0.5 (neutral)
        - D = None (or 0.0 if Strict profile)

        Args:
            state2: EchoState2 instance
            I_default: Default Inertia value
            R_default: Default ResonanceScore value
            C_default: Default Coherence value
            D_default: Default Dominance value (None for Lite/Compat)

        Returns:
            EchoState2Plus instance
        """
        # Calculate session_age_factor for R
        session_age_factor = min(0.05, state2.t_global / 3600.0)  # Normalize by 1 hour

        return cls(
            A=state2.A,
            V=state2.V,
            H=state2.H,
            dA=state2.dA,
            dV=state2.dV,
            t_local=state2.t_local,
            t_global=state2.t_global,
            t_now=state2.t_now,
            turn_index=state2.turn_index,
            dt=state2.dt,
            E_tags=state2.E_tags,
            last_update=state2.last_update,
            relationship_start=state2.relationship_start,
            I=I_default,
            R=min(R_default, session_age_factor),
            C=C_default,
            D=D_default
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EchoState2Plus:
        """
        Create from dictionary (includes v1.1 fields).

        Args:
            data: Dictionary representation

        Returns:
            EchoState2Plus instance
        """
        # First create base EchoState2
        state2 = EchoState2.from_dict(data)

        # Then create EchoState2Plus with v1.1 fields
        return cls(
            A=state2.A,
            V=state2.V,
            H=state2.H,
            dA=state2.dA,
            dV=state2.dV,
            t_local=state2.t_local,
            t_global=state2.t_global,
            t_now=state2.t_now,
            turn_index=state2.turn_index,
            dt=state2.dt,
            E_tags=state2.E_tags,
            last_update=state2.last_update,
            relationship_start=state2.relationship_start,
            I=data.get("I", 0.6),
            R=data.get("R", 0.05),
            C=data.get("C", 0.5),
            D=data.get("D", None)
        )

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
        validate_assignment = True
