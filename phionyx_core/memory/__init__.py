"""
Core Memory Module - Database & Vector Store
============================================

Supabase integration for persistent storage and RAG operations.

Exports:
- vector_store: VectorStore for semantic memory
- user_profile: UserProfile for database operations
- trace: Trace functions for Echo ontology
"""

from . import trace, trace_store, user_profile, vector_store

__all__ = [
    "vector_store",
    "user_profile",
    "trace",
    "trace_store",
    "TraceStore",
    "forgetting",
]

# Convenience exports
from .forgetting import (  # noqa: F401
    EventForgettingState,
    ForgettingConfig,
    ForgettingManager,
    apply_active_suppression,
    apply_forgetting_to_entropy,
    apply_full_erasure,
    apply_passive_decay,
    calculate_decay_rate_from_inertia,
    create_tombstone_reference,
    restore_suppressed_event,
)
from .trace import (  # noqa: F401
    aggregate_trace,
    calculate_trace_decay_rate,
    get_active_trace_events,
    trace_weight,
)
from .trace_store import TraceStore  # noqa: F401
from .user_profile import UserProfile  # noqa: F401
from .vector_store import VectorStore  # noqa: F401

__version__ = "1.0.0"

