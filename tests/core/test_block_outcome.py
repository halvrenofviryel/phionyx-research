"""P-1 and P-2: a block outcome that separates runtime from measurement.

`BlockResult.status` answered two questions with one word, and 35 blocks used
`ok` to mean "did not run, and we continued". These tests are the shape that
makes the second meaning unsayable.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.outcome import (
    COMPATIBILITY_ADAPTER, BlockOutcome, BlockRunStatus, CollapseError,
    Measurement, Observation, RecoveryAction, ScopeDecision, Verdict, errored,
    from_legacy, measured_pass, not_applicable, not_measured,
)


def _outcome(**kw) -> BlockOutcome:
    base = dict(block_id="test_block", legacy_control_status="ok",
                block_run_status=BlockRunStatus.COMPLETED,
                measurement=measured_pass(1))
    base.update(kw)
    return BlockOutcome(**base)


class TestTheMeasurementIsATypeNotAString:
    def test_a_string_status_is_refused(self) -> None:
        """The whole point: `measurement_status="PASS"` cannot be assigned."""
        with pytest.raises(CollapseError, match="not a Measurement"):
            _outcome(measurement="PASS")

    def test_there_is_no_permissive_default(self) -> None:
        """No field defaults to a passing value, so a caller must state one.

        An earlier draft proposed `measurement_status: str = "PASS"` on the
        grounds that it preserved the meaning of 138 existing constructions.
        It would have copied a false claim into a field where it looks
        authoritative.
        """
        with pytest.raises(TypeError):
            BlockOutcome(block_id="b", legacy_control_status="ok",  # type: ignore[call-arg]
                         block_run_status=BlockRunStatus.COMPLETED)

    def test_the_legacy_status_stays_the_control_channel(self) -> None:
        """The orchestrator decides rollback on it; that is unchanged."""
        outcome = _outcome(legacy_control_status="skipped")
        assert outcome.legacy_control_status == "skipped"

    def test_an_unknown_legacy_status_is_refused(self) -> None:
        with pytest.raises(CollapseError, match="not one of"):
            _outcome(legacy_control_status="degraded")


class TestTheRecordCannotContradictItself:
    def test_degraded_is_never_passing(self) -> None:
        """MA-4.4"""
        with pytest.raises(CollapseError, match="MA-4.4"):
            _outcome(operating_mode="degraded")
        _outcome(operating_mode="degraded",
                 measurement=not_measured("fell back", cause="not_executed"))

    def test_a_block_that_never_started_measured_nothing(self) -> None:
        with pytest.raises(CollapseError, match="NOT_MEASURED"):
            _outcome(block_run_status=BlockRunStatus.NOT_STARTED)
        _outcome(block_run_status=BlockRunStatus.NOT_STARTED,
                 measurement=not_measured("suppressed", cause="suppressed_by_tier"))

    def test_a_failed_run_may_still_carry_a_completed_measurement(self) -> None:
        """The fourth row of P-4's exception-phase table.

        A measurement that finished before an operational crash is not
        retroactively unmeasured; discarding it would be its own false record.
        """
        outcome = _outcome(block_run_status=BlockRunStatus.FAILED,
                           measurement=measured_pass(3),
                           recovery_action=RecoveryAction.FALLBACK)
        assert outcome.measurement.verdict is Verdict.PASS
        assert outcome.block_run_status is BlockRunStatus.FAILED


class TestMigrationStateIsNotAMeasurement:
    def test_legacy_unmapped_lives_in_the_pipeline_profile(self) -> None:
        """It is not a measurement_status value, and the vocabulary stays closed."""
        outcome = from_legacy("some_block", "ok")
        fields = outcome.to_record_fields()
        assert fields["measurement_status"] == "NOT_MEASURED"
        assert fields["profiles"]["phionyx_pipeline"]["mapping_status"] == (
            "legacy_unmapped")
        assert "legacy_unmapped" not in {v.value for v in Verdict}

    def test_a_block_built_outcome_reads_migrated(self) -> None:
        assert _outcome().mapping_status == "migrated"
        assert "compatibility_adapter" not in _outcome().to_profile_fields()


class TestTheLegacyAdapterGuessesNothing:
    """MA-3.7 asks for an adapter that handles every status explicitly.

    All three read NOT_MEASURED with cause `unknown`, because none of them
    carries evidence of what it established. `ok` did not reliably mean success
    — that finding produced this work. `error` does not establish the evaluator
    *started*, which is what ERROR asserts. `skipped` was written both by a
    policy bypass and by a block falling over.
    """

    @pytest.mark.parametrize("status", ["ok", "error", "skipped"])
    def test_every_legacy_status_is_handled_and_none_is_guessed(
        self, status: str
    ) -> None:
        outcome = from_legacy("b", status)
        assert outcome.measurement.verdict is Verdict.NOT_MEASURED
        assert outcome.measurement.cause == "unknown"
        assert outcome.compatibility_adapter == COMPATIBILITY_ADAPTER

    def test_error_does_not_become_ERROR(self) -> None:
        """The tempting mapping, and the wrong one."""
        assert from_legacy("b", "error").measurement.verdict is not Verdict.ERROR

    def test_skipped_does_not_become_NOT_APPLICABLE(self) -> None:
        assert (from_legacy("b", "skipped").measurement.verdict
                is not Verdict.NOT_APPLICABLE)

    def test_ok_does_not_become_PASS(self) -> None:
        assert from_legacy("b", "ok").measurement.verdict is not Verdict.PASS

    def test_an_unrecognised_status_is_refused_not_defaulted(self) -> None:
        with pytest.raises(CollapseError, match="handles every legacy value"):
            from_legacy("b", "fine")

    def test_the_run_status_follows_what_the_string_does_establish(self) -> None:
        """`error` does establish that something went wrong, if not what."""
        assert from_legacy("b", "error").block_run_status is BlockRunStatus.FAILED
        assert from_legacy("b", "ok").block_run_status is BlockRunStatus.COMPLETED


class TestTheEmittedRecord:
    def test_the_pipeline_profile_carries_the_runtime_axis(self) -> None:
        fields = _outcome(block_run_status=BlockRunStatus.TIMEOUT,
                          measurement=not_measured("timed out",
                                                   cause="not_executed"),
                          recovery_action=RecoveryAction.FALLBACK,
                          ).to_record_fields()
        profile = fields["profiles"]["phionyx_pipeline"]
        assert profile["block_run_status"] == "timeout"
        assert profile["recovery_action"] == "fallback"
        assert "block_run_status" not in fields, (
            "block runtime is a pipeline fact and belongs in the profile, not "
            "in the record's core")

    def test_measurement_detail_and_the_pipeline_profile_coexist(self) -> None:
        fields = _outcome(measurement=measured_pass(1, policy="P1")
                          ).to_record_fields()
        assert fields["profiles"]["reference_detail"] == {"policy": "P1"}
        assert fields["profiles"]["phionyx_pipeline"]["block_id"] == "test_block"

    def test_operating_mode_appears_only_when_degraded(self) -> None:
        assert "operating_mode" not in _outcome().to_record_fields()
        degraded = _outcome(operating_mode="degraded",
                            measurement=errored("crashed")).to_record_fields()
        assert degraded["operating_mode"] == "degraded"

    def test_a_scope_exclusion_survives_the_round_trip(self) -> None:
        fields = _outcome(
            measurement=not_applicable(ScopeDecision("doc://s#1", True))
        ).to_record_fields()
        assert fields["measurement_status"] == "NOT_APPLICABLE"
        assert fields["scope_decision"]["ref"] == "doc://s#1"


class TestTheOutcomeIsNotABoolean:
    def test_the_measurement_still_refuses_truthiness(self) -> None:
        """MA-3.5, reachable through the outcome as well as directly."""
        with pytest.raises(CollapseError, match="MA-3.5"):
            bool(_outcome().measurement)

    def test_reading_the_verdict_is_the_supported_path(self) -> None:
        assert _outcome().measurement.verdict.is_passing is True
        assert not_measured("x", cause="unknown").verdict.is_passing is False
