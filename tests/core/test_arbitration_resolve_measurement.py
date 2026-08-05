"""Canonical block 40 must not emit a conflict score it never received.

`arbitration_resolve` read `conflict_score` off `confidence.metadata`, which
`confidence_fusion` does not populate. So it read 0.0 every turn, emitted that
0.0, and — since both blocks merge into the same flat `conflict_score` key —
destroyed the value the fusion block had measured.

The second half of repair 2, wiring this signal into `response_revision_gate`,
is deliberately not done. `compute_conflict_score` is `1 - HHI` over normalised
shares: a dispersion index, which runs opposite to the gate's rule at the
extremes. The last test class pins that measurement so the reason is on the
record and does not have to be rediscovered.
"""
from __future__ import annotations

import pytest

from phionyx_core.contracts.v4.confidence_payload import ConfidencePayload
from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.arbitration_resolve import ArbitrationResolveBlock


def _context(payload=None, **metadata) -> BlockContext:
    context = BlockContext(user_input="t", card_type="", card_title="",
                           scene_context="", card_result="", metadata=metadata)
    context.v4_confidence = payload
    return context


@pytest.fixture
def block() -> ArbitrationResolveBlock:
    return ArbitrationResolveBlock()


class TestItDoesNotDestroyTheMeasuredValue:
    @pytest.mark.asyncio
    async def test_an_empty_payload_emits_no_conflict_score(self, block) -> None:
        """The defect: `confidence.metadata` is `{}`, so 0.0 was emitted and
        clobbered the 0.516 that `confidence_fusion` had just measured."""
        result = await block.execute(
            _context(ConfidencePayload(confidence_score=0.7), conflict_score=0.516))

        assert "conflict_score" not in result.data
        assert result.data["block_outcome"]["measurement_status"] == "NOT_MEASURED"

    @pytest.mark.asyncio
    async def test_the_upstream_value_survives_the_merge(self, block) -> None:
        """What the orchestrator would do with this result."""
        context = _context(ConfidencePayload(confidence_score=0.7),
                           conflict_score=0.516)

        result = await block.execute(context)
        context.metadata.update(
            {k: v for k, v in result.data.items() if k != "block_outcome"})

        assert context.metadata["conflict_score"] == pytest.approx(0.516)

    @pytest.mark.asyncio
    async def test_no_payload_at_all_is_also_not_measured(self, block) -> None:
        result = await block.execute(_context(None))

        assert "conflict_score" not in result.data
        assert result.data["block_outcome"]["non_measurement_cause"] == "input_absent"
        assert result.data["arbitration_needed"] is False

    @pytest.mark.asyncio
    async def test_a_crash_emits_no_conflict_score(self, block) -> None:
        class _ExplodingPayload:
            """`getattr(x, "metadata", None)` swallows AttributeError, not this."""

            @property
            def metadata(self):
                raise RuntimeError("payload backend down")

        result = await block.execute(_context(_ExplodingPayload()))

        assert "conflict_score" not in result.data
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"
        assert result.data["block_outcome"]["operating_mode"] == "degraded"
        assert result.is_error() is False, "fail-open on the pipeline is retained"


class TestAConflictScoreThatIsPresentIsResolved:
    @pytest.mark.asyncio
    async def test_below_the_threshold_needs_no_arbitration(self, block) -> None:
        payload = ConfidencePayload(confidence_score=0.7,
                                    metadata={"conflict_score": 0.2})

        result = await block.execute(_context(payload))

        assert result.data["arbitration_needed"] is False
        assert result.data["resolution_strategy"] == "none"
        assert result.data["block_outcome"]["measurement_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_above_the_threshold_with_ethics_enforced_defers_to_safety(
        self, block
    ) -> None:
        payload = ConfidencePayload(confidence_score=0.7,
                                    metadata={"conflict_score": 0.9})

        result = await block.execute(
            _context(payload, ethics_result={"enforced": True}))

        assert result.data["resolution_strategy"] == "safety_override"

    @pytest.mark.asyncio
    async def test_a_non_numeric_conflict_score_is_absent_not_zero(
        self, block
    ) -> None:
        payload = ConfidencePayload(confidence_score=0.7,
                                    metadata={"conflict_score": "high"})

        result = await block.execute(_context(payload))

        assert result.data["block_outcome"]["measurement_status"] == "NOT_MEASURED"


class TestTheSignalIsNowSafeToWire:
    """This class was `TestWhyThisIsNotWiredToTheRevisionGate`.

    It pinned the measurements that blocked repair 2's second half: under
    `1 - HHI`, three modules in perfect accord scored 0.667 and cleared the
    gate's 0.60 rewrite threshold, while a 0.95-against-0.05 split scored 0.095
    and cleared nothing. Wiring that would have made agreement rewrite
    responses.

    The formula was corrected on 2026-08-02 and these assertions were inverted
    rather than deleted — the block that was blocked is now wired, and the
    property that had to hold before it could be is asserted here.
    """

    def test_agreement_now_scores_below_sharp_disagreement(self) -> None:
        from phionyx_core.meta.arbitration_math import compute_conflict_score

        assert (compute_conflict_score([0.9, 0.9, 0.9])
                < compute_conflict_score([0.95, 0.05]))

    def test_agreement_alone_no_longer_clears_the_rewrite_threshold(self) -> None:
        from phionyx_core.meta.arbitration_math import compute_conflict_score
        from phionyx_core.pipeline.blocks.response_revision_gate import (
            RevisionThresholds,
        )

        assert (compute_conflict_score([0.9, 0.9, 0.9])
                < RevisionThresholds().conflict_rewrite)

    def test_the_value_no_longer_tracks_module_count(self) -> None:
        """`1 - 1/N` gave 0.5, 0.667 and 0.75 for two, three and four modules
        that all agreed. Agreement is agreement however many report it."""
        from phionyx_core.meta.arbitration_math import compute_conflict_score

        assert compute_conflict_score([0.8, 0.8]) == pytest.approx(0.0)
        assert compute_conflict_score([0.8, 0.8, 0.8]) == pytest.approx(0.0)
        assert compute_conflict_score([0.8] * 4) == pytest.approx(0.0)
