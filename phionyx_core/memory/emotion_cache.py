"""
Emotion Estimation Cache - LRU Cache Implementation
===================================================

Provides LRU cache for emotion estimation to ensure determinism and consistency.
Critical for parallel execution: Same input → Same output.

Features:
- LRU eviction policy
- Deterministic caching (same input → same output)
- Thread-safe operations (for async contexts)
- Cache hit/miss metrics
"""

import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


class EmotionCacheEntry:
    """Single cache entry with timestamp."""

    def __init__(self, valence: float, arousal: float, timestamp: float):
        """
        Initialize cache entry.

        Args:
            valence: Cached valence value
            arousal: Cached arousal value
            timestamp: Creation timestamp
        """
        self.valence = valence
        self.arousal = arousal
        self.timestamp = timestamp


class EmotionCache:
    """
    LRU cache for emotion estimation results.

    CRITICAL: Ensures determinism in parallel execution.
    Same input → Same output (guaranteed).

    Features:
    - LRU eviction when max size reached
    - Deterministic hashing (same input → same hash)
    - Thread-safe operations (for async contexts)
    - Cache metrics
    """

    def __init__(
        self,
        max_size: int = 10000,
        enable_metrics: bool = True
    ):
        """
        Initialize emotion cache.

        Args:
            max_size: Maximum number of entries (default: 10,000)
            enable_metrics: Enable cache hit/miss metrics (default: True)
        """
        self.max_size = max_size
        self.enable_metrics = enable_metrics
        self._cache: OrderedDict[str, EmotionCacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _hash_input(self, text: str) -> str:
        """
        Generate deterministic hash for input text.

        Args:
            text: Input text to hash

        Returns:
            SHA256 hash of normalized text
        """
        # Normalize text: lowercase, strip whitespace
        normalized = text.lower().strip()

        # Generate deterministic hash
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def get(self, text: str) -> tuple[float, float] | None:
        """
        Get cached emotion values for input text.

        Args:
            text: Input text

        Returns:
            Tuple of (valence, arousal) if cached, None otherwise
        """
        if not text:
            return None

        cache_key = self._hash_input(text)

        if cache_key in self._cache:
            # Move to end (LRU)
            entry = self._cache.pop(cache_key)
            self._cache[cache_key] = entry

            if self.enable_metrics:
                self._hits += 1

            logger.debug(f"Emotion cache HIT: text_hash={cache_key[:8]}..., valence={entry.valence:.4f}, arousal={entry.arousal:.4f}")
            return (entry.valence, entry.arousal)

        if self.enable_metrics:
            self._misses += 1

        logger.debug(f"Emotion cache MISS: text_hash={cache_key[:8]}...")
        return None

    def set(self, text: str, valence: float, arousal: float) -> None:
        """
        Cache emotion values for input text.

        Args:
            text: Input text
            valence: Valence value to cache
            arousal: Arousal value to cache
        """
        if not text:
            return

        cache_key = self._hash_input(text)
        current_time = time.time()

        # Remove if exists (update)
        if cache_key in self._cache:
            self._cache.pop(cache_key)

        # Add new entry
        entry = EmotionCacheEntry(
            valence=valence,
            arousal=arousal,
            timestamp=current_time
        )
        self._cache[cache_key] = entry

        # LRU eviction: remove oldest if over max size
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first)

        logger.debug(f"Emotion cache SET: text_hash={cache_key[:8]}..., valence={valence:.4f}, arousal={arousal:.4f}")

    def get_metrics(self) -> dict[str, Any]:
        """
        Get cache metrics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": hit_rate,
            "size": len(self._cache),
            "max_size": self.max_size
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Emotion cache cleared")

