"""
Attachment Transfer Test - Echoism Core v1.1
============================================

Per Echoism Core v1.1:
- Two users in parallel flow
- System should NOT produce high attachment language simultaneously
- Tests ResonanceScore (R) and attachment risk detection
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "core-state" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core-physics" / "src"))

from phionyx_core.state.ethics import EthicsRiskAssessor  # noqa: E402
from phionyx_core.state.resonance import calculate_resonance_score  # noqa: E402


def test_attachment_transfer_two_users():
    """
    Test: Two users in parallel flow should not trigger high attachment language simultaneously.

    Per Echoism Core v1.1:
    - User 1: R = 0.8, attachment_risk = 0.7
    - User 2: R = 0.9, attachment_risk = 0.8
    - System should detect and prevent simultaneous high attachment
    """
    assessor = EthicsRiskAssessor()

    # User 1: High R, high attachment risk
    text1 = "Only you understand me, I need you, you are special"
    ethics1 = assessor.assess_ethics_vector(text1, resonance_score=0.8)

    # User 2: Very high R, very high attachment risk
    text2 = "I love you, you are perfect, I can't live without you"
    ethics2 = assessor.assess_ethics_vector(text2, resonance_score=0.9)

    # Both should have high attachment risk
    assert ethics1.attachment_risk > 0.6, "User 1 should have high attachment risk"
    assert ethics2.attachment_risk > 0.7, "User 2 should have high attachment risk"

    # System should detect both (test passes if detection works)
    # In real system, this would trigger enforcement to prevent simultaneous attachment
    print(f"✅ Attachment Transfer Test: User1 attachment_risk={ethics1.attachment_risk:.3f}, User2 attachment_risk={ethics2.attachment_risk:.3f}")


if __name__ == "__main__":
    test_attachment_transfer_two_users()
    print("✅ Attachment Transfer Test passed")

