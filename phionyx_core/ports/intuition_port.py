"""
Intuition Port Interface
========================

Port interface for Intuition SDK module (GraphRAG).
Enables swapping GraphRAG with Null implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IntuitionPort(ABC):
    """Port interface for Intuition/GraphRAG operations."""

    @abstractmethod
    async def extract_concepts(
        self,
        text: str
    ) -> List[str]:
        """
        Extract concepts from text.

        Returns:
            List of extracted concepts
        """
        pass

    @abstractmethod
    async def discover_hidden_context(
        self,
        user_text: str,  # SPRINT 5: Accept user_text (will extract concepts internally)
        actor_ref: Optional[str] = None  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
    ) -> Optional[Dict[str, Any]]:
        """
        Discover hidden context from user text using GraphRAG.

        Args:
            user_text: User input text (concepts will be extracted internally)
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)

        Returns:
            Inferred context dictionary with intuitive_context, extracted_concepts, inferred_contexts
        """
        pass

    @abstractmethod
    async def infer_hidden_context(
        self,
        concepts: List[str],
        actor_ref: Optional[str] = None  # SPRINT 5: Replaced user_id with actor_ref (core-neutral)
    ) -> Optional[Dict[str, Any]]:
        """
        Infer hidden context from concepts using GraphRAG.

        Args:
            concepts: List of concepts
            actor_ref: Actor reference (core-neutral identifier, replaces user_id)

        Returns:
            Inferred context or None if no context found
        """
        pass

    @abstractmethod
    async def build_concept_graph(
        self,
        concepts: List[str],
        relationships: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Build concept graph."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if Intuition/GraphRAG is available."""
        pass

