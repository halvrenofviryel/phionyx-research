"""
Tests for RAG Cache Cognitive Impact Eviction — Patent SF3-14 + SF3-24
======================================================================

SF3-24: Cache eviction based on cognitive impact, not LRU/FIFO.
SF3-14: Low-impact data evicted when impact falls below threshold condition.
"""

import pytest
import time

from phionyx_core.memory.rag_cache import RAGCache, RAGCacheEntry


class TestCognitiveImpactScore:
    """RAGCacheEntry.cognitive_impact() computes trace_weight correctly."""

    def test_high_significance_high_impact(self):
        """High significance → high cognitive impact."""
        entry = RAGCacheEntry(
            memories=[{"text": "important"}],
            timestamp=1000.0,
            significance=0.9,
        )
        impact = entry.cognitive_impact(current_time=1000.0)
        assert impact > 0.8, f"High significance should yield high impact: {impact}"

    def test_low_significance_low_impact(self):
        """Low significance → low cognitive impact."""
        entry = RAGCacheEntry(
            memories=[{"text": "trivial"}],
            timestamp=1000.0,
            significance=0.1,
        )
        impact = entry.cognitive_impact(current_time=1000.0)
        assert impact < 0.2, f"Low significance should yield low impact: {impact}"

    def test_decay_reduces_impact_over_time(self):
        """Older entries have lower impact (semantic time decay)."""
        entry = RAGCacheEntry(
            memories=[{"text": "data"}],
            timestamp=1000.0,
            ttl=3600.0,
            significance=0.8,
        )
        fresh_impact = entry.cognitive_impact(current_time=1000.0)
        aged_impact = entry.cognitive_impact(current_time=2800.0)  # 30 min later
        assert aged_impact < fresh_impact, (
            f"Aged impact ({aged_impact}) should be less than fresh ({fresh_impact})"
        )

    def test_access_count_boosts_impact(self):
        """Frequently accessed entries have higher impact."""
        entry = RAGCacheEntry(
            memories=[{"text": "data"}],
            timestamp=1000.0,
            significance=0.5,
        )
        base_impact = entry.cognitive_impact(current_time=1000.0)
        entry.access_count = 10
        boosted_impact = entry.cognitive_impact(current_time=1000.0)
        assert boosted_impact > base_impact, (
            f"Boosted ({boosted_impact}) should exceed base ({base_impact})"
        )


class TestCognitiveEviction:
    """RAGCache evicts lowest-impact entry, not LRU."""

    def test_evicts_low_significance_over_high(self):
        """Low-significance entry evicted before high-significance."""
        cache = RAGCache(max_size=2, ttl=3600.0)
        t = 1000.0

        # Insert high-significance first
        cache.put("important query", [{"text": "critical data"}],
                  current_time=t, significance=0.95)
        # Insert low-significance second (would be LRU victim if LRU)
        cache.put("trivial query", [{"text": "minor data"}],
                  current_time=t + 1, significance=0.05)

        # Cache is full (2 entries). Insert third → eviction
        cache.put("new query", [{"text": "new data"}],
                  current_time=t + 2, significance=0.5)

        # High-significance entry should survive
        assert cache.get("important query", current_time=t + 2) is not None, (
            "High-significance entry was evicted (should survive)"
        )
        # Low-significance entry should be evicted
        assert cache.get("trivial query", current_time=t + 2) is None, (
            "Low-significance entry survived (should be evicted)"
        )

    def test_evicts_old_low_impact_over_recent(self):
        """Old + low significance evicted before recent + high significance."""
        cache = RAGCache(max_size=2, ttl=3600.0)

        # Old entry with low significance
        cache.put("old query", [{"text": "old"}],
                  current_time=100.0, significance=0.3)
        # Recent entry with high significance
        cache.put("recent query", [{"text": "recent"}],
                  current_time=5000.0, significance=0.9)

        # Trigger eviction
        cache.put("trigger", [{"text": "trigger"}],
                  current_time=5001.0, significance=0.5)

        # Recent high-significance should survive
        assert cache.get("recent query", current_time=5001.0) is not None
        # Old low-significance should be evicted
        assert cache.get("old query", current_time=5001.0) is None

    def test_significance_default_is_05(self):
        """Default significance is 0.5 (backward compatible)."""
        cache = RAGCache(max_size=3, ttl=3600.0)
        cache.put("q1", [{"text": "a"}], current_time=1000.0)
        # Access internal entry
        key = cache._generate_cache_key("q1")
        entry = cache._cache[key]
        assert entry.significance == 0.5

    def test_access_count_incremented_on_get(self):
        """get() increments access_count for impact calculation."""
        cache = RAGCache(max_size=5, ttl=3600.0)
        cache.put("q1", [{"text": "a"}], current_time=1000.0)

        key = cache._generate_cache_key("q1")
        assert cache._cache[key].access_count == 0

        cache.get("q1", current_time=1000.0)
        assert cache._cache[key].access_count == 1

        cache.get("q1", current_time=1000.0)
        assert cache._cache[key].access_count == 2

    def test_metrics_track_evictions(self):
        """Eviction counter still works with cognitive eviction."""
        cache = RAGCache(max_size=2, ttl=3600.0)
        cache.put("a", [{}], current_time=1000.0, significance=0.1)
        cache.put("b", [{}], current_time=1001.0, significance=0.9)
        cache.put("c", [{}], current_time=1002.0, significance=0.5)  # triggers eviction

        metrics = cache.get_metrics()
        assert metrics["evictions"] >= 1


class TestThresholdEviction:
    """SF3-14: Entries below impact threshold are evicted proactively."""

    def test_below_threshold_evicted_on_put(self):
        """Entries with impact < threshold are evicted when cache is full."""
        # Use high threshold so low-significance entries qualify
        cache = RAGCache(max_size=3, ttl=3600.0, impact_threshold=0.2)
        t = 1000.0

        cache.put("low1", [{}], current_time=t, significance=0.05)
        cache.put("low2", [{}], current_time=t, significance=0.08)
        cache.put("high", [{}], current_time=t, significance=0.9)

        # All 3 entries present (not at capacity trigger yet)
        assert len(cache._cache) == 3

        # Insert 4th → capacity reached → threshold eviction kicks in
        cache.put("new", [{}], current_time=t + 1, significance=0.5)

        # Both low entries should be evicted (impact < 0.2)
        assert cache.get("low1", current_time=t + 1) is None
        assert cache.get("low2", current_time=t + 1) is None
        # High and new entries survive
        assert cache.get("high", current_time=t + 1) is not None
        assert cache.get("new", current_time=t + 1) is not None

    def test_cleanup_below_threshold_proactive(self):
        """cleanup_below_threshold() removes low-impact entries without capacity trigger."""
        cache = RAGCache(max_size=100, ttl=3600.0, impact_threshold=0.15)
        t = 1000.0

        cache.put("low", [{}], current_time=t, significance=0.05)
        cache.put("mid", [{}], current_time=t, significance=0.5)
        cache.put("high", [{}], current_time=t, significance=0.9)

        # Cache is not full (3/100), but proactive cleanup should remove low-impact
        removed = cache.cleanup_below_threshold(current_time=t)

        assert removed == 1  # Only "low" (impact=0.05 < 0.15)
        assert cache.get("low", current_time=t) is None
        assert cache.get("mid", current_time=t) is not None
        assert cache.get("high", current_time=t) is not None

    def test_decay_pushes_entry_below_threshold(self):
        """Entry starts above threshold but decays below over time."""
        cache = RAGCache(max_size=100, ttl=3600.0, impact_threshold=0.15)

        # significance=0.3, at creation impact=0.3 (above 0.15)
        cache.put("decaying", [{}], current_time=1000.0, significance=0.3)

        # Right after creation: should survive
        removed_early = cache.cleanup_below_threshold(current_time=1000.0)
        assert removed_early == 0

        # Much later (well past TTL): decay pushes impact below threshold
        removed_late = cache.cleanup_below_threshold(current_time=10000.0)
        assert removed_late == 1

    def test_threshold_default_is_01(self):
        """Default impact threshold is 0.1."""
        cache = RAGCache(max_size=10)
        assert cache.impact_threshold == 0.1

    def test_custom_threshold(self):
        """Custom threshold is respected."""
        cache = RAGCache(max_size=10, impact_threshold=0.5)
        assert cache.impact_threshold == 0.5

    def test_above_threshold_survives(self):
        """Entries above threshold are not removed by cleanup."""
        cache = RAGCache(max_size=100, ttl=3600.0, impact_threshold=0.1)
        t = 1000.0

        cache.put("keeper", [{}], current_time=t, significance=0.8)
        removed = cache.cleanup_below_threshold(current_time=t)
        assert removed == 0
        assert cache.get("keeper", current_time=t) is not None
