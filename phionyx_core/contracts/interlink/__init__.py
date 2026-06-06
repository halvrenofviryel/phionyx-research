"""
Interlink Protocol Schema — Agent-to-Agent Envelope
====================================================

Schema for inter-agent communication envelopes. Previously lived at
`phionyx_interlink/envelope/envelope.py`; migrated here 2026-05-28 to break
the `phionyx_interlink` package dependency so the legacy package could be
archived without breaking `phionyx_agents/interlink/`.

The dataclass form is intentionally preserved (not translated to Pydantic
v4 style) — the public attribute API is what `phionyx_agents/interlink/`
depends on, and a translation would be scope-creep beyond the migration.
A future v5 schema pass may align this with the Pydantic v4 contracts.
"""

from .envelope import (
    EnvelopeHeader,
    EnvelopePayload,
    InterlinkEnvelope,
    StateMetrics,
    ValidationResult,
)

__all__ = [
    "EnvelopeHeader",
    "EnvelopePayload",
    "InterlinkEnvelope",
    "StateMetrics",
    "ValidationResult",
]
