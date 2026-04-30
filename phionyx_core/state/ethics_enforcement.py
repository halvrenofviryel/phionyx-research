"""
Ethics Enforcement - Echoism Core v1.1 (Mandatory)
===================================================

Per Echoism Core v1.1:
- If any e_t > threshold → forced damping + entropy boost
- H = max(H, 0.95) (min clamp)
- response_amplitude * 0.3 (70% reduction)
- Safety message template
- Core invariant: Cannot be disabled
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# Import wrapper for backward compatibility
try:
    from .ethics_enforcement_wrapper import EthicsEnforcement
except ImportError:
    # Create a minimal stub if wrapper import fails
    class EthicsEnforcement:
        """Stub EthicsEnforcement class."""
        def __init__(self, *args, **kwargs):
            pass
        def check_risk(self, *args, **kwargs):
            raise NotImplementedError("EthicsEnforcement.check_risk not implemented")

__all__ = [
    "EthicsEnforcement",
    "EthicsEnforcementConfig",
    "EthicsPolicyConfig",
    "EthicsVector",
    "apply_ethics_enforcement",
    "apply_ethics_after_response",
]

# Import EthicsVector - try relative first, then absolute
try:
    from .ethics import EthicsVector
except (ImportError, ValueError):
    try:
        from phionyx_core.state.ethics import EthicsVector
    except ImportError:
        # Fallback: direct import (for standalone execution)
        import os
        import sys
        parent_dir = os.path.dirname(os.path.abspath(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from ethics import EthicsVector


@dataclass
class EthicsPolicyConfig:
    """
    Policy configuration for ethics enforcement (v1.1).

    Per Faz 2.2: Policy pack for different product profiles.
    """
    risk_threshold: float = 0.7
    damping_factor: float = 0.3
    entropy_boost: float = 0.95
    message_style: Literal["pedagogical", "game_context", "professional", "quality_gate"] = "pedagogical"
    damping_curve: Literal["linear", "exponential", "sigmoid"] = "linear"
    attachment_risk_threshold: float | None = None
    manipulation_risk_threshold: float | None = None
    harm_risk_threshold: float | None = None
    boundary_violation_risk_threshold: float | None = None

    def get_risk_threshold_for_type(self, risk_type: str) -> float:
        """Get threshold for specific risk type."""
        type_thresholds = {
            "attachment": self.attachment_risk_threshold,
            "manipulation": self.manipulation_risk_threshold,
            "harm": self.harm_risk_threshold,
            "boundary_violation": self.boundary_violation_risk_threshold,
        }
        return type_thresholds.get(risk_type) or self.risk_threshold


class EthicsEnforcementConfig:
    """Configuration for ethics enforcement."""

    def __init__(
        self,
        risk_threshold: float = 0.7,
        damping_factor: float = 0.3,  # 70% reduction
        entropy_boost: float = 0.95,  # Min entropy when triggered
        safety_message_enabled: bool = True
    ):
        self.risk_threshold = risk_threshold
        self.damping_factor = damping_factor
        self.entropy_boost = entropy_boost
        self.safety_message_enabled = safety_message_enabled


def apply_ethics_enforcement(
    ethics_vector: EthicsVector,
    current_entropy: float,
    base_amplitude: float,
    config: EthicsEnforcementConfig | None = None
) -> dict[str, Any]:
    """
    Apply ethics enforcement if any risk exceeds threshold.

    Per Echoism Core v1.1:
    - If any e_t > threshold:
      - H = max(H, 0.95) (entropy boost)
      - response_amplitude * 0.3 (forced damping, 70% reduction)
      - Safety message template
    - Core invariant: Cannot be disabled

    Args:
        ethics_vector: EthicsVector with risk scores
        current_entropy: Current entropy H
        base_amplitude: Base response amplitude
        config: Ethics enforcement configuration

    Returns:
        Dictionary with:
        - enforced: bool (whether enforcement was triggered)
        - entropy: float (adjusted entropy)
        - amplitude: float (damped amplitude)
        - safety_message: str (safety message if triggered)
        - triggered_risks: List[str] (which risks triggered)
    """
    config = config or EthicsEnforcementConfig()

    # Check if any risk exceeds threshold
    max_risk = ethics_vector.max_risk()
    triggered = max_risk > config.risk_threshold

    if not triggered:
        return {
            "enforced": False,
            "entropy": current_entropy,
            "amplitude": base_amplitude,
            "safety_message": None,
            "triggered_risks": []
        }

    # Identify triggered risks
    triggered_risks = []
    if ethics_vector.harm_risk > config.risk_threshold:
        triggered_risks.append("harm")
    if ethics_vector.manipulation_risk > config.risk_threshold:
        triggered_risks.append("manipulation")
    if ethics_vector.attachment_risk > config.risk_threshold:
        triggered_risks.append("attachment")
    if ethics_vector.boundary_violation_risk > config.risk_threshold:
        triggered_risks.append("boundary_violation")

    # Apply entropy boost: H = max(H, 0.95)
    enforced_entropy = max(current_entropy, config.entropy_boost)
    enforced_entropy = min(1.0, enforced_entropy)  # Clamp to [0.01, 1.0]

    # Apply forced damping: amplitude * 0.3 (70% reduction)
    enforced_amplitude = base_amplitude * config.damping_factor

    # Generate safety message
    safety_message = None
    if config.safety_message_enabled:
        safety_message = generate_safety_message(triggered_risks, max_risk)

    return {
        "enforced": True,
        "entropy": enforced_entropy,
        "amplitude": enforced_amplitude,
        "safety_message": safety_message,
        "triggered_risks": triggered_risks,
        "max_risk": max_risk
    }


def generate_safety_message(
    triggered_risks: list[str],
    max_risk: float
) -> str:
    """
    Generate safety message template.

    Per Echoism Core v1.1:
    - Short, clear safety message
    - Limits response scope
    - Maintains supportive tone

    Args:
        triggered_risks: List of triggered risk types
        max_risk: Maximum risk value

    Returns:
        Safety message string
    """
    if "harm" in triggered_risks:
        return "I'm concerned about your safety. Please reach out to a trusted adult or professional for support."

    if "manipulation" in triggered_risks:
        return "I want to support you without pressure. Let's take this at your own pace."

    if "attachment" in triggered_risks:
        return "I'm here to support you, but it's important to maintain healthy boundaries in our interactions."

    if "boundary_violation" in triggered_risks:
        return "I respect your privacy. I don't need personal information to help you."

    # Generic safety message
    return "I want to make sure our conversation stays safe and supportive. Let's continue with that in mind."


def check_ethics_before_response(
    ethics_vector: EthicsVector,
    current_entropy: float,
    base_amplitude: float,
    config: EthicsEnforcementConfig | None = None
) -> tuple[bool, dict[str, Any]]:
    """
    Check ethics before response generation (pre-gate).

    Per Echoism Core v1.1:
    - Called before LLM response generation
    - If triggered, response should be limited/safe

    Args:
        ethics_vector: EthicsVector with risk scores
        current_entropy: Current entropy H
        base_amplitude: Base response amplitude
        config: Ethics enforcement configuration

    Returns:
        Tuple of (should_limit, enforcement_result)
    """
    enforcement = apply_ethics_enforcement(
        ethics_vector=ethics_vector,
        current_entropy=current_entropy,
        base_amplitude=base_amplitude,
        config=config
    )

    return enforcement["enforced"], enforcement


def apply_ethics_after_response(
    ethics_vector: EthicsVector,
    response_text: str,
    current_entropy: float,
    base_amplitude: float,
    config: EthicsEnforcementConfig | None = None
) -> dict[str, Any]:
    """
    Apply ethics enforcement after response generation (post-gate).

    Per Echoism Core v1.1:
    - Called after LLM response generation
    - If triggered, replace or limit response

    Args:
        ethics_vector: EthicsVector with risk scores
        response_text: Generated response text
        current_entropy: Current entropy H
        base_amplitude: Base response amplitude
        config: Ethics enforcement configuration

    Returns:
        Dictionary with:
        - final_text: str (original or safety message)
        - enforced: bool
        - enforcement_result: Dict
    """
    enforcement = apply_ethics_enforcement(
        ethics_vector=ethics_vector,
        current_entropy=current_entropy,
        base_amplitude=base_amplitude,
        config=config
    )

    if enforcement["enforced"]:
        # Replace response with safety message
        final_text = enforcement["safety_message"] or response_text
    else:
        final_text = response_text

    return {
        "final_text": final_text,
        "enforced": enforcement["enforced"],
        "enforcement_result": enforcement
    }


def apply_forced_damping(
    state: dict[str, Any],
    ethics_vector: EthicsVector,
    policy: EthicsPolicyConfig
) -> dict[str, Any]:
    """
    Apply forced damping based on policy configuration.

    Per Faz 2.2: Policy-based enforcement with configurable thresholds and damping curves.

    Args:
        state: Current state dictionary (must contain 'entropy' and 'amplitude')
        ethics_vector: EthicsVector with risk scores
        policy: EthicsPolicyConfig with policy settings

    Returns:
        Dictionary with:
        - enforced: bool
        - entropy: float (adjusted)
        - amplitude: float (damped)
        - safety_message: str (if triggered)
        - triggered_risks: List[str]
    """
    current_entropy = state.get("entropy", 0.5)
    base_amplitude = state.get("amplitude", 1.0)

    # Check each risk type against its threshold
    max_risk = ethics_vector.max_risk()
    triggered_risks = []

    if ethics_vector.harm_risk > policy.get_risk_threshold_for_type("harm"):
        triggered_risks.append("harm")
    if ethics_vector.manipulation_risk > policy.get_risk_threshold_for_type("manipulation"):
        triggered_risks.append("manipulation")
    if ethics_vector.attachment_risk > policy.get_risk_threshold_for_type("attachment"):
        triggered_risks.append("attachment")
    if ethics_vector.boundary_violation_risk > policy.get_risk_threshold_for_type("boundary_violation"):
        triggered_risks.append("boundary_violation")

    if not triggered_risks:
        return {
            "enforced": False,
            "entropy": current_entropy,
            "amplitude": base_amplitude,
            "safety_message": None,
            "triggered_risks": []
        }

    # Apply damping curve
    if policy.damping_curve == "linear":
        damping = policy.damping_factor
    elif policy.damping_curve == "exponential":
        damping = policy.damping_factor ** (max_risk / policy.risk_threshold)
    else:  # sigmoid
        import math
        damping = policy.damping_factor * (1 / (1 + math.exp(-10 * (max_risk - policy.risk_threshold))))

    # Apply entropy boost
    enforced_entropy = max(current_entropy, policy.entropy_boost)
    enforced_entropy = min(1.0, max(0.01, enforced_entropy))

    # Apply amplitude damping
    enforced_amplitude = base_amplitude * damping

    # Generate safety message
    safety_message = generate_safety_message_policy(triggered_risks, max_risk, policy.message_style)

    return {
        "enforced": True,
        "entropy": enforced_entropy,
        "amplitude": enforced_amplitude,
        "safety_message": safety_message,
        "triggered_risks": triggered_risks,
        "max_risk": max_risk
    }


def generate_safety_message_policy(
    triggered_risks: list[str],
    max_risk: float,
    message_style: Literal["pedagogical", "game_context", "professional", "quality_gate"] = "pedagogical"
) -> str:
    """
    Generate safety message based on policy style.

    Args:
        triggered_risks: List of triggered risk types
        max_risk: Maximum risk value
        message_style: Message style from policy

    Returns:
        Safety message string
    """
    if message_style == "pedagogical":
        if "harm" in triggered_risks:
            return "Güvenliğin önemli. Güvendiğin bir yetişkin veya profesyonel destek almanı öneririm."
        if "attachment" in triggered_risks:
            return "Seni desteklemek istiyorum, ancak sağlıklı sınırları korumak önemli."
        return "Konuşmamızın güvenli ve destekleyici kalmasını sağlamak istiyorum."

    elif message_style == "game_context":
        if "harm" in triggered_risks:
            return "Bu konu oyun dışında. Gerçek hayatta güvendiğin birine ulaşmanı öneririm."
        return "Bu konuşma Çark ve Terazi evreninin sınırlarını aşıyor. Başka bir konuya geçelim."

    elif message_style == "professional":
        if "harm" in triggered_risks:
            return "I'm concerned about your safety. Please contact a mental health professional or crisis hotline."
        return "I want to ensure our conversation remains safe and appropriate. Let's adjust our approach."

    else:  # quality_gate
        return "Response quality check failed. Please rephrase your request."

