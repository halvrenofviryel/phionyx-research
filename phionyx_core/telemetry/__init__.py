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


__all__ = [
    'get_tracer',
    'is_opentelemetry_enabled',
]

