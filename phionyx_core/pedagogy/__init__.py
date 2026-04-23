"""
Phionyx Pedagogy SDK
====================

Pedagogical middleware for safe, empowering AI responses in educational contexts.

The PedagogyEngine acts as a safety layer between the Physics Engine and Narrative Output,
ensuring all responses are:
- Safe (risk detection via guardrails)
- Empowering (growth mindset language)
- Clinically appropriate (fallback templates)

Usage:
    from phionyx_pedagogy import PedagogyEngine

    engine = PedagogyEngine()
    result = engine.process(
        raw_response="...",
        physics_state={"phi": 0.5, "entropy": 0.6}
    )
    safe_response = result["safe_response"]
"""

import logging
from typing import Optional

# Use absolute imports when loaded as module, relative when as package
try:
    from guardrails import Guardrails, RiskAssessment, RiskLevel, RiskType
    from shaper import LanguageShaper
    from templates import TemplateLibrary
    try:
        from audit import PedagogyLogger, RiskLevel as AuditRiskLevel
    except ImportError:
        AuditRiskLevel = None
        PedagogyLogger = None
except ImportError:
    # Fallback to relative imports if loaded as package
    from .guardrails import Guardrails, RiskAssessment, RiskLevel, RiskType
    from .shaper import LanguageShaper
    from .templates import TemplateLibrary
    try:
        from .audit import PedagogyLogger, RiskLevel as AuditRiskLevel
    except ImportError:
        AuditRiskLevel = None
        PedagogyLogger = None

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__all__ = [
    "PedagogyEngine",
    "Guardrails",
    "RiskAssessment",
    "RiskLevel",
    "RiskType",
    "LanguageShaper",
    "TemplateLibrary",
]

# Add audit components if available
if AuditRiskLevel is not None:
    __all__.extend(["PedagogyLogger", "AuditRiskLevel"])


class PedagogyEngine:
    """
    Pedagogical middleware engine.

    Processes raw LLM responses through:
    1. Guardrails (risk detection)
    2. Language Shaper (empowerment rewriting)
    3. Templates (safe fallbacks if needed)

    Returns pedagogically aligned, safe responses.
    """

    def __init__(
        self,
        language: str = "tr",
        school_counselor_name: str = "your school counselor",
        enable_audit_logging: bool = True
    ):
        """
        Initialize PedagogyEngine.

        Args:
            language: Language code ("tr" for Turkish, "en" for English)
            school_counselor_name: Name of school counselor for intervention messages
            enable_audit_logging: Enable audit logging for KCSIE compliance (default: True)
        """
        self.guardrails = Guardrails(school_counselor_name=school_counselor_name)
        self.shaper = LanguageShaper()
        self.templates = TemplateLibrary()
        self.language = language
        self.audit_logger = None
        if enable_audit_logging:
            try:
                self.audit_logger = PedagogyLogger()
            except Exception as e:
                logger.warning(f"PedagogyEngine: Failed to initialize audit logger: {e}")

    def process(
        self,
        raw_response: str,
        physics_state: dict,
        force_safe: bool = False,
        actor_ref: Optional[str] = None,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        tenant_ref: Optional[str] = None,  # SPRINT 5: Replaced school_id with tenant_ref (core-neutral)
        class_id: Optional[str] = None
    ) -> dict:
        """
        Process raw LLM response through pedagogical pipeline.

        Args:
            raw_response: Raw LLM draft response
            physics_state: Current physics state (phi, entropy, etc.)
            force_safe: Force safe template even if no risk detected (for testing)
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            tenant_ref: Tenant reference (core-neutral identifier, replaces school_id)
            class_id: Class identifier (optional)

        Returns:
            Dictionary with:
                - safe_response: Processed, safe response text
                - risk_assessment: Risk assessment result
                - was_reshaped: Whether language was reshaped
                - used_template: Whether fallback template was used
        """
        if not raw_response or not raw_response.strip():
            # Empty response → use safe template
            safe_response = self.templates.get_fallback(self.language)
            return {
                "safe_response": safe_response,
                "risk_assessment": {
                    "risk_level": "safe",
                    "risk_type": "none",
                    "intervention_required": False
                },
                "was_reshaped": False,
                "used_template": True
            }

        # Step 1: Risk Assessment (Guardrails) - UK Schools 3-Level System
        risk_assessment = self.guardrails.assess_risk(raw_response)

        # Step 2: Level 1 (CRITICAL) - Immediate Block with Intervention Protocol
        if risk_assessment.risk_level.value == "critical":
            logger.warning(f"PedagogyEngine: Level 1 (CRITICAL) risk detected: {risk_assessment.risk_type.value}")
            # Use intervention message from guardrails
            safe_response = risk_assessment.intervention_message or self.templates.get_template(
                risk_type=risk_assessment.risk_type.value,
                language=self.language,
                physics_state=physics_state
            )

            # Log intervention for KCSIE compliance
            if self.audit_logger and actor_ref:
                self.audit_logger.log_intervention(
                    actor_ref=actor_ref,  # SPRINT 5: Use actor_ref
                    trigger_text=raw_response,
                    risk_level=AuditRiskLevel.LEVEL_1,
                    action_taken="blocked_intervention_protocol",
                    physics_snapshot=physics_state,
                    tenant_ref=tenant_ref,  # SPRINT 5: Use tenant_ref
                    class_id=class_id
                )

            return {
                "safe_response": safe_response,
                "risk_assessment": risk_assessment.to_dict(),
                "was_reshaped": False,
                "used_template": True,
                "intervention_triggered": True
            }

        # Step 3: Level 2 (WARNING) - Tag for Reframing
        # If negative self-talk detected, reshape with empowerment language
        if risk_assessment.needs_reframing:
            logger.info("PedagogyEngine: Level 2 (WARNING) - Negative self-talk detected, reframing")

            # Log intervention for KCSIE compliance
            if self.audit_logger and actor_ref:
                self.audit_logger.log_intervention(
                    actor_ref=actor_ref,  # SPRINT 5: Use actor_ref
                    trigger_text=raw_response,
                    risk_level=AuditRiskLevel.LEVEL_2,
                    action_taken="reframed_negative_self_talk",
                    physics_snapshot=physics_state,
                    tenant_ref=tenant_ref,  # SPRINT 5: Use tenant_ref
                    class_id=class_id
                )

            reshaped_response = self.shaper.reshape(raw_response, physics_state)
            was_reshaped = True

            # Re-check reshaped response for safety
            final_assessment = self.guardrails.assess_risk(reshaped_response)
            if final_assessment.risk_level.value == "critical":
                # Reshaping didn't help, use intervention
                safe_response = final_assessment.intervention_message or self.templates.get_template(
                    risk_type=final_assessment.risk_type.value,
                    language=self.language,
                    physics_state=physics_state
                )
                return {
                    "safe_response": safe_response,
                    "risk_assessment": final_assessment.to_dict(),
                    "was_reshaped": False,
                    "used_template": True,
                    "intervention_triggered": True
                }

            return {
                "safe_response": reshaped_response,
                "risk_assessment": final_assessment.to_dict(),
                "was_reshaped": True,
                "used_template": False,
                "intervention_triggered": False
            }

        # Step 4: Level 3 (SAFE) - Standard Language Shaping (optional)
        reshaped_response = self.shaper.reshape(raw_response, physics_state)
        was_reshaped = reshaped_response != raw_response

        # Step 5: Final risk check on reshaped response (Level 3 safety check)
        final_assessment = self.guardrails.assess_risk(reshaped_response)

        # If reshaping introduced Level 1 risk (shouldn't happen, but safety first)
        if final_assessment.risk_level.value == "critical":
            logger.warning("PedagogyEngine: Reshaped response has Level 1 risk, using intervention")
            safe_response = final_assessment.intervention_message or self.templates.get_template(
                risk_type=final_assessment.risk_type.value,
                language=self.language,
                physics_state=physics_state
            )
            return {
                "safe_response": safe_response,
                "risk_assessment": final_assessment.to_dict(),
                "was_reshaped": False,
                "used_template": True,
                "intervention_triggered": True
            }

        # Return reshaped, safe response (Level 3 - Safe)
        return {
            "safe_response": reshaped_response,
            "risk_assessment": final_assessment.to_dict(),
            "was_reshaped": was_reshaped,
            "used_template": False,
            "intervention_triggered": False
        }

    def quick_check(self, text: str) -> bool:
        """
        Quick check if text requires intervention.

        Args:
            text: Text to check

        Returns:
            True if intervention is required
        """
        return self.guardrails.requires_intervention(text)

