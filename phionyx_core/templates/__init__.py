"""
Response Templates Package
===========================

Provides template-based responses for common intents to reduce LLM calls.
"""

from phionyx_core.templates.response_templates import (
    IntentType,
    ResponseTemplate,
    TemplateManager,
    get_template_manager,
)

__all__ = [
    'ResponseTemplate',
    'TemplateManager',
    'get_template_manager',
    'IntentType',
]

