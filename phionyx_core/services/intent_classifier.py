"""
Intent Classifier Service
==========================

Fast intent classification service with multiple fallback strategies.

Features:
- Rule-based classification (primary, <50ms)
- Embedding-based classification (fast path, <100ms)
- LLM-based classification (fallback, <200ms max)
- Fallback to default intent on failure
"""

import logging
import math
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Intent types."""
    GREETING = "greeting"
    QUESTION = "question"
    COMMAND = "command"
    CONVERSATION = "conversation"
    HIGH_RISK = "high_risk"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Intent classification result."""
    intent: IntentType
    confidence: float
    method: str  # "rule", "embedding", "llm", "fallback"
    processing_time_ms: float


class IntentClassifier:
    """
    Intent classifier with fast path requirement (<200ms).

    Uses multiple strategies:
    1. Rule-based (primary, fastest)
    2. Embedding-based (fast path)
    3. LLM-based (fallback, small model only)
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        embedding_cache: Any | None = None
    ):
        """
        Initialize intent classifier.

        Args:
            llm_provider: Optional LLM provider (for fallback only)
            embedding_cache: Optional embedding cache (for fast path)
        """
        self.llm_provider = llm_provider
        self.embedding_cache = embedding_cache

        # Rule-based patterns
        self._greeting_patterns = [
            r'\b(merhaba|selam|hey|hi|hello|hey|günaydın|iyi günler|iyi akşamlar)\b',
            r'\b(how are you|nasılsın|nasılsınız|naber|ne haber)\b',
        ]

        self._question_patterns = [
            r'\?',  # Contains question mark
            r'\b(ne|what|how|why|when|where|kim|nasıl|neden|ne zaman|nerede)\b',
            r'\b(soru|question|ask)\b',
        ]

        self._command_patterns = [
            r'\b(yap|do|make|create|build|run|execute|start|stop|delete|remove)\b',
            r'\b(komut|command|action)\b',
        ]

        self._high_risk_patterns = [
            r'\b(kendini|self|harm|hurt|kill|suicide|özkıyım|intihar)\b',
            r'\b(violence|şiddet|violence|attack|saldırı)\b',
            r'\b(drug|drugs|uyuşturucu|illegal|yasadışı)\b',
        ]

    async def classify_intent(
        self,
        user_input: str,
        timeout_ms: float = 200.0
    ) -> IntentResult:
        """
        Classify user intent with fast path requirement.

        Args:
            user_input: User input text
            timeout_ms: Maximum processing time in milliseconds (default: 200ms)

        Returns:
            IntentResult with intent, confidence, method, and processing time
        """
        start_time = time.time()

        # Normalize input
        normalized_input = user_input.strip().lower()

        if not normalized_input:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                method="fallback",
                processing_time_ms=(time.time() - start_time) * 1000
            )

        # Strategy 1: Rule-based classification (fastest, <50ms)
        try:
            rule_result = self._classify_rule_based(normalized_input)
            if rule_result and rule_result.confidence >= 0.7:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms < timeout_ms:
                    logger.debug(f"Intent classified via rule-based: {rule_result.intent.value} (confidence={rule_result.confidence:.2f}, time={elapsed_ms:.2f}ms)")
                    return IntentResult(
                        intent=rule_result.intent,
                        confidence=rule_result.confidence,
                        method="rule",
                        processing_time_ms=elapsed_ms
                    )
        except Exception as e:
            logger.warning(f"Rule-based classification failed: {e}")

        # Strategy 2: Embedding-based classification (fast path, <100ms)
        # Note: This requires embedding cache to be fast
        if self.embedding_cache:
            try:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms < timeout_ms * 0.7:  # Reserve time for LLM fallback
                    embedding_result = self._classify_embedding_based(normalized_input)
                    if embedding_result and embedding_result.confidence >= 0.6:
                        total_elapsed_ms = (time.time() - start_time) * 1000
                        if total_elapsed_ms < timeout_ms:
                            logger.debug(f"Intent classified via embedding: {embedding_result.intent.value} (confidence={embedding_result.confidence:.2f}, time={total_elapsed_ms:.2f}ms)")
                            return IntentResult(
                                intent=embedding_result.intent,
                                confidence=embedding_result.confidence,
                                method="embedding",
                                processing_time_ms=total_elapsed_ms
                            )
            except Exception as e:
                logger.warning(f"Embedding-based classification failed: {e}")

        # Strategy 3: LLM-based classification (fallback, small model only)
        # Only if we have time left and LLM provider is available
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms < timeout_ms * 0.5 and self.llm_provider:  # Reserve 50% time for LLM
            try:
                llm_result = await self._classify_llm_based(normalized_input, timeout_ms - elapsed_ms)
                if llm_result:
                    total_elapsed_ms = (time.time() - start_time) * 1000
                    if total_elapsed_ms < timeout_ms:
                        logger.debug(f"Intent classified via LLM: {llm_result.intent.value} (confidence={llm_result.confidence:.2f}, time={total_elapsed_ms:.2f}ms)")
                        return IntentResult(
                            intent=llm_result.intent,
                            confidence=llm_result.confidence,
                            method="llm",
                            processing_time_ms=total_elapsed_ms
                        )
            except Exception as e:
                logger.warning(f"LLM-based classification failed: {e}")

        # Fallback: Default intent
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(f"Intent classification fallback to default: conversation (time={elapsed_ms:.2f}ms)")
        return IntentResult(
            intent=IntentType.CONVERSATION,
            confidence=0.5,
            method="fallback",
            processing_time_ms=elapsed_ms
        )

    def _classify_rule_based(self, normalized_input: str) -> IntentResult | None:
        """
        Rule-based intent classification (fastest).

        Args:
            normalized_input: Normalized user input

        Returns:
            IntentResult if matched, None otherwise
        """
        # Check high-risk first (safety critical)
        for pattern in self._high_risk_patterns:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                return IntentResult(
                    intent=IntentType.HIGH_RISK,
                    confidence=0.9,
                    method="rule",
                    processing_time_ms=0.0
                )

        # Check greeting
        for pattern in self._greeting_patterns:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                return IntentResult(
                    intent=IntentType.GREETING,
                    confidence=0.8,
                    method="rule",
                    processing_time_ms=0.0
                )

        # Check question
        for pattern in self._question_patterns:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                return IntentResult(
                    intent=IntentType.QUESTION,
                    confidence=0.75,
                    method="rule",
                    processing_time_ms=0.0
                )

        # Check command
        for pattern in self._command_patterns:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                return IntentResult(
                    intent=IntentType.COMMAND,
                    confidence=0.75,
                    method="rule",
                    processing_time_ms=0.0
                )

        return None

    _INTENT_KEYWORDS: dict[IntentType, list[str]] = {
        IntentType.GREETING: [
            "merhaba", "selam", "hey", "hi", "hello", "günaydın",
            "iyi günler", "iyi akşamlar", "how are you", "nasılsın",
            "nasılsınız", "naber", "ne haber", "hoş geldin", "welcome",
        ],
        IntentType.QUESTION: [
            "ne", "what", "how", "why", "when", "where", "kim", "nasıl",
            "neden", "ne zaman", "nerede", "soru", "question", "ask",
            "which", "hangi", "kaç", "explain", "anlat", "açıkla",
        ],
        IntentType.COMMAND: [
            "yap", "do", "make", "create", "build", "run", "execute",
            "start", "stop", "delete", "remove", "komut", "command",
            "open", "close", "send", "gönder", "kaydet", "save", "update",
        ],
        IntentType.HIGH_RISK: [
            "kendini", "self", "harm", "hurt", "kill", "suicide",
            "özkıyım", "intihar", "violence", "şiddet", "attack",
            "saldırı", "drug", "drugs", "uyuşturucu", "illegal",
        ],
        IntentType.CONVERSATION: [
            "ben", "bana", "benim", "i", "me", "my", "feel", "think",
            "hissediyorum", "düşünüyorum", "bugün", "today", "hayat",
            "life", "want", "istiyorum", "need", "like", "talk", "chat",
        ],
    }

    def _classify_embedding_based(self, normalized_input: str) -> IntentResult | None:
        """
        Embedding-based intent classification (fast path).

        Uses keyword-vector cosine similarity against pre-defined intent
        vocabularies stored in the embedding cache.
        """
        if not self.embedding_cache:
            return None

        cached = self.embedding_cache.get(normalized_input)
        if cached is not None and len(cached) > 0:
            intent_types = list(self._INTENT_KEYWORDS.keys())
            best_idx = max(range(len(cached)), key=lambda i: cached[i])
            best_score = cached[best_idx]
            if best_score >= 0.6 and best_idx < len(intent_types):
                return IntentResult(
                    intent=intent_types[best_idx],
                    confidence=min(best_score, 1.0),
                    method="embedding",
                    processing_time_ms=0.0,
                )

        input_tokens = set(re.findall(r'\b\w+\b', normalized_input))
        if not input_tokens:
            return None

        scores: list[float] = []
        for intent_type in self._INTENT_KEYWORDS:
            keywords = self._INTENT_KEYWORDS[intent_type]
            keyword_set = set(keywords)
            overlap = input_tokens & keyword_set
            if not overlap:
                scores.append(0.0)
                continue
            denom = math.sqrt(len(input_tokens) * len(keyword_set))
            score = len(overlap) / denom if denom > 0 else 0.0
            scores.append(score)

        self.embedding_cache.put(normalized_input, scores)

        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_score = scores[best_idx]

        if best_score < 0.15:
            return None

        intent_types = list(self._INTENT_KEYWORDS.keys())
        confidence = 0.6 + min(best_score, 1.0) * 0.25
        return IntentResult(
            intent=intent_types[best_idx],
            confidence=confidence,
            method="embedding",
            processing_time_ms=0.0,
        )

    async def _classify_llm_based(
        self,
        normalized_input: str,
        timeout_ms: float
    ) -> IntentResult | None:
        """
        LLM-based intent classification (fallback, small model only).

        Args:
            normalized_input: Normalized user input
            timeout_ms: Remaining timeout in milliseconds

        Returns:
            IntentResult if classified, None otherwise
        """
        if not self.llm_provider or not self.llm_provider.available:
            return None

        try:
            # Use small model for fast classification
            # Format: "Classify intent: {input}. Options: greeting, question, command, conversation, high_risk"
            prompt = f"""Classify the intent of this user input into one of these categories: greeting, question, command, conversation, high_risk.

User input: {normalized_input}

Respond with only the intent category name (lowercase)."""

            # Call LLM with timeout
            # Note: This should use a small/fast model (GPT-3.5-Turbo or Claude Haiku)
            response = await self.llm_provider.completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-3.5-turbo",  # Small model for speed
                temperature=0.1,  # Low temperature for deterministic classification
                max_tokens=10  # Only need category name
            )

            # Parse response
            intent_str = response.strip().lower()

            # Map to IntentType
            intent_mapping = {
                "greeting": IntentType.GREETING,
                "question": IntentType.QUESTION,
                "command": IntentType.COMMAND,
                "conversation": IntentType.CONVERSATION,
                "high_risk": IntentType.HIGH_RISK,
            }

            intent = intent_mapping.get(intent_str, IntentType.UNKNOWN)

            if intent != IntentType.UNKNOWN:
                return IntentResult(
                    intent=intent,
                    confidence=0.7,  # Lower confidence for LLM
                    method="llm",
                    processing_time_ms=0.0
                )
        except Exception as e:
            logger.warning(f"LLM-based classification error: {e}")

        return None

