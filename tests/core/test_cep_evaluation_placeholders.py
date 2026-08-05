"""cep_evaluation must not feed a safety check values the turn never set.

Canonical block 19. OD-16 removed six hardcoded placeholders from the adapter
in two passes, and the second pass is the interesting one: the first pass
closed three and left three **with a stated reason that was right for two and
wrong for one**. Tracing them one at a time is what separated them:

- **`time_delta=1.0` had a source all along.** `time_update_sot` is canonical
  2 and writes `context.metadata["time_delta"]`; this block is canonical 19.
  The value reaches `temporal_delay` in the CEP metrics through
  `cep_engine.py:268`, whose own default for an absent value is **0.0** — so
  the hardcoded 1.0 did not match the engine it was feeding. The claim that
  "no context field exists" was simply false.

- **`character_archetype="shadow"` had no source, and forcing it was worse
  than passing nothing.** It reaches `npc_role`, and `cep_engine.py:825`
  renders it into text a **user reads** after trauma-content sanitization:
  "Shadow is navigating a difficult moment." The engine's own fallback,
  "this character", is what an unestablished archetype actually is.

- **`profile_name="edu"` was never consumed.** `CEPEngine.evaluate_response`
  accepts the parameter and its body reads it zero times — the config is
  fixed at construction — and `config/cep_profiles/` does not exist in this
  repo. Passing it selected nothing. The dead parameter is filed as OD-18,
  because a safety-profile override that is accepted and silently ignored
  outranks whichever value was being handed to it.

The tests below assert the wiring at the block boundary. What the adapter
does with an absent `time_delta` is asserted separately, because the block
passing `None` and the adapter substituting the engine default are two
different decisions and only one of them is this block's.
"""
from __future__ import annotations

import inspect

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.cep_evaluation import CepEvaluationBlock


class _Evaluator:
    """Records every keyword the block hands it."""

    def __init__(self, raises: BaseException | None = None):
        self._raises = raises
        self.seen: dict = {}

    async def evaluate(self, **kwargs):
        if self._raises is not None:
            raise self._raises
        self.seen = dict(kwargs)
        return ("flags", "config")


def _context(**metadata):
    context = BlockContext(
        user_input="test",
        card_type="test",
        card_title="Test",
        scene_context="test",
        card_result="",
        metadata={"frame": {"id": "f"}, "narrative_text": "answer", **metadata},
    )
    return context


@pytest.mark.asyncio
class TestTheTurnsClockReachesTheSafetyEvaluation:
    async def test_a_real_time_delta_is_threaded(self):
        evaluator = _Evaluator()
        block = CepEvaluationBlock(evaluator=evaluator)

        await block.execute(_context(time_delta=2.75))

        assert evaluator.seen["time_delta"] == 2.75, (
            "the block held a real time_delta from canonical block 2 and the "
            "adapter was substituting 1.0 for it")

    async def test_an_absent_time_delta_is_passed_as_none_not_invented(self):
        evaluator = _Evaluator()
        block = CepEvaluationBlock(evaluator=evaluator)

        result = await block.execute(_context())

        assert evaluator.seen["time_delta"] is None, (
            "the block must not invent a clock; choosing the substitute is "
            "the adapter's decision and it is asserted separately")
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "NOT_MEASURED"
        assert outcome["operating_mode"] == "degraded"

    async def test_a_measured_turn_records_no_non_measurement(self):
        """The control. Without it, a block that always recorded NOT_MEASURED
        would pass the assertion above.

        A turn is only fully measured when phi and entropy are there too: the
        CEP verdict is computed from them, and an absent entropy flips
        is_self_narrative_blocked at 18 measured points. This test failed when
        that widening landed, correctly — the fixture was supplying a clock
        and calling the turn measured.
        """
        block = CepEvaluationBlock(evaluator=_Evaluator())

        result = await block.execute(_context(
            time_delta=2.75,
            physics_state={"phi": 0.62, "entropy": 0.31},
        ))

        assert "block_outcome" not in result.data
        assert result.data["cep_flags"] == "flags"


@pytest.mark.asyncio
class TestTheVerdictsInputsAreRecorded:
    """An absent phi or entropy is named, because the verdict depends on them.

    `guard_processor.py:220` substitutes 0.0 for either. The entropy one is
    not inert — it drives phi_echo_density to its maximum, which flips
    is_self_narrative_blocked in the window 0.24 < self_reference <= 0.30.
    Measured in test_cep_thresholds_reachability.py; recorded here.
    """

    async def test_an_absent_entropy_is_named(self):
        block = CepEvaluationBlock(evaluator=_Evaluator())

        result = await block.execute(_context(
            time_delta=1.0, physics_state={"phi": 0.62}))

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "NOT_MEASURED"
        assert "entropy" in outcome["reason"]
        assert "phi" not in outcome["reason"].replace("phi_", ""), (
            "phi was measured this turn and must not be listed as absent")

    async def test_an_absent_phi_is_named(self):
        block = CepEvaluationBlock(evaluator=_Evaluator())

        result = await block.execute(_context(
            time_delta=1.0, physics_state={"entropy": 0.31}))

        assert "phi" in result.data["block_outcome"]["reason"]

    async def test_the_flags_are_still_reported(self):
        """Fail-open is unchanged: the verdict stands, its provenance is added."""
        block = CepEvaluationBlock(evaluator=_Evaluator())

        result = await block.execute(_context(time_delta=1.0))

        assert result.data["cep_flags"] == "flags", (
            "recording that the inputs were unmeasured must not suppress the "
            "safety verdict itself")


class TestTheAdapterSubstitutesTheEnginesOwnDefault:
    """Where the substitute is chosen, and why it is 0.0 rather than 1.0.

    Asserted on the adapter's **call**, parsed, rather than on the module
    text. The first version of these three tests grepped the source and all
    three failed — against the docstring above the call, which names the
    values that were removed. That is the same failure mode as the finding
    itself: a string match cannot tell a live default from a record of a dead
    one, and here the record is directly above the fix.

    What matters is the number and its provenance: `cep_engine.py:268` reads
    `unified_state.get('time_delta', 0.0)`, so 0.0 is the engine's answer for
    "no temporal information" and 1.0 was an answer from nowhere.
    """

    @staticmethod
    def _cep_call_keywords() -> dict:
        """The keywords the adapter actually passes, from the AST."""
        import ast

        from phionyx_core.orchestrator import block_factory

        tree = ast.parse(inspect.getsource(block_factory))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if getattr(node.func, "attr", "") != "evaluate_cep_and_update_safety":
                continue
            return {kw.arg: kw.value for kw in node.keywords if kw.arg}
        raise AssertionError(
            "the CEP adapter no longer calls evaluate_cep_and_update_safety")

    def test_the_adapter_no_longer_hardcodes_one_point_zero(self):
        import ast

        keywords = self._cep_call_keywords()

        assert "time_delta" in keywords
        value = keywords["time_delta"]
        assert not (isinstance(value, ast.Constant) and value.value == 1.0), (
            "the adapter is inventing a clock again")
        assert isinstance(value, ast.IfExp), (
            "time_delta should be the threaded value with the engine default "
            "as the fallback, not a literal")

    def test_the_archetype_is_no_longer_forced_to_shadow(self):
        import ast

        keywords = self._cep_call_keywords()

        value = keywords.get("character_archetype")
        assert isinstance(value, ast.Constant) and value.value == "", (
            '"shadow" reaches text the user reads after a trauma-content '
            "sanitization: 'Shadow is navigating a difficult moment.' The "
            'engine falls back to "this character" on an empty value.')

    def test_the_dead_profile_override_is_no_longer_passed(self):
        keywords = self._cep_call_keywords()

        assert "profile_name" not in keywords, (
            "evaluate_response never reads it; passing a value selected "
            "nothing — see OD-18")


class TestTheProfileOverrideIsStillDead:
    """OD-18, pinned here rather than asserted as fixed.

    Dropping the value does not make the parameter work. This fails the day
    `evaluate_response` starts honouring its `profile_name` argument, which is
    when the override becomes worth wiring from a real source rather than
    leaving unpassed.
    """

    def test_evaluate_response_still_ignores_profile_name(self):
        import ast

        from phionyx_core.cep import cep_engine

        tree = ast.parse(inspect.getsource(cep_engine))
        uses = 0
        for node in ast.walk(tree):
            if not (isinstance(node, ast.AsyncFunctionDef)
                    or isinstance(node, ast.FunctionDef)):
                continue
            if node.name != "evaluate_response":
                continue
            for inner in ast.walk(node):
                if isinstance(inner, ast.Name) and inner.id == "profile_name":
                    uses += 1

        assert uses == 0, (
            "evaluate_response now reads profile_name. OD-18 is live: pick a "
            "real source for it in block_factory instead of not passing it, "
            "and delete this test.")

    def test_the_engine_reads_no_profile_from_disk_here(self):
        """The second half of why passing 'edu' selected nothing."""
        import pathlib

        root = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())

        assert not (root / "config" / "cep_profiles").exists(), (
            "cep_profiles now exists, so a profile_name could select real "
            "thresholds — revisit OD-18 before trusting the default config")


@pytest.mark.asyncio
class TestTheExistingBehaviourSurvives:
    """The paths this change must not disturb."""

    async def test_a_missing_frame_still_short_circuits(self):
        block = CepEvaluationBlock(evaluator=_Evaluator())

        context = BlockContext(
            user_input="test", card_type="test", card_title="Test",
            scene_context="test", card_result="", metadata={})
        result = await block.execute(context)

        assert result.data["cep_flags"] is None
        assert "block_outcome" not in result.data, (
            "no evaluation was attempted, so there is no temporal_delay to "
            "report a non-measurement for")

    async def test_a_raising_evaluator_is_still_reported_as_skipped(self):
        block = CepEvaluationBlock(
            evaluator=_Evaluator(raises=RuntimeError("cep down")))

        result = await block.execute(_context(time_delta=1.5))

        assert result.status == "skipped", (
            "status='ok' here made a CEP evaluation that raised look like one "
            "that ran and found nothing")
        assert result.data["cep_flags"] is None
