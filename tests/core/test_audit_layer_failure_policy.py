"""Canonical block 44 must not report a turn as audited when it was not.

The first of the nine T1 blocks migrated under P-4/P-5. `audit_layer` is
oversight, not an output gate: a failed assessment is an evidence gap, so the
pipeline continues and the record says the assessment did not happen.

This block is also the one four public compliance mappings cited as an "Ed25519
hash chain" while rating a control Full. It writes no record and never did. The
tests below assert both halves: what it does, and what it does not.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.audit_layer import AuditLayerBlock


def _context(**metadata) -> BlockContext:
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


class _RaisingProcessor:
    async def process_audit(self, **_kwargs):
        raise RuntimeError("audit backend unreachable")


class _DegradedProcessor:
    async def process_audit(self, **_kwargs):
        return {"status": "degraded", "integrity_score": 0.3,
                "issues": ["state_leak_detected"]}


class TestAFailedAssessmentIsNotAnAuditedTurn:
    @pytest.mark.asyncio
    async def test_a_raising_processor_is_not_reported_as_success(self) -> None:
        """It returned status="ok", which telemetry reads through is_success()."""
        block = AuditLayerBlock(processor=_RaisingProcessor())

        result = await block.execute(_context(frame=object()))

        assert result.status == "skipped"
        assert result.is_success() is False
        assert "RuntimeError" in (result.skip_reason or "")
        assert result.data["audit_result"] is None

    @pytest.mark.asyncio
    async def test_it_stays_fail_open(self) -> None:
        """`error` would attempt a rollback: audit_layer is outside the
        orchestrator's always-on set. The decision is to stop claiming the turn
        was audited, not to convert oversight into a gate."""
        block = AuditLayerBlock(processor=_RaisingProcessor())

        result = await block.execute(_context(frame=object()))

        assert result.is_error() is False
        assert result.is_skipped() is True

    @pytest.mark.asyncio
    async def test_the_record_says_the_assessment_errored(self) -> None:
        block = AuditLayerBlock(processor=_RaisingProcessor())

        outcome = (await block.execute(_context(frame=object()))
                   ).data["block_outcome"]

        assert outcome["measurement_status"] == "ERROR"
        assert outcome["operating_mode"] == "degraded"
        profile = outcome["profiles"]["phionyx_pipeline"]
        assert profile["block_run_status"] == "failed"
        assert profile["recovery_action"] == "fallback"


class TestAnAbsentFrameIsNotACleanAudit:
    @pytest.mark.asyncio
    async def test_no_frame_is_not_measured_rather_than_ok(self) -> None:
        """`ok` made "there was no input" and "the check passed" one record."""
        result = await AuditLayerBlock().execute(_context())

        assert result.status == "skipped"
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "NOT_MEASURED"
        assert outcome["non_measurement_cause"] == "input_absent"
        assert outcome["profiles"]["phionyx_pipeline"]["block_run_status"] == (
            "not_started")


class TestAnAssessmentThatRanIsMeasured:
    @pytest.mark.asyncio
    async def test_the_inline_fallback_passes_on_a_healthy_turn(self) -> None:
        result = await AuditLayerBlock().execute(
            _context(frame=object(), narrative_text="a full response",
                     physics_state={"phi": 0.4}))

        assert result.status == "ok"
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "PASS"
        assert outcome["measured"]["items_checked"] == 1, (
            "one turn was assessed; this is not a count of audit records "
            "written, which is zero on every path")

    @pytest.mark.asyncio
    async def test_a_degraded_assessment_is_FAIL_not_PASS(self) -> None:
        """A measured negative is FAIL. It is not an error and not a
        non-measurement: the check ran and its criterion was not met."""
        block = AuditLayerBlock(processor=_DegradedProcessor())

        outcome = (await block.execute(_context(frame=object()))
                   ).data["block_outcome"]

        assert outcome["measurement_status"] == "FAIL"
        assert "state_leak_detected" in outcome["reason"]

    @pytest.mark.asyncio
    async def test_a_statusless_assessment_is_not_measured(self) -> None:
        """Reading a missing status as success is the shape this block had."""
        class _Statusless:
            async def process_audit(self, **_kwargs):
                return {"integrity_score": 0.9}

        outcome = (await AuditLayerBlock(processor=_Statusless())
                   .execute(_context(frame=object()))).data["block_outcome"]

        assert outcome["measurement_status"] == "NOT_MEASURED"


class TestTheBlockDoesNotWriteAnAuditRecord:
    """The claim four public mappings made, checked here so it cannot return.

    If someone later wires signing into this block, this test fails and the
    person who wired it decides what the compliance rows should say. That is
    the right order — the rows followed the code by four months last time.
    """

    def test_the_source_contains_no_signing_or_chaining(self) -> None:
        from pathlib import Path

        source = (next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()) / "phionyx_core"
                  / "pipeline" / "blocks" / "audit_layer.py").read_text("utf-8")
        body = source.split('"""', 2)[-1]          # skip the module docstring
        for absent in ("Ed25519", "ed25519", "previous_hash", "AuditRecord"):
            assert absent not in body, (
                f"{absent!r} now appears in audit_layer. If this block has "
                "started writing an audit record, the compliance mappings that "
                "were corrected on 2026-08-02 need revisiting — they were "
                "corrected precisely because it did not.")

    def test_the_docstring_says_what_it_is_not(self) -> None:
        from phionyx_core.pipeline.blocks import audit_layer

        assert "does **not** write an audit record" in (audit_layer.__doc__ or "")
