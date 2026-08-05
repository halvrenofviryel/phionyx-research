"""Parallel and sequential execution must leave the same turn state.

OD-22, closed 2026-08-04 with founder approval.

CLAUDE.md invariant 5 is that identical inputs give a reproducible path. The
orchestrator had two copies of the post-block state folding — one in the
parallel loop, one in the sequential — and a structural diff of the two
copies found **four** differences:

1. **Type coercion.** Parallel wrote `float(phi)` and `float(entropy)`;
   sequential wrote the block's raw value. `context.previous_phi` is
   annotated `Optional[float]` in `pipeline/base.py:51` and held a float in
   one mode and the engine's type in the other. (The sequential path's
   `cast(float, ...)` on amplitude/integrity is a typing no-op — it converts
   nothing.)
2. **amplitude and integrity.** Handled only in the sequential loop, so in
   parallel mode `context.current_integrity` never moved off its initial
   value — and that is the value threaded into the CEP safety evaluation
   (OD-16). A safety check read a stale integrity in one execution mode.
3. **coherence_qa redaction.** Sequential only. Dead in both today: the block
   is in no canonical order and lives in `blocks/archive/` (OD-2). Folded in
   anyway so the redaction reaches both paths when OD-2 is decided.
4. **A guard.** `if unified_state:` versus
   `if unified_state and not isinstance(unified_state, type):`. The stricter
   one — which rejects the class being passed where an instance was meant —
   is what both use now.

The fix merged the copies into `_apply_post_block_state_updates`. Patching
two copies to agree would have left two copies, and two copies drift; that is
how these four arose.

**These tests are the closure.** A refactor that passes the existing suite
proves nothing about mode-equivalence, because nothing in the suite compared
the modes. They run the same input through both and compare the resulting
state field by field.
"""
from __future__ import annotations

import inspect

import pytest

from phionyx_core.orchestrator.echo_orchestrator import (
    EchoOrchestrator,
    OrchestratorServices,
)
from phionyx_core.pipeline.base import BlockContext, BlockResult

#: The fields the folder is responsible for. Named rather than discovered, so
#: a field that stops being folded shows up as a missing key rather than
#: silently dropping out of the comparison.
FOLDED_ATTRIBUTES = (
    "current_entropy",
    "previous_phi",
    "current_amplitude",
    "current_integrity",
)
FOLDED_METADATA = (
    "current_entropy",
    "previous_phi",
    "current_amplitude",
    "current_integrity",
    "physics_state",
)


def _orchestrator(parallel: bool) -> EchoOrchestrator:
    return EchoOrchestrator(services=OrchestratorServices(),
                            enable_parallel=parallel)


def _context() -> BlockContext:
    return BlockContext(
        user_input="test", card_type="test", card_title="Test",
        scene_context="test", card_result="", metadata={})


def _fold(parallel: bool, block_id: str, data: dict) -> BlockContext:
    """Fold one block result through the mode's folder and return the state."""
    orchestrator = _orchestrator(parallel)
    context = _context()
    result = BlockResult(block_id=block_id, status="ok", data=data)
    orchestrator._apply_post_block_state_updates(
        context, block_id, result,
        mode="Parallel" if parallel else "Sequential")
    return context


def _snapshot(context: BlockContext) -> dict:
    state = {f"ctx.{name}": getattr(context, name, None)
             for name in FOLDED_ATTRIBUTES}
    state.update({f"meta.{key}": (context.metadata or {}).get(key)
                  for key in FOLDED_METADATA})
    return state


CASES = [
    ("entropy_computation", {"entropy": 0.37}),
    ("phi_computation", {"phi": 0.62}),
    ("emotion_estimation", {"valence": 0.4, "arousal": 0.7}),
    ("emotion_estimation", {"valence": 0.4}),
    ("state_update_physics", {"amplitude": 4.25, "integrity": 87.5}),
    ("state_update_physics", {"integrity": 12.0}),
    # Integers, because coercion is one of the four differences: an int
    # reaching one mode as int and the other as float is the defect.
    ("entropy_computation", {"entropy": 1}),
    ("phi_computation", {"phi": 0}),
]


@pytest.mark.parametrize("block_id,data", CASES)
class TestBothModesLeaveTheSameState:

    def test_the_state_is_identical(self, block_id, data):
        parallel = _snapshot(_fold(True, block_id, data))
        sequential = _snapshot(_fold(False, block_id, data))

        differing = {k: (parallel[k], sequential[k])
                     for k in parallel if parallel[k] != sequential[k]}

        assert differing == {}, (
            f"{block_id} with {data} leaves different state per mode: "
            f"{differing}. That is CLAUDE.md invariant 5.")

    def test_the_types_are_identical(self, block_id, data):
        """Equality is not enough: 1 == 1.0 while `type` differs, and the
        original defect was exactly a coercion that happened in one mode."""
        parallel = _snapshot(_fold(True, block_id, data))
        sequential = _snapshot(_fold(False, block_id, data))

        differing = {k: (type(parallel[k]).__name__,
                         type(sequential[k]).__name__)
                     for k in parallel
                     if type(parallel[k]) is not type(sequential[k])}

        assert differing == {}, f"{block_id}: types differ per mode: {differing}"


class TestTheFoldedValuesAreNumeric:
    """`context.previous_phi` is Optional[float]. It used to hold whatever the
    block published in sequential mode."""

    @pytest.mark.parametrize("block_id,key,attribute", [
        ("entropy_computation", "entropy", "current_entropy"),
        ("phi_computation", "phi", "previous_phi"),
        ("state_update_physics", "amplitude", "current_amplitude"),
        ("state_update_physics", "integrity", "current_integrity"),
    ])
    def test_an_int_is_stored_as_a_float(self, block_id, key, attribute):
        for parallel in (True, False):
            context = _fold(parallel, block_id, {key: 3})
            assert isinstance(getattr(context, attribute), float)

    @pytest.mark.parametrize("value", ["nan-ish", object(), [1.0]])
    def test_a_non_numeric_value_is_refused_rather_than_crashing(self, value):
        """The crash that started this: `is not None` does not mean numeric,
        and an unguarded float() took the parallel pipeline down on an input
        the sequential path survived."""
        for parallel in (True, False):
            context = _fold(parallel, "phi_computation", {"phi": value})
            assert context.previous_phi is None
            assert "previous_phi" not in (context.metadata or {})


class TestThereIsOnlyOneCopy:
    """The structural guarantee. Two copies that agree today drift again —
    that is how all four differences arose."""

    def test_both_loops_call_the_shared_folder(self):
        source = inspect.getsource(EchoOrchestrator.execute_pipeline)

        calls = source.count("_apply_post_block_state_updates(")

        assert calls == 2, (
            f"execute_pipeline calls the shared folder {calls} times; the "
            "parallel and sequential loops should each call it exactly once. "
            "A loop folding state inline again is OD-22 reopening.")

    def test_the_folder_handles_every_key_both_loops_used_to(self):
        source = inspect.getsource(
            EchoOrchestrator._apply_post_block_state_updates)

        for key in ("entropy_computation", "phi_computation",
                    "emotion_estimation", "coherence_qa",
                    "amplitude", "integrity"):
            assert key in source, (
                f"{key} was folded by one of the two original loops and the "
                "shared folder no longer mentions it")
