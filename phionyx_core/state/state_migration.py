"""
State Migration - UnifiedEchoState ↔ EchoState2 Adapter
========================================================

Per Echoism Core v1.0:
- UnifiedEchoState is LEGACY (DEPRECATED)
- EchoState2 is CANONICAL
- Migration adapter provides backward compatibility

Migration utilities for converting between:
- UnifiedEchoState (old/legacy) -> EchoState2 + AuxState (new/canonical)
- EchoState2 + AuxState -> UnifiedEchoState (backward compatibility)
"""

from __future__ import annotations

from datetime import datetime

from phionyx_core.state.aux_state import AuxState

# Import new state models
from phionyx_core.state.echo_state_2 import EchoState2

# Import old state model (optional, for backward compatibility)
OLD_STATE_AVAILABLE = False
UnifiedEchoState = None

try:
    from app.core.echo.unified_state import UnifiedEchoState  # type: ignore
    OLD_STATE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    pass


def unified_to_echo_state2(
    old_state: UnifiedEchoState,
    relationship_start: datetime | None = None
) -> tuple[EchoState2, AuxState]:
    """
    Convert UnifiedEchoState (LEGACY) to EchoState2 + AuxState (CANONICAL).

    Per Echoism Core v1.0:
    - UnifiedEchoState is LEGACY
    - EchoState2 is CANONICAL
    - This function migrates legacy state to canonical state

    Args:
        old_state: Legacy UnifiedEchoState instance
        relationship_start: Relationship start timestamp (default: now)

    Returns:
        Tuple of (EchoState2, AuxState) - canonical state
    """
    if not OLD_STATE_AVAILABLE:
        raise ImportError("UnifiedEchoState not available")

    if relationship_start is None:
        relationship_start = datetime.now()

    # Extract primary state (A, V, H)
    A = old_state.arousal
    V = old_state.valence
    H = max(0.01, old_state.entropy)  # Invariant: H >= 0.01

    # Extract derivatives (if available in metadata)
    dA = old_state.dA if hasattr(old_state, 'dA') else 0.0
    dV = old_state.dV if hasattr(old_state, 'dV') else 0.0

    # Extract time fields (if available)
    t_local = old_state.t_local if hasattr(old_state, 't_local') else 0.0
    t_global = old_state.t_global if hasattr(old_state, 't_global') else 0.0
    dt = old_state.dt if hasattr(old_state, 'dt') else 0.0

    # Extract event tags from E_tags or memory_tags
    E_tags = []
    if hasattr(old_state, 'E_tags') and old_state.E_tags:
        E_tags = old_state.E_tags
    elif hasattr(old_state, 'memory_tags') and old_state.memory_tags:
        # Convert memory tags to event references
        from phionyx_core.state.echo_event import EventReference
        for tag_str in old_state.memory_tags:
            E_tags.append(EventReference(
                event_id=f"legacy_{len(E_tags)}",
                event_type="memory",
                intensity=0.5,
                tags=[tag_str]
            ))

    # Create EchoState2 (CANONICAL)
    echo_state2 = EchoState2(
        A=A,
        V=V,
        H=H,
        dA=dA,
        dV=dV,
        t_local=t_local,
        t_global=t_global,
        E_tags=E_tags,
        dt=dt,
        relationship_start=relationship_start
    )

    # Extract auxiliary state (trust, regulation, risk)
    aux_state = AuxState(
        trust_score=old_state.trust_score if hasattr(old_state, 'trust_score') else 0.5,
        trust_trend=old_state.trust_trend if hasattr(old_state, 'trust_trend') else 0.0,
        regulation_score=getattr(old_state, 'regulation_score', 0.5),
        regulation_trend=0.0,
        risk_score=old_state.risk_score if hasattr(old_state, 'risk_score') else 0.0,
        high_risk_flag=old_state.high_risk_flag if hasattr(old_state, 'high_risk_flag') else False,
    )

    return echo_state2, aux_state


def echo_state2_to_unified(
    echo_state2: EchoState2,
    aux_state: AuxState | None = None
) -> UnifiedEchoState:
    """
    Convert EchoState2 + AuxState (CANONICAL) to UnifiedEchoState (LEGACY).

    Per Echoism Core v1.0:
    - EchoState2 is CANONICAL
    - UnifiedEchoState is LEGACY (for backward compatibility only)
    - This function provides backward compatibility

    Args:
        echo_state2: Canonical EchoState2 instance
        aux_state: Optional AuxState instance

    Returns:
        UnifiedEchoState instance (legacy, for backward compatibility)
    """
    if not OLD_STATE_AVAILABLE:
        raise ImportError("UnifiedEchoState not available")

    # Use default aux_state if not provided
    if aux_state is None:
        aux_state = AuxState()

    # Compute phi from EchoState2 (derived metric)
    phi = echo_state2.phi

    # Create UnifiedEchoState with backward compatibility
    unified_state = UnifiedEchoState(
        entropy=echo_state2.H,
        resonance_force=echo_state2.resonance,
        valence=echo_state2.V,
        arousal=echo_state2.A,
        trust_score=aux_state.trust_score,
        trust_trend=aux_state.trust_trend,
        risk_score=aux_state.risk_score,
        high_risk_flag=aux_state.high_risk_flag,
        memory_tags=[tag.tag for tag in echo_state2.E_tags] if echo_state2.E_tags else [],
        memory_strength=0.5,
        metadata={
            **aux_state.metadata,
            "dA": echo_state2.dA,
            "dV": echo_state2.dV,
            "t_local": echo_state2.t_local,
            "t_global": echo_state2.t_global,
            "dt": echo_state2.dt,
            "last_update": echo_state2.t_now.isoformat(),
            "relationship_start": echo_state2.relationship_start.isoformat(),
            "regulation_score": aux_state.regulation_score,
            "regulation_trend": aux_state.regulation_trend,
            "derived_metrics": {
                "phi": phi,
                "stability": echo_state2.stability,
                "resonance": echo_state2.resonance
            }
        }
    )

    # Update quadrant
    unified_state.update_quadrant()

    return unified_state
