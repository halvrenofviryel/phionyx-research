"""
Unit tests for RAG Service
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from phionyx_core.services.rag_service import RAGService
from phionyx_core.memory.rag_cache import RAGCache


class TestRAGService:
    """Test RAGService."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = Mock()
        store.is_connected.return_value = True
        store.search = AsyncMock(return_value=[
            {
                "id": "1",
                "content": "Test memory 1",
                "similarity": 0.8,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "content": "Test memory 2",
                "similarity": 0.75,
                "created_at": (datetime.now() - timedelta(hours=12)).isoformat()
            }
        ])
        return store

    @pytest.fixture
    def rag_service(self, mock_vector_store):
        """Create RAGService instance with fresh cache (no singleton leakage)."""
        return RAGService(
            vector_store=mock_vector_store,
            max_context_tokens=2000,
            relevance_threshold=0.7,
            rag_cache=RAGCache(max_size=100, ttl=3600.0),
        )

    @pytest.mark.asyncio
    async def test_retrieve_context_success(self, rag_service):
        """Test successful context retrieval."""
        result = await rag_service.retrieve_context(
            query="test query",
            intent="question",
            actor_ref="test_user",
            limit=5
        )

        assert result["method"] == "rag"
        assert "context_string" in result
        assert "memories" in result
        assert "token_count" in result
        assert len(result["memories"]) > 0
        assert result["intent_optimized"] is True

    @pytest.mark.asyncio
    async def test_retrieve_context_no_vector_store(self):
        """Test context retrieval without vector store."""
        service = RAGService(vector_store=None)
        result = await service.retrieve_context("test query")

        assert result["method"] == "fallback"
        assert result["context_string"] == ""
        assert len(result["memories"]) == 0

    @pytest.mark.asyncio
    async def test_retrieve_context_vector_store_not_connected(self, rag_service):
        """Test context retrieval when vector store is not connected."""
        rag_service.vector_store.is_connected.return_value = False
        result = await rag_service.retrieve_context("test query")

        assert result["method"] == "fallback"
        assert result["context_string"] == ""

    @pytest.mark.asyncio
    async def test_intent_based_query_optimization(self, rag_service):
        """Test intent-based query optimization."""
        # Test question intent optimization
        _result = await rag_service.retrieve_context(
            query="test",
            intent="question"
        )

        # Verify that query was optimized (check mock call)
        rag_service.vector_store.search.assert_called()
        call_args = rag_service.vector_store.search.call_args
        optimized_query = call_args[1]["query"]

        # Question intent should add "answer explanation"
        assert "answer" in optimized_query.lower() or "explanation" in optimized_query.lower()

    @pytest.mark.asyncio
    async def test_semantic_decay_application(self, rag_service):
        """Test semantic decay application."""
        # Create memories with different ages
        old_memory = {
            "id": "old",
            "content": "Old memory",
            "similarity": 0.8,
            "created_at": (datetime.now() - timedelta(hours=48)).isoformat()
        }

        new_memory = {
            "id": "new",
            "content": "New memory",
            "similarity": 0.8,
            "created_at": datetime.now().isoformat()
        }

        rag_service.vector_store.search = AsyncMock(return_value=[old_memory, new_memory])

        result = await rag_service.retrieve_context("test query")

        # Old memory should have lower similarity after decay
        memories = result["memories"]
        old_mem = next((m for m in memories if m["id"] == "old"), None)
        new_mem = next((m for m in memories if m["id"] == "new"), None)

        if old_mem and new_mem:
            # Old memory should have decay factor applied
            assert "decay_factor" in old_mem
            assert old_mem["decay_factor"] < 1.0

    @pytest.mark.asyncio
    async def test_relevance_threshold_filtering(self, rag_service):
        """Test relevance threshold filtering."""
        # Create memories with varying similarity scores
        memories = [
            {"id": "1", "content": "High relevance", "similarity": 0.9, "created_at": datetime.now().isoformat()},
            {"id": "2", "content": "Medium relevance", "similarity": 0.75, "created_at": datetime.now().isoformat()},
            {"id": "3", "content": "Low relevance", "similarity": 0.5, "created_at": datetime.now().isoformat()}
        ]

        rag_service.vector_store.search = AsyncMock(return_value=memories)
        rag_service.relevance_threshold = 0.7

        result = await rag_service.retrieve_context("test query")

        # Only memories above threshold should be included
        for memory in result["memories"]:
            assert memory["similarity"] >= 0.7

    @pytest.mark.asyncio
    async def test_token_budget_management(self, rag_service):
        """Test token budget management."""
        # Create many large memories
        large_memories = [
            {
                "id": str(i),
                "content": "A" * 1000,  # Large content
                "similarity": 0.8,
                "created_at": datetime.now().isoformat()
            }
            for i in range(10)
        ]

        rag_service.vector_store.search = AsyncMock(return_value=large_memories)
        rag_service.max_context_tokens = 100  # Small budget

        result = await rag_service.retrieve_context("test query")

        # Token count should not exceed budget
        assert result["token_count"] <= rag_service.max_context_tokens

    @pytest.mark.asyncio
    async def test_cache_integration(self, rag_service):
        """Test RAG cache integration."""
        # First call should use vector store
        result1 = await rag_service.retrieve_context("test query")
        assert result1["method"] == "rag"

        # Second call should use cache
        result2 = await rag_service.retrieve_context("test query")
        assert result2["method"] == "rag_cache"

        # Vector store should not be called again
        assert rag_service.vector_store.search.call_count == 1

