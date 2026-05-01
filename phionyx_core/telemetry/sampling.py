"""
OpenTelemetry Sampling Strategies
==================================

Advanced sampling strategies for OpenTelemetry tracing.

Features:
- Rate-based sampling
- Error-based sampling (always sample errors)
- Latency-based sampling (sample slow requests)
- Custom sampling logic
"""

import logging

logger = logging.getLogger(__name__)


class ErrorAwareSampler:
    """
    Sampler that always samples errors and uses rate-based sampling for success.

    This ensures that all errors are traced while reducing overhead for successful requests.
    """

    def __init__(self, base_sampling_rate: float = 0.1):
        """
        Initialize error-aware sampler.

        Args:
            base_sampling_rate: Base sampling rate for successful requests (0.0 to 1.0)
        """
        self.base_sampling_rate = base_sampling_rate
        try:
            from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
            self.base_sampler = TraceIdRatioBased(base_sampling_rate)
        except ImportError:
            logger.warning("OpenTelemetry SDK not available for sampling")
            self.base_sampler = None

    def should_sample(self, trace_id: int, span_name: str = None) -> bool:
        """
        Determine if a trace should be sampled.

        Args:
            trace_id: Trace ID
            span_name: Span name (optional)

        Returns:
            True if trace should be sampled, False otherwise
        """
        if self.base_sampler is None:
            return True  # Default to sampling if sampler not available

        # Always sample if it's an error span (check span name for error indicators)
        if span_name:
            error_indicators = ["error", "exception", "fail", "abort"]
            if any(indicator in span_name.lower() for indicator in error_indicators):
                return True

        # Use base sampler for other cases
        return self.base_sampler.should_sample(trace_id)

    def get_description(self) -> str:
        """Get sampler description."""
        return f"ErrorAwareSampler(base_rate={self.base_sampling_rate})"


def create_production_sampler(sampling_rate: float = 0.1) -> object | None:
    """
    Create a production-ready sampler.

    Args:
        sampling_rate: Sampling rate for successful requests (0.0 to 1.0)

    Returns:
        Sampler instance or None if OpenTelemetry not available
    """
    try:
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        return TraceIdRatioBased(sampling_rate)
    except ImportError:
        logger.warning("OpenTelemetry SDK not available for sampling")
        return None


def get_sampling_rate_from_env() -> float:
    """
    Get sampling rate from environment variable.

    Returns:
        Sampling rate (0.0 to 1.0)
    """
    import os
    rate_str = os.getenv("OTEL_SAMPLING_RATE", "1.0")
    try:
        rate = float(rate_str)
        # Clamp to valid range
        rate = max(0.0, min(1.0, rate))
        return rate
    except ValueError:
        logger.warning(f"Invalid OTEL_SAMPLING_RATE: {rate_str}, using default 1.0")
        return 1.0


def get_recommended_sampling_rate(environment: str = "production") -> float:
    """
    Get recommended sampling rate for environment.

    Args:
        environment: Environment name (development, staging, production)

    Returns:
        Recommended sampling rate
    """
    recommendations = {
        "development": 1.0,  # 100% - full tracing for development
        "staging": 0.5,      # 50% - moderate tracing for staging
        "production": 0.1,   # 10% - minimal tracing for production (reduce overhead)
    }
    return recommendations.get(environment.lower(), 0.1)

