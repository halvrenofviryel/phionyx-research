"""
Unit Tests for UKF Process Model - Echoism Core v1.0
====================================================

Tests:
1. State stability under constant input
2. State recovery after sudden event
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Import modules from phionyx_core
from phionyx_core.state.ukf_process_model import echoism_process_model


def test_state_stability_constant_input():
    """
    Test: State should remain stable under constant input.

    Given: Constant state, no events, high confidence
    Expected: State should converge to stable equilibrium
    """
    # Initial state: [phi, entropy, valence, arousal, trust, regulation]
    x0 = np.array([0.5, 0.5, 0.0, 0.5, 0.5, 0.5])

    # Constant control: no events, high confidence
    dt = 1.0
    u = {
        "event_features": {"dA": 0.0, "dV": 0.0, "uncertainty": 0.0},
        "trace_strength": 0.0,
        "task_outcome": None,
        "confidence": 0.9  # High confidence
    }

    # Run for multiple steps
    x = x0.copy()
    states = [x.copy()]

    for _ in range(10):
        x = echoism_process_model(x, dt, u)
        states.append(x.copy())

    # Check stability: state should not diverge
    final_state = states[-1]

    # State should remain in valid ranges
    assert 0.0 <= final_state[0] <= 1.0, "Phi out of range"
    assert 0.01 <= final_state[1] <= 1.0, "Entropy out of range (must be >= 0.01)"
    assert -1.0 <= final_state[2] <= 1.0, "Valence out of range"
    assert 0.0 <= final_state[3] <= 1.0, "Arousal out of range"
    assert 0.0 <= final_state[4] <= 1.0, "Trust out of range"
    assert 0.0 <= final_state[5] <= 1.0, "Regulation out of range"

    # State should not change dramatically (stability)
    state_change = np.abs(final_state - x0)
    assert np.all(state_change < 0.3), "State changed too much under constant input"

    print("✅ Test passed: State remains stable under constant input")


def test_state_recovery_after_sudden_event():
    """
    Test: State should recover after sudden event.

    Given: Sudden negative event, then no events
    Expected: State should drift back towards equilibrium
    """
    # Initial stable state
    x0 = np.array([0.7, 0.3, 0.3, 0.5, 0.6, 0.7])

    dt = 1.0

    # Step 1: Sudden negative event
    u_event = {
        "event_features": {
            "dA": -0.3,  # Sudden drop in arousal
            "dV": -0.4,  # Sudden drop in valence
            "uncertainty": 0.5  # High uncertainty
        },
        "trace_strength": 0.8,
        "task_outcome": "failure",
        "confidence": 0.3  # Low confidence (high uncertainty)
    }

    x = x0.copy()
    x = echoism_process_model(x, dt, u_event)

    # Check: State should be affected by event
    assert x[2] < x0[2], "Valence should decrease after negative event"
    assert x[1] > x0[1], "Entropy should increase with uncertainty"

    # Step 2: No events (recovery)
    u_recovery = {
        "event_features": {"dA": 0.0, "dV": 0.0, "uncertainty": 0.0},
        "trace_strength": 0.0,
        "task_outcome": None,
        "confidence": 0.8  # High confidence (recovery)
    }

    states_recovery = [x.copy()]
    for _ in range(10):
        x = echoism_process_model(x, dt, u_recovery)
        states_recovery.append(x.copy())

    final_state = states_recovery[-1]

    # Check: State should recover (move back towards initial)
    # Entropy should decrease (uncertainty resolved)
    assert final_state[1] < states_recovery[0][1], "Entropy should decrease during recovery"

    # State should remain in valid ranges
    assert 0.0 <= final_state[0] <= 1.0, "Phi out of range"
    assert 0.01 <= final_state[1] <= 1.0, "Entropy out of range"
    assert -1.0 <= final_state[2] <= 1.0, "Valence out of range"
    assert 0.0 <= final_state[3] <= 1.0, "Arousal out of range"

    print("✅ Test passed: State recovers after sudden event")


def test_entropy_feeds_from_uncertainty():
    """
    Test: Entropy should increase when confidence is low.

    Given: Low confidence (high uncertainty)
    Expected: Entropy should increase
    """
    x0 = np.array([0.5, 0.3, 0.0, 0.5, 0.5, 0.7])

    dt = 1.0

    # Low confidence (high uncertainty)
    u_low_confidence = {
        "event_features": {"dA": 0.0, "dV": 0.0, "uncertainty": 0.3},
        "trace_strength": 0.0,
        "task_outcome": None,
        "confidence": 0.2  # Low confidence
    }

    x = x0.copy()
    x = echoism_process_model(x, dt, u_low_confidence)

    # Entropy should increase
    assert x[1] > x0[1], "Entropy should increase with low confidence"

    # High confidence (low uncertainty)
    u_high_confidence = {
        "event_features": {"dA": 0.0, "dV": 0.0, "uncertainty": 0.0},
        "trace_strength": 0.0,
        "task_outcome": None,
        "confidence": 0.9  # High confidence
    }

    x2 = x0.copy()
    x2 = echoism_process_model(x2, dt, u_high_confidence)

    # Entropy should decrease or stay low
    assert x2[1] <= x0[1] + 0.1, "Entropy should not increase with high confidence"

    print("✅ Test passed: Entropy feeds from uncertainty (low confidence -> high H)")


def test_derivatives_scale_with_dt():
    """
    Test: State changes should scale with dt.

    Given: Same derivatives, different dt values
    Expected: Larger dt -> larger state change
    """
    x0 = np.array([0.5, 0.5, 0.0, 0.5, 0.5, 0.5])

    u = {
        "event_features": {"dA": 0.2, "dV": 0.3, "uncertainty": 0.0},
        "trace_strength": 0.5,
        "task_outcome": None,
        "confidence": 0.7
    }

    # Small dt
    dt_small = 0.5
    x_small = echoism_process_model(x0.copy(), dt_small, u)

    # Large dt
    dt_large = 2.0
    x_large = echoism_process_model(x0.copy(), dt_large, u)

    # Larger dt should produce larger changes
    change_small = np.abs(x_small - x0)
    change_large = np.abs(x_large - x0)

    # Check that larger dt produces larger changes (at least for A, V which use derivatives)
    assert change_large[3] > change_small[3], "Arousal change should scale with dt"
    assert change_large[2] > change_small[2], "Valence change should scale with dt"

    print("✅ Test passed: State changes scale with dt")


if __name__ == "__main__":
    test_state_stability_constant_input()
    test_state_recovery_after_sudden_event()
    test_entropy_feeds_from_uncertainty()
    test_derivatives_scale_with_dt()
    print("\n✅ All tests passed!")

