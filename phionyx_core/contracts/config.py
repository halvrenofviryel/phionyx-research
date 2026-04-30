"""
Configuration Contracts
=======================
Protocols/interfaces for configuration access in phionyx_core.

Core modules should depend on these protocols, not on environment variables
or hard-coded values. Implementations should be provided by phionyx_bridge.
"""

from typing import Protocol


class ConfigProtocol(Protocol):
    """
    Protocol for configuration values.

    Core modules use this protocol to access configuration instead of
    directly reading environment variables or using hard-coded defaults.
    """

    # LLM Configuration
    def get_llm_provider(self) -> str:
        """Get LLM provider name (e.g., 'ollama', 'openai', 'anthropic')."""
        ...

    def get_llm_model(self) -> str:
        """Get LLM model name (e.g., 'llama3.1:latest', 'gpt-4o')."""
        ...

    def get_llm_api_key(self) -> str | None:
        """Get LLM API key (optional, None for local models)."""
        ...

    def get_llm_base_url(self) -> str | None:
        """Get LLM base URL (optional, for local models like Ollama)."""
        ...

    # Embedding Configuration
    def get_embedding_provider(self) -> str:
        """Get embedding provider name (e.g., 'ollama', 'openai')."""
        ...

    def get_embedding_model(self) -> str:
        """Get embedding model name (e.g., 'qwen2.5:7b', 'text-embedding-3-small')."""
        ...

    def get_embedding_api_key(self) -> str | None:
        """Get embedding API key (optional, None for local models)."""
        ...

    def get_embedding_base_url(self) -> str | None:
        """Get embedding base URL (optional, for local models)."""
        ...

    def get_embedding_dimension(self) -> int:
        """
        Get embedding dimension.

        Returns:
            Embedding vector dimension (e.g., 1536, 768, 1024).
            Should match the model's output dimension.
        """
        ...

    # Database Configuration (for backward compatibility fallback)
    def get_supabase_url(self) -> str | None:
        """Get Supabase URL (optional, for backward compatibility)."""
        ...

    def get_supabase_key(self) -> str | None:
        """Get Supabase service key (optional, for backward compatibility)."""
        ...


# Abstract base class for type checking and documentation

class Config(Protocol):
    """
    Abstract base class for configuration implementations.

    Implementations should be provided by phionyx_bridge.
    """

    def get_llm_provider(self) -> str:
        """Get LLM provider name."""
        ...

    def get_llm_model(self) -> str:
        """Get LLM model name."""
        ...

    def get_llm_api_key(self) -> str | None:
        """Get LLM API key."""
        ...

    def get_llm_base_url(self) -> str | None:
        """Get LLM base URL."""
        ...

    def get_embedding_provider(self) -> str:
        """Get embedding provider name."""
        ...

    def get_embedding_model(self) -> str:
        """Get embedding model name."""
        ...

    def get_embedding_api_key(self) -> str | None:
        """Get embedding API key."""
        ...

    def get_embedding_base_url(self) -> str | None:
        """Get embedding base URL."""
        ...

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        ...

    def get_supabase_url(self) -> str | None:
        """Get Supabase URL."""
        ...

    def get_supabase_key(self) -> str | None:
        """Get Supabase service key."""
        ...

