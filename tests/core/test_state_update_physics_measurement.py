"""state_update_physics must not report a state it did not update.

Canonical block 30, and the highest-consequence of the passive ten: seven
call sites read `metadata["physics_state"]`, which is the state this block
exists to advance.

Its crash path republished `metadata.get("physics_state", {})` — the state
that came *in* — under the block's own result key. Two problems, one obvious
and one not:

- an un-updated state and an updated one shared a field with nothing to tell
  them apart, the same shape entropy_computation had;
- the `{}` default made an **absent** state read as an **empty** one, which is
  the absence-as-confirmation case the doctrine's M1.1 names.

Omitting it is safe and that was checked rather than assumed: every consumer
reads `metadata["physics_state"]`, not this block's result data. The state
carries forward because nothing overwrites it. What stops is this block
reporting a state it did not update.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.state_update_physics import (
    StateUpdatePhysicsBlock,
)


class _Boom:
    """An updater that raises. The method name is `update_physics_state`,
    taken from the block rather than guessed — a fixture with the wrong name
    lands in the exception path for the wrong reason and still looks like it
    tested the right thing."""

    def update_physics_state(self, *args, **kwargs):
        raise RuntimeError("physics down")


class _State:
    """A stand-in unified_state. Its presence matters: the updater is called
    only under `if self.updater and unified_state`, so a context without one
    takes the in-block fallback and never reaches the injected updater at all.
    A fixture missing it tests the fallback while appearing to test the crash."""

    phi = 0.6
    entropy = 0.3


def _context(physics_state=None):
    metadata = {"unified_state": _State()}
    if physics_state:
        metadata["physics_state"] = physics_state
    return BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata=metadata,
    )


@pytest.mark.asyncio
class TestACrashDoesNotReportAnUnupdatedState:
    async def test_no_physics_state_is_published_on_a_crash(self):
        block = StateUpdatePhysicsBlock(updater=_Boom())
        context = _context({"phi": 0.6, "entropy": 0.3})

        result = await block.execute(context)

        assert result.status == "ok", "fail-open: the turn continues"
        assert "physics_state" not in result.data, (
            "the state that came in was republished as this block's output")

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "ERROR"
        assert outcome["operating_mode"] == "degraded"

    async def test_the_carried_state_survives_the_crash(self):
        """Dropping the publication would be worthless if it dropped the carry."""
        block = StateUpdatePhysicsBlock(updater=_Boom())
        context = _context({"phi": 0.6, "entropy": 0.3})

        await block.execute(context)

        assert context.metadata["physics_state"] == {"phi": 0.6, "entropy": 0.3}


class TestTheConsumersReadMetadataNotThisResult:
    """The precondition for omitting the key, asserted so it stays true."""

    def test_every_physics_state_reader_uses_metadata(self):
        import pathlib
        import re

        root = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()) / "phionyx_core"
        offenders = []
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in str(path) or path.name == "state_update_physics.py":
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if re.search(r'\.data\[?\.?\(?["\']physics_state', line):
                    offenders.append(f"{path.name}: {line.strip()[:60]}")

        assert offenders == [], (
            f"a consumer now reads physics_state off a block result: "
            f"{offenders}. Omitting it on the crash path is only safe while "
            "every reader goes through metadata.")
