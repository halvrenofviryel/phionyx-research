"""The two unified_state blocks, and the midpoint that came back one block later.

Canonical 25 (`unified_state_update_esc`) and 26 (`phi_publish`). They share a
contract, and the sameness was measured rather than assumed: both publish
`unified_state`, both had the identical crash path, and every consumer of that
key reads `metadata["unified_state"]` — not the block result.

**The crash paths republished the state that came in**, under each block's own
result key, so an updated state and an un-updated one shared a field. Omitting
it is safe for the reason above; the state carries forward because nothing
overwrites it.

**phi_publish had a second, worse problem**, and it is the reason this pair was
worth reading rather than batching. `metadata.get("phi", 0.5)` — and this block
*writes what it reads* into `unified_state.phi`, which twenty-odd call sites
then read. phi_computation (canonical 37) had just been fixed to omit `phi`
when its engine measured nothing. This block put the midpoint straight back
into the state, one block later.

That is the third instance of the same shape today — phi_computation then
response_build, entropy_computation then its downstream defaults, and now
this. **A repair one block deep is undone by a default one block later**, which
is the argument for tracing consumers instead of pattern-matching handlers.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.phi_publish import PhiPublishBlock
from phionyx_core.pipeline.blocks.unified_state_update_esc import (
    UnifiedStateUpdateEscBlock,
)


class _State:
    def __init__(self):
        self.phi = 0.11


def _context(**metadata):
    return BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata=dict(metadata),
    )


@pytest.mark.asyncio
class TestPhiPublishDoesNotReintroduceTheMidpoint:
    async def test_an_absent_phi_is_not_written_into_the_state(self):
        state = _State()
        block = PhiPublishBlock(publisher=None)

        result = await block.execute(_context(unified_state=state))

        assert state.phi == 0.11, (
            "0.5 was written into unified_state.phi for a phi nobody "
            "measured — twenty-odd call sites read that field")
        assert "unified_state" not in result.data
        assert result.data["block_outcome"]["measurement_status"] == (
            "NOT_MEASURED")

    async def test_a_measured_phi_is_published(self):
        """The control. A block that published nothing at all would pass the
        assertion above."""
        state = _State()
        block = PhiPublishBlock(publisher=None)

        result = await block.execute(
            _context(unified_state=state, phi=0.73))

        assert state.phi == 0.73
        assert result.data["unified_state"] is state


@pytest.mark.asyncio
class TestNeitherBlockRepublishesAnUnupdatedState:
    @pytest.mark.parametrize("block_cls,kwargs", [
        (PhiPublishBlock, {"publisher": object()}),
        (UnifiedStateUpdateEscBlock, {"updater": object()}),
    ])
    async def test_a_crash_publishes_no_unified_state(self, block_cls, kwargs):
        class _Boom:
            def __getattr__(self, name):
                def _raise(*a, **k):
                    raise RuntimeError("service down")
                return _raise

        block = block_cls(**{k: _Boom() for k in kwargs})
        context = _context(unified_state=_State(), phi=0.5, physics_state={})

        result = await block.execute(context)

        assert result.status == "ok", "fail-open: the turn continues"
        assert "unified_state" not in result.data, (
            "the state that came in was republished as this block's output")
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"

    async def test_the_carried_state_survives(self):
        class _Boom:
            def __getattr__(self, name):
                def _raise(*a, **k):
                    raise RuntimeError("service down")
                return _raise

        state = _State()
        context = _context(unified_state=state, phi=0.5)
        await PhiPublishBlock(publisher=_Boom()).execute(context)

        assert context.metadata["unified_state"] is state
