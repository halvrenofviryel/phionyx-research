"""
Echoism Core Minimal - Example Usage
====================================

Didactic example of Echoism Core v1.1 principles.

NOTE: This is a reference/example file. Print statements are acceptable here
as this is meant to be run as a standalone example script.
"""

from state import EchoState2Plus


def main() -> None:
    """Example usage of Echoism Core v1.1 minimal implementation."""
    # Note: Print statements are acceptable in reference/example code
    print("=" * 60)
    print("Echoism Core v1.1 - Minimal Reference Implementation")
    print("=" * 60)
    print()

    # Create state
    state = EchoState2Plus(
        A=0.6,
        V=0.3,
        H=0.4,
        I=0.7,
        R=0.2,
        C=0.8
    )

    print("Initial State:")
    print(f"  A={state.A:.3f}, V={state.V:.3f}, H={state.H:.3f}")
    print(f"  I={state.I:.3f}, R={state.R:.3f}, C={state.C:.3f}")
    print(f"  Phi (derived)={state.phi:.3f}")
    print()

    # Update time
    state.update_time()
    print(f"Time updated: dt={state.dt:.3f}, turn={state.turn_index}")
    print()

    print("✅ Minimal reference implementation working!")
    print()
    print("NOTE: This is a didactic example, NOT the production SDK.")
    print("For production use, see core-state, core-physics, core-memory modules.")


if __name__ == "__main__":
    main()

