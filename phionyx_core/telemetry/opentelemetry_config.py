"""
OpenTelemetry Configuration
===========================

Configuration and initialization for OpenTelemetry tracing in Phionyx.

Features:
- Tracer provider initialization
- OTLP exporter configuration
- Resource attributes
- Sampling configuration
- Environment-based setup
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global tracer provider (initialized once)
_tracer_provider = None
_tracer = None


def initialize_opentelemetry(
    service_name: str = "phionyx-echo-server",
    service_version: str = "2.5.0",
    otlp_endpoint: Optional[str] = None,
    enabled: Optional[bool] = None,
    sampling_rate: float = 1.0,
    enable_metrics: bool = False
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Service name for resource attributes
        service_version: Service version
        otlp_endpoint: OTLP exporter endpoint (default: http://localhost:4317)
        enabled: Enable OpenTelemetry (default: from OTEL_ENABLED env var)
        sampling_rate: Sampling rate (0.0 to 1.0, default: 1.0 = 100%)

    Returns:
        True if initialization successful, False otherwise
    """
    global _tracer_provider, _tracer

    # Check if already initialized
    if _tracer_provider is not None:
        logger.debug("OpenTelemetry already initialized")
        return True

    # Check if enabled
    if enabled is None:
        enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"

    if not enabled:
        logger.info("OpenTelemetry is disabled")
        return False

    # Try to import OpenTelemetry packages
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
        logger.warning("Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
        return False

    try:
        # Get OTLP endpoint from environment or parameter
        if otlp_endpoint is None:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        # Create resource attributes
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "service.namespace": "phionyx",
            "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        })

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(_tracer_provider)

        # Configure sampling
        if sampling_rate < 1.0:
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
            _tracer_provider.sampler = TraceIdRatioBased(sampling_rate)
            logger.info(f"OpenTelemetry sampling enabled: {sampling_rate * 100}%")
        else:
            logger.info("OpenTelemetry sampling disabled (100% - all traces sampled)")

        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True  # For local development (use TLS in production)
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        _tracer_provider.add_span_processor(span_processor)

        # Create tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(f"✅ OpenTelemetry initialized: service={service_name}, endpoint={otlp_endpoint}, sampling={sampling_rate}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        _tracer_provider = None
        _tracer = None
        return False


def get_or_create_tracer(name: str = __name__):
    """
    Get or create OpenTelemetry tracer.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance or None if not available
    """
    global _tracer, _tracer_provider

    # Initialize if not already done
    if _tracer_provider is None:
        initialize_opentelemetry()

    if _tracer is None:
        try:
            from opentelemetry import trace
            _tracer = trace.get_tracer(name)
        except ImportError:
            return None

    return _tracer


def get_tracer_provider():
    """Get the global tracer provider."""
    return _tracer_provider


def shutdown_opentelemetry():
    """Shutdown OpenTelemetry (flush spans)."""
    global _tracer_provider, _tracer

    if _tracer_provider is not None:
        try:
            from opentelemetry.sdk.trace import TracerProvider
            if isinstance(_tracer_provider, TracerProvider):
                _tracer_provider.shutdown()
            logger.info("OpenTelemetry tracer provider shut down")
        except Exception as e:
            logger.warning(f"Error shutting down OpenTelemetry: {e}")

    _tracer_provider = None
    _tracer = None


# Auto-initialize on import (if enabled)
if os.getenv("OTEL_AUTO_INIT", "true").lower() == "true":
    initialize_opentelemetry()

