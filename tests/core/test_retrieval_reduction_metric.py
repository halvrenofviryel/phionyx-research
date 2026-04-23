"""
Tests for RetrievalReductionMetric — Patent SF3-25
Compute resource reduction measurement for trace-weight filtering.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from phionyx_core.memory.trace_weight_standard import (
    RetrievalReductionMetric,
    get_trace_tags_with_metric,
)


def _make_event_ref(tag: str, intensity: float = 0.8, timestamp=None):
    """Create a mock event reference."""
    ref = MagicMock()
    ref.tag = tag
    ref.intensity = intensity
    ref.timestamp = timestamp or datetime.now()
    return ref


def _make_state(tags, entropy=0.1):
    """Create a mock EchoState2 with E_tags."""
    state = MagicMock()
    state.E_tags = [_make_event_ref(t) for t in tags]
    state.H = entropy
    state.t_now = datetime.now()
    return state


class TestRetrievalReductionMetric:
    """Test the reduction metric dataclass and measurement."""

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_metric_correct_before_after_counts(self):
        """Metric reports correct tags_before and tags_after."""
        state = _make_state(["a", "b", "c", "d", "e", "f"])
        tags, metric = get_trace_tags_with_metric(state, max_tags=3)
        assert metric.tags_before == 6
        assert metric.tags_after == len(tags)
        assert metric.tags_after <= 3

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_reduction_ratio_calculation(self):
        """reduction_ratio = 1 - (after/before)."""
        state = _make_state(["a", "b", "c", "d"])
        tags, metric = get_trace_tags_with_metric(state, max_tags=2)
        expected = 1.0 - (metric.tags_after / metric.tags_before)
        assert abs(metric.reduction_ratio - expected) < 1e-9

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_empty_state_zero_ratio(self):
        """Empty state → ratio 0.0, no crash."""
        state = MagicMock()
        state.E_tags = []
        tags, metric = get_trace_tags_with_metric(state)
        assert tags == []
        assert metric.tags_before == 0
        assert metric.tags_after == 0
        assert metric.reduction_ratio == 0.0

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_no_filtering_zero_ratio(self):
        """When all tags pass filter, ratio is low (only max_tags limit)."""
        state = _make_state(["a", "b"])
        tags, metric = get_trace_tags_with_metric(state, max_tags=10, min_weight=0.0)
        assert metric.tags_before == 2
        assert metric.tags_after == 2
        assert metric.reduction_ratio == 0.0

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_high_threshold_more_filtering(self):
        """High min_weight filters more tags → higher ratio."""
        # Low-intensity tags will be filtered by high threshold
        state = MagicMock()
        state.E_tags = [
            _make_event_ref("strong", intensity=0.9),
            _make_event_ref("weak1", intensity=0.01),
            _make_event_ref("weak2", intensity=0.01),
            _make_event_ref("weak3", intensity=0.01),
        ]
        state.H = 0.0
        state.t_now = datetime.now()
        _, metric = get_trace_tags_with_metric(state, max_tags=10, min_weight=0.5)
        assert metric.reduction_ratio > 0.0
        assert metric.tags_after < metric.tags_before

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_metric_timestamp_populated(self):
        """Metric timestamp_utc is a non-empty ISO string."""
        state = _make_state(["a"])
        _, metric = get_trace_tags_with_metric(state)
        assert metric.timestamp_utc
        assert "T" in metric.timestamp_utc  # ISO8601

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_metric_weight_threshold_recorded(self):
        """Metric records the min_weight used."""
        state = _make_state(["a"])
        _, metric = get_trace_tags_with_metric(state, min_weight=0.42)
        assert metric.weight_threshold == 0.42

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_metric_max_tags_recorded(self):
        """Metric records the max_tags used."""
        state = _make_state(["a"])
        _, metric = get_trace_tags_with_metric(state, max_tags=7)
        assert metric.max_tags == 7

    @patch("phionyx_core.memory.trace_weight_standard.ECHO_STATE_AVAILABLE", True)
    @patch("phionyx_core.memory.trace_weight_standard.EchoState2", MagicMock)
    def test_duplicate_tags_counted_once(self):
        """Duplicate tag names in E_tags are counted as 1 unique tag."""
        state = MagicMock()
        state.E_tags = [
            _make_event_ref("dup", intensity=0.8),
            _make_event_ref("dup", intensity=0.7),
            _make_event_ref("unique", intensity=0.6),
        ]
        state.H = 0.0
        state.t_now = datetime.now()
        _, metric = get_trace_tags_with_metric(state, max_tags=10, min_weight=0.0)
        assert metric.tags_before == 2  # "dup" + "unique"
