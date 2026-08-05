"""A block that did not run must say what went unmeasured. OD-21.

The migration gave every fail-open handler a measurement record. It had not
reached the one path where a block produces no result at all: the skip. A
skipped block carried `skip_reason` — a CONTROL-channel string — and nothing
on the measurement channel, so the record said "did not run" and never said
what was therefore not measured.

`neurotransmitter_memory_growth` is the case that surfaced it. OD-15 removed
its adapter because the adapter returned a literal
`{"neurotransmitter_updated": True}` and called nothing; there is no growth
updater in `phionyx_core` for it to have delegated to. So the block skips.

**It is not retired, and the canonical count does not move.** Three reasons,
each checked rather than assumed:

- `.claude/CLAUDE.md` invariant: blocks are never deleted, only
  policy-bypassed with an audit trail.
- 46 is load-bearing outside this repo. `PATENT_CLAIM_CODE_TEST_MAP.md` cites
  "v3.8.0, 46 canonical blocks" against claim SF1-C4, and
  `PATENT_PAPER_CROSS_REF.md` maps it to the paper's Appendix A.
- The published wording already draws the distinction that makes this
  consistent: `apps/phionyx-website/app/platform/page.tsx:48` says
  phionyx-core *defines* a canonical 46-block pipeline, and :53 says "you do
  not have to deploy all 46 blocks."

So the contract keeps 46 and the record gains the sentence it was missing.

(The patent test itself, `test_sf1_claim4_block_sequence`, asserts
`len(block_order) >= 13` and names ten required blocks;
neurotransmitter_memory_growth is not among them. Checked, because
recommending a retirement without checking is how this nearly went wrong.)
"""
from __future__ import annotations

import pytest

from phionyx_core.contracts.telemetry import get_canonical_blocks
from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.neurotransmitter_memory_growth import (
    NeurotransmitterMemoryGrowthBlock,
)


def _context() -> BlockContext:
    return BlockContext(
        user_input="test", card_type="test", card_title="Test",
        scene_context="test", card_result="", metadata={})


class TestTheCanonicalCountIsUnchanged:
    """The constraint the repair had to satisfy, asserted rather than trusted."""

    def test_the_contract_still_defines_46_blocks(self):
        assert len(get_canonical_blocks()) == 46, (
            "the canonical count moved. It is cited in "
            "PATENT_CLAIM_CODE_TEST_MAP.md against claim SF1-C4 and mapped to "
            "the paper's Appendix A — changing it is a portfolio-wide event, "
            "not a side effect of a block repair.")

    def test_the_block_is_still_in_the_canonical_order(self):
        assert "neurotransmitter_memory_growth" in get_canonical_blocks(), (
            "the block was retired. CLAUDE.md: blocks are never deleted, only "
            "policy-bypassed with an audit trail.")


class TestTheBlockDeclaresWhyItCannotRun:
    def test_it_skips_with_a_named_reason_when_no_updater_exists(self):
        block = NeurotransmitterMemoryGrowthBlock(growth_updater=None)

        assert block.should_skip(_context()) == "growth_updater_not_available"

    def test_it_runs_when_an_updater_is_supplied(self):
        """The control. Without it, a block hardcoded to skip would pass."""
        class _Updater:
            def update_growth(self, **kwargs):
                return {"boost": 1.0}

        block = NeurotransmitterMemoryGrowthBlock(growth_updater=_Updater())

        assert block.should_skip(_context()) is None


@pytest.mark.asyncio
class TestASkippedBlockCarriesAMeasurementRecord:
    """The repair itself, at the orchestrator where skips are produced."""

    async def _run(self):
        from phionyx_core.orchestrator.block_factory import create_all_blocks
        from phionyx_core.orchestrator.echo_orchestrator import (
            EchoOrchestrator,
            OrchestratorServices,
        )

        services = OrchestratorServices()
        orchestrator = EchoOrchestrator(services=services, enable_parallel=False)
        orchestrator.blocks = create_all_blocks(services=services)
        return await orchestrator.execute_pipeline(_context())

    async def test_every_skipped_block_records_what_went_unmeasured(self):
        """End to end. A service-less run skips 37 of the 46 — measured — so
        this exercises the path on a real pipeline rather than asserting the
        record's shape and calling it done.

        The first version of this test guessed `orchestrator._last_results`,
        found nothing and skipped itself, which would have left the whole
        end-to-end claim unasserted while the file reported green.
        `execute_pipeline` returns a dict keyed `results`, `final_context`,
        `skipped_blocks` and `execution_guard` — read, not assumed.
        """
        from phionyx_core.pipeline.base import BlockResult

        results = (await self._run())["results"]
        skipped = [b for b, r in results.items()
                   if isinstance(r, BlockResult) and r.status == "skipped"]
        assert skipped, "nothing skipped, so this asserts nothing"

        bare = [
            block_id for block_id, result in results.items()
            if isinstance(result, BlockResult) and result.status == "skipped"
            and "block_outcome" not in (result.data or {})
        ]
        assert bare == [], (
            f"{bare} skipped without a measurement record. skip_reason is the "
            "control channel; it does not say what went unmeasured.")

    async def test_the_skip_record_has_the_right_shape(self):
        """Asserted directly on the outcome type, so it holds regardless of
        how the orchestrator exposes results."""
        from phionyx_core.pipeline.outcome import (
            BlockOutcome,
            BlockRunStatus,
            not_measured,
        )

        record = BlockOutcome(
            block_id="neurotransmitter_memory_growth",
            legacy_control_status="skipped",
            block_run_status=BlockRunStatus.NOT_STARTED,
            measurement=not_measured(
                "the block did not run: growth_updater_not_available",
                cause="input_absent"),
            operating_mode="degraded",
        ).to_record_fields()

        assert record["measurement_status"] == "NOT_MEASURED"
        assert "growth_updater_not_available" in record["reason"]
        assert record["operating_mode"] == "degraded"

    async def test_not_started_is_the_status_a_skip_gets(self):
        """BlockRunStatus has COMPLETED, FAILED, TIMEOUT and NOT_STARTED —
        checked. A skipped block did not start, so adding a SKIPPED member
        would have been a contract change made by accident."""
        from phionyx_core.pipeline.outcome import BlockRunStatus

        assert {m.name for m in BlockRunStatus} == {
            "COMPLETED", "FAILED", "TIMEOUT", "NOT_STARTED"}
