"""
Memory Consolidation — v4 §8 (AGI Layer 8)
=============================================

Consolidates episodic (short-term) memories into semantic (long-term)
memories by detecting repeated patterns and abstracting them.

Inspired by neuroscience:
- Hippocampal replay: episodic memories replayed during "rest"
- Pattern completion: similar memories merged into abstractions
- Strength-based promotion: frequently accessed memories promoted

Integrates with:
- contracts/v4/memory_entry.py (MemoryEntry, BoundaryZone, MemoryType)
- memory/forgetting.py (decay semantics)
"""

import math
import logging
from typing import Callable, List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Type alias: sync callable that maps text → embedding vector (or None on failure)
EmbeddingFn = Callable[[str], Optional[List[float]]]

# ── Tunable Parameters (Tier A: Research Engine may modify) ──
min_cluster_size = 2
similarity_threshold = 0.5
promotion_access_threshold = 3
decay_strength_threshold = 0.1


@dataclass
class ConsolidationCandidate:
    """A cluster of related memories that could be consolidated."""
    cluster_id: str
    memories: List[Dict]  # Serialized MemoryEntry dicts
    centroid_content: str
    mean_strength: float
    access_count: int
    similarity_score: float


@dataclass
class ConsolidationResult:
    """Result of memory consolidation run."""
    consolidated_count: int  # Number of semantic memories created
    promoted_count: int  # Number of memories promoted (episodic→semantic)
    decayed_count: int  # Number of weak memories marked for decay
    candidates: List[ConsolidationCandidate]
    timestamp: str


class MemoryConsolidator:
    """
    Consolidate episodic memories into semantic memories.

    Process:
    1. Cluster episodic memories by text similarity
    2. For clusters with 3+ members: create abstract semantic memory
    3. Promote frequently-accessed episodic memories to semantic
    4. Flag weak memories (low strength) for accelerated decay

    Usage:
        consolidator = MemoryConsolidator()
        result = consolidator.consolidate(episodic_memories)
        for semantic in result.candidates:
            # Store as semantic memory
    """

    def __init__(
        self,
        _min_cluster_size: int | None = None,
        _similarity_threshold: float | None = None,
        _promotion_access_threshold: int | None = None,
        _decay_strength_threshold: float | None = None,
        embedding_fn: Optional[EmbeddingFn] = None,
        **kwargs,
    ):
        """
        Args:
            _min_cluster_size: Override module-level min_cluster_size
            _similarity_threshold: Override module-level similarity_threshold
            _promotion_access_threshold: Override module-level promotion_access_threshold
            _decay_strength_threshold: Override module-level decay_strength_threshold
            embedding_fn: Optional sync callable (text → List[float]) for
                          embedding-based similarity. When provided, cosine
                          similarity replaces Jaccard word overlap.

        Also accepts non-prefixed kwargs for backward compatibility.
        """
        # Accept both _prefixed and non-prefixed param names
        if _min_cluster_size is None:
            _min_cluster_size = kwargs.get("min_cluster_size")
        if _similarity_threshold is None:
            _similarity_threshold = kwargs.get("similarity_threshold")
        if _promotion_access_threshold is None:
            _promotion_access_threshold = kwargs.get("promotion_access_threshold")
        if _decay_strength_threshold is None:
            _decay_strength_threshold = kwargs.get("decay_strength_threshold")

        self.min_cluster_size = _min_cluster_size if _min_cluster_size is not None else min_cluster_size
        self.similarity_threshold = _similarity_threshold if _similarity_threshold is not None else similarity_threshold
        self.promotion_access_threshold = _promotion_access_threshold if _promotion_access_threshold is not None else promotion_access_threshold
        self.decay_strength_threshold = _decay_strength_threshold if _decay_strength_threshold is not None else decay_strength_threshold
        self.embedding_fn = embedding_fn
        self._embedding_cache: Dict[str, List[float]] = {}

    def consolidate(
        self,
        memories: List[Dict],
    ) -> ConsolidationResult:
        """
        Run consolidation on a set of episodic memories.

        Args:
            memories: List of serialized MemoryEntry dicts with at least:
                      content, memory_type, current_strength, tags

        Returns:
            ConsolidationResult with candidates for semantic creation
        """
        if not memories:
            return ConsolidationResult(
                consolidated_count=0,
                promoted_count=0,
                decayed_count=0,
                candidates=[],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Step 1: Filter to episodic/working memories
        episodic = [
            m for m in memories
            if m.get("memory_type") in ("episodic", "working")
        ]

        # Step 2: Cluster by text similarity
        clusters = self._cluster_by_similarity(episodic)

        # Step 3: Identify consolidation candidates
        candidates = []
        consolidated_count = 0
        for cluster_id, cluster_members in clusters.items():
            if len(cluster_members) >= self.min_cluster_size:
                candidate = self._create_candidate(cluster_id, cluster_members)
                candidates.append(candidate)
                consolidated_count += 1

        # Step 4: Identify promotion candidates
        promoted_count = 0
        for m in episodic:
            access_count = m.get("metadata", {}).get("access_count", 0)
            if access_count >= self.promotion_access_threshold:
                promoted_count += 1

        # Step 5: Identify decay candidates
        decayed_count = sum(
            1 for m in memories
            if m.get("current_strength", 1.0) < self.decay_strength_threshold
        )

        return ConsolidationResult(
            consolidated_count=consolidated_count,
            promoted_count=promoted_count,
            decayed_count=decayed_count,
            candidates=candidates,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def promote_memory(self, memory: Dict) -> Dict:
        """
        Promote an episodic memory to semantic.

        Args:
            memory: Serialized MemoryEntry dict

        Returns:
            Updated memory dict with memory_type="semantic"
        """
        promoted = dict(memory)
        promoted["memory_type"] = "semantic"
        promoted["current_strength"] = min(1.0, memory.get("current_strength", 0.5) * 1.5)
        promoted["metadata"] = dict(promoted.get("metadata", {}))
        promoted["metadata"]["promoted_at"] = datetime.now(timezone.utc).isoformat()
        promoted["metadata"]["promotion_reason"] = "access_count_threshold"
        return promoted

    def abstract_cluster(self, candidate: ConsolidationCandidate) -> Dict:
        """
        Create an abstract semantic memory from a cluster.

        Args:
            candidate: ConsolidationCandidate with cluster details

        Returns:
            New semantic MemoryEntry dict
        """
        return {
            "content": candidate.centroid_content,
            "memory_type": "semantic",
            "boundary_zone": "adaptive",
            "current_strength": min(1.0, candidate.mean_strength * 1.2),
            "decay_rate": 0.05,  # Semantic memories decay slower
            "tags": self._extract_common_tags(candidate.memories),
            "metadata": {
                "consolidated_from": len(candidate.memories),
                "consolidated_at": datetime.now(timezone.utc).isoformat(),
                "cluster_similarity": candidate.similarity_score,
            },
        }

    def _cluster_by_similarity(
        self, memories: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Cluster memories by semantic similarity.

        Uses embedding-based cosine similarity when embeddings are available
        (via embedding_vector field or embedding_fn). Falls back to Jaccard
        word overlap when embeddings are unavailable.
        """
        clusters: Dict[str, List[Dict]] = {}
        assigned: set = set()

        for i, mem_a in enumerate(memories):
            if i in assigned:
                continue

            cluster_id = f"cluster_{i}"
            cluster = [mem_a]
            assigned.add(i)

            for j, mem_b in enumerate(memories):
                if j in assigned or j == i:
                    continue

                sim = self._compute_similarity(mem_a, mem_b)
                if sim >= self.similarity_threshold:
                    cluster.append(mem_b)
                    assigned.add(j)

            if len(cluster) > 1:
                clusters[cluster_id] = cluster

        return clusters

    def _create_candidate(
        self, cluster_id: str, members: List[Dict]
    ) -> ConsolidationCandidate:
        """Create a ConsolidationCandidate from a cluster."""
        # Pick the most representative content (highest strength)
        best = max(members, key=lambda m: m.get("current_strength", 0.0))
        centroid = best.get("content", "")

        mean_strength = sum(
            m.get("current_strength", 0.5) for m in members
        ) / len(members)

        total_access = sum(
            m.get("metadata", {}).get("access_count", 0) for m in members
        )

        # Average pairwise similarity
        sims = []
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                sims.append(self._compute_similarity(a, b))
        avg_sim = sum(sims) / len(sims) if sims else 0.0

        return ConsolidationCandidate(
            cluster_id=cluster_id,
            memories=members,
            centroid_content=centroid,
            mean_strength=mean_strength,
            access_count=total_access,
            similarity_score=avg_sim,
        )

    def _compute_similarity(self, mem_a: Dict, mem_b: Dict) -> float:
        """Compute similarity between two memories.

        Priority:
        1. Pre-computed embedding_vector in memory dict → cosine similarity
        2. On-the-fly embedding via embedding_fn → cosine similarity (cached)
        3. Jaccard word overlap fallback
        """
        vec_a = mem_a.get("embedding_vector") or self._get_embedding(
            mem_a.get("content", "")
        )
        vec_b = mem_b.get("embedding_vector") or self._get_embedding(
            mem_b.get("content", "")
        )
        if vec_a is not None and vec_b is not None:
            return self._cosine_similarity(vec_a, vec_b)
        return self._text_similarity(
            mem_a.get("content", ""), mem_b.get("content", "")
        )

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text via embedding_fn with local caching."""
        if not text or not self.embedding_fn:
            return None
        if text in self._embedding_cache:
            return self._embedding_cache[text]
        try:
            vec = self.embedding_fn(text)
        except Exception:
            logger.debug("embedding_fn failed for text, falling back to Jaccard")
            return None
        if vec is not None:
            self._embedding_cache[text] = vec
        return vec

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _text_similarity(self, a: str, b: str) -> float:
        """Jaccard similarity between word sets (fallback)."""
        if not a or not b:
            return 0.0
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        intersection = words_a & words_b
        union = words_a | words_b
        if not union:
            return 0.0
        return len(intersection) / len(union)

    def _extract_common_tags(self, memories: List[Dict]) -> List[str]:
        """Extract tags common to majority of cluster members."""
        if not memories:
            return []
        tag_counts: Dict[str, int] = {}
        for m in memories:
            for tag in m.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        threshold = len(memories) / 2
        return [tag for tag, count in tag_counts.items() if count >= threshold]

    # ── Feedback Channel 4: Priority Boost (Reflect → UpdateMemory) ──────

    def set_priority_boost(
        self,
        memory_ids: List[str],
        boost: float = 1.5,
    ) -> int:
        """
        Set consolidation priority boost for specific memories.

        Boosted memories receive higher effective similarity during clustering,
        making them more likely to form or join clusters and be consolidated.
        Boost is consumed after one consolidation run (single-use).

        Args:
            memory_ids: List of memory IDs to boost
            boost: Multiplier for effective similarity (1.0 = no boost, 2.0 = max)

        Returns:
            Number of boosts applied
        """
        if not hasattr(self, '_priority_boosts'):
            self._priority_boosts: Dict[str, float] = {}

        boost = max(1.0, min(2.0, boost))
        count = 0
        for mid in memory_ids:
            self._priority_boosts[mid] = boost
            count += 1
        return count

    def get_priority_boosts(self) -> Dict[str, float]:
        """Get current priority boost map."""
        if not hasattr(self, '_priority_boosts'):
            return {}
        return dict(self._priority_boosts)

    def clear_priority_boosts(self) -> None:
        """Clear all priority boosts (called after consolidation run)."""
        if hasattr(self, '_priority_boosts'):
            self._priority_boosts.clear()

    def get_effective_strength(self, memory: Dict) -> float:
        """Get memory strength with priority boost applied."""
        base_strength = memory.get("current_strength", 0.5)
        if not hasattr(self, '_priority_boosts'):
            return base_strength
        memory_id = memory.get("id", memory.get("memory_id", ""))
        boost = self._priority_boosts.get(memory_id, 1.0)
        return min(1.0, base_strength * boost)
