"""
Phionyx Telemetry Package
===========================

OpenTelemetry integration for distributed tracing and observability.
"""

# Lazy imports to avoid dependency issues
_tracer = None
_tracer_provider = None


def get_tracer(name: str = __name__):
    """Get OpenTelemetry tracer (lazy initialization)."""
    global _tracer
    if _tracer is None:
        try:
            from .opentelemetry_config import get_or_create_tracer
            _tracer = get_or_create_tracer(name)
        except ImportError:
            # OpenTelemetry not available, return None
            return None
    return _tracer


def is_opentelemetry_enabled() -> bool:
    """Check if OpenTelemetry is enabled and available."""
    try:
        from opentelemetry import trace  # noqa: F401
        return True
    except ImportError:
        return False


def _lazy_import_export():
    """Import otel_export lazily so phionyx-core stays import-safe without OTel SDK."""
    from .otel_export import (
        DEFAULT_SEMANTIC_VERSION,
        ENV_EXPORT_ENVELOPES,
        ENV_SEMANTIC_VERSION,
        EnvelopeToSpanMapper,
        envelope_export_enabled,
        export_envelope,
    )
    return {
        "DEFAULT_SEMANTIC_VERSION": DEFAULT_SEMANTIC_VERSION,
        "ENV_EXPORT_ENVELOPES": ENV_EXPORT_ENVELOPES,
        "ENV_SEMANTIC_VERSION": ENV_SEMANTIC_VERSION,
        "EnvelopeToSpanMapper": EnvelopeToSpanMapper,
        "envelope_export_enabled": envelope_export_enabled,
        "export_envelope": export_envelope,
    }


def __getattr__(name: str):
    """PEP 562: lazy attribute access for the envelope-export surface."""
    if name in {
        "DEFAULT_SEMANTIC_VERSION",
        "ENV_EXPORT_ENVELOPES",
        "ENV_SEMANTIC_VERSION",
        "EnvelopeToSpanMapper",
        "envelope_export_enabled",
        "export_envelope",
    }:
        return _lazy_import_export()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'get_tracer',
    'is_opentelemetry_enabled',
    # Envelope export (W3 — F2 OTel exporter, v0.4.0)
    'DEFAULT_SEMANTIC_VERSION',
    'ENV_EXPORT_ENVELOPES',
    'ENV_SEMANTIC_VERSION',
    'EnvelopeToSpanMapper',
    'envelope_export_enabled',
    'export_envelope',
]

