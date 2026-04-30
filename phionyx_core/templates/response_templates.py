"""
Response Templates - Template-Based Response System
====================================================

Provides template-based responses for common intents to reduce LLM calls
and improve latency for simple queries.

Features:
- Intent-based template selection
- Entropy-based template eligibility
- Template metrics
- Configurable templates
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Intent types for template matching."""
    GREETING = "greeting"
    QUESTION = "question"
    COMMAND = "command"
    CONVERSATION = "conversation"
    HIGH_RISK = "high_risk"
    UNKNOWN = "unknown"


@dataclass
class ResponseTemplate:
    """Response template definition."""
    intent: IntentType
    template: str
    min_entropy: float = 0.0
    max_entropy: float = 0.5
    variables: list[str] | None = None

    def render(self, **kwargs: Any) -> str:
        """
        Render template with variables.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered template string
        """
        result = self.template
        if self.variables:
            for var in self.variables:
                value = kwargs.get(var, "")
                result = result.replace(f"{{{var}}}", str(value))
        return result


class TemplateManager:
    """
    Manages response templates and template selection logic.

    Features:
    - Intent-based template selection
    - Entropy-based eligibility check
    - Template metrics
    """

    def __init__(self):
        """Initialize template manager with default templates."""
        self._templates: dict[IntentType, list[ResponseTemplate]] = {}
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        """Initialize default templates."""
        # Greeting templates
        greeting_templates = [
            ResponseTemplate(
                intent=IntentType.GREETING,
                template="Merhaba! Size nasıl yardımcı olabilirim?",
                min_entropy=0.0,
                max_entropy=0.3
            ),
            ResponseTemplate(
                intent=IntentType.GREETING,
                template="Selam! Bugün nasılsınız?",
                min_entropy=0.0,
                max_entropy=0.3
            ),
            ResponseTemplate(
                intent=IntentType.GREETING,
                template="Hoş geldiniz! Ne yapmak istersiniz?",
                min_entropy=0.0,
                max_entropy=0.3
            ),
        ]
        self._templates[IntentType.GREETING] = greeting_templates

        # Error templates
        error_templates = [
            ResponseTemplate(
                intent=IntentType.UNKNOWN,
                template="Üzgünüm, bunu anlayamadım. Lütfen tekrar deneyin.",
                min_entropy=0.0,
                max_entropy=0.4
            ),
            ResponseTemplate(
                intent=IntentType.UNKNOWN,
                template="Anlamadım. Daha açık bir şekilde ifade edebilir misiniz?",
                min_entropy=0.0,
                max_entropy=0.4
            ),
        ]
        self._templates[IntentType.UNKNOWN] = error_templates

        # Confirmation templates
        confirmation_templates = [
            ResponseTemplate(
                intent=IntentType.COMMAND,
                template="İşlem onaylandı.",
                min_entropy=0.0,
                max_entropy=0.3
            ),
            ResponseTemplate(
                intent=IntentType.COMMAND,
                template="Tamam, yapıldı.",
                min_entropy=0.0,
                max_entropy=0.3
            ),
        ]
        self._templates[IntentType.COMMAND] = confirmation_templates

    def add_template(self, template: ResponseTemplate) -> None:
        """
        Add custom template.

        Args:
            template: ResponseTemplate instance
        """
        if template.intent not in self._templates:
            self._templates[template.intent] = []
        self._templates[template.intent].append(template)
        logger.info(f"Added template for intent: {template.intent}")

    def get_template(
        self,
        intent: IntentType,
        entropy: float,
        **kwargs: Any
    ) -> str | None:
        """
        Get template response for intent and entropy level.

        Args:
            intent: Intent type
            entropy: Current entropy value
            **kwargs: Template variables

        Returns:
            Template response if eligible, None otherwise
        """
        self._metrics["total_requests"] += 1

        # Check if templates exist for this intent
        if intent not in self._templates:
            self._metrics["misses"] += 1
            return None

        # Find eligible template (entropy within range)
        eligible_templates = [
            t for t in self._templates[intent]
            if t.min_entropy <= entropy <= t.max_entropy
        ]

        if not eligible_templates:
            self._metrics["misses"] += 1
            return None

        # Select first eligible template (can be randomized later)
        template = eligible_templates[0]

        # Render template
        response = template.render(**kwargs)

        self._metrics["hits"] += 1
        logger.debug(f"Template hit: intent={intent}, entropy={entropy:.2f}")

        return response

    def is_eligible(
        self,
        intent: IntentType,
        entropy: float
    ) -> bool:
        """
        Check if template is eligible for intent and entropy.

        Args:
            intent: Intent type
            entropy: Current entropy value

        Returns:
            True if template is eligible, False otherwise
        """
        if intent not in self._templates:
            return False

        eligible_templates = [
            t for t in self._templates[intent]
            if t.min_entropy <= entropy <= t.max_entropy
        ]

        return len(eligible_templates) > 0

    def get_metrics(self) -> dict[str, Any]:
        """
        Get template metrics.

        Returns:
            Dictionary with template statistics
        """
        total = self._metrics["total_requests"]
        hit_rate = (self._metrics["hits"] / total * 100) if total > 0 else 0.0

        return {
            "hits": self._metrics["hits"],
            "misses": self._metrics["misses"],
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2)
        }

    def reset_metrics(self) -> None:
        """Reset metrics."""
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }


# Global template manager instance (singleton pattern)
_global_template_manager: TemplateManager | None = None


def get_template_manager() -> TemplateManager:
    """
    Get or create global template manager instance.

    Returns:
        Global TemplateManager instance
    """
    global _global_template_manager

    if _global_template_manager is None:
        _global_template_manager = TemplateManager()
        logger.info("Template manager initialized")

    return _global_template_manager


def reset_global_template_manager() -> None:
    """Reset global template manager instance (for testing)."""
    global _global_template_manager
    _global_template_manager = None

