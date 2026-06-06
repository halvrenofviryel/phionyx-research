"""
Policy Engine - Policy Selection Logic
======================================

Selects appropriate behavioral policy based on context, risk level, and user role.
"""

import logging
from typing import Optional, Dict, Any

from .policies import Policy, PolicyPresets

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Cognitive Policy Engine for context-aware behavioral policies.

    Selects the appropriate policy based on:
    - Context mode (from CRL)
    - Risk level (from Guardrails)
    - User role (teacher, student, etc.)
    """

    def __init__(self, mode: Optional[str] = None, **kwargs):
        """
        Initialize policy engine.

        Args:
            mode: Policy mode (optional, for backward compatibility)
            **kwargs: Additional arguments (ignored for backward compatibility)
        """
        self.presets = PolicyPresets()
        self.mode = mode  # Store mode but don't require it
        logger.info(f"PolicyEngine initialized (mode: {mode or 'default'})")

    def select_policy(
        self,
        context_mode: Optional[str] = None,
        risk_level: int = 0,
        user_role: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Policy:
        """
        Select appropriate policy based on context.

        Priority Order:
        1. Risk Level > 1 -> SAFE_MODE_POLICY (highest priority)
        2. Context Mode == "SCHOOL" or "COMPLIANCE" -> TEACHING_POLICY or COMPLIANCE_POLICY
        3. Context Mode == "FANTASY_WRITING" or "LORE" -> LORE_POLICY
        4. Default -> DEFAULT_POLICY

        Args:
            context_mode: Context mode from CRL (e.g., "LIFE_PLANNING", "ENGINEERING", "FANTASY_WRITING")
            risk_level: Risk level from Guardrails (0=SAFE, 1=WARNING, 2=CRITICAL)
            user_role: User role (e.g., "teacher", "student", "admin")
            additional_context: Additional context for policy selection

        Returns:
            Selected Policy object
        """
        # Priority 1: Risk-based override (highest priority)
        if risk_level > 1:  # CRITICAL risk
            logger.warning(
                f"PolicyEngine: CRITICAL risk detected (level {risk_level}), "
                f"forcing SAFE_MODE_POLICY"
            )
            return self.presets.SAFE_MODE_POLICY

        # Priority 2: Context mode-based selection
        if context_mode:
            context_mode_upper = context_mode.upper()

            # School/Educational contexts
            if context_mode_upper in ["SCHOOL", "LIFE_PLANNING", "ENGINEERING"]:
                # Check user role for teaching context
                if user_role == "teacher" or context_mode_upper == "SCHOOL":
                    logger.info(
                        f"PolicyEngine: School context detected, using TEACHING_POLICY "
                        f"(mode: {context_mode}, role: {user_role})"
                    )
                    return self.presets.TEACHING_POLICY
                else:
                    # Student in educational context - still use teaching policy but slightly adjusted
                    logger.info(
                        f"PolicyEngine: Educational context detected, using TEACHING_POLICY "
                        f"(mode: {context_mode})"
                    )
                    return self.presets.TEACHING_POLICY

            # Compliance/Legal contexts
            if context_mode_upper == "COMPLIANCE":
                logger.info(
                    "PolicyEngine: Compliance context detected, using COMPLIANCE_POLICY"
                )
                return self.presets.COMPLIANCE_POLICY

            # Game/Lore contexts
            if context_mode_upper in ["FANTASY_WRITING", "LORE", "XR_DEV"]:
                logger.info(
                    f"PolicyEngine: Creative context detected, using LORE_POLICY "
                    f"(mode: {context_mode})"
                )
                return self.presets.LORE_POLICY

        # Priority 3: User role-based selection
        if user_role:
            if user_role == "teacher":
                logger.info(
                    "PolicyEngine: Teacher role detected, using TEACHING_POLICY"
                )
                return self.presets.TEACHING_POLICY

        # Priority 4: Risk warning (moderate risk)
        if risk_level == 1:  # WARNING level
            # Use a slightly more conservative version of default policy
            logger.info(
                f"PolicyEngine: Warning risk detected (level {risk_level}), "
                f"using conservative DEFAULT_POLICY"
            )
            # Create a modified default policy with higher safety
            conservative_policy = Policy(
                temperature=self.presets.DEFAULT_POLICY.temperature * 0.8,  # Lower temperature
                tone=self.presets.DEFAULT_POLICY.tone,
                safety_strictness=2,  # Moderate safety
                interaction_style=self.presets.DEFAULT_POLICY.interaction_style,
                max_tokens=self.presets.DEFAULT_POLICY.max_tokens,
                system_prompt_modifier=(
                    f"{self.presets.DEFAULT_POLICY.system_prompt_modifier} "
                    "Be extra careful with sensitive topics."
                )
            )
            return conservative_policy

        # Default: Use DEFAULT_POLICY
        logger.info(
            f"PolicyEngine: Using DEFAULT_POLICY "
            f"(context_mode: {context_mode}, risk_level: {risk_level}, role: {user_role})"
        )
        return self.presets.DEFAULT_POLICY

    def get_policy_config(self, policy: Policy) -> Dict[str, Any]:
        """
        Convert policy to configuration dictionary for LLM calls.

        Args:
            policy: Policy object

        Returns:
            Dictionary with LLM configuration parameters
        """
        config = {
            "temperature": policy.temperature,
            "max_tokens": policy.max_tokens,
            "tone": policy.tone,
            "safety_strictness": policy.safety_strictness,
            "interaction_style": policy.interaction_style,
        }

        if policy.system_prompt_modifier:
            config["system_prompt_modifier"] = policy.system_prompt_modifier

        return config

