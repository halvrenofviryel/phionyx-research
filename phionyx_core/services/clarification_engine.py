"""
Clarification Request Engine
============================

Faz 3.1: Kalan Özellikler

Confusion yönetimi için clarification request prompting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConfusionType(Enum):
    """Type of confusion."""
    AMBIGUOUS_REQUIREMENT = "ambiguous_requirement"
    UNCLEAR_CONTEXT = "unclear_context"
    MISSING_INFORMATION = "missing_information"
    CONFLICTING_REQUIREMENTS = "conflicting_requirements"
    UNCERTAIN_APPROACH = "uncertain_approach"


@dataclass
class ClarificationRequest:
    """Clarification request structure."""
    id: str
    type: ConfusionType
    question: str
    context: str
    priority: str = "medium"  # "low", "medium", "high", "critical"
    suggested_options: list[str] = None

    def __post_init__(self):
        if self.suggested_options is None:
            self.suggested_options = []


class ClarificationRequestEngine:
    """
    Full-featured Clarification Request Engine.

    Provides:
    - Confusion detection
    - Clarification question generation
    - User feedback processing
    """

    def __init__(self):
        """Initialize clarification engine."""
        self.request_history: list[ClarificationRequest] = []

    def detect_confusion(
        self,
        user_input: str,
        context: dict[str, Any] | None = None
    ) -> list[ClarificationRequest]:
        """
        Detect confusion points and generate clarification requests.

        Args:
            user_input: User input text
            context: Additional context (optional)

        Returns:
            List of ClarificationRequest
        """
        requests = []

        # Check for ambiguous requirements
        if self._is_ambiguous(user_input):
            requests.append(ClarificationRequest(
                id=f"clar_{len(self.request_history)}",
                type=ConfusionType.AMBIGUOUS_REQUIREMENT,
                question="Could you clarify what you mean by this requirement?",
                context=user_input,
                priority="high",
                suggested_options=self._generate_clarification_options(user_input)
            ))

        # Check for missing information
        missing_info = self._detect_missing_information(user_input, context)
        if missing_info:
            requests.append(ClarificationRequest(
                id=f"clar_{len(self.request_history) + len(requests)}",
                type=ConfusionType.MISSING_INFORMATION,
                question=f"Could you provide more information about: {missing_info}?",
                context=user_input,
                priority="medium",
                suggested_options=[]
            ))

        # Check for conflicting requirements
        if self._has_conflicting_requirements(user_input):
            requests.append(ClarificationRequest(
                id=f"clar_{len(self.request_history) + len(requests)}",
                type=ConfusionType.CONFLICTING_REQUIREMENTS,
                question="I notice some conflicting requirements. Which one should take priority?",
                context=user_input,
                priority="high",
                suggested_options=[]
            ))

        # Store in history
        self.request_history.extend(requests)

        return requests

    def _is_ambiguous(self, text: str) -> bool:
        """Check if text is ambiguous."""
        ambiguous_indicators = [
            "maybe", "perhaps", "possibly", "might", "could",
            "not sure", "unclear", "vague", "ambiguous"
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in ambiguous_indicators)

    def _detect_missing_information(
        self,
        user_input: str,
        context: dict[str, Any] | None = None
    ) -> str | None:
        """Detect missing information."""
        # Check for common missing information patterns
        missing_patterns = [
            ("what", "What specific functionality?"),
            ("how", "How should it work?"),
            ("when", "When should it be done?"),
            ("where", "Where should it be implemented?"),
        ]

        # Simple heuristic: if question words are used, might need clarification
        for pattern, message in missing_patterns:
            if pattern in user_input.lower() and "?" in user_input:
                return message

        return None

    def _has_conflicting_requirements(self, text: str) -> bool:
        """Check for conflicting requirements."""
        conflict_indicators = [
            "but", "however", "although", "on the other hand",
            "contradict", "conflict", "opposite"
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in conflict_indicators)

    def _generate_clarification_options(self, text: str) -> list[str]:
        """Generate clarification options."""
        options = [
            "Could you provide more details?",
            "Could you give an example?",
            "Could you specify the requirements?",
        ]
        return options

    def process_clarification_response(
        self,
        request_id: str,
        response: str
    ) -> dict[str, Any]:
        """
        Process user clarification response.

        Args:
            request_id: Clarification request ID
            response: User response

        Returns:
            Processed response data
        """
        # Find request
        request = None
        for req in self.request_history:
            if req.id == request_id:
                request = req
                break

        if not request:
            return {"error": "Request not found"}

        return {
            "request_id": request_id,
            "request_type": request.type.value,
            "response": response,
            "processed": True
        }


__all__ = [
    'ClarificationRequestEngine',
    'ClarificationRequest',
    'ConfusionType',
]

