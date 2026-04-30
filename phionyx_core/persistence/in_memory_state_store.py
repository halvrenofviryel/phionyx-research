"""
In-Memory State Store
======================

Simple in-memory implementation for testing or single-instance deployments.
NOT suitable for production multi-instance deployments.
"""

import logging

from phionyx_core.state.echo_state_2 import EchoState2

logger = logging.getLogger(__name__)


class InMemoryStateStore:
    """
    In-memory state store implementation.

    WARNING: This is NOT suitable for production multi-instance deployments.
    Use PostgreSQLStateStore for production.
    """

    def __init__(self):
        """Initialize in-memory state store."""
        self._storage: dict[str, EchoState2] = {}
        logger.info("InMemoryStateStore initialized")

    async def save_state(self, session_id: str, state: EchoState2) -> None:
        """
        Save state to memory.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to save
        """
        self._storage[session_id] = state
        logger.debug(f"State saved for session: {session_id}")

    async def load_state(self, session_id: str) -> EchoState2 | None:
        """
        Load state from memory.

        Args:
            session_id: Session identifier

        Returns:
            EchoState2 instance if found, None otherwise
        """
        state = self._storage.get(session_id)
        if state:
            logger.debug(f"State loaded for session: {session_id}")
        return state

    async def update_state(self, session_id: str, state: EchoState2) -> None:
        """
        Update state in memory.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to update
        """
        self._storage[session_id] = state
        logger.debug(f"State updated for session: {session_id}")

    async def delete_state(self, session_id: str) -> None:
        """
        Delete state from memory.

        Args:
            session_id: Session identifier
        """
        if session_id in self._storage:
            del self._storage[session_id]
            logger.debug(f"State deleted for session: {session_id}")

    async def initialize(self) -> None:
        """Initialize the state store (no-op for in-memory)."""
        logger.debug("InMemoryStateStore initialized")

    async def close(self) -> None:
        """Close the state store (clear memory)."""
        self._storage.clear()
        logger.debug("InMemoryStateStore closed")

