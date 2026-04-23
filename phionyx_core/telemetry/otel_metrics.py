"""
OpenTelemetry Metrics Export
=============================

Exports Phionyx metrics to OpenTelemetry for Prometheus/Grafana integration.

Metrics:
- Entropy (heatmap)
- Ethics blocking rate
- Average latency
- LLM cost counter
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# OpenTelemetry metrics (optional)
_metrics_available = False
_meter = None
_entropy_gauge = None
_ethics_blocking_counter = None
_latency_histogram = None
_llm_cost_counter = None

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    _metrics_available = True
except ImportError:
    logger.debug("OpenTelemetry metrics not available")


def initialize_otel_metrics(
    otlp_endpoint: str = "http://localhost:4317",
    enabled: bool = True
) -> bool:
    """
    Initialize OpenTelemetry metrics.

    Args:
        otlp_endpoint: OTLP exporter endpoint
        enabled: Enable metrics export

    Returns:
        True if initialization successful, False otherwise
    """
    global _meter, _entropy_gauge, _ethics_blocking_counter, _latency_histogram, _llm_cost_counter

    if not _metrics_available or not enabled:
        return False

    try:
        # Create metric exporter
        metric_exporter = OTLPMetricExporter(
            endpoint=otlp_endpoint,
            insecure=True  # For local development
        )

        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=5000  # Export every 5 seconds
        )

        # Create meter provider
        meter_provider = MeterProvider(metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        # Create meter
        _meter = metrics.get_meter(__name__)

        # Create metrics
        _entropy_gauge = _meter.create_up_down_counter(
            name="phionyx.entropy.current",
            description="Current entropy value (kafa karışıklığı seviyesi)",
            unit="1"
        )

        _ethics_blocking_counter = _meter.create_counter(
            name="phionyx_ethics_blocking_total",
            description="Total number of requests blocked by ethics blocks",
            unit="1"
        )

        _latency_histogram = _meter.create_histogram(
            name="phionyx_pipeline_latency_seconds",
            description="Pipeline execution latency in seconds",
            unit="s"
        )

        _llm_cost_counter = _meter.create_counter(
            name="phionyx_llm_cost_usd_total",
            description="Total LLM cost in USD",
            unit="USD"
        )

        logger.info(f"✅ OpenTelemetry metrics initialized: endpoint={otlp_endpoint}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry metrics: {e}", exc_info=True)
        return False


def record_entropy(entropy: float, block_id: Optional[str] = None):
    """
    Record entropy value.

    Args:
        entropy: Entropy value
        block_id: Block ID that computed entropy (optional)
    """
    global _entropy_values
    if _metrics_available:
        try:
            # Store entropy value for observable gauge callback
            key = block_id if block_id else "pipeline"
            _entropy_values[key] = entropy
        except Exception as e:
            logger.debug(f"Failed to record entropy metric: {e}")


def record_ethics_blocking(block_id: str, reason: Optional[str] = None):
    """
    Record ethics blocking event.

    Args:
        block_id: Block ID that blocked the request
        reason: Reason for blocking (optional)
    """
    global _ethics_blocking_counter
    if _ethics_blocking_counter:
        try:
            attributes = {"block_id": block_id}
            if reason:
                attributes["reason"] = reason
            _ethics_blocking_counter.add(1, attributes=attributes)
        except Exception as e:
            logger.debug(f"Failed to record ethics blocking metric: {e}")


def record_latency(latency_seconds: float, block_id: Optional[str] = None):
    """
    Record pipeline or block latency.

    Args:
        latency_seconds: Latency in seconds
        block_id: Block ID (optional, if None records pipeline latency)
    """
    global _latency_histogram
    if _latency_histogram:
        try:
            attributes = {}
            if block_id:
                attributes["block_id"] = block_id
            else:
                attributes["type"] = "pipeline"
            _latency_histogram.record(latency_seconds, attributes=attributes)
        except Exception as e:
            logger.debug(f"Failed to record latency metric: {e}")


def record_llm_cost(cost_usd: float, provider: str, model: str):
    """
    Record LLM cost.

    Args:
        cost_usd: Cost in USD
        provider: LLM provider (e.g., "ollama", "openai")
        model: Model name
    """
    global _llm_cost_counter
    if _llm_cost_counter:
        try:
            attributes = {
                "provider": provider,
                "model": model
            }
            _llm_cost_counter.add(cost_usd, attributes=attributes)
        except Exception as e:
            logger.debug(f"Failed to record LLM cost metric: {e}")


def is_metrics_enabled() -> bool:
    """Check if OpenTelemetry metrics are enabled."""
    return _metrics_available and _meter is not None

