"""
Memory Port Interface
=====================

Port interface for Memory SDK module.
Enables swapping Memory with Null implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class MemoryPort(ABC):
    """Port interface for Memory operations."""

    @abstractmethod
    async def add_memory(
        self,
        content: str,
        actor_ref: str,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        importance: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add memory to vector store.

        Args:
            content: Memory content
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            importance: Importance score (0-1)
            metadata: Optional metadata

        Returns:
            Memory ID if successful, None otherwise
        """
        pass

    @abstractmethod
    async def search_memories(
        self,
        query: str,
        actor_ref: str,  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories by semantic similarity.

        Args:
            query: Search query
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        pass

    @abstractmethod
    async def get_memory_by_id(
        self,
        memory_id: str,
        actor_ref: str  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
    ) -> Optional[Dict[str, Any]]:
        """
        Get memory by ID.

        Args:
            memory_id: Memory ID
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)

        Returns:
            Memory dictionary or None
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if memory store is connected."""
        pass

