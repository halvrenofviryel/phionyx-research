"""Repair 3 of 3 — drift reaches the revision gate, and only when measured.

`response_revision_gate` read `drift_result`, which nothing writes;
`behavioral_drift_detection` (canonical 23) writes `drift_score` flat. So the
gate's drift rule never fired.

This producer is the clean one of the three: its exception path returns
`status="error"` rather than a quiet `ok`, and it never invented a score. The
fabrication was one layer down. `BehavioralDriftDetector.detect_drift` returns,
when it finds no baseline for the session:

    drift_score=0.0, recommendation="allow", semantic_similarity=1.0,
    confidence=0.0

— a perfectly clean report, from the branch whose own comment reads "cannot
detect drift". Publishing that under the key the gate now reads would have made
the criterion record as checked and clean on every baseline-less turn, which is
the exact substitution the doctrine names. `confidence` is the one honest field
in that report, and it is what the block now gates publication on.
"""
from __future__ import annotations

import pytest

from phionyx_core.monitoring.behavioral_drift import DriftReport
from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.behavioral_drift_detection import (
    BehavioralDriftDetectionBlock,
)
from phionyx_core.pipeline.blocks.response_revision_gate import (
    ResponseRevisionGateBlock,
)


def _report(drift_score: float, confidence: float, detected: bool = False,
            drift_type=None) -> DriftReport:
    return DriftReport(
        drift_detected=detected,
        drift_score=drift_score,
        drift_type=drift_type or [],
        degraded_metrics=[],
        recommendation="allow",
        semantic_similarity=1.0,
        physics_drift={},
        ethics_escalation=None,
        confidence=confidence,
    )


class _Detector:
    drift_threshold = 0.6

    def __init__(self, report: DriftReport) -> None:
        self._report = report

    async def detect_drift(self, **_kwargs) -> DriftReport:
        return self._report


class _RaisingDetector:
    drift_threshold = 0.6

    async def detect_drift(self, **_kwargs):
        raise RuntimeError("baseline store unreachable")


def _context(**metadata) -> BlockContext:
    metadata.setdefault("narrative_text", "a response")
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


class TestAZeroConfidenceReportIsNotAMeasurement:
    @pytest.mark.asyncio
    async def test_no_baseline_publishes_no_drift_score(self) -> None:
        block = BehavioralDriftDetectionBlock(
            drift_detector=_Detector(_report(0.0, confidence=0.0)))
        context = _context()

        result = await block.execute(context)

        assert "drift_score" not in result.data
        assert "drift_score" not in context.metadata
        assert result.data["block_outcome"]["measurement_status"] == "NOT_MEASURED"
        assert result.data["block_outcome"]["non_measurement_cause"] == "input_absent"

    @pytest.mark.asyncio
    async def test_the_gate_then_does_not_count_drift_as_checked(self) -> None:
        """End to end: the reason the publication gate exists."""
        block = BehavioralDriftDetectionBlock(
            drift_detector=_Detector(_report(0.0, confidence=0.0)))
        context = _context()
        drift = await block.execute(context)
        context.metadata.update(
            {k: v for k, v in drift.data.items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        detail = gate.data["block_outcome"]["profiles"]["reference_detail"]
        assert "drift" not in detail["criteria_measured"]
        assert "drift" in detail["criteria_absent"]

    @pytest.mark.asyncio
    async def test_a_measured_report_is_published(self) -> None:
        block = BehavioralDriftDetectionBlock(
            drift_detector=_Detector(_report(0.2, confidence=0.8)))
        context = _context()

        result = await block.execute(context)

        assert result.data["drift_score"] == pytest.approx(0.2)
        assert context.metadata["drift_score"] == pytest.approx(0.2)
        assert result.data["block_outcome"]["measurement_status"] == "PASS"


class TestTheDriftRuleNowFires:
    @pytest.mark.asyncio
    async def test_drift_above_the_threshold_rewrites(self) -> None:
        """The point of repair 3. Until 2026-08-02 this rule was unreachable."""
        gate = await ResponseRevisionGateBlock().execute(
            _context(drift_score=0.7, phi=0.9, entropy=0.1))

        assert gate.data["directive"] == "rewrite"
        assert any("drift" in r for r in gate.data["reasons"])

    @pytest.mark.asyncio
    async def test_drift_below_the_threshold_passes(self) -> None:
        gate = await ResponseRevisionGateBlock().execute(
            _context(drift_score=0.2, phi=0.9, entropy=0.1))

        assert gate.data["directive"] == "pass"
        assert "drift" in gate.data["block_outcome"][
            "profiles"]["reference_detail"]["criteria_measured"]

    @pytest.mark.asyncio
    async def test_the_documented_key_still_wins(self) -> None:
        gate = await ResponseRevisionGateBlock().execute(
            _context(drift_result={"drift_score": 0.1}, drift_score=0.9,
                     phi=0.9, entropy=0.1))

        assert gate.data["directive"] == "pass"

    @pytest.mark.asyncio
    async def test_end_to_end_a_drifting_turn_reaches_the_directive(self) -> None:
        from phionyx_core.monitoring.behavioral_drift import DriftType

        block = BehavioralDriftDetectionBlock(
            drift_detector=_Detector(
                _report(0.75, confidence=0.9, detected=True,
                        drift_type=[DriftType.SEMANTIC])))
        context = _context(phi=0.9, entropy=0.1)
        drift = await block.execute(context)
        context.metadata.update(
            {k: v for k, v in drift.data.items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        assert drift.data["block_outcome"]["measurement_status"] == "FAIL"
        assert gate.data["directive"] == "rewrite"


class TestTheFailurePathStaysLoud:
    @pytest.mark.asyncio
    async def test_a_crash_still_reports_error_and_publishes_no_score(self) -> None:
        """This block already failed loudly; that is left alone. What is added
        is the record, and the absence of a score a crash could be read as."""
        block = BehavioralDriftDetectionBlock(drift_detector=_RaisingDetector())
        context = _context()

        result = await block.execute(context)

        assert result.status == "error"
        assert result.is_error() is True
        assert "drift_score" not in result.data
        assert "drift_score" not in context.metadata
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"
        assert result.data["block_outcome"]["operating_mode"] == "degraded"
