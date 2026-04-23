"""
Embedding Cache - LRU Cache Implementation
===========================================

Provides LRU cache for embeddings to reduce LLM API calls and improve latency.

Features:
- LRU eviction policy
- TTL (Time To Live) support
- Configurable max size
- Cache hit/miss metrics
"""

import hashlib
import time
from typing import List, Optional, Dict
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class EmbeddingCacheEntry:
    """Single cache entry with TTL support."""

    def __init__(self, embedding: List[float], timestamp: float, ttl: float = 86400.0):
        """
        Initialize cache entry.

        Args:
            embedding: Embedding vector
            timestamp: Creation timestamp
            ttl: Time to live in seconds (default: 24 hours)
        """
        self.embedding = embedding
        self.timestamp = timestamp
        self.ttl = ttl

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Check if entry is expired."""
        if current_time is None:
            current_time = time.time()
        return (current_time - self.timestamp) > self.ttl

    def age(self, current_time: Optional[float] = None) -> float:
        """Get entry age in seconds."""
        if current_time is None:
            current_time = time.time()
        return current_time - self.timestamp


class EmbeddingCache:
    """
    LRU cache for embeddings with TTL support.

    Features:
    - LRU eviction when max size reached
    - TTL-based expiration
    - Thread-safe operations (for async contexts)
    - Cache metrics
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl: float = 86400.0,  # 24 hours in seconds
        enable_metrics: bool = True
    ):
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of entries (default: 10,000)
            ttl: Time to live in seconds (default: 24 hours)
            enable_metrics: Enable cache hit/miss metrics (default: True)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enable_metrics = enable_metrics

        # LRU cache: OrderedDict maintains insertion order
        # Key: cache_key (hash), Value: EmbeddingCacheEntry
        self._cache: OrderedDict[str, EmbeddingCacheEntry] = OrderedDict()

        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def _generate_cache_key(self, text: str, profile_id: Optional[str] = None) -> str:
        """
        Generate cache key from text and optional profile_id.

        Args:
            text: Input text
            profile_id: Optional profile ID for scoping

        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize text (strip whitespace, lowercase for consistency)
        normalized_text = text.strip().lower()

        # Create key string
        if profile_id:
            key_string = f"{normalized_text}:{profile_id}"
        else:
            key_string = normalized_text

        # Generate SHA256 hash
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

    def get(
        self,
        text: str,
        profile_id: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> Optional[List[float]]:
        """
        Get embedding from cache.

        Args:
            text: Input text
            profile_id: Optional profile ID
            current_time: Current timestamp (for testing)

        Returns:
            Embedding vector if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(text, profile_id)

        if current_time is None:
            current_time = time.time()

        # Check if key exists
        if cache_key not in self._cache:
            if self.enable_metrics:
                self._misses += 1
            return None

        entry = self._cache[cache_key]

        # Check if expired
        if entry.is_expired(current_time):
            # Remove expired entry
            del self._cache[cache_key]
            if self.enable_metrics:
                self._expirations += 1
                self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(cache_key)

        if self.enable_metrics:
            self._hits += 1

        return entry.embedding

    def put(
        self,
        text: str,
        embedding: List[float],
        profile_id: Optional[str] = None,
        current_time: Optional[float] = None
    ) -> None:
        """
        Store embedding in cache.

        Args:
            text: Input text
            embedding: Embedding vector
            profile_id: Optional profile ID
            current_time: Current timestamp (for testing)
        """
        if current_time is None:
            current_time = time.time()

        cache_key = self._generate_cache_key(text, profile_id)

        # Create new entry
        entry = EmbeddingCacheEntry(embedding, current_time, self.ttl)

        # If key exists, update it
        if cache_key in self._cache:
            self._cache[cache_key] = entry
            self._cache.move_to_end(cache_key)
            return

        # Check if we need to evict
        if len(self._cache) >= self.max_size:
            # Evict least recently used (first item)
            self._cache.popitem(last=False)
            if self.enable_metrics:
                self._evictions += 1

        # Add new entry
        self._cache[cache_key] = entry

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        if self.enable_metrics:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

    def cleanup_expired(self, current_time: Optional[float] = None) -> int:
        """
        Remove expired entries.

        Args:
            current_time: Current timestamp (for testing)

        Returns:
            Number of expired entries removed
        """
        if current_time is None:
            current_time = time.time()

        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(current_time)
        ]

        for key in expired_keys:
            del self._cache[key]
            if self.enable_metrics:
                self._expirations += 1

        return len(expired_keys)

    def get_metrics(self) -> Dict[str, int]:
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
            "evictions": self._evictions,
            "expirations": self._expirations,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "current_size": len(self._cache),
            "max_size": self.max_size
        }

    def get_stats(self) -> Dict[str, any]:
        """
        Get detailed cache statistics.

        Returns:
            Dictionary with detailed statistics
        """
        metrics = self.get_metrics()

        # Calculate average age of entries
        current_time = time.time()
        ages = [entry.age(current_time) for entry in self._cache.values()]
        avg_age = sum(ages) / len(ages) if ages else 0.0

        return {
            **metrics,
            "average_age_seconds": round(avg_age, 2),
            "ttl_seconds": self.ttl
        }


# Global cache instance (singleton pattern)
_global_cache: Optional[EmbeddingCache] = None


def get_embedding_cache(
    max_size: int = 10000,
    ttl: float = 86400.0,
    enable_metrics: bool = True
) -> EmbeddingCache:
    """
    Get or create global embedding cache instance.

    Args:
        max_size: Maximum number of entries
        ttl: Time to live in seconds
        enable_metrics: Enable metrics

    Returns:
        Global EmbeddingCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = EmbeddingCache(
            max_size=max_size,
            ttl=ttl,
            enable_metrics=enable_metrics
        )
        logger.info(f"Embedding cache initialized: max_size={max_size}, ttl={ttl}s")

    return _global_cache


def reset_global_cache() -> None:
    """Reset global cache instance (for testing)."""
    global _global_cache
    _global_cache = None

