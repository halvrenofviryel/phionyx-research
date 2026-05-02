"""
RAG Query Cache - LRU Cache Implementation
===========================================

Provides LRU cache for RAG queries to reduce vector store searches and improve latency.

Features:
- LRU eviction policy
- TTL (Time To Live) support
- Configurable max size
- Cache hit/miss metrics
"""

import hashlib
import logging
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class RAGCacheEntry:
    """Single cache entry with TTL and cognitive impact support."""

    def __init__(
        self,
        memories: list[dict],
        timestamp: float,
        ttl: float = 3600.0,
        significance: float = 0.5,
    ):
        """
        Initialize cache entry.

        Args:
            memories: Retrieved memories
            timestamp: Creation timestamp
            ttl: Time to live in seconds (default: 1 hour)
            significance: Cognitive significance score (0-1, default 0.5)
        """
        self.memories = memories
        self.timestamp = timestamp
        self.ttl = ttl
        self.significance = max(0.0, min(1.0, significance))
        self.access_count: int = 0

    def is_expired(self, current_time: float | None = None) -> bool:
        """Check if entry is expired."""
        if current_time is None:
            current_time = time.time()
        return (current_time - self.timestamp) > self.ttl

    def age(self, current_time: float | None = None) -> float:
        """Get entry age in seconds."""
        if current_time is None:
            current_time = time.time()
        return current_time - self.timestamp

    def cognitive_impact(self, current_time: float | None = None) -> float:
        """
        Compute cognitive impact score for eviction decisions.

        trace_weight = significance * semantic_time_decay * access_boost

        - significance: how important this entry is (0-1)
        - semantic_time_decay: exponential decay over age (half-life = ttl/2)
        - access_boost: 1 + log(1 + access_count) reward for frequent use

        Higher impact → more likely to survive eviction.
        """
        import math
        if current_time is None:
            current_time = time.time()
        age_seconds = max(0.0, current_time - self.timestamp)
        half_life = self.ttl / 2.0
        if half_life <= 0:
            half_life = 1800.0
        decay = math.exp(-0.693 * age_seconds / half_life)  # ln(2) ≈ 0.693
        access_boost = 1.0 + math.log1p(self.access_count)
        return self.significance * decay * access_boost


class RAGCache:
    """
    LRU cache for RAG queries with TTL support.

    Features:
    - LRU eviction when max size reached
    - TTL-based expiration
    - Thread-safe operations (for async contexts)
    - Cache metrics
    """

    # SF3-14: Minimum cognitive impact threshold for eviction eligibility.
    # Entries with impact below this threshold are evicted proactively,
    # not only when the cache is at capacity.
    DEFAULT_IMPACT_THRESHOLD: float = 0.1

    def __init__(
        self,
        max_size: int = 5000,
        ttl: float = 3600.0,  # 1 hour in seconds
        enable_metrics: bool = True,
        impact_threshold: float = DEFAULT_IMPACT_THRESHOLD,
    ):
        """
        Initialize RAG cache.

        Args:
            max_size: Maximum number of entries (default: 5,000)
            ttl: Time to live in seconds (default: 1 hour)
            enable_metrics: Enable cache hit/miss metrics (default: True)
            impact_threshold: Minimum cognitive impact to survive eviction (default: 0.1)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enable_metrics = enable_metrics
        self.impact_threshold = impact_threshold

        # LRU cache: OrderedDict maintains insertion order
        # Key: cache_key (hash), Value: RAGCacheEntry
        self._cache: OrderedDict[str, RAGCacheEntry] = OrderedDict()

        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def _generate_cache_key(
        self,
        query: str,
        intent: str | None = None,
        actor_ref: str | None = None
    ) -> str:
        """
        Generate cache key from query, intent, and optional actor_ref.

        Args:
            query: Query text
            intent: Optional intent type
            actor_ref: Optional actor reference for scoping

        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize query (strip whitespace, lowercase for consistency)
        normalized_query = query.strip().lower()

        # Create key string
        key_parts = [normalized_query]
        if intent:
            key_parts.append(intent.lower())
        if actor_ref:
            key_parts.append(actor_ref)

        key_string = ":".join(key_parts)

        # Generate SHA256 hash
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()

    def get(
        self,
        query: str,
        intent: str | None = None,
        actor_ref: str | None = None,
        current_time: float | None = None
    ) -> list[dict] | None:
        """
        Get RAG results from cache.

        Args:
            query: Query text
            intent: Optional intent type
            actor_ref: Optional actor reference
            current_time: Current timestamp (for testing)

        Returns:
            List of memories if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(query, intent, actor_ref)

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

        # Move to end (most recently used) and track access
        self._cache.move_to_end(cache_key)
        entry.access_count += 1

        if self.enable_metrics:
            self._hits += 1

        return entry.memories

    def put(
        self,
        query: str,
        memories: list[dict],
        intent: str | None = None,
        actor_ref: str | None = None,
        current_time: float | None = None,
        significance: float = 0.5,
    ) -> None:
        """
        Store RAG results in cache.

        Args:
            query: Query text
            memories: Retrieved memories
            intent: Optional intent type
            actor_ref: Optional actor reference
            current_time: Current timestamp (for testing)
            significance: Cognitive significance score (0-1) for eviction priority
        """
        if current_time is None:
            current_time = time.time()

        cache_key = self._generate_cache_key(query, intent, actor_ref)

        # Create new entry with significance
        entry = RAGCacheEntry(memories, current_time, self.ttl, significance=significance)

        # If key exists, update it
        if cache_key in self._cache:
            self._cache[cache_key] = entry
            self._cache.move_to_end(cache_key)
            return

        # Check if we need to evict
        if len(self._cache) >= self.max_size:
            self._evict_lowest_impact(current_time)

        # Add new entry
        self._cache[cache_key] = entry

    def _evict_lowest_impact(self, current_time: float) -> None:
        """
        Evict entries with cognitive impact below threshold, then the lowest.

        Patent SF3-14: "Low-impact data is evicted when the impact value
        falls below a threshold condition."
        Patent SF3-24: "Cache eviction based on cognitive impact, not LRU/FIFO."
        """
        if not self._cache:
            return

        # Phase 1: Evict ALL entries below impact threshold (SF3-14)
        below_threshold = [
            key for key, entry in self._cache.items()
            if entry.cognitive_impact(current_time) < self.impact_threshold
        ]
        for key in below_threshold:
            del self._cache[key]
            if self.enable_metrics:
                self._evictions += 1

        # Phase 2: If still at capacity, evict single lowest impact (SF3-24)
        if len(self._cache) >= self.max_size:
            min_key = None
            min_impact = float('inf')
            for key, entry in self._cache.items():
                impact = entry.cognitive_impact(current_time)
                if impact < min_impact:
                    min_impact = impact
                    min_key = key

            if min_key is not None:
                del self._cache[min_key]
                if self.enable_metrics:
                    self._evictions += 1

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        if self.enable_metrics:
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            self._expirations = 0

    def cleanup_below_threshold(self, current_time: float | None = None) -> int:
        """
        Proactively remove entries with cognitive impact below threshold.

        Patent SF3-14: Threshold-based eviction independent of capacity.

        Args:
            current_time: Current timestamp (for testing)

        Returns:
            Number of entries removed
        """
        if current_time is None:
            current_time = time.time()

        below = [
            key for key, entry in self._cache.items()
            if entry.cognitive_impact(current_time) < self.impact_threshold
        ]
        for key in below:
            del self._cache[key]
            if self.enable_metrics:
                self._evictions += 1

        return len(below)

    def cleanup_expired(self, current_time: float | None = None) -> int:
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

    def get_metrics(self) -> dict[str, int | float]:
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


# Global cache instance (singleton pattern)
_global_cache: RAGCache | None = None


def get_rag_cache(
    max_size: int = 5000,
    ttl: float = 3600.0,
    enable_metrics: bool = True
) -> RAGCache:
    """
    Get or create global RAG cache instance.

    Args:
        max_size: Maximum number of entries
        ttl: Time to live in seconds
        enable_metrics: Enable metrics

    Returns:
        Global RAGCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = RAGCache(
            max_size=max_size,
            ttl=ttl,
            enable_metrics=enable_metrics
        )
        logger.info(f"RAG cache initialized: max_size={max_size}, ttl={ttl}s")

    return _global_cache


def reset_global_cache() -> None:
    """Reset global cache instance (for testing)."""
    global _global_cache
    _global_cache = None

