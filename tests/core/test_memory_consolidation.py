"""
Tests for MemoryConsolidator — v4 §8 (AGI Layer 8)
====================================================
"""

import pytest
from phionyx_core.memory.consolidation import (
    MemoryConsolidator,
    ConsolidationCandidate,
    ConsolidationResult,
)


# ── Helpers ──


def _make_memory(content, memory_type="episodic", strength=0.5, tags=None, access_count=0):
    return {
        "content": content,
        "memory_type": memory_type,
        "current_strength": strength,
        "tags": tags or [],
        "metadata": {"access_count": access_count},
    }


# ── Empty / No-op Cases ──


def test_consolidate_empty():
    c = MemoryConsolidator()
    result = c.consolidate([])
    assert result.consolidated_count == 0
    assert result.promoted_count == 0
    assert result.decayed_count == 0
    assert result.candidates == []


def test_consolidate_no_episodic():
    c = MemoryConsolidator()
    memories = [_make_memory("hello world", memory_type="semantic")]
    result = c.consolidate(memories)
    assert result.consolidated_count == 0


def test_consolidate_single_memory():
    c = MemoryConsolidator()
    memories = [_make_memory("the quick brown fox")]
    result = c.consolidate(memories)
    assert result.consolidated_count == 0


# ── Clustering ──


def test_similar_memories_clustered():
    c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.3)
    memories = [
        _make_memory("the cat sat on the mat"),
        _make_memory("the cat sat on the hat"),
        _make_memory("completely different topic about space exploration"),
    ]
    result = c.consolidate(memories)
    assert result.consolidated_count >= 1
    assert len(result.candidates) >= 1


def test_dissimilar_memories_not_clustered():
    c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.9)
    memories = [
        _make_memory("alpha beta gamma"),
        _make_memory("delta epsilon zeta"),
        _make_memory("eta theta iota"),
    ]
    result = c.consolidate(memories)
    assert result.consolidated_count == 0


def test_cluster_needs_min_size():
    c = MemoryConsolidator(min_cluster_size=5, similarity_threshold=0.3)
    memories = [
        _make_memory("the cat sat on the mat"),
        _make_memory("the cat sat on the hat"),
        _make_memory("the cat sat on the bat"),
    ]
    result = c.consolidate(memories)
    # Cluster has 3 members but min is 5
    assert result.consolidated_count == 0


# ── Promotion ──


def test_promotion_count():
    c = MemoryConsolidator(promotion_access_threshold=5)
    memories = [
        _make_memory("memory A", access_count=10),
        _make_memory("memory B", access_count=3),
        _make_memory("memory C", access_count=7),
    ]
    result = c.consolidate(memories)
    assert result.promoted_count == 2  # A and C have >= 5 accesses


def test_no_promotion_below_threshold():
    c = MemoryConsolidator(promotion_access_threshold=10)
    memories = [_make_memory("x", access_count=5)]
    result = c.consolidate(memories)
    assert result.promoted_count == 0


# ── Decay Detection ──


def test_decay_detection():
    c = MemoryConsolidator(decay_strength_threshold=0.2)
    memories = [
        _make_memory("strong", strength=0.8),
        _make_memory("weak", strength=0.1),
        _make_memory("very weak", strength=0.05, memory_type="semantic"),
    ]
    result = c.consolidate(memories)
    assert result.decayed_count == 2  # 0.1 and 0.05 are below 0.2


# ── promote_memory() ──


def test_promote_memory():
    c = MemoryConsolidator()
    memory = _make_memory("remember this", strength=0.6)
    promoted = c.promote_memory(memory)
    assert promoted["memory_type"] == "semantic"
    assert promoted["current_strength"] == pytest.approx(0.9)  # 0.6 * 1.5
    assert "promoted_at" in promoted["metadata"]
    assert promoted["metadata"]["promotion_reason"] == "access_count_threshold"


def test_promote_memory_caps_at_1():
    c = MemoryConsolidator()
    memory = _make_memory("strong memory", strength=0.9)
    promoted = c.promote_memory(memory)
    assert promoted["current_strength"] == pytest.approx(1.0)  # min(1.0, 0.9*1.5)


def test_promote_preserves_original():
    c = MemoryConsolidator()
    memory = _make_memory("original", strength=0.5)
    promoted = c.promote_memory(memory)
    assert memory["memory_type"] == "episodic"  # original unchanged
    assert promoted["memory_type"] == "semantic"


# ── abstract_cluster() ──


def test_abstract_cluster():
    c = MemoryConsolidator()
    candidate = ConsolidationCandidate(
        cluster_id="c1",
        memories=[
            _make_memory("the cat sat", tags=["animal", "action"]),
            _make_memory("the cat ran", tags=["animal", "action"]),
            _make_memory("the cat jumped", tags=["animal", "movement"]),
        ],
        centroid_content="the cat sat",
        mean_strength=0.6,
        access_count=10,
        similarity_score=0.7,
    )
    abstract = c.abstract_cluster(candidate)
    assert abstract["memory_type"] == "semantic"
    assert abstract["content"] == "the cat sat"
    assert abstract["current_strength"] == pytest.approx(0.72)  # 0.6 * 1.2
    assert abstract["decay_rate"] == 0.05
    assert abstract["metadata"]["consolidated_from"] == 3
    assert "consolidated_at" in abstract["metadata"]


def test_abstract_cluster_caps_strength():
    c = MemoryConsolidator()
    candidate = ConsolidationCandidate(
        cluster_id="c2",
        memories=[],
        centroid_content="strong",
        mean_strength=0.95,
        access_count=0,
        similarity_score=0.8,
    )
    abstract = c.abstract_cluster(candidate)
    assert abstract["current_strength"] == pytest.approx(1.0)


# ── Common Tags Extraction ──


def test_common_tags_majority():
    c = MemoryConsolidator()
    candidate = ConsolidationCandidate(
        cluster_id="c3",
        memories=[
            _make_memory("a", tags=["x", "y"]),
            _make_memory("b", tags=["x", "z"]),
            _make_memory("c", tags=["x", "y"]),
        ],
        centroid_content="a",
        mean_strength=0.5,
        access_count=0,
        similarity_score=0.6,
    )
    abstract = c.abstract_cluster(candidate)
    # "x" appears 3/3, "y" 2/3 (>= 1.5), "z" 1/3 (< 1.5)
    assert "x" in abstract["tags"]
    assert "y" in abstract["tags"]
    assert "z" not in abstract["tags"]


# ── Text Similarity ──


def test_text_similarity_identical():
    c = MemoryConsolidator()
    assert c._text_similarity("hello world", "hello world") == pytest.approx(1.0)


def test_text_similarity_no_overlap():
    c = MemoryConsolidator()
    assert c._text_similarity("alpha beta", "gamma delta") == pytest.approx(0.0)


def test_text_similarity_partial():
    c = MemoryConsolidator()
    sim = c._text_similarity("the cat sat", "the dog sat")
    # intersection: {the, sat} = 2, union: {the, cat, sat, dog} = 4
    assert sim == pytest.approx(0.5)


def test_text_similarity_empty():
    c = MemoryConsolidator()
    assert c._text_similarity("", "hello") == 0.0
    assert c._text_similarity("hello", "") == 0.0
    assert c._text_similarity("", "") == 0.0


def test_text_similarity_case_insensitive():
    c = MemoryConsolidator()
    assert c._text_similarity("Hello World", "hello world") == pytest.approx(1.0)


# ── Timestamp ──


def test_result_has_timestamp():
    c = MemoryConsolidator()
    result = c.consolidate([])
    assert result.timestamp is not None
    assert "T" in result.timestamp  # ISO format


# ── Integration: Full Pipeline ──


def test_full_consolidation_pipeline():
    c = MemoryConsolidator(
        min_cluster_size=2,
        similarity_threshold=0.3,
        promotion_access_threshold=3,
        decay_strength_threshold=0.15,
    )
    memories = [
        _make_memory("the cat sat on the mat", strength=0.7, tags=["animal"], access_count=5),
        _make_memory("the cat sat on the hat", strength=0.6, tags=["animal"], access_count=1),
        _make_memory("the cat played on the mat", strength=0.5, tags=["animal"], access_count=4),
        _make_memory("quantum physics explains entanglement", strength=0.3, access_count=0),
        _make_memory("weak forgotten memory", strength=0.1, access_count=0),
    ]
    result = c.consolidate(memories)

    assert result.consolidated_count >= 1  # cat cluster
    assert result.promoted_count >= 1  # access_count >= 3
    assert result.decayed_count >= 1  # strength 0.1 < 0.15

    # Verify candidates
    for candidate in result.candidates:
        abstract = c.abstract_cluster(candidate)
        assert abstract["memory_type"] == "semantic"
        assert abstract["current_strength"] > 0
