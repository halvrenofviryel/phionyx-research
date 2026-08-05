"""response_build must not put fabricated physics in the user's answer.

Canonical block 42, and the last one before the response leaves the pipeline —
so nothing downstream corrects what it writes. `chat.py:409` reads the
`response` payload and the whole dict goes out to the client.

This block is **not a producer**. It is an enforcement point: it reads
`revision_directive` from `response_revision_gate` (canonical 41) and turns a
`reject` into a refusal the user reads. That makes what it publishes alongside
the narrative part of a safety-relevant surface, not incidental telemetry.

Two fabrications were removed on 2026-08-03, and they were not equally bad:

- the **crash path** emitted ``"physics": {"phi": 0.5, "entropy": 0.5}`` —
  two midpoints, unlabelled, inside the payload that reaches the client;
- the **success path** substituted ``physics_state['phi'] = 0.5`` under
  ``phi_source: 'fallback'``. Labelled, which is better, and still a midpoint
  sitting in the same field a measurement uses.

The second mattered because of where it sat: `phi_computation` (canonical 37)
was fixed to omit `phi` when its engine measured nothing, and this block ran
eleven positions later and put a value back. A repair one block deep is undone
by a default one block later, which is why these are worth tracing rather than
pattern-matching.

The narrative fallback is kept. A user who asked a question needs an answer;
that is a different thing from telemetry nobody measured.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.response_build import ResponseBuildBlock


class _Builder:
    """Records what the block hands it, and echoes it back."""

    def __init__(self, raises: BaseException | None = None):
        self.raises = raises
        self.physics_state: dict | None = None
        self.narrative: str | None = None

    def build_response(self, frame, narrative_response, physics_state, **kwargs):
        if self.raises is not None:
            raise self.raises
        self.physics_state = dict(physics_state)
        self.narrative = narrative_response
        return {"narrative": narrative_response, "physics": dict(physics_state)}


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
class TestNoFabricatedPhysicsReachesTheUser:
    async def test_an_unmeasured_phi_is_not_substituted(self):
        """The repair that would otherwise be undone eleven blocks later."""
        builder = _Builder()
        block = ResponseBuildBlock(builder=builder)

        await block.execute(_context(
            physics_state={"entropy": 0.31},
            narrative_text="answer",
        ))

        assert builder.physics_state is not None
        assert "phi" not in builder.physics_state, (
            "a midpoint was substituted for a phi nobody measured. "
            "phi_computation omits the key on purpose; putting one back here "
            "makes that omission pointless.")
        assert builder.physics_state["phi_source"] == "not_measured"

    async def test_a_measured_phi_is_passed_through(self):
        """The control. Without it, a block that dropped phi entirely would
        pass the assertion above."""
        builder = _Builder()
        block = ResponseBuildBlock(builder=builder)

        await block.execute(_context(
            physics_state={"entropy": 0.31, "phi": 0.812},
            narrative_text="answer",
        ))

        assert builder.physics_state["phi"] == 0.812
        assert "phi_source" not in builder.physics_state, (
            "a phi that arrived measured needs no provenance label invented "
            "for it here")

    async def test_a_crash_ships_a_narrative_and_no_physics(self):
        """What the user gets when the builder fails.

        An answer, because they asked a question. Not two midpoints dressed as
        telemetry in the same payload.
        """
        block = ResponseBuildBlock(builder=_Builder(raises=RuntimeError("boom")))

        result = await block.execute(_context(physics_state={"entropy": 0.31}))

        assert result.status == "ok", "fail-open: the turn still answers"
        response = result.data["response"]
        assert response["narrative"], "the user is left with something"
        assert "physics" not in response, (
            "fabricated telemetry inside the client payload, from the last "
            "block before it ships")
        assert response["physics_measured"] is False

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "ERROR"
        assert outcome["operating_mode"] == "degraded"


@pytest.mark.asyncio
class TestTheEnforcementPathStillEnforces:
    """The reason this block's class is enforcement rather than producer.

    `response_revision_gate` decides; this block is where the decision becomes
    something the user reads. The narrative arrives under `narrative_text`,
    which is what narrative_layer writes — not `narrative_response`, which is
    the builder protocol's parameter name. The two differ, and a test that
    guessed the wrong one still passed its reject case, because the reject
    path overwrites whatever was there. If that stopped working, a reject verdict would
    be computed, recorded, and silently ignored — a warning without damping,
    which the doctrine names as invalid.
    """

    async def test_a_reject_directive_replaces_the_answer(self):
        builder = _Builder()
        block = ResponseBuildBlock(builder=builder)

        await block.execute(_context(
            physics_state={"entropy": 0.31},
            narrative_text="the unsafe answer",
            revision_directive={"directive": "reject"},
        ))

        assert builder.narrative is not None
        assert "the unsafe answer" not in builder.narrative
        assert "can't safely respond" in builder.narrative

    async def test_a_pass_directive_leaves_the_answer_alone(self):
        builder = _Builder()
        block = ResponseBuildBlock(builder=builder)

        await block.execute(_context(
            physics_state={"entropy": 0.31},
            narrative_text="the ordinary answer",
            revision_directive={"directive": "pass"},
        ))

        assert builder.narrative == "the ordinary answer"
