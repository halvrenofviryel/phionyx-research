"""The two entropy gates must not record a check they did not perform.

Canonical blocks 12 and 27, migrated under P-4/P-5 as the quality/revision
class: explicitly non-authorising, so bounded degradation on failure is
legitimate and the pipeline keeps running. What is not legitimate is the record
these blocks used to write — `status="ok"`, `gate_action="pass"` — for a raised
exception, an absent entropy, and a delegate whose verdict never crossed the
boundary.

The post-gate carried a second shape worth its own tests: it read a missing
entropy as 0.5 and a missing coherence as 1.0. Both defaults sit on the passing
side of their thresholds, so a turn with no measurable input produced the same
record as a turn that was measured and found clean.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext, BlockResult
from phionyx_core.pipeline.blocks.entropy_amplitude_post_gate import (
    EntropyAmplitudePostGateBlock,
)
from phionyx_core.pipeline.blocks.entropy_amplitude_pre_gate import (
    EntropyAmplitudePreGateBlock,
)


def _context(entropy: float | None = None, **metadata) -> BlockContext:
    context = BlockContext(user_input="t", card_type="", card_title="",
                           scene_context="", card_result="", metadata=metadata)
    context.current_entropy = entropy
    return context


def _outcome(result: BlockResult) -> dict:
    return result.data["block_outcome"]


class _RaisingGate:
    def apply_gate(self, **_kwargs):
        raise RuntimeError("gate service unreachable")


class _SilentGate:
    """The real protocol: it returns state, and no verdict."""

    def apply_gate(self, enhanced_context_string="", **_kwargs):
        return (enhanced_context_string + "\n[gated]", {"gated": True})


class TestThePreGateOnFailure:
    @pytest.mark.asyncio
    async def test_a_raising_gate_is_not_reported_as_success(self) -> None:
        block = EntropyAmplitudePreGateBlock(gate=_RaisingGate())

        result = await block.execute(_context(0.9))

        assert result.status == "skipped"
        assert result.is_success() is False
        assert _outcome(result)["measurement_status"] == "ERROR"

    @pytest.mark.asyncio
    async def test_it_stays_fail_open(self) -> None:
        """A non-authorising quality gate must not become a hard stop.

        `error` would attempt a rollback: block 12 is outside the orchestrator's
        always-on set. The decision is to stop claiming the check ran.
        """
        result = await EntropyAmplitudePreGateBlock(gate=_RaisingGate()).execute(
            _context(0.9))

        assert result.is_error() is False
        assert result.is_skipped() is True
        profile = _outcome(result)["profiles"]["phionyx_pipeline"]
        assert profile["block_run_status"] == "failed"
        assert profile["recovery_action"] == "fallback"
        assert _outcome(result)["operating_mode"] == "degraded"

    @pytest.mark.asyncio
    async def test_the_context_string_still_flows(self) -> None:
        """Fail-open means the downstream block still gets its input."""
        result = await EntropyAmplitudePreGateBlock(gate=_RaisingGate()).execute(
            _context(0.9, enhanced_context_string="upstream context"))

        assert result.data["enhanced_context_string"] == "upstream context"


class TestThePreGateWhenItRuns:
    @pytest.mark.asyncio
    async def test_absent_entropy_is_not_measured_rather_than_pass(self) -> None:
        result = await EntropyAmplitudePreGateBlock().execute(_context(None))

        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "input_absent"
        assert result.data["gate_action"] != "pass"

    @pytest.mark.asyncio
    async def test_elevated_entropy_is_FAIL_not_an_error(self) -> None:
        """The check ran and its criterion was not met. That is a measured
        negative, and the injected warning is the block's product — not a
        recovery from a failure."""
        result = await EntropyAmplitudePreGateBlock().execute(_context(0.95))

        assert _outcome(result)["measurement_status"] == "FAIL"
        assert result.status == "ok"
        assert "[HIGH UNCERTAINTY]" in result.data["enhanced_context_string"]
        assert _outcome(result)["profiles"]["phionyx_pipeline"][
            "recovery_action"] == "none"

    @pytest.mark.asyncio
    async def test_entropy_below_the_threshold_is_a_real_pass(self) -> None:
        result = await EntropyAmplitudePreGateBlock().execute(_context(0.3))

        assert _outcome(result)["measurement_status"] == "PASS"
        assert _outcome(result)["measured"]["items_checked"] == 1

    @pytest.mark.asyncio
    async def test_a_delegate_verdict_is_not_invented(self) -> None:
        """`apply_gate` returns a context string and a state. No verdict crosses
        this boundary, so this record must not claim one."""
        result = await EntropyAmplitudePreGateBlock(gate=_SilentGate()).execute(
            _context(0.9))

        assert result.status == "ok"
        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "unknown"
        assert result.data["gate_action"] == "delegated"


class TestThePostGateOnFailure:
    @pytest.mark.asyncio
    async def test_a_raising_gate_is_not_reported_as_success(self) -> None:
        block = EntropyAmplitudePostGateBlock(gate=_RaisingGate())

        result = await block.execute(_context(physics_state={"entropy": 0.9}))

        assert result.status == "skipped"
        assert result.is_error() is False
        assert _outcome(result)["measurement_status"] == "ERROR"
        assert _outcome(result)["operating_mode"] == "degraded"

    @pytest.mark.asyncio
    async def test_the_physics_state_still_flows(self) -> None:
        state = {"entropy": 0.9}
        result = await EntropyAmplitudePostGateBlock(gate=_RaisingGate()).execute(
            _context(physics_state=state))

        assert result.data["physics_state"] == state


class TestThePostGateNoLongerFabricatesItsInputs:
    @pytest.mark.asyncio
    async def test_an_absent_physics_state_is_not_a_pass(self) -> None:
        result = await EntropyAmplitudePostGateBlock().execute(_context())

        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "input_absent"
        assert result.data["gate_action"] != "pass"

    @pytest.mark.asyncio
    async def test_a_missing_entropy_is_not_read_as_0_5(self) -> None:
        """The old default put an unmeasured turn on the passing side."""
        result = await EntropyAmplitudePostGateBlock().execute(
            _context(physics_state={"phi": 0.4}))

        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "input_absent"

    @pytest.mark.asyncio
    async def test_a_missing_coherence_is_not_read_as_1_0(self) -> None:
        """Entropy is over the threshold and the conjunction needs coherence.
        The evaluator ran and could not settle it: INCONCLUSIVE."""
        result = await EntropyAmplitudePostGateBlock().execute(
            _context(physics_state={"entropy": 0.95}))

        assert _outcome(result)["measurement_status"] == "INCONCLUSIVE"
        assert result.data["gate_action"] == "inconclusive"

    @pytest.mark.asyncio
    async def test_a_non_numeric_coherence_is_treated_as_absent(self) -> None:
        result = await EntropyAmplitudePostGateBlock().execute(
            _context(physics_state={"entropy": 0.95},
                     coherence_qa_result={"coherence_score": "high"}))

        assert _outcome(result)["measurement_status"] == "INCONCLUSIVE"


class TestThePostGateWhenItCanDecide:
    @pytest.mark.asyncio
    async def test_low_entropy_settles_the_conjunction_without_coherence(
        self,
    ) -> None:
        """`entropy > 0.8 AND coherence < 0.7` is false whatever coherence was,
        so this is a measured pass rather than a second inconclusive."""
        result = await EntropyAmplitudePostGateBlock().execute(
            _context(physics_state={"entropy": 0.2}))

        assert _outcome(result)["measurement_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_both_criteria_bad_is_FAIL_and_still_flags(self) -> None:
        context = _context(physics_state={"entropy": 0.95},
                           coherence_qa_result={"coherence_score": 0.4})

        result = await EntropyAmplitudePostGateBlock().execute(context)

        assert _outcome(result)["measurement_status"] == "FAIL"
        assert result.data["gate_action"] == "flagged"
        assert context.metadata["entropy_gate_warning"] is True, (
            "the gating behaviour is unchanged by the migration; only the "
            "record changed")

    @pytest.mark.asyncio
    async def test_high_entropy_with_good_coherence_passes(self) -> None:
        result = await EntropyAmplitudePostGateBlock().execute(
            _context(physics_state={"entropy": 0.95},
                     coherence_qa_result={"coherence_score": 0.9}))

        assert _outcome(result)["measurement_status"] == "PASS"

    @pytest.mark.asyncio
    async def test_a_delegate_verdict_is_not_invented(self) -> None:
        class _SilentPostGate:
            def apply_gate(self, physics_state):
                return {**physics_state, "gated": True}

        result = await EntropyAmplitudePostGateBlock(
            gate=_SilentPostGate()).execute(
                _context(physics_state={"entropy": 0.9}))

        assert _outcome(result)["measurement_status"] == "NOT_MEASURED"
        assert _outcome(result)["non_measurement_cause"] == "unknown"


class TestNeitherGateAuthorises:
    """P-5 puts these in the quality/revision class, which is only available to
    a gate that cannot authorise output. If either ever gains a decision
    outcome, it has moved class and its failure policy must be re-decided.
    """

    @pytest.mark.parametrize("block_module", [
        "entropy_amplitude_pre_gate", "entropy_amplitude_post_gate",
    ])
    def test_no_decision_outcome_is_emitted(self, block_module: str) -> None:
        from pathlib import Path

        source = (next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()) / "phionyx_core"
                  / "pipeline" / "blocks" / f"{block_module}.py").read_text("utf-8")
        assert "decision_outcome" not in source, (
            f"{block_module} now emits a decision outcome. It was migrated as "
            "explicitly non-authorising; a gate that authorises output belongs "
            "in the safety/ethics class, where a non-measurement escalates "
            "rather than degrades.")
