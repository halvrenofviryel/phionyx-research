"""
Unit tests for EmbeddingCache
"""
import time
from phionyx_core.memory.embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheEntry,
    get_embedding_cache,
    reset_global_cache
)


class TestEmbeddingCacheEntry:
    """Test EmbeddingCacheEntry."""

    def test_entry_creation(self):
        """Test entry creation."""
        embedding = [0.1, 0.2, 0.3]
        timestamp = time.time()
        entry = EmbeddingCacheEntry(embedding, timestamp, ttl=3600.0)

        assert entry.embedding == embedding
        assert entry.timestamp == timestamp
        assert entry.ttl == 3600.0

    def test_entry_not_expired(self):
        """Test entry is not expired."""
        embedding = [0.1, 0.2, 0.3]
        timestamp = time.time()
        entry = EmbeddingCacheEntry(embedding, timestamp, ttl=3600.0)

        assert not entry.is_expired()

    def test_entry_expired(self):
        """Test entry is expired."""
        embedding = [0.1, 0.2, 0.3]
        timestamp = time.time() - 7200.0  # 2 hours ago
        entry = EmbeddingCacheEntry(embedding, timestamp, ttl=3600.0)

        assert entry.is_expired()

    def test_entry_age(self):
        """Test entry age calculation."""
        embedding = [0.1, 0.2, 0.3]
        timestamp = time.time() - 1800.0  # 30 minutes ago
        entry = EmbeddingCacheEntry(embedding, timestamp, ttl=3600.0)

        age = entry.age()
        assert 1700 < age < 1900  # Approximately 1800 seconds


class TestEmbeddingCache:
    """Test EmbeddingCache."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = EmbeddingCache(max_size=100, ttl=3600.0)

        assert cache.max_size == 100
        assert cache.ttl == 3600.0
        assert len(cache._cache) == 0

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = EmbeddingCache()

        key1 = cache._generate_cache_key("Hello World")
        key2 = cache._generate_cache_key("Hello World")
        key3 = cache._generate_cache_key("Different Text")

        # Same text should generate same key
        assert key1 == key2
        # Different text should generate different key
        assert key1 != key3

    def test_cache_key_with_profile_id(self):
        """Test cache key generation with profile_id."""
        cache = EmbeddingCache()

        key1 = cache._generate_cache_key("Hello", profile_id="user1")
        key2 = cache._generate_cache_key("Hello", profile_id="user2")
        key3 = cache._generate_cache_key("Hello", profile_id="user1")

        # Same text + same profile should generate same key
        assert key1 == key3
        # Same text + different profile should generate different key
        assert key1 != key2

    def test_cache_put_and_get(self):
        """Test cache put and get."""
        cache = EmbeddingCache(max_size=10)
        embedding = [0.1, 0.2, 0.3]

        # Put embedding
        cache.put("Hello World", embedding)

        # Get embedding
        result = cache.get("Hello World")

        assert result == embedding

    def test_cache_miss(self):
        """Test cache miss."""
        cache = EmbeddingCache()

        result = cache.get("Non-existent")

        assert result is None
        assert cache._misses == 1

    def test_cache_hit_metrics(self):
        """Test cache hit metrics."""
        cache = EmbeddingCache(enable_metrics=True)
        embedding = [0.1, 0.2, 0.3]

        # Put and get
        cache.put("Hello", embedding)
        cache.get("Hello")

        metrics = cache.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 0

    def test_cache_miss_metrics(self):
        """Test cache miss metrics."""
        cache = EmbeddingCache(enable_metrics=True)

        cache.get("Non-existent")

        metrics = cache.get_metrics()
        assert metrics["hits"] == 0
        assert metrics["misses"] == 1

    def test_cache_expiration(self):
        """Test cache expiration."""
        cache = EmbeddingCache(ttl=1.0)  # 1 second TTL
        embedding = [0.1, 0.2, 0.3]

        # Put embedding
        cache.put("Hello", embedding, current_time=1000.0)

        # Get immediately (should work)
        result = cache.get("Hello", current_time=1000.5)
        assert result == embedding

        # Get after expiration (should return None)
        result = cache.get("Hello", current_time=1002.0)
        assert result is None
        assert cache._expirations == 1

    def test_cache_lru_eviction(self):
        """Test LRU eviction."""
        cache = EmbeddingCache(max_size=3)

        # Fill cache
        cache.put("key1", [1.0])
        cache.put("key2", [2.0])
        cache.put("key3", [3.0])

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new key (should evict key2, least recently used)
        cache.put("key4", [4.0])

        # key2 should be evicted
        assert cache.get("key2") is None
        # key1, key3, key4 should still be there
        assert cache.get("key1") == [1.0]
        assert cache.get("key3") == [3.0]
        assert cache.get("key4") == [4.0]
        assert cache._evictions == 1

    def test_cache_cleanup_expired(self):
        """Test cleanup expired entries."""
        cache = EmbeddingCache(ttl=1.0)

        # Add entries with different timestamps
        cache.put("key1", [1.0], current_time=1000.0)
        cache.put("key2", [2.0], current_time=1001.0)
        cache.put("key3", [3.0], current_time=1002.0)

        # Cleanup at time 1002.5 (key1 and key2 should be expired)
        removed = cache.cleanup_expired(current_time=1002.5)

        assert removed == 2
        assert cache.get("key1", current_time=1002.5) is None
        assert cache.get("key2", current_time=1002.5) is None
        assert cache.get("key3", current_time=1002.5) == [3.0]

    def test_cache_clear(self):
        """Test cache clear."""
        cache = EmbeddingCache()

        cache.put("key1", [1.0])
        cache.put("key2", [2.0])
        cache.get("key1")

        cache.clear()

        assert len(cache._cache) == 0
        metrics = cache.get_metrics()
        assert metrics["hits"] == 0
        assert metrics["misses"] == 0

    def test_cache_get_stats(self):
        """Test cache statistics."""
        cache = EmbeddingCache(ttl=3600.0)

        cache.put("key1", [1.0], current_time=1000.0)
        cache.get("key1", current_time=1001.0)

        stats = cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "average_age_seconds" in stats
        assert "ttl_seconds" in stats
        assert stats["ttl_seconds"] == 3600.0


class TestGlobalCache:
    """Test global cache functions."""

    def test_get_embedding_cache_singleton(self):
        """Test global cache is singleton."""
        reset_global_cache()

        cache1 = get_embedding_cache()
        cache2 = get_embedding_cache()

        assert cache1 is cache2

    def test_reset_global_cache(self):
        """Test reset global cache."""
        cache1 = get_embedding_cache()
        reset_global_cache()
        cache2 = get_embedding_cache()

        assert cache1 is not cache2

