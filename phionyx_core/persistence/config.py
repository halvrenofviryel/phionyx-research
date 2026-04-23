"""
State Store Configuration
=========================

Helper functions for creating and configuring state stores based on environment variables.
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


async def create_state_store_from_env() -> Optional[Any]:
    """
    Create state store based on environment variables.

    Environment Variables:
        - STATE_STORE_TYPE: "in_memory" or "postgresql" (default: None, no persistence)
        - DATABASE_URL: PostgreSQL connection string (required for postgresql type)
        - STATE_STORE_POOL_SIZE: Connection pool size (default: 10, for postgresql)

    Returns:
        StateStoreProtocol instance if configured, None otherwise
    """
    store_type = os.getenv("STATE_STORE_TYPE", "").lower().strip()

    # If not configured, return None (no persistence)
    if not store_type:
        logger.debug("STATE_STORE_TYPE not set, state persistence disabled")
        return None

    if store_type == "in_memory":
        logger.info("Creating InMemoryStateStore")
        try:
            from phionyx_core.persistence.in_memory_state_store import InMemoryStateStore
            store = InMemoryStateStore()
            await store.initialize()
            logger.info("✅ InMemoryStateStore initialized")
            return store
        except ImportError as e:
            logger.error(f"Failed to import InMemoryStateStore: {e}")
            return None

    elif store_type == "postgresql":
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            logger.warning("STATE_STORE_TYPE=postgresql but DATABASE_URL not set, skipping PostgreSQL state store")
            return None

        logger.info("Creating PostgreSQLStateStore")
        try:
            from phionyx_core.persistence.postgres_state_store import PostgreSQLStateStore

            pool_size = int(os.getenv("STATE_STORE_POOL_SIZE", "10"))
            store = PostgreSQLStateStore(connection_string, pool_size=pool_size)
            await store.initialize()
            logger.info(f"✅ PostgreSQLStateStore initialized (pool_size={pool_size})")
            return store
        except ImportError as e:
            logger.error(f"Failed to import PostgreSQLStateStore: {e}. Install asyncpg for PostgreSQL support.")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQLStateStore: {e}", exc_info=True)
            return None

    else:
        logger.warning(f"Unknown STATE_STORE_TYPE: {store_type}, skipping state persistence")
        logger.info("Supported types: 'in_memory', 'postgresql'")
        return None


def get_state_store_type() -> Optional[str]:
    """
    Get configured state store type from environment.

    Returns:
        State store type string or None if not configured
    """
    return os.getenv("STATE_STORE_TYPE", "").lower().strip() or None


def is_state_persistence_enabled() -> bool:
    """
    Check if state persistence is enabled.

    Returns:
        True if STATE_STORE_TYPE is set, False otherwise
    """
    return bool(get_state_store_type())

