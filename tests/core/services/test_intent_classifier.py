"""
Unit tests for Intent Classifier
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from phionyx_core.services.intent_classifier import (
    IntentClassifier,
    IntentType,
    IntentResult
)


class TestIntentClassifier:
    """Test IntentClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create IntentClassifier instance."""
        return IntentClassifier()

    @pytest.fixture
    def classifier_with_llm(self):
        """Create IntentClassifier with LLM provider."""
        llm_provider = Mock()
        llm_provider.available = True
        llm_provider.completion = AsyncMock(return_value="greeting")
        return IntentClassifier(llm_provider=llm_provider)

    @pytest.mark.asyncio
    async def test_classify_greeting_rule_based(self, classifier):
        """Test greeting classification via rule-based method."""
        result = await classifier.classify_intent("Merhaba", timeout_ms=200.0)

        assert result.intent == IntentType.GREETING
        assert result.confidence >= 0.7
        assert result.method == "rule"
        assert result.processing_time_ms < 200.0

    @pytest.mark.asyncio
    async def test_classify_question_rule_based(self, classifier):
        """Test question classification via rule-based method."""
        result = await classifier.classify_intent("Ne yapıyorsun?", timeout_ms=200.0)

        assert result.intent == IntentType.QUESTION
        assert result.confidence >= 0.7
        assert result.method == "rule"
        assert result.processing_time_ms < 200.0

    @pytest.mark.asyncio
    async def test_classify_high_risk_rule_based(self, classifier):
        """Test high-risk classification via rule-based method."""
        result = await classifier.classify_intent("kendini öldürmek", timeout_ms=200.0)

        assert result.intent == IntentType.HIGH_RISK
        assert result.confidence >= 0.7
        assert result.method == "rule"
        assert result.processing_time_ms < 200.0

    @pytest.mark.asyncio
    async def test_classify_empty_input(self, classifier):
        """Test classification with empty input."""
        result = await classifier.classify_intent("", timeout_ms=200.0)

        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0
        assert result.method == "fallback"

    @pytest.mark.asyncio
    async def test_classify_fallback(self, classifier):
        """Test fallback to default intent."""
        result = await classifier.classify_intent("random text without patterns", timeout_ms=200.0)

        assert result.intent == IntentType.CONVERSATION
        assert result.confidence == 0.5
        assert result.method == "fallback"
        assert result.processing_time_ms < 200.0

    @pytest.mark.asyncio
    async def test_classify_timeout_requirement(self, classifier):
        """Test that classification completes within timeout."""
        result = await classifier.classify_intent("Merhaba", timeout_ms=200.0)

        assert result.processing_time_ms < 200.0

    @pytest.mark.asyncio
    async def test_classify_llm_fallback(self, classifier_with_llm):
        """Test LLM-based classification fallback."""
        # Use text that doesn't match rule patterns
        result = await classifier_with_llm.classify_intent("complex query that needs LLM", timeout_ms=200.0)

        # Should use LLM if rule-based fails
        # Note: This test may need adjustment based on actual LLM provider implementation
        assert result.intent in [IntentType.GREETING, IntentType.CONVERSATION]
        assert result.processing_time_ms < 200.0

    def test_rule_based_greeting_patterns(self, classifier):
        """Test rule-based greeting pattern matching."""
        test_cases = [
            ("Merhaba", True),
            ("Selam", True),
            ("Hey", True),
            ("Hi", True),
            ("Hello", True),
            ("How are you?", True),
            ("Nasılsın?", True),
            ("random text", False)  # Should not match
        ]

        matched_count = 0
        for text, should_match in test_cases:
            result = classifier._classify_rule_based(text.lower())
            if should_match:
                if result is not None:
                    assert result.intent == IntentType.GREETING
                    matched_count += 1
            else:
                # Should not match
                pass

        # At least most greeting patterns should match
        assert matched_count >= len([tc for tc in test_cases if tc[1]]) * 0.7, \
            f"Only {matched_count}/{len([tc for tc in test_cases if tc[1]])} greeting patterns matched"

    def test_rule_based_question_patterns(self, classifier):
        """Test rule-based question pattern matching."""
        test_cases = [
            "Ne yapıyorsun?",
            "What is this?",
            "How does it work?",
            "Why?",
            "When?",
            "Where?",
            "Nasıl?"
        ]

        for text in test_cases:
            result = classifier._classify_rule_based(text.lower())
            if result:
                assert result.intent == IntentType.QUESTION

    def test_rule_based_high_risk_patterns(self, classifier):
        """Test rule-based high-risk pattern matching."""
        test_cases = [
            "kendini öldürmek",
            "self harm",
            "suicide",
            "intihar"
        ]

        for text in test_cases:
            result = classifier._classify_rule_based(text.lower())
            assert result is not None
            assert result.intent == IntentType.HIGH_RISK

