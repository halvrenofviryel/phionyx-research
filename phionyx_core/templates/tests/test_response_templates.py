"""
Unit tests for Response Templates
"""
import pytest
from phionyx_core.templates.response_templates import (
    ResponseTemplate,
    TemplateManager,
    IntentType,
    get_template_manager,
    reset_global_template_manager
)


class TestResponseTemplate:
    """Test ResponseTemplate."""

    def test_template_creation(self):
        """Test template creation."""
        template = ResponseTemplate(
            intent=IntentType.GREETING,
            template="Hello {name}!",
            min_entropy=0.0,
            max_entropy=0.3,
            variables=["name"]
        )

        assert template.intent == IntentType.GREETING
        assert template.template == "Hello {name}!"
        assert template.min_entropy == 0.0
        assert template.max_entropy == 0.3

    def test_template_render(self):
        """Test template rendering."""
        template = ResponseTemplate(
            intent=IntentType.GREETING,
            template="Hello {name}!",
            variables=["name"]
        )

        result = template.render(name="World")
        assert result == "Hello World!"

    def test_template_render_no_variables(self):
        """Test template rendering without variables."""
        template = ResponseTemplate(
            intent=IntentType.GREETING,
            template="Hello World!"
        )

        result = template.render()
        assert result == "Hello World!"


class TestTemplateManager:
    """Test TemplateManager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = TemplateManager()

        # Check default templates are loaded
        assert IntentType.GREETING in manager._templates
        assert IntentType.UNKNOWN in manager._templates
        assert IntentType.COMMAND in manager._templates

    def test_get_template_greeting(self):
        """Test getting greeting template."""
        manager = TemplateManager()

        # Low entropy greeting should match
        response = manager.get_template(IntentType.GREETING, entropy=0.2)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_get_template_high_entropy(self):
        """Test template with high entropy (should not match)."""
        manager = TemplateManager()

        # High entropy greeting should not match (max_entropy=0.3)
        response = manager.get_template(IntentType.GREETING, entropy=0.5)

        assert response is None

    def test_get_template_unknown_intent(self):
        """Test template for unknown intent."""
        manager = TemplateManager()

        # Unknown intent should not have templates (yet)
        response = manager.get_template(IntentType.QUESTION, entropy=0.2)

        assert response is None

    def test_is_eligible(self):
        """Test eligibility check."""
        manager = TemplateManager()

        # Low entropy greeting should be eligible
        assert manager.is_eligible(IntentType.GREETING, entropy=0.2) is True

        # High entropy greeting should not be eligible
        assert manager.is_eligible(IntentType.GREETING, entropy=0.5) is False

        # Unknown intent should not be eligible
        assert manager.is_eligible(IntentType.QUESTION, entropy=0.2) is False

    def test_add_template(self):
        """Test adding custom template."""
        manager = TemplateManager()

        custom_template = ResponseTemplate(
            intent=IntentType.QUESTION,
            template="I don't know.",
            min_entropy=0.0,
            max_entropy=0.4
        )

        manager.add_template(custom_template)

        # Should now be able to get template
        response = manager.get_template(IntentType.QUESTION, entropy=0.2)
        assert response == "I don't know."

    def test_metrics(self):
        """Test template metrics."""
        manager = TemplateManager()

        # Make some requests
        manager.get_template(IntentType.GREETING, entropy=0.2)  # Hit
        manager.get_template(IntentType.GREETING, entropy=0.5)  # Miss
        manager.get_template(IntentType.QUESTION, entropy=0.2)  # Miss

        metrics = manager.get_metrics()

        assert metrics["hits"] == 1
        assert metrics["misses"] == 2
        assert metrics["total_requests"] == 3
        assert metrics["hit_rate_percent"] == pytest.approx(33.33, abs=0.1)

    def test_reset_metrics(self):
        """Test metrics reset."""
        manager = TemplateManager()

        manager.get_template(IntentType.GREETING, entropy=0.2)
        manager.reset_metrics()

        metrics = manager.get_metrics()
        assert metrics["hits"] == 0
        assert metrics["misses"] == 0
        assert metrics["total_requests"] == 0


class TestGlobalTemplateManager:
    """Test global template manager functions."""

    def test_get_template_manager_singleton(self):
        """Test global manager is singleton."""
        reset_global_template_manager()

        manager1 = get_template_manager()
        manager2 = get_template_manager()

        assert manager1 is manager2

    def test_reset_global_template_manager(self):
        """Test reset global manager."""
        manager1 = get_template_manager()
        reset_global_template_manager()
        manager2 = get_template_manager()

        assert manager1 is not manager2

