"""
Tests for Embedding-Based Memory Consolidation
================================================

Validates that MemoryConsolidator correctly uses embedding-based cosine
similarity when available, with proper fallback to Jaccard word overlap.

Three embedding sources tested:
1. Pre-computed embedding_vector in memory dict
2. On-the-fly embedding via embedding_fn callable
3. Jaccard fallback when neither is available

Mind-loop stages: UpdateMemory (memory consolidation)
Cognitive vs. automation: Cognitive (semantic memory formation)
"""

import math
import pytest

from phionyx_core.memory.consolidation import (
    EmbeddingFn,
    MemoryConsolidator,
    ConsolidationCandidate,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_memory(
    content,
    memory_type="episodic",
    strength=0.5,
    tags=None,
    access_count=0,
    embedding_vector=None,
):
    m = {
        "content": content,
        "memory_type": memory_type,
        "current_strength": strength,
        "tags": tags or [],
        "metadata": {"access_count": access_count},
    }
    if embedding_vector is not None:
        m["embedding_vector"] = embedding_vector
    return m


def _simple_embedding(text: str) -> list[float]:
    """Deterministic toy embedding: word-hash based 8-dim vector, normalized."""
    if not text:
        return [0.0] * 8
    vec = [0.0] * 8
    for word in text.lower().split():
        h = hash(word) % 1000
        for i in range(8):
            vec[i] += ((h >> i) & 1) * 0.1
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


# ── Cosine Similarity Unit Tests ─────────────────────────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        c = MemoryConsolidator()
        vec = [1.0, 0.0, 0.0]
        assert c._cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        c = MemoryConsolidator()
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert c._cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        c = MemoryConsolidator()
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert c._cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_similar_vectors(self):
        c = MemoryConsolidator()
        a = [1.0, 1.0, 0.0]
        b = [1.0, 0.9, 0.1]
        sim = c._cosine_similarity(a, b)
        assert 0.9 < sim < 1.0

    def test_empty_vectors(self):
        c = MemoryConsolidator()
        assert c._cosine_similarity([], []) == 0.0

    def test_zero_vectors(self):
        c = MemoryConsolidator()
        assert c._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_mismatched_lengths(self):
        c = MemoryConsolidator()
        assert c._cosine_similarity([1.0, 0.0], [1.0]) == 0.0


# ── Pre-computed Embedding Tests ─────────────────────────────────────────────


class TestPrecomputedEmbeddings:
    def test_similar_embeddings_cluster(self):
        """Memories with similar pre-computed embeddings cluster together."""
        vec_a = [0.9, 0.1, 0.0, 0.0]
        vec_b = [0.85, 0.15, 0.0, 0.0]
        vec_c = [0.0, 0.0, 0.9, 0.1]  # Orthogonal

        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.9)
        memories = [
            _make_memory("topic A first", embedding_vector=vec_a),
            _make_memory("topic A second", embedding_vector=vec_b),
            _make_memory("topic B unrelated", embedding_vector=vec_c),
        ]
        result = c.consolidate(memories)
        assert result.consolidated_count >= 1
        # A and B should cluster, C should not
        cluster = result.candidates[0]
        assert len(cluster.memories) == 2

    def test_dissimilar_embeddings_no_cluster(self):
        """Memories with orthogonal embeddings don't cluster."""
        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.8)
        memories = [
            _make_memory("alpha", embedding_vector=[1.0, 0.0, 0.0]),
            _make_memory("beta", embedding_vector=[0.0, 1.0, 0.0]),
            _make_memory("gamma", embedding_vector=[0.0, 0.0, 1.0]),
        ]
        result = c.consolidate(memories)
        assert result.consolidated_count == 0

    def test_embedding_overrides_jaccard(self):
        """embedding_vector takes priority over text content for similarity."""
        # Same words but orthogonal embeddings → should NOT cluster
        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.5)
        memories = [
            _make_memory(
                "the cat sat on the mat",
                embedding_vector=[1.0, 0.0, 0.0],
            ),
            _make_memory(
                "the cat sat on the hat",  # high Jaccard similarity
                embedding_vector=[0.0, 1.0, 0.0],  # but orthogonal embedding
            ),
        ]
        result = c.consolidate(memories)
        # Should NOT cluster because cosine(orthogonal) = 0.0 < 0.5
        assert result.consolidated_count == 0

    def test_partial_embeddings_mixed(self):
        """When only some memories have embeddings, pairs without fall back to Jaccard."""
        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.3)
        memories = [
            _make_memory(
                "the cat sat on the mat",
                embedding_vector=[0.9, 0.1, 0.0],
            ),
            _make_memory("the cat sat on the hat"),  # no embedding → Jaccard
            _make_memory("completely different topic about space"),
        ]
        result = c.consolidate(memories)
        # Cat memories should still cluster via Jaccard fallback
        assert result.consolidated_count >= 1


# ── On-the-fly Embedding (embedding_fn) Tests ────────────────────────────────


class TestEmbeddingFn:
    def test_embedding_fn_used_for_similarity(self):
        """embedding_fn produces vectors for similarity computation."""
        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.5,
            embedding_fn=_simple_embedding,
        )
        memories = [
            _make_memory("the cat sat on the mat"),
            _make_memory("the cat sat on the hat"),
            _make_memory("quantum physics string theory"),
        ]
        result = c.consolidate(memories)
        # Cat memories should cluster (similar embeddings)
        assert result.consolidated_count >= 1

    def test_embedding_fn_cached(self):
        """Same text should not call embedding_fn twice."""
        call_count = 0

        def counting_embedding(text):
            nonlocal call_count
            call_count += 1
            return _simple_embedding(text)

        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.3,
            embedding_fn=counting_embedding,
        )
        memories = [
            _make_memory("same content here"),
            _make_memory("same content here"),  # duplicate text
        ]
        c.consolidate(memories)
        # "same content here" should be embedded once (cached), not twice
        assert call_count == 1

    def test_embedding_fn_failure_falls_back(self):
        """If embedding_fn raises, fall back to Jaccard without crashing."""

        def failing_embedding(text):
            raise RuntimeError("embedding service down")

        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.3,
            embedding_fn=failing_embedding,
        )
        memories = [
            _make_memory("the cat sat on the mat"),
            _make_memory("the cat sat on the hat"),
        ]
        result = c.consolidate(memories)
        # Should still work via Jaccard fallback
        assert result.consolidated_count >= 1

    def test_embedding_fn_returns_none_falls_back(self):
        """If embedding_fn returns None, fall back to Jaccard."""
        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.3,
            embedding_fn=lambda text: None,
        )
        memories = [
            _make_memory("the cat sat on the mat"),
            _make_memory("the cat sat on the hat"),
        ]
        result = c.consolidate(memories)
        assert result.consolidated_count >= 1

    def test_precomputed_overrides_embedding_fn(self):
        """Pre-computed embedding_vector takes priority over embedding_fn."""
        fn_called = False

        def tracking_fn(text):
            nonlocal fn_called
            fn_called = True
            return _simple_embedding(text)

        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.9,
            embedding_fn=tracking_fn,
        )
        # Both have pre-computed embeddings → fn should not be called
        memories = [
            _make_memory("a", embedding_vector=[0.9, 0.1, 0.0]),
            _make_memory("b", embedding_vector=[0.85, 0.15, 0.0]),
        ]
        c.consolidate(memories)
        assert not fn_called


# ── Candidate Similarity Score with Embeddings ───────────────────────────────


class TestCandidateSimilarityScore:
    def test_candidate_similarity_uses_embedding(self):
        """Pairwise similarity in candidates uses embedding when available."""
        vec = [0.9, 0.1, 0.0]
        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.5)
        memories = [
            _make_memory("a", embedding_vector=vec),
            _make_memory("b", embedding_vector=vec),
        ]
        result = c.consolidate(memories)
        assert result.consolidated_count == 1
        # Identical vectors → similarity ≈ 1.0
        assert result.candidates[0].similarity_score == pytest.approx(1.0)

    def test_candidate_similarity_mixed(self):
        """Candidate with mixed embeddings computes correct avg similarity."""
        c = MemoryConsolidator(
            min_cluster_size=2,
            similarity_threshold=0.5,
            embedding_fn=_simple_embedding,
        )
        memories = [
            _make_memory("the cat sat on the mat"),
            _make_memory("the cat sat on the hat"),
            _make_memory("the cat played on the mat"),
        ]
        result = c.consolidate(memories)
        if result.candidates:
            # Similarity score should be a reasonable value
            assert 0.0 < result.candidates[0].similarity_score <= 1.0


# ── Backward Compatibility ───────────────────────────────────────────────────


class TestBackwardCompatibility:
    def test_no_embedding_uses_jaccard(self):
        """Without embedding_fn or embedding_vector, Jaccard is used."""
        c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.3)
        memories = [
            _make_memory("the cat sat on the mat"),
            _make_memory("the cat sat on the hat"),
        ]
        result = c.consolidate(memories)
        assert result.consolidated_count >= 1

    def test_jaccard_still_works_directly(self):
        """_text_similarity still available and functional."""
        c = MemoryConsolidator()
        assert c._text_similarity("hello world", "hello world") == pytest.approx(1.0)
        assert c._text_similarity("alpha beta", "gamma delta") == pytest.approx(0.0)

    def test_existing_kwargs_still_work(self):
        """Non-prefixed kwargs backward compatibility preserved."""
        c = MemoryConsolidator(
            min_cluster_size=3,
            similarity_threshold=0.7,
            promotion_access_threshold=10,
            decay_strength_threshold=0.2,
        )
        assert c.min_cluster_size == 3
        assert c.similarity_threshold == 0.7
        assert c.promotion_access_threshold == 10
        assert c.decay_strength_threshold == 0.2


# ── Determinism ──────────────────────────────────────────────────────────────


class TestEmbeddingDeterminism:
    def test_embedding_consolidation_deterministic(self):
        """Same inputs with embeddings → same output every time."""
        vec_a = [0.9, 0.1, 0.0]
        vec_b = [0.85, 0.15, 0.0]
        vec_c = [0.0, 0.0, 1.0]

        results = []
        for _ in range(5):
            c = MemoryConsolidator(min_cluster_size=2, similarity_threshold=0.8)
            memories = [
                _make_memory("a", embedding_vector=vec_a),
                _make_memory("b", embedding_vector=vec_b),
                _make_memory("c", embedding_vector=vec_c),
            ]
            result = c.consolidate(memories)
            results.append(result.consolidated_count)
        assert len(set(results)) == 1

    def test_embedding_fn_consolidation_deterministic(self):
        """Same inputs with embedding_fn → same output every time."""
        results = []
        for _ in range(5):
            c = MemoryConsolidator(
                min_cluster_size=2,
                similarity_threshold=0.5,
                embedding_fn=_simple_embedding,
            )
            memories = [
                _make_memory("the cat sat"),
                _make_memory("the cat ran"),
                _make_memory("quantum physics"),
            ]
            result = c.consolidate(memories)
            results.append(result.consolidated_count)
        assert len(set(results)) == 1
