"""
Contract tests — AgentSlaMetrics (v4, F19)
==========================================

Pins the SLA metrics SCHEMA (not a contract): six bounded metrics, all Optional (None != 0),
sample sizes, and a single canonical source per metric. Reviewers rely on this shape.
"""

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.v4 import AgentSlaMetrics, MetricSource, METRIC_SOURCES

_SIX = [
    "verified_completion_rate",
    "rejection_rate",
    "policy_gate_failure_rate",
    "replay_success_rate",
    "evidence_completeness_score",
    "mean_time_to_evidence_reconstruction_ms",
]


class TestSlaMetricsSchema:
    def test_all_six_metrics_present_and_optional(self):
        fields = AgentSlaMetrics.model_fields
        for name in _SIX:
            assert name in fields, f"missing metric field {name}"
        # all-None is valid (a period with no data is representable, not coerced to 0.0)
        m = AgentSlaMetrics()
        for name in _SIX:
            assert getattr(m, name) is None

    def test_metric_sources_cover_all_six_with_known_enum(self):
        assert set(METRIC_SOURCES) == set(_SIX)
        for src in METRIC_SOURCES.values():
            assert isinstance(src, MetricSource)

    def test_rates_are_bounded_0_1(self):
        ok = AgentSlaMetrics(verified_completion_rate=0.0, rejection_rate=1.0,
                             evidence_completeness_score=0.5)
        assert ok.verified_completion_rate == 0.0
        for bad in (-0.01, 1.01):
            with pytest.raises(ValidationError):
                AgentSlaMetrics(rejection_rate=bad)

    def test_mttr_is_nonnegative_unbounded(self):
        assert AgentSlaMetrics(mean_time_to_evidence_reconstruction_ms=12345.6) is not None
        with pytest.raises(ValidationError):
            AgentSlaMetrics(mean_time_to_evidence_reconstruction_ms=-1.0)

    def test_sample_sizes_default_zero_and_nonnegative(self):
        m = AgentSlaMetrics()
        assert m.n_governed_claims == 0 and m.n_directives == 0 and m.n_traces == 0
        with pytest.raises(ValidationError):
            AgentSlaMetrics(n_traces=-1)

    def test_incomplete_map_and_roundtrip(self):
        m = AgentSlaMetrics(
            replay_success_rate=1.0, n_traces=2,
            incomplete={"verified_completion_rate": "no governed claims this period"},
        )
        dumped = m.model_dump()
        again = AgentSlaMetrics(**dumped)
        assert again.replay_success_rate == 1.0
        assert again.incomplete["verified_completion_rate"].startswith("no governed claims")
        # None metrics survive a JSON round-trip as null (not 0.0)
        assert again.verified_completion_rate is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
