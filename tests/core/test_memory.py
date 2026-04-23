"""
Unit Tests: Memory Module
==========================

Tests for:
- Insert/retrieve operations
- RLS policy tracking (in-memory mock)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, List, Optional

from phionyx_core.memory.vector_store import VectorStore


class InMemoryRepository:
    """In-memory repository that satisfies MemoryRepositoryProtocol for testing."""

    def __init__(self):
        self.client = True  # non-None so is_connected() returns True
        self._store: Dict[str, dict] = {}

    def insert_memory(self, data: dict) -> Optional[str]:
        memory_id = str(uuid.uuid4())
        self._store[memory_id] = {**data, "id": memory_id}
        return memory_id

    def get_memory(self, memory_id: str) -> Optional[dict]:
        return self._store.get(memory_id)

    def query_by_actor(self, actor_ref: str, limit: int = 10) -> List[dict]:
        return [
            m for m in self._store.values()
            if m.get("user_id") == actor_ref or m.get("actor_ref") == actor_ref
        ][:limit]


def _make_fake_llm_provider():
    """Create a fake LLM provider that returns deterministic embeddings."""
    provider = MagicMock()
    provider.available = True
    call_count = {"n": 0}

    async def fake_embedding(text, model=None, use_cache=False):
        call_count["n"] += 1
        base = [float(ord(c) % 10) / 10.0 for c in text[:1536].ljust(1536, "x")]
        return base

    provider.embedding = AsyncMock(side_effect=fake_embedding)
    return provider


def _make_vector_store(repo=None):
    """Build a VectorStore wired to in-memory mocks."""
    if repo is None:
        repo = InMemoryRepository()
    return VectorStore(
        llm_provider=_make_fake_llm_provider(),
        memory_repository=repo,
    ), repo


class TestMemoryOperations:
    """Test memory insert/retrieve operations."""

    @pytest.mark.asyncio
    async def test_insert_memory(self):
        """Test inserting a memory returns a valid ID."""
        store, _ = _make_vector_store()
        memory_id = await store.store(
            content="User said: I'm feeling anxious about exams.",
            metadata={"user_id": "student_001", "context": "SCHOOL"},
            context_tags=["anxiety", "school"],
        )
        assert memory_id is not None
        assert isinstance(memory_id, str)

    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        """Test storing then retrieving a memory."""
        repo = InMemoryRepository()
        store, _ = _make_vector_store(repo)

        await store.store(
            content="User's favorite color is blue.",
            metadata={"user_id": "student_002"},
            context_tags=["preference"],
        )

        stored = repo.query_by_actor("student_002")
        assert len(stored) > 0
        assert any("blue" in m.get("content", "").lower() for m in stored)

    @pytest.mark.asyncio
    async def test_rls_policy_isolation(self):
        """Test that actor A's memories are not returned for actor B."""
        repo = InMemoryRepository()
        store, _ = _make_vector_store(repo)

        user_a = f"user_a_{uuid.uuid4().hex[:8]}"
        user_b = f"user_b_{uuid.uuid4().hex[:8]}"

        await store.store(
            content="User A's secret: I love pizza.",
            metadata={"user_id": user_a},
            context_tags=["secret"],
        )

        results_b = repo.query_by_actor(user_b)
        assert len(results_b) == 0

        results_a = repo.query_by_actor(user_a)
        assert len(results_a) == 1
        assert "pizza" in results_a[0]["content"]
