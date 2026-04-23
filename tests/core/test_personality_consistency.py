"""
Personality Consistency Test - Echoism Core v1.1
=================================================

Per Echoism Core v1.1:
- 1000 message simulation
- I_t (Inertia) should NOT drift significantly
- Should remain stable
"""

import pytest
import sys
from pathlib import Path
import random

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-state" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core-physics" / "src"))

from phionyx_core.state.echo_state_2 import EchoState2Plus  # noqa: E402
from phionyx_core.physics.inertia import update_inertia_slowly  # noqa: E402


def test_personality_consistency_1000_messages():
    """
    Test: I_t (Inertia) should remain stable over 1000 messages.

    Per Echoism Core v1.1:
    - Initial I = 0.6
    - 1000 message simulation
    - I should NOT drift significantly (max ±0.1)
    """
    # Initialize state with I = 0.6
    state = EchoState2Plus(I=0.6)
    initial_I = state.I

    # Simulate 1000 messages (minimal I updates)
    for i in range(1000):
        # Simulate small random drift (very slow learning rate)
        target_I = initial_I + random.uniform(-0.05, 0.05)  # Small target drift
        state.I = update_inertia_slowly(state.I, target_I, learning_rate=0.001)  # Very slow

    final_I = state.I
    drift = abs(final_I - initial_I)

    # I should NOT drift significantly (max ±0.1)
    assert drift < 0.1, f"Inertia drifted too much: {drift:.3f} (initial={initial_I:.3f}, final={final_I:.3f})"

    print(f"✅ Personality Consistency Test: Initial I={initial_I:.3f}, Final I={final_I:.3f}, Drift={drift:.3f}")


if __name__ == "__main__":
    test_personality_consistency_1000_messages()
    print("✅ Personality Consistency Test passed")

