"""
State Persistence Module
========================

Provides interfaces and implementations for persisting EchoState2.
"""

from typing import Protocol, Optional, TYPE_CHECKING, Any
from phionyx_core.state.echo_state_2 import EchoState2

if TYPE_CHECKING:
    from phionyx_core.persistence.in_memory_state_store import InMemoryStateStore  # noqa: F401
    from phionyx_core.persistence.postgres_state_store import PostgreSQLStateStore  # noqa: F401

__all__ = ["StateStoreProtocol", "create_state_store_from_env", "get_state_store_type", "is_state_persistence_enabled"]

# Export configuration helpers
try:
    from phionyx_core.persistence.config import (
        create_state_store_from_env,
        get_state_store_type,
        is_state_persistence_enabled
    )
except ImportError:
    # Fallback if config module not available
    async def create_state_store_from_env() -> Optional[Any]:
        return None

    def get_state_store_type() -> Optional[str]:
        return None

    def is_state_persistence_enabled() -> bool:
        return False


class StateStoreProtocol(Protocol):
    """
    Protocol for state persistence.

    All state store implementations must implement these methods.
    """

    async def save_state(self, session_id: str, state: EchoState2) -> None:
        """
        Save state to persistent storage.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to save
        """
        ...

    async def load_state(self, session_id: str) -> Optional[EchoState2]:
        """
        Load state from persistent storage.

        Args:
            session_id: Session identifier

        Returns:
            EchoState2 instance if found, None otherwise
        """
        ...

    async def update_state(self, session_id: str, state: EchoState2) -> None:
        """
        Update state in persistent storage.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to update
        """
        ...

    async def delete_state(self, session_id: str) -> None:
        """
        Delete state from persistent storage.

        Args:
            session_id: Session identifier
        """
        ...

    async def initialize(self) -> None:
        """
        Initialize the state store (e.g., create tables, connect to database).
        """
        ...

    async def close(self) -> None:
        """
        Close the state store (e.g., close connections, cleanup).
        """
        ...
