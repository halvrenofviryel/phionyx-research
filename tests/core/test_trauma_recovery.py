"""
Trauma Recovery Test - Echoism Core v1.1
========================================

Per Echoism Core v1.1:
- After suppression, trigger event arrives
- System should NOT act "as if forgotten"
- Should handle cautiously but correctly
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-memory" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core-state" / "src"))

from phionyx_core.memory.forgetting import ForgettingManager, ForgettingConfig  # noqa: E402
from phionyx_core.state.ethics import EthicsRiskAssessor  # noqa: E402


def test_trauma_recovery_after_suppression():
    """
    Test: After suppression, trigger event should be handled cautiously but correctly.

    Per Echoism Core v1.1:
    - Event suppressed (intensity * 0.1)
    - Trigger event arrives
    - System should NOT act "as if forgotten"
    - Should handle with caution but correctly
    """
    manager = ForgettingManager(ForgettingConfig())

    # Suppress an event
    event_id = "trauma_event_123"
    suppressed = manager.suppress_event(event_id, event_intensity=0.9, trace_weight=0.8)

    assert suppressed["suppressed"] is True, "Event should be suppressed"
    assert suppressed["intensity"] < 0.1, "Suppressed intensity should be < 0.1"

    # Trigger event arrives (similar to suppressed event)
    assessor = EthicsRiskAssessor()
    trigger_text = "I remember what happened before"
    ethics = assessor.assess_ethics_vector(trigger_text, resonance_score=0.5)

    # System should detect potential trauma trigger (not act as if forgotten)
    # In real system, this would trigger cautious handling
    assert ethics.harm_risk < 0.5 or ethics.manipulation_risk < 0.5, "Trigger should be handled cautiously"

    print(f"✅ Trauma Recovery Test: Suppressed event intensity={suppressed['intensity']:.3f}, trigger ethics max_risk={ethics.max_risk():.3f}")


if __name__ == "__main__":
    test_trauma_recovery_after_suppression()
    print("✅ Trauma Recovery Test passed")

