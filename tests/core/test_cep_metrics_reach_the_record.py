"""The CEP metrics must survive into the record, or OD-19 cannot be decided.

OD-19 asks which of two numbers is wrong: the `phi / 10` normalisation or the
0.72 `phi_self_threshold`. The gate needs phi = 7.2 and the formula tops out
near 3.24 under the declared parameter bounds, so one of them has to move.

Picking a reachable threshold means knowing what `phi_echo_quality` actually
looks like on real turns. **That distribution was never recorded.** CEPMetrics
is a plain object and `echo_orchestrator.py:787` drops any result value that
is not JSON-safe, so every turn computed eight safety metrics and discarded
all eight before anything could read them.

So the decision was blocked on evidence that the system was already producing
and throwing away. This publishes them as plain floats. The threshold is
deliberately NOT changed — that is the founder's call, and it should be made
from the distribution rather than from arithmetic about ceilings.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.cep_evaluation import (
    _METRIC_FIELDS,
    CepEvaluationBlock,
    _metrics_to_record,
)


class _Metrics:
    """Stands in for CEPMetrics: a plain object, which is the whole problem."""

    def __init__(self, **values):
        for name in _METRIC_FIELDS:
            setattr(self, name, values.get(name, 0.0))


class _Evaluator:
    def __init__(self, metrics=None):
        self._metrics = metrics

    async def evaluate(self, **kwargs):
        return ("flags", self._metrics)


def _context(**metadata):
    return BlockContext(
        user_input="test", card_type="test", card_title="Test",
        scene_context="test", card_result="",
        metadata={"frame": {"id": "f"}, "narrative_text": "answer", **metadata},
    )


class TestTheOrchestratorWouldHaveDroppedThem:
    """The mechanism, asserted so the fix is not mistaken for decoration."""

    def test_a_plain_metrics_object_is_not_json_safe(self):
        json_safe = (dict, list, tuple, str, int, float, bool, type(None))

        assert not isinstance(_Metrics(), json_safe), (
            "CEPMetrics became JSON-safe on its own, so the orchestrator no "
            "longer drops it and this flattening may be redundant — check "
            "echo_orchestrator.py:787 before deleting it")

    def test_the_flattened_form_is_json_safe(self):
        record = _metrics_to_record(_Metrics(phi_echo_quality=0.05))

        assert all(isinstance(v, float) for v in record.values())


class TestEveryMetricIsRecorded:
    def test_all_eight_fields_survive(self):
        record = _metrics_to_record(_Metrics(
            phi_echo_quality=0.05, phi_echo_density=0.7, echo_stability=0.8,
            temporal_delay=1.5, self_reference_ratio=0.26,
            trauma_language_score=0.1, mirror_self_score=0.2,
            variation_novelty_score=0.9))

        assert set(record) == set(_METRIC_FIELDS)
        assert record["phi_echo_quality"] == 0.05, (
            "the field OD-19 is about must be the one that arrives")
        assert record["self_reference_ratio"] == 0.26, (
            "0.24 < self_ref <= 0.30 is the window where the entropy "
            "substitution flips a decision; the record has to show it")

    def test_a_non_numeric_field_goes_missing_rather_than_stringified(self):
        metrics = _Metrics(phi_echo_quality=0.05)
        metrics.mirror_self_score = "n/a"

        record = _metrics_to_record(metrics)

        assert "mirror_self_score" not in record, (
            "a repr in a numeric field would look like data in the record")
        assert record["phi_echo_quality"] == 0.05

    def test_booleans_are_not_counted_as_numbers(self):
        """bool is a subclass of int, so True would serialise as 1.0."""
        metrics = _Metrics(phi_echo_quality=0.05)
        metrics.echo_stability = True

        assert "echo_stability" not in _metrics_to_record(metrics)

    def test_no_metrics_records_nothing(self):
        assert _metrics_to_record(None) is None


@pytest.mark.asyncio
class TestTheBlockPublishesThem:
    async def test_the_metrics_land_in_the_block_data(self):
        block = CepEvaluationBlock(
            evaluator=_Evaluator(_Metrics(phi_echo_quality=0.033)))

        result = await block.execute(_context(
            time_delta=1.0, physics_state={"phi": 0.44, "entropy": 0.3}))

        assert result.data["cep_metrics"]["phi_echo_quality"] == 0.033, (
            "without this the distribution OD-19 needs is computed and "
            "discarded every turn")

    async def test_an_evaluator_returning_no_metrics_publishes_no_key(self):
        """The control: an absent key is not the same as a zeroed one."""
        block = CepEvaluationBlock(evaluator=_Evaluator(None))

        result = await block.execute(_context(
            time_delta=1.0, physics_state={"phi": 0.44, "entropy": 0.3}))

        assert "cep_metrics" not in result.data


class TestTheThresholdIsStillUnreachable:
    """OD-19 is instrumented, not resolved. This says so out loud.

    It fails when the threshold or the divisor moves, which is the moment the
    decision was actually made and this file needs revisiting.
    """

    def test_the_gate_still_needs_a_phi_the_formula_cannot_produce(self):
        from phionyx_core.cep.cep_engine import ConsciousEchoProofEngine

        threshold = ConsciousEchoProofEngine().config.thresholds
        required_phi = threshold.phi_self_threshold * 10.0

        assert required_phi > 3.24, (
            "the phi gate is now reachable — OD-19 has been decided. Record "
            "which number moved and why, then delete this test.")
