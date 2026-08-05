"""neurotransmitter_memory_growth must not report growth measured at zero.

Canonical block 28. Both non-measuring paths published `growth_metrics: {}` —
the no-updater path and the crash path.

That is not confined to the block's own record. `echo_orchestrator.py:776`
merges block result data into `metadata`, and `response_build.py:205` reads
`metadata.get("growth_metrics")` and hands it to the response builder. So an
empty dict travelled from "nothing measured this" to "growth was measured and
it was zero", through a merge neither block mentions.

Neither path publishes the key now. `response_build` receives `None`, which
its builder already accepts — the parameter is `Optional`.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.neurotransmitter_memory_growth import (
    NeurotransmitterMemoryGrowthBlock,
)


def _context():
    return BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={"narrative_response": "answer", "physics_state": {}},
    )


@pytest.mark.asyncio
class TestNoGrowthIsNotZeroGrowth:
    async def test_no_updater_publishes_no_metrics(self):
        block = NeurotransmitterMemoryGrowthBlock(growth_updater=None)

        result = await block.execute(_context())

        assert result.status == "ok"
        assert "growth_metrics" not in result.data, (
            "an empty dict here is merged into metadata and read by "
            "response_build as growth measured at zero")
        assert result.data["block_outcome"]["measurement_status"] == (
            "NOT_MEASURED")

    async def test_a_crash_publishes_no_metrics(self):
        class _Boom:
            def update_growth(self, *args, **kwargs):
                raise RuntimeError("tracker down")

        block = NeurotransmitterMemoryGrowthBlock(growth_updater=_Boom())

        result = await block.execute(_context())

        assert "growth_metrics" not in result.data
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"

    async def test_measured_growth_is_published(self):
        """The control. A block publishing nothing ever would pass the rest."""
        class _Updater:
            def update_growth(self, *args, **kwargs):
                return {"dopamine": 0.4}

        block = NeurotransmitterMemoryGrowthBlock(growth_updater=_Updater())

        result = await block.execute(_context())

        assert result.data["growth_metrics"] == {"dopamine": 0.4}


class TestTheMergeThatCarriedIt:
    """The mechanism, asserted because it is what made a block-local value
    into a cross-block claim — and because neither block mentions it."""

    def test_the_orchestrator_merges_block_data_into_metadata(self):
        import pathlib

        source = (next(p for p in pathlib.Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
                  / "phionyx_core" / "orchestrator" / "echo_orchestrator.py"
                  ).read_text(encoding="utf-8")

        assert "current_context.metadata.update(filtered_data)" in source, (
            "the merge is gone; the reasoning for omitting growth_metrics "
            "assumed block data reaches metadata and should be rechecked")
