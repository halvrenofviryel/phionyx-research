"""entropy_computation must not republish last turn's value as this turn's.

Canonical block 38. Two substitutions, and the second is the one that took
reading the block to see.

**The success path defaulted to 0.5.** `entropy_result.get("entropy", 0.5)` —
the midpoint, and the same value four other blocks already fall back to:
`phi_computation.py:120`, `knowledge_boundary_check.py:145` and
`ethics_pre_response.py:104`. So the reading nobody took was indistinguishable
from the reading everybody assumes, in a field five blocks read.

**The crash path republished `context.current_entropy`.** That value is not
wrong — it is last turn's entropy, and carrying it forward is what the state
wants. What was wrong is *where it was published*: under this block's own
`entropy` result key, so a carried-forward number and a freshly computed one
occupied the same field with nothing to tell them apart.

The state still carries forward. Nothing overwrites `context.current_entropy`
on either failure path, which is exactly the carry. What stops is this block
claiming to have measured it.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.entropy_computation import (
    EntropyComputationBlock,
)


class _Computer:
    def __init__(self, result=None, raises: BaseException | None = None):
        self._result = result
        self._raises = raises

    def compute_entropy(self, *args, **kwargs):
        if self._raises is not None:
            raise self._raises
        return self._result


def _context(current_entropy=0.42):
    context = BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={},
    )
    context.current_entropy = current_entropy
    return context


@pytest.mark.asyncio
class TestAnUncomputedEntropyIsNotPublished:
    async def test_a_result_without_entropy_publishes_none(self):
        block = EntropyComputationBlock(
            entropy_computer=_Computer(result={"components": {}}))

        result = await block.execute(_context())

        assert result.status == "ok"
        assert "entropy" not in result.data, (
            "0.5 here was the midpoint four other blocks already default to, "
            "so an unmeasured reading looked exactly like the assumed one")
        assert result.data["block_outcome"]["measurement_status"] == (
            "NOT_MEASURED")

    async def test_the_carried_state_is_left_alone_when_nothing_was_computed(self):
        """The carry-forward is the state's business, not this block's claim."""
        context = _context(current_entropy=0.42)
        block = EntropyComputationBlock(
            entropy_computer=_Computer(result={"components": {}}))

        await block.execute(context)

        assert context.current_entropy == 0.42, (
            "the state should keep its value; overwriting it with a midpoint "
            "is how a fabrication outlives the turn")
        assert "current_entropy" not in context.metadata

    async def test_a_crash_publishes_no_entropy_and_keeps_the_state(self):
        context = _context(current_entropy=0.42)
        block = EntropyComputationBlock(
            entropy_computer=_Computer(raises=RuntimeError("computer down")))

        result = await block.execute(context)

        assert result.status == "ok", "fail-open: the turn continues"
        assert "entropy" not in result.data, (
            "republishing last turn's entropy under this block's result key "
            "made a carried value and a computed one the same field")
        assert context.current_entropy == 0.42, "the carry-forward survives"

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "ERROR"
        assert outcome["operating_mode"] == "degraded"

    async def test_a_computed_entropy_flows_through_and_updates_the_state(self):
        """The control. Without it, a block that published nothing at all and
        never updated the state would pass every assertion above."""
        context = _context(current_entropy=0.42)
        block = EntropyComputationBlock(
            entropy_computer=_Computer(result={"entropy": 0.77,
                                               "components": {"a": 1}}))

        result = await block.execute(context)

        assert result.data["entropy"] == 0.77
        assert context.current_entropy == 0.77
        assert context.metadata["current_entropy"] == 0.77


class TestTheMidpointIsStillAssumedElsewhere:
    """What this change did not fix, recorded so it is not mistaken for done.

    Removing the substitution here does not remove the readers that supply
    their own. A consumer defaulting an absent entropy to 0.5 reintroduces
    the same indistinguishability one block later — the pattern that made
    response_build worth tracing after phi_computation was fixed.
    """

    def test_the_downstream_defaults_are_still_there(self):
        import pathlib

        root = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()) / "phionyx_core"
        blocks = root / "pipeline" / "blocks"
        still_defaulting = [
            path.name
            for path in sorted(blocks.glob("*.py"))
            if "current_entropy or 0.5" in path.read_text(encoding="utf-8")
            or "current_entropy is not None else 0.5" in path.read_text(
                encoding="utf-8")
        ]

        assert still_defaulting, (
            "no block substitutes 0.5 for an absent entropy any more — good. "
            "Delete this test and the note in the inventory rather than "
            "leaving a claim about the codebase that is no longer true.")
