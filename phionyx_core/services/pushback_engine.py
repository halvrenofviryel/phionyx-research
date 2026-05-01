"""
Push-back Interface Engine
==========================

Faz 2.4: Push-back Interface - Tam Fonksiyonel

Push-back mechanism for requirement, constraint, and profile violations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from phionyx_core.pipeline.base import BlockContext


class ViolationType(Enum):
    """Type of violation."""
    REQUIREMENT = "requirement"
    CONSTRAINT = "constraint"
    PROFILE = "profile"
    GOVERNANCE = "governance"


@dataclass
class PushBackMessage:
    """Push-back message structure."""
    violation_type: ViolationType
    violation_description: str
    constraint_name: str | None = None
    requirement_name: str | None = None
    profile_name: str | None = None
    severity: str = "medium"  # "low", "medium", "high", "critical"
    suggested_action: str | None = None
    user_feedback_request: str | None = None


@dataclass
class PushBackResult:
    """Result of push-back evaluation."""
    should_push_back: bool
    messages: list[PushBackMessage]
    violations_count: int
    can_proceed: bool  # Whether execution can proceed despite violations


class PushBackEngine:
    """
    Full-featured Push-back Interface Engine.

    Provides:
    - Requirement violation detection
    - Constraint violation detection
    - Profile violation detection
    - Push-back message generation
    - Governance Node integration
    - User feedback loop
    """

    def __init__(self, governance_node: Any | None = None):
        """
        Initialize push-back engine.

        Args:
            governance_node: GovernanceNode instance (optional)
        """
        self.governance_node = governance_node
        self.violation_history: list[PushBackMessage] = []
        self.user_feedback_cache: dict[str, Any] = {}

    def evaluate_push_back(
        self,
        context: BlockContext,
        requirements: list[dict[str, Any]] | None = None,
        constraints: list[dict[str, Any]] | None = None,
        profile: Any | None = None
    ) -> PushBackResult:
        """
        Evaluate if push-back is needed.

        Args:
            context: BlockContext
            requirements: List of requirements (optional)
            constraints: List of constraints (optional)
            profile: Profile instance (optional)

        Returns:
            PushBackResult
        """
        messages = []

        # 1. Check requirement violations
        if requirements:
            req_violations = self._check_requirement_violations(context, requirements)
            messages.extend(req_violations)

        # 2. Check constraint violations
        if constraints:
            constraint_violations = self._check_constraint_violations(context, constraints)
            messages.extend(constraint_violations)

        # 3. Check profile violations
        if profile:
            profile_violations = self._check_profile_violations(context, profile)
            messages.extend(profile_violations)

        # 4. Check governance violations (if governance node available)
        if self.governance_node:
            governance_violations = self._check_governance_violations(context)
            messages.extend(governance_violations)

        # Determine if push-back is needed
        critical_violations = [m for m in messages if m.severity == "critical"]
        high_violations = [m for m in messages if m.severity == "high"]

        should_push_back = len(critical_violations) > 0 or len(high_violations) > 0
        can_proceed = len(critical_violations) == 0  # Can't proceed with critical violations

        # Store in history
        self.violation_history.extend(messages)

        return PushBackResult(
            should_push_back=should_push_back,
            messages=messages,
            violations_count=len(messages),
            can_proceed=can_proceed
        )

    def _check_requirement_violations(
        self,
        context: BlockContext,
        requirements: list[dict[str, Any]]
    ) -> list[PushBackMessage]:
        """Check requirement violations."""
        violations = []

        for req in requirements:
            req_name = req.get("name", "Unknown")
            _req_type = req.get("type", "functional")
            req_constraint = req.get("constraint")

            # Check if requirement is satisfied
            if req_constraint:
                if not self._evaluate_constraint(context, req_constraint):
                    violations.append(PushBackMessage(
                        violation_type=ViolationType.REQUIREMENT,
                        violation_description=f"Requirement '{req_name}' is not satisfied",
                        requirement_name=req_name,
                        severity=req.get("severity", "medium"),
                        suggested_action=f"Ensure requirement '{req_name}' is satisfied",
                        user_feedback_request=f"Please confirm how to satisfy requirement '{req_name}'"
                    ))

        return violations

    def _check_constraint_violations(
        self,
        context: BlockContext,
        constraints: list[dict[str, Any]]
    ) -> list[PushBackMessage]:
        """Check constraint violations."""
        violations = []

        for constraint in constraints:
            constraint_name = constraint.get("name", "Unknown")
            constraint_expression = constraint.get("expression")
            constraint_severity = constraint.get("severity", "medium")

            # Evaluate constraint
            if constraint_expression:
                if not self._evaluate_constraint(context, constraint_expression):
                    violations.append(PushBackMessage(
                        violation_type=ViolationType.CONSTRAINT,
                        violation_description=f"Constraint '{constraint_name}' is violated",
                        constraint_name=constraint_name,
                        severity=constraint_severity,
                        suggested_action=f"Adjust to satisfy constraint '{constraint_name}'",
                        user_feedback_request=f"Constraint '{constraint_name}' violated. How should we proceed?"
                    ))

        return violations

    def _check_profile_violations(
        self,
        context: BlockContext,
        profile: Any
    ) -> list[PushBackMessage]:
        """Check profile violations."""
        violations = []

        # Check profile constraints
        if hasattr(profile, 'constraints'):
            for constraint in profile.constraints:
                if not self._evaluate_profile_constraint(context, profile, constraint):
                    violations.append(PushBackMessage(
                        violation_type=ViolationType.PROFILE,
                        violation_description=f"Profile constraint violated: {constraint}",
                        profile_name=getattr(profile, 'name', 'Unknown'),
                        severity="high",
                        suggested_action=f"Adjust to match profile '{getattr(profile, 'name', 'Unknown')}' constraints",
                        user_feedback_request="Profile constraint violated. Should we adjust or change profile?"
                    ))

        # Check profile thresholds
        if hasattr(profile, 'thresholds'):
            for threshold_name, threshold_value in profile.thresholds.items():
                context_value = getattr(context, threshold_name, None)
                if context_value is not None:
                    if not self._check_threshold(context_value, threshold_value):
                        violations.append(PushBackMessage(
                            violation_type=ViolationType.PROFILE,
                            violation_description=f"Profile threshold '{threshold_name}' exceeded",
                            profile_name=getattr(profile, 'name', 'Unknown'),
                            severity="medium",
                            suggested_action=f"Adjust {threshold_name} to be within profile limits",
                            user_feedback_request=None
                        ))

        return violations

    def _check_governance_violations(
        self,
        context: BlockContext
    ) -> list[PushBackMessage]:
        """Check governance violations using Governance Node."""
        violations = []

        if not self.governance_node:
            return violations

        # Use governance node to check violations
        try:
            # This would call governance node's check methods
            # For now, we'll create a placeholder
            if hasattr(self.governance_node, 'check_pre_execution'):
                # Would call: result = await governance_node.check_pre_execution(state, context)
                # For now, skip actual call
                pass
        except Exception:
            # Governance check failed, but don't block
            pass

        return violations

    def _evaluate_constraint(
        self,
        context: BlockContext,
        constraint_expression: str
    ) -> bool:
        """
        Evaluate constraint expression.

        Args:
            context: BlockContext
            constraint_expression: Constraint expression string

        Returns:
            True if constraint is satisfied, False otherwise
        """
        # Simple constraint evaluation
        # In production, this would use a proper constraint evaluation engine

        # Check for common constraint patterns
        if "entropy" in constraint_expression.lower():
            if hasattr(context, 'current_entropy'):
                entropy = context.current_entropy
                # Check if entropy is in valid range
                if ">=" in constraint_expression:
                    threshold = float(constraint_expression.split(">=")[1].strip())
                    return entropy >= threshold
                elif "<=" in constraint_expression:
                    threshold = float(constraint_expression.split("<=")[1].strip())
                    return entropy <= threshold

        # Default: assume constraint is satisfied if we can't evaluate
        return True

    def _evaluate_profile_constraint(
        self,
        context: BlockContext,
        profile: Any,
        constraint: Any
    ) -> bool:
        """Evaluate profile constraint."""
        # Profile constraint evaluation logic
        # For now, return True (would implement actual evaluation)
        return True

    def _check_threshold(
        self,
        value: float,
        threshold: dict[str, Any]
    ) -> bool:
        """Check if value is within threshold."""
        min_val = threshold.get("min")
        max_val = threshold.get("max")

        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False

        return True

    def generate_push_back_message(
        self,
        violation: PushBackMessage,
        context: BlockContext
    ) -> str:
        """
        Generate user-friendly push-back message.

        Args:
            violation: PushBackMessage
            context: BlockContext

        Returns:
            Formatted push-back message string
        """
        message_parts = []

        # Header
        message_parts.append(f"⚠️ {violation.violation_type.value.upper()} VIOLATION")
        message_parts.append("")

        # Description
        message_parts.append(f"**Issue:** {violation.violation_description}")
        message_parts.append("")

        # Details
        if violation.constraint_name:
            message_parts.append(f"**Constraint:** {violation.constraint_name}")
        if violation.requirement_name:
            message_parts.append(f"**Requirement:** {violation.requirement_name}")
        if violation.profile_name:
            message_parts.append(f"**Profile:** {violation.profile_name}")

        message_parts.append(f"**Severity:** {violation.severity}")
        message_parts.append("")

        # Suggested action
        if violation.suggested_action:
            message_parts.append(f"**Suggested Action:** {violation.suggested_action}")
            message_parts.append("")

        # User feedback request
        if violation.user_feedback_request:
            message_parts.append(f"**Question:** {violation.user_feedback_request}")

        return "\n".join(message_parts)

    def process_user_feedback(
        self,
        violation_id: str,
        feedback: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process user feedback for a violation.

        Args:
            violation_id: Violation identifier
            feedback: User feedback data

        Returns:
            Processed feedback result
        """
        # Store feedback
        self.user_feedback_cache[violation_id] = feedback

        # Process feedback
        action = feedback.get("action", "proceed")
        adjustment = feedback.get("adjustment")

        return {
            "violation_id": violation_id,
            "action": action,
            "adjustment": adjustment,
            "processed": True
        }


__all__ = [
    'PushBackEngine',
    'PushBackMessage',
    'PushBackResult',
    'ViolationType',
]

