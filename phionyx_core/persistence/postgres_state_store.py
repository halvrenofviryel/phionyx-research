"""
PostgreSQL State Store
======================

PostgreSQL-based state persistence for EchoState2.
Uses asyncpg for async PostgreSQL operations.
Uses JSONB column for EchoState2 storage.
"""

import logging
import json
from typing import Optional
import asyncpg
from phionyx_core.state.echo_state_2 import EchoState2

logger = logging.getLogger(__name__)


class PostgreSQLStateStore:
    """
    PostgreSQL-based state store implementation.

    Stores EchoState2 instances in PostgreSQL JSONB column.
    Suitable for production multi-instance deployments.
    """

    def __init__(self, connection_string: str, pool_size: int = 10):
        """
        Initialize PostgreSQL state store.

        Args:
            connection_string: PostgreSQL connection string (e.g., postgresql://user:pass@host/db)
            pool_size: Connection pool size (default: 10)
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool: Optional[asyncpg.Pool] = None
        logger.info(f"PostgreSQLStateStore initialized (pool_size={pool_size})")

    async def initialize(self) -> None:
        """
        Initialize connection pool and create table if not exists.
        """
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=self.pool_size,
                command_timeout=30
            )
            logger.info("PostgreSQL connection pool created")

            # Create table if not exists
            await self._create_table_if_not_exists()
            logger.info("PostgreSQL state store initialized")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL state store: {e}", exc_info=True)
            raise

    async def _create_table_if_not_exists(self) -> None:
        """Create echo_states table if it doesn't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS echo_states (
                    session_id VARCHAR(255) PRIMARY KEY,
                    state_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_echo_states_updated_at
                ON echo_states(updated_at)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_echo_states_expires_at
                ON echo_states(expires_at)
            """)

            logger.debug("echo_states table and indexes created")

    async def save_state(self, session_id: str, state: EchoState2) -> None:
        """
        Save state to PostgreSQL.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to save
        """
        if not self.pool:
            raise RuntimeError("State store not initialized. Call initialize() first.")

        try:
            state_json = state.model_dump_json()

            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO echo_states (session_id, state_data, updated_at)
                    VALUES ($1, $2::jsonb, NOW())
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        state_data = $2::jsonb,
                        updated_at = NOW()
                """, session_id, state_json)

            logger.debug(f"State saved for session: {session_id}")

        except Exception as e:
            logger.error(f"Failed to save state for session {session_id}: {e}", exc_info=True)
            raise

    async def load_state(self, session_id: str) -> Optional[EchoState2]:
        """
        Load state from PostgreSQL.

        Args:
            session_id: Session identifier

        Returns:
            EchoState2 instance if found, None otherwise
        """
        if not self.pool:
            raise RuntimeError("State store not initialized. Call initialize() first.")

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT state_data FROM echo_states WHERE session_id = $1",
                    session_id
                )

                if row:
                    state_data = row['state_data']
                    # Parse JSONB to dict
                    if isinstance(state_data, str):
                        state_dict = json.loads(state_data)
                    else:
                        state_dict = state_data

                    state = EchoState2.model_validate(state_dict)
                    logger.debug(f"State loaded for session: {session_id}")
                    return state

                logger.debug(f"No state found for session: {session_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to load state for session {session_id}: {e}", exc_info=True)
            raise

    async def update_state(self, session_id: str, state: EchoState2) -> None:
        """
        Update state in PostgreSQL.

        Args:
            session_id: Session identifier
            state: EchoState2 instance to update
        """
        # Update is same as save (upsert)
        await self.save_state(session_id, state)

    async def delete_state(self, session_id: str) -> None:
        """
        Delete state from PostgreSQL.

        Args:
            session_id: Session identifier
        """
        if not self.pool:
            raise RuntimeError("State store not initialized. Call initialize() first.")

        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM echo_states WHERE session_id = $1",
                    session_id
                )

                if result == "DELETE 1":
                    logger.debug(f"State deleted for session: {session_id}")
                else:
                    logger.debug(f"No state found to delete for session: {session_id}")

        except Exception as e:
            logger.error(f"Failed to delete state for session {session_id}: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

