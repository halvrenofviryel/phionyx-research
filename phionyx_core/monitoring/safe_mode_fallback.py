"""
Safe-Mode Fallback Mechanism
Graceful degradation when circuit breaker is OPEN.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SafeModeResponse:
    """Safe mode fallback response."""
    response_text: str
    degraded: bool
    fallback_reason: str
    cached: bool
    metadata: Dict[str, Any]


class SafeModeFallback:
    """
    Safe-mode fallback mechanism for circuit breaker OPEN state.

    Provides graceful degradation when circuit breaker blocks execution:
    1. Cached response retrieval (if available)
    2. Minimal safe response generation
    3. Degraded mode operation
    """

    def __init__(
        self,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 3600,  # 1 hour
        safe_response_template: str = "I'm currently operating in safe mode. Please try again in a few moments."
    ):
        """
        Initialize safe mode fallback.

        Args:
            enable_caching: Enable response caching
            cache_ttl_seconds: Cache TTL in seconds
            safe_response_template: Template for safe mode responses
        """
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl_seconds
        self.safe_response_template = safe_response_template

        # In-memory cache (can be replaced with Redis/database)
        self._response_cache: Dict[str, Dict[str, Any]] = {}

    def get_cached_response(
        self,
        session_id: str,
        user_input: str,
        similarity_threshold: float = 0.7
    ) -> Optional[SafeModeResponse]:
        """
        Retrieve cached response if available and similar.

        Args:
            session_id: Session ID
            user_input: User input text
            similarity_threshold: Minimum similarity for cache hit

        Returns:
            SafeModeResponse if cache hit, None otherwise
        """
        if not self.enable_caching:
            return None

        cache_key = f"{session_id}:{self._hash_input(user_input)}"
        cached = self._response_cache.get(cache_key)

        if not cached:
            return None

        # Check TTL
        age_seconds = (datetime.now() - cached["timestamp"]).total_seconds()
        if age_seconds > self.cache_ttl:
            # Expired
            del self._response_cache[cache_key]
            return None

        # Simple similarity check (can be enhanced with vector similarity)
        similarity = self._simple_similarity(user_input, cached["user_input"])
        if similarity < similarity_threshold:
            return None

        logger.info(f"Cache hit for session {session_id}: similarity={similarity:.2f}")
        return SafeModeResponse(
            response_text=cached["response_text"],
            degraded=True,
            fallback_reason="cached_response",
            cached=True,
            metadata={
                "cache_age_seconds": age_seconds,
                "similarity": similarity,
                "original_timestamp": cached["timestamp"].isoformat()
            }
        )

    def generate_safe_response(
        self,
        user_input: str,
        circuit_state: str,
        drift_info: Optional[Dict[str, Any]] = None
    ) -> SafeModeResponse:
        """
        Generate minimal safe response.

        Args:
            user_input: User input text
            circuit_state: Circuit breaker state
            drift_info: Optional drift detection information

        Returns:
            SafeModeResponse with safe mode message
        """
        # Build safe response
        response_parts = [self.safe_response_template]

        if drift_info:
            drift_score = drift_info.get("drift_score", 0.0)
            if drift_score > 0.5:
                response_parts.append("The system detected unusual behavior and is operating in safe mode.")

        response_text = " ".join(response_parts)

        return SafeModeResponse(
            response_text=response_text,
            degraded=True,
            fallback_reason=f"circuit_{circuit_state}",
            cached=False,
            metadata={
                "circuit_state": circuit_state,
                "drift_info": drift_info,
                "generated_at": datetime.now().isoformat()
            }
        )

    def cache_response(
        self,
        session_id: str,
        user_input: str,
        response_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache response for future use.

        Args:
            session_id: Session ID
            user_input: User input text
            response_text: Response text to cache
            metadata: Optional metadata
        """
        if not self.enable_caching:
            return

        cache_key = f"{session_id}:{self._hash_input(user_input)}"
        self._response_cache[cache_key] = {
            "user_input": user_input,
            "response_text": response_text,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }

        # Cleanup old entries (simple LRU - keep last 1000)
        if len(self._response_cache) > 1000:
            # Remove oldest entries
            sorted_entries = sorted(
                self._response_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            for key, _ in sorted_entries[:-1000]:
                del self._response_cache[key]

    def _hash_input(self, text: str) -> str:
        """Generate simple hash for input text."""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()[:8]

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (Jaccard similarity)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear cache for session or all sessions.

        Args:
            session_id: Optional session ID to clear, or None for all
        """
        if session_id:
            # Clear only for this session
            keys_to_remove = [
                key for key in self._response_cache.keys()
                if key.startswith(f"{session_id}:")
            ]
            for key in keys_to_remove:
                del self._response_cache[key]
        else:
            # Clear all
            self._response_cache.clear()

        logger.info(f"Cache cleared for session: {session_id or 'all'}")

