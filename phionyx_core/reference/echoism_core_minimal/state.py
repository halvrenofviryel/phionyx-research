"""
EchoState2Plus - Minimal Reference Implementation
=================================================

Per Echoism Core v1.1:
- State: [A, V, H, dA, dV, t_local, t_global, E_tags, I, R, C, D?]
- Phi is derived, not in state
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class EventReference:
    """Event reference in E_tags."""
    id: str
    tag: str
    intensity: float


@dataclass
class EchoState2Plus:
    """
    EchoState2Plus - Minimal reference implementation.

    Per Echoism Core v1.1:
    - Primary: [A, V, H, dA, dV, t_local, t_global, E_tags]
    - Extended: [I, R, C, D?]
    """
    # Primary state
    A: float = 0.5  # Arousal
    V: float = 0.0  # Valence
    H: float = 0.5  # Entropy
    dA: float = 0.0
    dV: float = 0.0
    t_local: float = 0.0
    t_global: float = 0.0
    E_tags: List[EventReference] = field(default_factory=list)

    # v1.1 Extended
    I: float = 0.6  # Inertia  # noqa: E741
    R: float = 0.05  # ResonanceScore
    C: float = 0.5  # Coherence
    D: Optional[float] = None  # Dominance (optional)

    # Time semantics
    t_now: datetime = field(default_factory=datetime.now)
    turn_index: int = 0
    dt: float = 0.0

    @property
    def phi(self) -> float:
        """Derived metric: Phi from A, V, H."""
        stability = 1.0 - self.H
        valence_norm = (self.V + 1.0) / 2.0
        return min(1.0, stability * (valence_norm * 0.6 + self.A * 0.4))

    def update_time(self, current_time: Optional[datetime] = None) -> float:
        """Update time fields."""
        if current_time is None:
            current_time = datetime.now()

        if hasattr(self, '_last_update') and self._last_update:
            delta = current_time - self._last_update
            self.dt = max(0.0, delta.total_seconds())
        else:
            self.dt = 0.0

        self.t_now = current_time
        self.t_local = self.dt
        self.turn_index += 1
        self._last_update = current_time

        return self.dt

