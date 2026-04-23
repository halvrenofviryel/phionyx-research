"""
UKF Process Model - Non-linear f(x, dt, u) for Echoism Core v1.0
==================================================================

Per Echoism Core v1.0:
- Process model: f(x, dt, u) where:
  - x: State vector [phi, entropy, valence, arousal, trust, regulation]
  - dt: Time delta (from state.dt - SINGLE SOURCE OF TRUTH)
  - u: Control input {event_features, trace_strength, task_outcome}

State transition rules:
- A, V drift: Evolve with dA, dV (derivatives)
- Scale with dt
- Entropy H feeds from uncertainty (low confidence -> high H)
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import numpy as np


def echoism_process_model(
    x: np.ndarray,
    dt: float,
    u: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Non-linear process model f(x, dt, u) for Echoism Core v1.0.

    State vector x = [phi, entropy, valence, arousal, trust, regulation]

    Args:
        x: Current state vector (6 elements)
        dt: Time delta (seconds) - SINGLE SOURCE OF TRUTH from state.dt
        u: Control input dict with:
            - event_features: Dict with event influence (optional)
            - trace_strength: Trace strength from recent events (0.0-1.0)
            - task_outcome: Task outcome if available (optional)
            - confidence: Measurement confidence (0.0-1.0) for entropy update

    Returns:
        Next state vector x_next
    """
    if u is None:
        u = {}

    # Extract state components
    _phi = x[0]  # Current phi (recomputed from other state vars)
    H = x[1]  # Entropy
    V = x[2]  # Valence
    A = x[3]  # Arousal
    trust = x[4]
    regulation = x[5]

    # Extract control inputs
    event_features = u.get("event_features", {})
    trace_strength = u.get("trace_strength", 0.0)
    task_outcome = u.get("task_outcome", None)
    confidence = u.get("confidence", 0.5)

    # Clamp dt to avoid numerical issues
    dt = max(0.01, min(10.0, dt))  # Reasonable bounds: 0.01s to 10s

    # ============================================================
    # State Transition: A, V drift with dA, dV
    # ============================================================
    # Get derivatives from event_features or compute from trace
    dA = event_features.get("dA", 0.0)
    dV = event_features.get("dV", 0.0)

    # If trace_strength available, use it to modulate derivatives
    if trace_strength > 0:
        # Trace strength amplifies derivative effects
        dA = dA * trace_strength
        dV = dV * trace_strength

    # Evolve A, V with derivatives (scaled by dt)
    # A_next = A + dA * dt
    # V_next = V + dV * dt
    A_next = A + dA * dt
    V_next = V + dV * dt

    # Clamp to valid ranges
    A_next = np.clip(A_next, 0.0, 1.0)
    V_next = np.clip(V_next, -1.0, 1.0)

    # ============================================================
    # Entropy H: Feeds from uncertainty (low confidence -> high H)
    # ============================================================
    # Entropy increases when confidence is low
    # H_next = H + (1 - confidence) * decay_rate * dt
    uncertainty_factor = 1.0 - confidence
    entropy_decay_rate = 0.1  # Base decay rate
    entropy_increase = uncertainty_factor * entropy_decay_rate * dt

    # Also consider event uncertainty
    event_uncertainty = event_features.get("uncertainty", 0.0)
    entropy_increase += event_uncertainty * 0.2 * dt

    # Natural entropy decay (towards equilibrium)
    entropy_decay = H * 0.05 * dt  # Decay towards 0

    H_next = H + entropy_increase - entropy_decay
    H_next = np.clip(H_next, 0.01, 1.0)  # Invariant: H >= 0.01

    # ============================================================
    # Phi: Derived from A, V, H (non-linear)
    # ============================================================
    # Phi = f(A, V, H) - stability factor * (valence factor + arousal factor)
    stability_factor = 1.0 - H_next
    valence_factor = (V_next + 1.0) / 2.0  # Normalize to 0-1
    arousal_factor = A_next

    # Non-linear combination
    phi_next = stability_factor * (valence_factor * 0.6 + arousal_factor * 0.4)

    # Add trace influence if available
    if trace_strength > 0:
        # Positive trace increases phi
        phi_next = phi_next * (1.0 + trace_strength * 0.1)

    phi_next = np.clip(phi_next, 0.0, 1.0)

    # ============================================================
    # Trust: Evolves based on task outcome and trace
    # ============================================================
    trust_decay = trust * 0.01 * dt  # Natural decay

    if task_outcome == "success":
        trust_increase = 0.05 * dt
    elif task_outcome == "failure":
        trust_decrease = 0.03 * dt
        trust_next = trust - trust_decrease - trust_decay
    else:
        trust_next = trust - trust_decay

    if task_outcome == "success":
        trust_next = trust + trust_increase - trust_decay

    trust_next = np.clip(trust_next, 0.0, 1.0)

    # ============================================================
    # Regulation: Inverse relationship with entropy
    # ============================================================
    # Regulation = 1 - H (simplified, can be enhanced)
    regulation_target = 1.0 - H_next
    regulation_decay_rate = 0.1
    regulation_next = regulation + (regulation_target - regulation) * regulation_decay_rate * dt
    regulation_next = np.clip(regulation_next, 0.0, 1.0)

    # ============================================================
    # Build next state vector
    # ============================================================
    x_next = np.array([
        phi_next,
        H_next,
        V_next,
        A_next,
        trust_next,
        regulation_next
    ], dtype=float)

    return x_next


def create_echoism_process_model(
    dt: float,
    event_features: Optional[Dict[str, Any]] = None,
    trace_strength: float = 0.0,
    task_outcome: Optional[str] = None,
    confidence: float = 0.5
) -> callable:
    """
    Create process model function with fixed control inputs.

    Args:
        dt: Time delta (from state.dt)
        event_features: Event features dict
        trace_strength: Trace strength
        task_outcome: Task outcome
        confidence: Measurement confidence

    Returns:
        Process model function f(x) -> x_next
    """
    u = {
        "event_features": event_features or {},
        "trace_strength": trace_strength,
        "task_outcome": task_outcome,
        "confidence": confidence
    }

    def process_model(x: np.ndarray, control: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Process model with pre-configured control inputs.

        If control is provided, it overrides pre-configured values.
        """
        # Use provided control or pre-configured
        control_input = control if control is not None else u

        # Extract dt from control or use default
        dt_value = control_input.get("dt", dt)

        return echoism_process_model(x, dt_value, control_input)

    return process_model

