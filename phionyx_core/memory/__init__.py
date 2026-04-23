"""
Core Memory Module - Database & Vector Store
============================================

Supabase integration for persistent storage and RAG operations.

Exports:
- vector_store: VectorStore for semantic memory
- user_profile: UserProfile for database operations
- trace: Trace functions for Echo ontology
"""

from . import vector_store
from . import user_profile
from . import trace
from . import trace_store

__all__ = [
    "vector_store",
    "user_profile",
    "trace",
    "trace_store",
    "TraceStore",
    "forgetting",
]

# Convenience exports
from .vector_store import VectorStore  # noqa: F401
from .user_profile import UserProfile  # noqa: F401
from .trace import (  # noqa: F401
    trace_weight,
    aggregate_trace,
    calculate_trace_decay_rate,
    get_active_trace_events
)
from .trace_store import TraceStore  # noqa: F401
from .forgetting import (  # noqa: F401
    ForgettingConfig,
    EventForgettingState,
    apply_passive_decay,
    apply_active_suppression,
    restore_suppressed_event,
    apply_full_erasure,
    create_tombstone_reference,
    apply_forgetting_to_entropy,
    calculate_decay_rate_from_inertia,
    ForgettingManager,
)

__version__ = "1.0.0"

