"""phi_computation must not publish a midpoint nobody measured.

Canonical block 37. Written 2026-08-03 as the behaviour test the block should
have had when its fabrication was removed, and it exists for a second reason
worth stating: the removal shipped with a missing import on the very branch it
introduced, and nothing caught it.

`not_measured` was called at line 177 and never imported. mypy on CI said so;
a full local test run did not, because **no test exercised that branch**. A
missing name in a reachable branch is a `NameError` at runtime, not a lint
nit — the block would have crashed the first time a phi engine returned a
result carrying no phi. The type checker found it; the suite could not,
because the suite never went there.

What the block must do, and what these tests pin:

- an engine that returns no phi **measured no phi**. Nothing is published
  under `phi`, and `context.metadata["previous_phi"]` is left alone rather
  than seeded with a midpoint the next turn would read as last turn's result;
- an engine that raises publishes no phi either;
- a real phi flows through untouched.

`phi: 0.5` was the old value on both failure paths. It is the midpoint of the
range and the same value `confidence_fusion.py:85` defaults to, so a crash and
a genuine mid-range measurement were indistinguishable downstream.
`audit_layer.py:127` already branches on `physics_state.get("phi") is None`,
which means absence is a signal this pipeline supports and the fabricated
midpoint destroyed it.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.phi_computation import PhiComputationBlock


class _Engine:
    """A phi computer whose return value each test chooses."""

    def __init__(self, result=None, raises: BaseException | None = None):
        self._result = result
        self._raises = raises
        self.calls = 0

    def compute_phi(self, *args, **kwargs):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


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
class TestAnUnmeasuredPhiIsNotPublished:
    async def test_a_result_without_phi_publishes_no_phi(self):
        """The branch whose missing import shipped. Exercised now."""
        block = PhiComputationBlock(phi_computer=_Engine(result={"components": {}}))
        context = _context(physics_state={"entropy": 0.4})

        result = await block.execute(context)

        assert result.status == "ok", "the pipeline continues; this is fail-open"
        assert "phi" not in result.data, (
            "an engine that returned no phi measured no phi. Publishing 0.5 "
            "here made a crash indistinguishable from a mid-range reading.")
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "NOT_MEASURED"
        assert outcome["non_measurement_cause"] == "input_absent", (
            "the engine ran and returned; what was absent was the phi in its "
            "result — that is an absent input, not an error")

    async def test_previous_phi_is_not_seeded_with_a_midpoint(self):
        """The consequence that outlives the turn.

        `context.metadata["previous_phi"]` is read by the next turn. Seeding it
        from an unmeasured result turns a midpoint nobody measured into last
        turn's measurement.
        """
        block = PhiComputationBlock(phi_computer=_Engine(result={"components": {}}))
        context = _context(physics_state={"entropy": 0.4})

        await block.execute(context)

        assert context.metadata.get("previous_phi") is None
        assert getattr(context, "previous_phi", None) in (None, 0.0), (
            "the block wrote a previous_phi from a result that carried none")

    async def test_a_raising_engine_publishes_no_phi(self):
        block = PhiComputationBlock(
            phi_computer=_Engine(raises=RuntimeError("engine down")))

        result = await block.execute(_context(physics_state={"entropy": 0.4}))

        assert result.status == "ok"
        assert "phi" not in result.data
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "ERROR", (
            "a raised engine is ERROR, not NOT_MEASURED — the difference is "
            "whether anything was attempted")
        assert outcome["operating_mode"] == "degraded"

    async def test_a_measured_phi_flows_through_unchanged(self):
        """The control case. Without it, a block that published nothing at all
        would pass every assertion above."""
        block = PhiComputationBlock(
            phi_computer=_Engine(result={"phi": 0.731, "components": {"a": 1}}))
        context = _context(physics_state={"entropy": 0.4})

        result = await block.execute(context)

        assert result.data["phi"] == 0.731
        assert context.metadata["previous_phi"] == 0.731

    # A structural "every called name is importable" check was written here and
    # removed: it could not tell a module-level name from one imported inside a
    # function, and mypy already makes exactly this assertion in CI — where it
    # is what caught the missing import. A second, weaker copy of a check that
    # works is not coverage.
