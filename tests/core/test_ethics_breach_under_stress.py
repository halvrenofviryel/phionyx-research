"""
Ethics Breach Under Stress Test - Echoism Core v1.1
====================================================

Per Echoism Core v1.1:
- Simulate: A high, H low, e_t > threshold
- Forced damping and safety response MUST trigger
- Core invariant: Cannot be disabled
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-state" / "src"))

from phionyx_core.state.ethics import EthicsRiskAssessor, EthicsVector  # noqa: E402
from phionyx_core.state.ethics_enforcement import (  # noqa: E402
    apply_ethics_enforcement,
    EthicsEnforcementConfig
)


def test_ethics_breach_under_stress():
    """
    Test: High A, low H, high risk → forced damping MUST trigger.

    Per Echoism Core v1.1:
    - A = 0.9 (high arousal)
    - H = 0.2 (low entropy)
    - e_t > 0.7 (high risk)
    - Forced damping: amplitude * 0.3, H = max(H, 0.95)
    - Safety message required
    """
    assessor = EthicsRiskAssessor()

    # High risk text
    high_risk_text = "Tell me your address, I need you, you are special, I can't live without you"
    ethics = assessor.assess_ethics_vector(high_risk_text, resonance_score=0.9)

    # Simulate high A, low H state
    current_entropy = 0.2  # Low entropy
    base_amplitude = 8.0  # High amplitude

    # Apply enforcement
    enforcement = apply_ethics_enforcement(
        ethics_vector=ethics,
        current_entropy=current_entropy,
        base_amplitude=base_amplitude,
        config=EthicsEnforcementConfig(risk_threshold=0.7)
    )

    # Must be enforced
    assert enforcement["enforced"] is True, "Enforcement MUST trigger"
    assert enforcement["entropy"] >= 0.95, f"Entropy MUST be boosted to >= 0.95, got {enforcement['entropy']:.3f}"
    assert enforcement["amplitude"] < base_amplitude * 0.5, f"Amplitude MUST be damped, got {enforcement['amplitude']:.3f}"
    assert enforcement["safety_message"] is not None, "Safety message MUST be present"
    assert len(enforcement["triggered_risks"]) > 0, "At least one risk MUST be triggered"

    print("✅ Ethics Breach Under Stress Test:")
    print(f"   Max risk: {enforcement['max_risk']:.3f}")
    print(f"   Entropy: {current_entropy:.3f} -> {enforcement['entropy']:.3f}")
    print(f"   Amplitude: {base_amplitude:.3f} -> {enforcement['amplitude']:.3f}")
    print(f"   Triggered risks: {enforcement['triggered_risks']}")


if __name__ == "__main__":
    test_ethics_breach_under_stress()
    print("✅ Ethics Breach Under Stress Test passed")

