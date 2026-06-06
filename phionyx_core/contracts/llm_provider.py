"""
LLM Provider Protocol - Dependency Injection Interface
=======================================================

Defines the interface for LLM services to enable dependency injection
and break circular dependencies between phionyx_core and echo_server.

This protocol allows phionyx_core to use LLM services without importing
from echo_server, maintaining proper layer isolation.
"""

from typing import Protocol, List, Optional, Dict, Any


class LLMProviderProtocol(Protocol):
    """
    Protocol defining the interface for LLM service providers.

    Implementations should provide:
    - completion: Generate text completions
    - embedding: Generate embeddings
    - extract_concepts: Extract concepts from text
    - available: Check if service is available
    """

    @property
    def available(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if service is available, False otherwise
        """
        ...

    async def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate text completion.

        Args:
            messages: List of message dictionaries with "role" and "content"
            model: Model identifier (optional, uses default if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            Generated text string

        Raises:
            RuntimeError: If service is unavailable or generation fails
        """
        ...

    async def embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed
            model: Embedding model identifier (optional)
            use_cache: Whether to use caching

        Returns:
            Embedding vector or None if failed
        """
        ...

    async def extract_concepts(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[Any]:
        """
        Extract concepts from text.

        Args:
            text: Input text
            model: Optional model identifier

        Returns:
            List of Concept objects (any type that has name, category, confidence attributes)
        """
        ...


# Type alias for convenience
LLMProvider = LLMProviderProtocol

