"""Canonical block 39 must not fuse placeholders into a number a gate acts on.

`confidence_fusion` is the producer half of repair 1. Before it, wiring
`response_revision_gate` to `w_final` would have been worse than leaving the
gate inert, because two of this block's paths emitted a `w_final` of 0.5 that
had measured nothing:

- `compute_w_final({})` returns 0.5 for "nothing to fuse";
- the exception handler returned `w_final: 0.5` outright.

0.5 sits exactly on the revision gate's `confidence_rewrite` threshold, so
either path would have prefixed every response with "[Revised under
cognitive-state governance]" the moment the gate started reading the key.

A third placeholder was quieter: a missing ethics risk read as 0.0, so
`ethics_safety` contributed 1.0 to the fusion on every turn whether or not
ethics had run.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.confidence_fusion import ConfidenceFusionBlock


def _context(**metadata) -> BlockContext:
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


@pytest.fixture
def block() -> ConfidenceFusionBlock:
    return ConfidenceFusionBlock()


class TestNothingToFuseIsNotAConfidenceOfHalf:
    @pytest.mark.asyncio
    async def test_no_signals_writes_no_w_final(self, block) -> None:
        result = await block.execute(_context())

        assert "w_final" not in result.data
        assert result.data["block_outcome"]["measurement_status"] == "NOT_MEASURED"
        assert result.data["block_outcome"]["non_measurement_cause"] == "input_absent"

    @pytest.mark.asyncio
    async def test_the_absent_value_does_not_reach_the_context(self, block) -> None:
        """Every downstream reader guards on `w_final` being absent; what none
        of them can do is tell a measured 0.5 from a manufactured one."""
        context = _context()

        await block.execute(context)

        assert "w_final" not in context.metadata

    @pytest.mark.asyncio
    async def test_a_crash_writes_no_w_final_either(self, block) -> None:
        context = _context(physics_state={"phi": 0.9})

        def _boom(*a, **k):
            raise RuntimeError("fusion backend down")

        import phionyx_core.meta.arbitration_math as arbitration_math
        original = arbitration_math.compute_w_final
        arbitration_math.compute_w_final = _boom
        try:
            result = await block.execute(context)
        finally:
            arbitration_math.compute_w_final = original

        assert "w_final" not in result.data
        assert "w_final" not in context.metadata
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"
        assert result.data["block_outcome"]["operating_mode"] == "degraded"
        assert result.is_error() is False, "fail-open on the pipeline is retained"


class TestOnlyModulesThatReportedAreFused:
    @pytest.mark.asyncio
    async def test_a_missing_ethics_risk_no_longer_contributes_a_perfect_score(
        self, block
    ) -> None:
        """`ethics_result.get("max_risk_score", 0.0)` made `ethics_safety` 1.0
        on every turn, including turns where ethics never ran."""
        result = await block.execute(_context(physics_state={"phi": 0.4}))

        assert result.data["modules_fused"] == 1
        detail = result.data["block_outcome"]["profiles"]["reference_detail"]
        assert detail["modules"] == "physics_phi"

    @pytest.mark.asyncio
    async def test_a_reported_ethics_risk_does_contribute(self, block) -> None:
        result = await block.execute(
            _context(physics_state={"phi": 0.4}, ethics_result={"risk_score": 0.5}))

        assert result.data["modules_fused"] == 2
        assert "ethics_safety" in result.data["block_outcome"][
            "profiles"]["reference_detail"]["modules"]

    @pytest.mark.asyncio
    async def test_items_checked_counts_modules_that_reported(self, block) -> None:
        result = await block.execute(
            _context(physics_state={"phi": 0.4},
                     confidence_result={"confidence_score": 0.8},
                     ethics_result={"max_risk_score": 0.1}))

        assert result.data["block_outcome"]["measured"]["items_checked"] == 3

    @pytest.mark.asyncio
    async def test_a_non_numeric_signal_is_not_fused(self, block) -> None:
        result = await block.execute(
            _context(physics_state={"phi": 0.4},
                     ethics_result={"risk_score": "high"}))

        assert result.data["modules_fused"] == 1


class TestTheRepairEndToEnd:
    """Producer and consumer together — the reason repair 1 is one unit."""

    @pytest.mark.asyncio
    async def test_an_unmeasured_turn_does_not_trigger_a_rewrite(self) -> None:
        """The hazard this ordering exists to avoid: had the gate been wired
        first, a turn with nothing to fuse would have carried w_final 0.5 into
        `confidence <= 0.50` and rewritten every response."""
        from phionyx_core.pipeline.blocks.response_revision_gate import (
            ResponseRevisionGateBlock,
        )

        context = _context()
        fusion = await ConfidenceFusionBlock().execute(context)
        context.metadata.update(
            {k: v for k, v in (fusion.data or {}).items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        assert gate.data["directive"] == "pass"
        assert "confidence" not in gate.data["block_outcome"][
            "profiles"]["reference_detail"]["criteria_measured"]

    @pytest.mark.asyncio
    async def test_a_measured_low_confidence_does_reach_the_directive(self) -> None:
        from phionyx_core.pipeline.blocks.response_revision_gate import (
            ResponseRevisionGateBlock,
        )

        context = _context(physics_state={"phi": 0.1, "entropy": 0.1}, phi=0.1)
        fusion = await ConfidenceFusionBlock().execute(context)
        context.metadata.update(
            {k: v for k, v in (fusion.data or {}).items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        assert fusion.data["w_final"] == pytest.approx(0.1)
        assert gate.data["directive"] == "regenerate"
