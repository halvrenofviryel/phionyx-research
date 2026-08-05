"""The three safety/ethics-class blocks must not report a check they did not run.

Canonical 17, 21 and 22, migrated together because they are one chain: the two
ethics blocks write `ethics_result`, and `action_intent_gate` turns it into an
`ethics_cleared` flag.

Each of the three shared `status="ok"` across states that are not alike — an
absent frame, an absent evaluator, a raised check — and `action_intent_gate`
closed the chain by asserting clearance from whatever came out. When the ethics
blocks failed they wrote `ethics_result: None`, the orchestrator merged it
(`type(None)` passes its filter), `None.get("enforced", False)` raised, the
broad handler caught it, and the block returned `ok`. Two silent failures in a
row ending in an affirmative safety claim.

`legacy_control_status` follows the rule the arbitration migration established:
a block that ran to completion reports `ok` whatever it measured, and `skipped`
is for not running or raising. Forcing the control channel to carry measurement
meaning is the conflation this work exists to undo.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.action_intent_gate import ActionIntentGateBlock
from phionyx_core.pipeline.blocks.ethics_post_response import EthicsPostResponseBlock
from phionyx_core.pipeline.blocks.ethics_pre_response import EthicsPreResponseBlock


def _context(**metadata) -> BlockContext:
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


def _outcome(result) -> dict:
    return result.data["block_outcome"]


class _Raising:
    def check_ethics_pre_response(self, **_kwargs):
        raise RuntimeError("ethics backend unreachable")

    def check_ethics_post_response(self, **_kwargs):
        raise RuntimeError("ethics backend unreachable")


class _Clear:
    def check_ethics_pre_response(self, **_kwargs):
        return {"status": "ok", "risk_level": 0.1}

    def check_ethics_post_response(self, **_kwargs):
        return {"status": "ok", "risk_level": 0.1}


class _Enforcing:
    def check_ethics_pre_response(self, **_kwargs):
        return {"status": "blocked", "enforced": True, "risk_score": 0.9}

    def check_ethics_post_response(self, **_kwargs):
        return {"status": "blocked", "enforced": True, "risk_score": 0.9}


@pytest.mark.parametrize("block_cls", [EthicsPreResponseBlock, EthicsPostResponseBlock])
class TestBothEthicsBlocks:
    @pytest.mark.asyncio
    async def test_a_raised_check_is_not_a_successful_one(self, block_cls) -> None:
        result = await block_cls(processor=_Raising()).execute(
            _context(frame={"user_input": "x"}))

        assert result.is_success() is False
        assert result.is_error() is False, "fail-open on the pipeline is retained"
        assert _outcome(result)["measurement_status"] == "ERROR"
        assert _outcome(result)["operating_mode"] == "degraded"
        assert result.data["ethics_result"] is None

    @pytest.mark.asyncio
    async def test_an_absent_frame_is_not_measured(self, block_cls) -> None:
        result = await block_cls(processor=_Clear()).execute(_context())

        assert result.status == "ok", (
            "the block ran and correctly found nothing to assess; that is not "
            "a skip")
        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "input_absent"

    @pytest.mark.asyncio
    async def test_an_absent_evaluator_is_not_measured(self, block_cls) -> None:
        result = await block_cls().execute(_context(frame={"user_input": "x"}))

        assert result.status == "ok"
        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "not_executed"

    @pytest.mark.asyncio
    async def test_a_clear_result_is_a_measured_pass(self, block_cls) -> None:
        result = await block_cls(processor=_Clear()).execute(
            _context(frame={"user_input": "x"}))

        assert _outcome(result)["measurement_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_enforcement_is_FAIL_not_an_error(self, block_cls) -> None:
        result = await block_cls(processor=_Enforcing()).execute(
            _context(frame={"user_input": "x"}))

        assert _outcome(result)["measurement_status"] == "FAIL"

    @pytest.mark.asyncio
    async def test_a_statusless_result_is_not_read_as_clear(self, block_cls) -> None:
        class _Statusless:
            def check_ethics_pre_response(self, **_kwargs):
                return {"risk_level": 0.2}

            def check_ethics_post_response(self, **_kwargs):
                return {"risk_level": 0.2}

        result = await block_cls(processor=_Statusless()).execute(
            _context(frame={"user_input": "x"}))

        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"


class TestActionIntentGate:
    @pytest.mark.asyncio
    async def test_ethics_that_never_ran_does_not_clear_the_intent(self) -> None:
        """The defect: `not ethics_result.get("enforced", False)` made an
        unmeasured turn a cleared one."""
        result = await ActionIntentGateBlock().execute(_context())

        assert result.data["ethics_cleared"] is False
        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "input_absent"

    @pytest.mark.asyncio
    async def test_a_none_ethics_result_no_longer_crashes_into_ok(self) -> None:
        """`metadata.get("ethics_result", {})` returned None when the key was
        present and null — which the orchestrator's filter does merge — so
        `.get` raised and the handler reported success anyway."""
        result = await ActionIntentGateBlock().execute(_context(ethics_result=None))

        assert result.status == "ok"
        assert "error" not in result.data
        assert result.data["ethics_cleared"] is False

    @pytest.mark.asyncio
    async def test_an_unmeasured_turn_requires_approval(self) -> None:
        context = _context()

        await ActionIntentGateBlock().execute(context)

        assert context.v4_action_intent.requires_approval is True

    @pytest.mark.asyncio
    async def test_a_clear_ethics_result_clears_the_intent(self) -> None:
        result = await ActionIntentGateBlock().execute(
            _context(ethics_result={"enforced": False, "status": "ok"}))

        assert result.data["ethics_cleared"] is True
        assert _outcome(result)["measurement_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_enforced_ethics_blocks_clearance(self) -> None:
        result = await ActionIntentGateBlock().execute(
            _context(ethics_result={"enforced": True}))

        assert result.data["ethics_cleared"] is False
        assert _outcome(result)["measurement_status"] == "FAIL"

    def test_the_hitl_wiring_it_would_depend_on_still_does_not_exist(self) -> None:
        """This block is oversight-class *only* because nothing reads its
        output. If that changes it becomes safety/ethics authority and the
        failure policy above has to be re-decided, so the fact is asserted
        rather than left in a comment.
        """
        import subprocess

        hits = subprocess.run(
            ["grep", "-rn", "v4_action_intent", "--include=*.py",
             "phionyx_core", "phionyx_bridge"],
            capture_output=True, text=True).stdout.splitlines()
        readers = [h for h in hits
                   if "action_intent_gate.py" not in h and "base.py" not in h]

        assert readers == [], (
            "something now reads context.v4_action_intent: "
            f"{readers}. This block's class and failure policy must be "
            "re-decided — see its module docstring.")
