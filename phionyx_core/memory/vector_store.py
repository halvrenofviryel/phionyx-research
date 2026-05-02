# mypy: ignore-errors
"""
Vector Store - RAG Operations
==============================

Semantic memory storage and retrieval using Supabase pgvector.

Why ignore-errors: same pattern as `user_profile.py` — supabase is an
optional adapter (`pip install phionyx-core[supabase]`). When it's not
installed, `Client` and `create_client` fall through to `None`. Every
call site is gated on a runtime `if not SUPABASE_AVAILABLE` check, but
mypy can't narrow across that pattern. The type errors are real
ambiguities of an optional integration that is dead code in the public
SDK without the extra installed.
"""

import logging
import os
from typing import TYPE_CHECKING, Optional

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None

# litellm imports removed - using centralized LLM service instead

if TYPE_CHECKING:
    from phionyx_core.contracts.config import ConfigProtocol
    from phionyx_core.contracts.database import MemoryRepositoryProtocol
    from phionyx_core.contracts.llm_provider import LLMProviderProtocol

# Import embedding cache
from phionyx_core.memory.embedding_cache import EmbeddingCache, get_embedding_cache

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector-based memory store using Supabase pgvector.

    Features:
    - Semantic embedding generation (Ollama by default)
    - Similarity search (cosine)
    - Memory importance scoring
    """

    def __init__(
        self,
        llm_provider: Optional['LLMProviderProtocol'] = None,
        memory_repository: Optional['MemoryRepositoryProtocol'] = None,
        embedding_cache: EmbeddingCache | None = None,
        config: Optional['ConfigProtocol'] = None
    ):
        """
        Initialize vector store with Supabase and LLM service for embeddings.

        Args:
            llm_provider: LLM provider service (optional, will attempt to import if not provided).
                         This parameter enables dependency injection and breaks circular dependencies.
            memory_repository: Memory repository (optional). If provided, uses repository for DB access.
                             If None, falls back to direct Supabase client (backward compatible).
        """
        # Store repository (if provided)
        self._memory_repository = memory_repository
        # Configuration: Use config if provided, otherwise fall back to environment variables (backward compatible)
        if config is not None:
            # Preferred path: Use config protocol
            self.supabase_url = config.get_supabase_url()
            self.supabase_key = config.get_supabase_key()
            self.embedding_provider = config.get_embedding_provider()
            self.embedding_model = config.get_embedding_model()
            self.embedding_api_key = config.get_embedding_api_key()
            self.embedding_base_url = config.get_embedding_base_url()
            self._embedding_dimension = config.get_embedding_dimension()
        else:
            # Fallback: Use environment variables (backward compatible)
            self.supabase_url = (
                os.getenv("SUPABASE_URL") or
                os.getenv("ECHO_SUPABASE_URL") or
                os.getenv("SUPABASE_URL")
            )
            self.supabase_key = (
                os.getenv("SUPABASE_SERVICE_KEY") or
                os.getenv("SUPABASE_KEY") or
                os.getenv("ECHO_SUPABASE_KEY") or
                os.getenv("ECHO_SUPABASE_SERVICE_KEY")
            )

            # Embedding provider configuration (via LiteLLM)
            self.embedding_provider = (
                os.getenv("EMBEDDING_PROVIDER") or
                os.getenv("ECHO_EMBEDDING_PROVIDER") or
                "ollama"  # Default to Ollama for local embeddings
            )
            # Default model based on provider
            default_model = "qwen2.5:7b" if self.embedding_provider == "ollama" else "text-embedding-3-small"
            self.embedding_model = (
                os.getenv("EMBEDDING_MODEL") or
                os.getenv("ECHO_EMBEDDING_MODEL") or
                default_model
            )
            # Ollama doesn't require API key for local usage
            self.embedding_api_key = (
                os.getenv("EMBEDDING_API_KEY") or
                os.getenv("ECHO_EMBEDDING_API_KEY") or
                None  # None is OK for Ollama
            )
            self.embedding_base_url = (
                os.getenv("EMBEDDING_BASE_URL") or
                os.getenv("ECHO_EMBEDDING_BASE_URL")
            )  # For local models like Ollama
            self._embedding_dimension = 1536  # Default dimension (backward compatible)

        # Supabase client (fallback if repository not provided)
        if memory_repository is None:
            # Backward compatible: Use direct Supabase client
            if not self.supabase_url or not self.supabase_key:
                logger.warning("Supabase credentials not found. Vector store disabled.")
                self.client: Client | None = None
            else:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase vector store initialized (direct client - backward compatible)")
        else:
            # Use repository (preferred path)
            self.client = None
            logger.info("Vector store initialized with repository (preferred path)")

        # Embedding availability will be checked by LLM service
        # Always assume enabled - LLM service handles availability
        self.embeddings_enabled = True
        self._llm_provider = llm_provider

        # Initialize embedding cache
        if embedding_cache is None:
            # Get cache configuration from config or use defaults
            cache_max_size = 10000
            cache_ttl = 86400.0  # 24 hours
            if config is not None:
                cache_max_size = getattr(config, 'embedding_cache_max_size', cache_max_size)
                cache_ttl = getattr(config, 'embedding_cache_ttl', cache_ttl)
            self._embedding_cache = get_embedding_cache(
                max_size=cache_max_size,
                ttl=cache_ttl,
                enable_metrics=True
            )
        else:
            self._embedding_cache = embedding_cache

        logger.info(f"Embeddings enabled: {self.embedding_provider}/{self.embedding_model} (using LLM service with cache)")

    def is_connected(self) -> bool:
        """Check if Supabase is configured."""
        if self._memory_repository is not None:
            # Repository path: check if repository client is available
            return hasattr(self._memory_repository, 'client') and self._memory_repository.client is not None
        # Fallback: check direct client
        return self.client is not None

    async def generate_embedding(
        self,
        text: str,
        profile_id: str | None = None
    ) -> list[float]:
        """
        Generate semantic embedding for text using centralized LLM service with caching.

        Args:
            text: Text to embed
            profile_id: Optional profile ID for cache scoping

        Returns:
            Embedding vector (dimension depends on model)
        """
        if not self.embeddings_enabled:
            logger.warning("Embeddings not configured. Returning zero vector.")
            return [0.0] * self._embedding_dimension

        # Check cache first
        cached_embedding = self._embedding_cache.get(text, profile_id)
        if cached_embedding is not None:
            logger.debug(f"Embedding cache hit for text: {text[:50]}...")
            return cached_embedding

        logger.debug(f"Embedding cache miss for text: {text[:50]}...")

        llm_service = self._get_llm_provider()
        if not llm_service or not llm_service.available:
            logger.warning("VectorStore: LLM service not available, returning zero vector")
            return [0.0] * 1536

        try:
            # Generate embedding using LLM service
            # Note: use_cache=False here because we handle caching at this layer
            embedding_vector = await llm_service.embedding(text, model=self.embedding_model, use_cache=False)

            if embedding_vector:
                # Store in cache
                self._embedding_cache.put(text, embedding_vector, profile_id)
                logger.debug(f"Embedding cached for text: {text[:50]}...")
                return embedding_vector
            else:
                logger.warning("VectorStore: Failed to generate embedding: Service returned None")
                return [0.0] * 1536

        except Exception as e:
            logger.error(f"Failed to generate embedding with {self.embedding_provider}/{self.embedding_model}: {e}")
            return [0.0] * 1536

    def _get_llm_provider(self) -> Optional['LLMProviderProtocol']:
        """
        Get LLM provider (dependency injection only).

        Returns:
            LLM provider instance or None if unavailable

        Raises:
            RuntimeError: If LLM provider is not injected (architectural violation)
        """
        # If provided via dependency injection, use it
        if self._llm_provider is not None:
            return self._llm_provider

        # No fallback - architectural violation removed
        logger.error(
            "LLM provider not injected. "
            "VectorStore requires LLMProviderProtocol to be passed via __init__. "
            "This is a dependency injection requirement to maintain layer isolation."
        )
        return None

    async def add_memory(
        self,
        content: str,
        actor_ref: str,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        embedding: list[float] | None = None,
        importance: float = 0.5,
        metadata: dict | None = None,
        context_tags: list[str] | None = None
    ) -> str | None:
        """
        Add a memory to the vector store.

        Args:
            content: Memory text
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            embedding: Pre-computed embedding (optional)
            importance: Importance score (0-1)
            metadata: Additional metadata
            context_tags: Optional list of context tags (e.g., ["sdk_architecture", "api_design"])

        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.is_connected():
            logger.warning("Supabase not connected. Memory not saved.")
            return None

        # Generate embedding if not provided (with cache, scoped to actor_ref)
        if embedding is None:
            embedding = await self.generate_embedding(content, profile_id=actor_ref)

        try:
            # Store metadata as JSONB
            # Note: Database column is still "user_id" for backward compatibility with existing data
            # SPRINT 5: We pass actor_ref but store it in user_id column (migration can happen later)
            insert_data = {
                "user_id": actor_ref,  # SPRINT 5: Store actor_ref in user_id column (DB migration later)
                "actor_ref": actor_ref,  # Also include actor_ref for future migration
                "content": content,
                "embedding": embedding,
                "importance": importance
            }
            if metadata:
                insert_data["metadata"] = metadata
            if context_tags:
                insert_data["context_tags"] = context_tags

            # Use repository if available (preferred path)
            if self._memory_repository is not None:
                memory_id = self._memory_repository.insert_memory(insert_data)
                if memory_id:
                    logger.info(f"Memory saved via repository: {memory_id}")
                    return memory_id
                return None

            # Fallback: Direct Supabase client (backward compatible)
            if not self.client:
                logger.warning("Supabase client not available. Memory not saved.")
                return None

            result = self.client.table("memories").insert(insert_data).execute()

            if result.data:
                memory_id = result.data[0]["id"]
                logger.info(f"Memory saved: {memory_id}")
                return memory_id
            return None
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return None

    async def store(
        self,
        content: str,
        metadata: dict | None = None,
        context_tags: list[str] | None = None
    ) -> str | None:
        """
        Store a memory (alias for add_memory for backward compatibility).

        Args:
            content: Memory text
            metadata: Additional metadata (must include user_id)
            context_tags: Optional list of context tags

        Returns:
            Memory ID if successful, None otherwise
        """
        # SPRINT 5: Support both actor_ref and user_id in metadata for backward compatibility during migration
        actor_ref = metadata.get("actor_ref") or metadata.get("user_id")
        if not actor_ref:
            logger.error("VectorStore.store: metadata must include 'actor_ref' or 'user_id'")
            return None

        importance = metadata.get("importance", 0.5)

        return await self.add_memory(
            content=content,
            actor_ref=actor_ref,  # SPRINT 5: Use actor_ref
            importance=importance,
            metadata=metadata,
            context_tags=context_tags
        )

    async def search_similar(
        self,
        query_embedding: list[float],
        actor_ref: str,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        limit: int = 3,
        threshold: float = 0.7,
        filter_tags: list[str] | None = None
    ) -> list[dict]:
        """
        Search for similar memories using cosine similarity.

        Args:
            query_embedding: Query vector
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            limit: Max results
            threshold: Similarity threshold
            filter_tags: Optional list of context tags to filter by (e.g., ["sdk_architecture"])

        Returns:
            List of similar memories
        """
        if not self.is_connected():
            return []

        try:
            # Build RPC arguments
            # Note: RPC function still uses "match_user_id" parameter name (DB migration later)
            rpc_args = {
                "query_embedding": query_embedding,
                "match_user_id": actor_ref,  # SPRINT 5: Pass actor_ref to match_user_id (DB migration later)
                "match_threshold": threshold,
                "match_count": limit
            }

            # Add filter_tags if provided
            if filter_tags:
                rpc_args["filter_tags"] = filter_tags

            # Use Supabase RPC function for similarity search
            result = self.client.rpc("match_memories", rpc_args).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def search(
        self,
        query: str,
        actor_ref: str,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        limit: int = 3,
        min_similarity: float = 0.7,
        metadata_filter: dict | None = None
    ) -> list[dict]:
        """
        Search for relevant memories with optional metadata filtering.

        Args:
            query: Query text
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            limit: Max results
            min_similarity: Minimum similarity threshold
            metadata_filter: Optional metadata filter (e.g., {"memory_type": "behavioral_correction"})

        Returns:
            List of relevant memories with content and metadata
        """
        # Generate query embedding (with cache, scoped to actor_ref)
        query_embedding = await self.generate_embedding(query, profile_id=actor_ref)

        if not self.is_connected():
            return []

        try:
            # If metadata filter is provided, we need to filter after retrieval
            # (match_memories function doesn't support metadata filtering yet)
            # Extract filter_tags from metadata_filter if present
            filter_tags = None
            if metadata_filter and "tags" in metadata_filter:
                filter_tags = metadata_filter["tags"]
                if isinstance(filter_tags, str):
                    filter_tags = [filter_tags]

            results = await self.search_similar(
                query_embedding,
                actor_ref,  # SPRINT 5: Use actor_ref
                limit * 2,
                min_similarity,
                filter_tags=filter_tags
            )

            # Apply metadata filter if provided
            if metadata_filter and results:
                filtered_results = []
                for result in results:
                    # Get full memory record to check metadata
                    memory_id = result.get("id")
                    if memory_id:
                        try:
                            # Use repository if available (preferred path)
                            if self._memory_repository is not None:
                                full_memory_dict = self._memory_repository.get_memory(memory_id)
                                if full_memory_dict:
                                    memory_metadata = full_memory_dict.get("metadata", {})
                                else:
                                    continue
                            else:
                                # Fallback: Direct Supabase client (backward compatible)
                                full_memory = self.client.table("memories").select("*").eq("id", memory_id).execute()
                                if full_memory.data:
                                    memory_metadata = full_memory.data[0].get("metadata", {})
                                else:
                                    continue

                            # Check if all filter conditions match
                            match = True
                            for key, value in metadata_filter.items():
                                if isinstance(memory_metadata, dict):
                                    if memory_metadata.get(key) != value:
                                        match = False
                                        break
                                else:
                                    match = False
                                    break

                            if match:
                                filtered_results.append(result)
                                if len(filtered_results) >= limit:
                                    break
                        except Exception as e:
                            logger.warning(f"Failed to check metadata for memory {memory_id}: {e}")
                            continue

                return filtered_results[:limit]

            return results[:limit]
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def retrieve_relevant(
        self,
        query: str,
        limit: int = 5,
        filter_tags: list[str] | None = None,
        actor_ref: str | None = None  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
    ) -> list[dict]:
        """
        Retrieve relevant memories (alias for search_similar for backward compatibility).

        Args:
            query: Query text
            limit: Max results
            filter_tags: Optional list of context tags to filter by
            actor_ref: Optional actor reference for filtering (core-neutral identifier, replaces user_id)

        Returns:
            List of relevant memories
        """
        if not self.is_connected():
            return []

        # Generate embedding for query (with cache, scoped to actor_ref)
        query_embedding = await self.generate_embedding(query, profile_id=actor_ref or "anonymous")

        # Use search_similar
        results = await self.search_similar(
            query_embedding=query_embedding,
            actor_ref=actor_ref or "anonymous",  # SPRINT 5: Use actor_ref
            limit=limit,
            filter_tags=filter_tags
        )

        return results

    async def retrieve_relevant_legacy(
        self,
        query_text: str,
        user_id: str,
        limit: int = 3,
        filter_tags: list[str] | None = None
    ) -> list[dict]:
        """
        Retrieve relevant memories for a query with optional context tag filtering.

        Args:
            query_text: Query text
            user_id: User UUID
            limit: Max results
            filter_tags: Optional list of context tags to filter by (e.g., ["sdk_architecture", "api_design"])
                        Only memories with at least one matching tag will be returned.

        Returns:
            List of relevant memories with content and metadata
        """
        # Generate query embedding (with cache, scoped to user_id for backward compatibility)
        query_embedding = await self.generate_embedding(query_text, profile_id=user_id)

        # Search similar with tag filtering
        results = await self.search_similar(
            query_embedding,
            user_id,
            limit,
            filter_tags=filter_tags
        )

        return results

