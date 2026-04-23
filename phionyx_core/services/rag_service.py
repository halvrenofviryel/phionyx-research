"""
RAG Service
===========

Retrieval Augmented Generation (RAG) service with intent-based optimization.

Features:
- Intent-based query optimization
- Context window pruning
- Semantic decay application (Patent Aile 4)
- Token budget management
- Relevance threshold filtering
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from phionyx_core.memory.rag_cache import get_rag_cache, RAGCache
from phionyx_core.physics.semantic_time_decay import SemanticTimeDecayManager

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG service with intent-based optimization and context management.

    Features:
    - Intent-based query optimization
    - Context window pruning
    - Semantic decay (time-based relevance)
    - Token budget management
    """

    def __init__(
        self,
        vector_store: Optional[Any] = None,
        max_context_tokens: int = 2000,
        relevance_threshold: float = 0.7,
        semantic_decay_half_life_hours: float = 24.0,
        rag_cache: Optional[RAGCache] = None,
        use_semantic_time_decay: bool = True
    ):
        """
        Initialize RAG service.

        Args:
            vector_store: Vector store instance for memory retrieval
            max_context_tokens: Maximum context tokens to inject
            relevance_threshold: Minimum similarity threshold
            semantic_decay_half_life_hours: Semantic decay half-life in hours (Patent Aile 4)
            rag_cache: Optional RAG cache instance
        """
        self.vector_store = vector_store
        self.max_context_tokens = max_context_tokens
        self.relevance_threshold = relevance_threshold
        self.semantic_decay_half_life_hours = semantic_decay_half_life_hours
        self.use_semantic_time_decay = use_semantic_time_decay

        # Initialize Semantic Time Decay Manager (Patent Aile 4)
        if use_semantic_time_decay:
            # Convert hours to seconds for semantic time decay
            half_life_seconds = semantic_decay_half_life_hours * 3600.0
            self.semantic_decay_manager = SemanticTimeDecayManager(
                default_half_life_seconds=half_life_seconds,
                use_local_time=True
            )
        else:
            self.semantic_decay_manager = None

        # Initialize RAG cache
        if rag_cache is None:
            self.rag_cache = get_rag_cache(
                max_size=5000,
                ttl=3600.0,  # 1 hour
                enable_metrics=True
            )
        else:
            self.rag_cache = rag_cache

    async def retrieve_context(
        self,
        query: str,
        intent: Optional[str] = None,
        actor_ref: Optional[str] = None,
        limit: int = 5,
        t_local: Optional[float] = None,
        t_global: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context using RAG.

        Args:
            query: Query text
            intent: Optional intent type for query optimization
            actor_ref: Optional actor reference for scoping
            limit: Maximum number of results

        Returns:
            Dictionary with retrieved context and metadata
        """
        if not self.vector_store or not self.vector_store.is_connected():
            logger.warning("Vector store not available, returning empty context")
            return {
                "context_string": "",
                "memories": [],
                "token_count": 0,
                "relevance_scores": [],
                "method": "fallback"
            }

        try:
            # Check cache first
            cached_memories = self.rag_cache.get(query, intent, actor_ref)
            if cached_memories is not None:
                logger.debug(f"RAG cache hit for query: {query[:50]}...")
                # Build context string from cached memories
                context_string, token_count = self._build_context_string(
                    cached_memories,
                    max_tokens=self.max_context_tokens
                )
                return {
                    "context_string": context_string,
                    "memories": cached_memories,
                    "token_count": token_count,
                    "relevance_scores": [m.get("similarity", 0.0) for m in cached_memories],
                    "method": "rag_cache",
                    "intent_optimized": intent is not None
                }

            logger.debug(f"RAG cache miss for query: {query[:50]}...")

            # Optimize query based on intent
            optimized_query = self._optimize_query_for_intent(query, intent)

            # Retrieve memories
            memories = await self.vector_store.search(
                query=optimized_query,
                actor_ref=actor_ref or "anonymous",
                limit=limit * 2,  # Get more for filtering
                min_similarity=self.relevance_threshold
            )

            # Apply semantic decay (Patent Aile 4)
            # Use semantic time if available, otherwise fall back to wall-clock time
            memories = self._apply_semantic_decay(memories, t_local=t_local, t_global=t_global)

            # Filter by relevance threshold
            filtered_memories = [
                m for m in memories
                if m.get("similarity", 0.0) >= self.relevance_threshold
            ]

            # Limit results
            filtered_memories = filtered_memories[:limit]

            # Build context string with token budget management
            context_string, token_count = self._build_context_string(
                filtered_memories,
                max_tokens=self.max_context_tokens
            )

            # Store in cache
            self.rag_cache.put(query, filtered_memories, intent, actor_ref)
            logger.debug(f"RAG results cached for query: {query[:50]}...")

            # Extract relevance scores
            relevance_scores = [
                m.get("similarity", 0.0) for m in filtered_memories
            ]

            return {
                "context_string": context_string,
                "memories": filtered_memories,
                "token_count": token_count,
                "relevance_scores": relevance_scores,
                "method": "rag",
                "intent_optimized": intent is not None
            }

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}", exc_info=True)
            # Fallback: empty context
            return {
                "context_string": "",
                "memories": [],
                "token_count": 0,
                "relevance_scores": [],
                "method": "fallback",
                "error": str(e)
            }

    def _optimize_query_for_intent(
        self,
        query: str,
        intent: Optional[str] = None
    ) -> str:
        """
        Optimize query based on intent.

        Args:
            query: Original query
            intent: Intent type

        Returns:
            Optimized query string
        """
        if not intent:
            return query

        # Intent-based query optimization
        intent_optimizations = {
            "greeting": query,  # No optimization needed for greetings
            "question": f"{query} answer explanation",  # Emphasize answer-seeking
            "command": f"{query} action instruction",  # Emphasize action
            "conversation": query,  # No optimization
            "high_risk": query,  # No optimization (safety critical)
        }

        return intent_optimizations.get(intent, query)

    def _apply_semantic_decay(
        self,
        memories: List[Dict],
        t_local: Optional[float] = None,
        t_global: Optional[float] = None
    ) -> List[Dict]:
        """
        Apply semantic decay to memories (Patent Aile 4).

        Uses semantic time (t_local, t_global) if available, otherwise falls back
        to wall-clock time for backward compatibility.

        Args:
            memories: List of memory dictionaries
            t_local: Semantic time since last update (seconds) - Patent Aile 4
            t_global: Semantic time since relationship start (seconds) - Patent Aile 4

        Returns:
            Memories with decay-adjusted relevance scores
        """
        if not memories:
            return memories

        # Use semantic time decay if semantic time available and enabled
        if self.use_semantic_time_decay and self.semantic_decay_manager and t_local is not None:
            return self._apply_semantic_time_decay(memories, t_local, t_global)

        # Fall back to wall-clock time decay (backward compatibility)
        return self._apply_wall_clock_decay(memories)

    def _apply_semantic_time_decay(
        self,
        memories: List[Dict],
        t_local: float,
        t_global: Optional[float] = None
    ) -> List[Dict]:
        """
        Apply semantic time decay to memories (Patent Aile 4).

        Uses semantic time (t_local, t_global) instead of wall-clock time.
        This is the core implementation of Patent Family 4: Semantic Time.

        Args:
            memories: List of memory dictionaries
            t_local: Semantic time since last update (seconds)
            t_global: Semantic time since relationship start (seconds)

        Returns:
            Memories with decay-adjusted relevance scores
        """
        if not memories or self.semantic_decay_manager is None:
            return memories

        decayed_memories = []

        for memory in memories:
            try:
                original_similarity = memory.get("similarity", 0.0)

                # Apply semantic time decay using SemanticTimeDecayManager
                decayed_similarity = self.semantic_decay_manager.decay_value(
                    initial_value=original_similarity,
                    t_local=t_local,
                    t_global=t_global or 0.0,
                    use_local_time=True
                )

                # Get decay metadata for reporting
                decay_metadata = self.semantic_decay_manager.get_decay_metadata(
                    t_local=t_local,
                    t_global=t_global or 0.0,
                    use_local_time=True
                )

                # Update memory with decayed score
                memory_copy = memory.copy()
                memory_copy["similarity"] = decayed_similarity
                memory_copy["decay_factor"] = decay_metadata.get("decay_factor", 1.0)
                memory_copy["t_semantic"] = decay_metadata.get("t_semantic", t_local)
                memory_copy["decay_method"] = "semantic_time"  # Patent Aile 4

                decayed_memories.append(memory_copy)
            except Exception as e:
                logger.warning(f"Failed to apply semantic time decay to memory: {e}")
                decayed_memories.append(memory)

        # Re-sort by decayed similarity
        decayed_memories.sort(key=lambda m: m.get("similarity", 0.0), reverse=True)

        return decayed_memories

    def _apply_wall_clock_decay(self, memories: List[Dict]) -> List[Dict]:
        """
        Apply wall-clock time decay to memories (backward compatibility).

        Uses wall-clock time for backward compatibility when semantic time
        is not available.

        Args:
            memories: List of memory dictionaries

        Returns:
            Memories with decay-adjusted relevance scores
        """
        if not memories:
            return memories

        current_time = datetime.now()
        decayed_memories = []

        for memory in memories:
            # Get memory timestamp
            created_at = memory.get("created_at")
            if not created_at:
                # No timestamp - assume recent (no decay)
                decayed_memories.append(memory)
                continue

            # Parse timestamp (assuming ISO format)
            try:
                if isinstance(created_at, str):
                    memory_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    memory_time = created_at

                # Calculate age in hours (wall-clock time)
                age_hours = (current_time - memory_time.replace(tzinfo=None)).total_seconds() / 3600.0

                # Apply exponential decay
                decay_factor = 2 ** (-age_hours / self.semantic_decay_half_life_hours)

                # Adjust similarity score
                original_similarity = memory.get("similarity", 0.0)
                decayed_similarity = original_similarity * decay_factor

                # Update memory with decayed score
                memory_copy = memory.copy()
                memory_copy["similarity"] = decayed_similarity
                memory_copy["decay_factor"] = decay_factor
                memory_copy["age_hours"] = age_hours
                memory_copy["decay_method"] = "wall_clock"  # Backward compatibility

                decayed_memories.append(memory_copy)
            except Exception as e:
                logger.warning(f"Failed to apply wall-clock decay to memory: {e}")
                decayed_memories.append(memory)

        # Re-sort by decayed similarity
        decayed_memories.sort(key=lambda m: m.get("similarity", 0.0), reverse=True)

        return decayed_memories

    def _build_context_string(
        self,
        memories: List[Dict],
        max_tokens: int
    ) -> tuple[str, int]:
        """
        Build context string from memories with token budget management.

        Args:
            memories: List of memory dictionaries
            max_tokens: Maximum token budget

        Returns:
            Tuple of (context_string, token_count)
        """
        if not memories:
            return "", 0

        context_parts = []
        token_count = 0

        # Rough token estimation: 1 token ≈ 4 characters
        chars_per_token = 4

        for memory in memories:
            content = memory.get("content", "")
            if not content:
                continue

            # Estimate tokens
            estimated_tokens = len(content) // chars_per_token

            # Check if adding this memory would exceed budget
            if token_count + estimated_tokens > max_tokens:
                # Try to fit partial content
                remaining_tokens = max_tokens - token_count
                if remaining_tokens > 10:  # Only if meaningful space left
                    remaining_chars = remaining_tokens * chars_per_token
                    content = content[:remaining_chars] + "..."
                    context_parts.append(content)
                    token_count += remaining_tokens
                break

            # Add full memory
            context_parts.append(content)
            token_count += estimated_tokens

        context_string = "\n\n".join(context_parts)

        return context_string, token_count

