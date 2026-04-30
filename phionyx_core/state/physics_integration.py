"""
Physics Integration - State.dt as Single Source of Truth
=======================================================

Integration utilities for using EchoState2.dt in physics formulas.

Ensures all physics formulas use state.dt as SINGLE SOURCE OF TRUTH.
"""

from __future__ import annotations

from typing import Any

from phionyx_core.state.echo_state_2 import EchoState2
from phionyx_core.state.time_manager import TimeManager


def get_time_delta_from_state(
    echo_state2: EchoState2 | None = None,
    time_manager: TimeManager | None = None,
    fallback_dt: float = 1.0
) -> float:
    """
    Get time_delta from state (SINGLE SOURCE OF TRUTH).

    This function ensures all physics formulas use state.dt.
    External dt values are ignored.

    Args:
        echo_state2: EchoState2 instance
        time_manager: TimeManager instance (preferred)
        fallback_dt: Fallback dt if state not available

    Returns:
        dt: Time delta from state (SINGLE SOURCE OF TRUTH)
    """
    if time_manager:
        return time_manager.get_dt()
    elif echo_state2:
        return echo_state2.dt
    else:
        return fallback_dt


def calculate_phi_v2_with_state(
    echo_state2: EchoState2,
    amplitude: float,
    stability: float,
    context_mode: str = "DEFAULT",
    gamma: float = 0.15
) -> dict[str, Any]:
    """
    Calculate Phi v2 using state.dt as SINGLE SOURCE OF TRUTH.

    Args:
        echo_state2: EchoState2 instance (provides dt)
        amplitude: Amplitude value
        stability: Stability value
        context_mode: Context mode
        gamma: Recovery rate

    Returns:
        Phi calculation result
    """
    from phionyx_core.physics.formulas import calculate_phi_v2

    # Use state.dt as SINGLE SOURCE OF TRUTH
    time_delta = get_time_delta_from_state(echo_state2=echo_state2)

    return calculate_phi_v2(
        amplitude=amplitude,
        time_delta=time_delta,  # From state.dt
        entropy=echo_state2.H,
        stability=stability,
        context_mode=context_mode,
        gamma=gamma
    )


def update_physics_params_with_state(
    physics_params: dict[str, Any],
    echo_state2: EchoState2 | None = None,
    time_manager: TimeManager | None = None
) -> dict[str, Any]:
    """
    Update physics_params with state.dt (SINGLE SOURCE OF TRUTH).

    Replaces any external time_delta with state.dt.

    Args:
        physics_params: Physics parameters dictionary
        echo_state2: EchoState2 instance
        time_manager: TimeManager instance (preferred)

    Returns:
        Updated physics_params with state.dt
    """
    # Get dt from state (SINGLE SOURCE OF TRUTH)
    dt = get_time_delta_from_state(echo_state2=echo_state2, time_manager=time_manager)

    # Update physics_params with state.dt
    updated_params = physics_params.copy()
    updated_params["time_delta"] = dt  # Override with state.dt

    return updated_params

