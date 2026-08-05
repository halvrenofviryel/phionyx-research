"""Canonical block 41 must not authorise a response it did not assess.

`response_revision_gate` is the only block that can replace the whole
user-visible answer: `response_build` turns a `reject` directive into a refusal.
Its exception handler emitted `directive: PASS` — an authorising verdict
manufactured by a crash — and its state extraction defaulted all nine criteria
to the non-triggering side, so a turn with no signals produced `pass` with an
empty `reasons` list.

Two things are asserted here, and the second matters as much as the first:

1. the failure and absence paths no longer claim a clean check;
2. **the directive is unchanged in every case the pipeline can actually
   produce.** This migration corrects the record, not the behaviour, and a
   migration that quietly changed which turns get rejected would be a far worse
   defect than the one it fixes.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.response_revision_gate import (
    CRITERIA, DIRECTIVE_PASS, ResponseRevisionGateBlock,
)


def _context(**metadata) -> BlockContext:
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


@pytest.fixture
def gate() -> ResponseRevisionGateBlock:
    return ResponseRevisionGateBlock()


class TestTheFailurePathAuthorisesNothing:
    @pytest.mark.asyncio
    async def test_a_crash_does_not_emit_pass(self, gate) -> None:
        """The defect: a bug in the gate produced an approval."""
        gate._decide = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))

        result = await gate.execute(_context(phi=0.9, entropy=0.1))

        assert result.data.get("directive") is None, (
            "a gate that crashed must not emit a directive at all; `pass` is "
            "an authorising verdict and OUTCOMES_ALLOWED_WHEN_UNMEASURED is "
            "{block, escalate, abstain}")
        assert result.data["block_outcome"]["measurement_status"] == "ERROR"

    @pytest.mark.asyncio
    async def test_a_crash_does_not_emit_reject_either(self, gate) -> None:
        """The opposite collapse, and the tempting one.

        `reject` would record a measured violation when what happened was a
        crash, and would refuse the user with an empty `reasons` list. FAIL and
        ERROR are separate verdicts so that this cannot be written.
        """
        gate._decide = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))

        result = await gate.execute(_context(phi=0.9, entropy=0.1))

        assert result.data.get("directive") != "reject"
        assert result.data["reasons"] == []

    @pytest.mark.asyncio
    async def test_response_build_sees_no_directive_exactly_as_before(
        self, gate
    ) -> None:
        """Behaviour neutrality of the failure path.

        The old handler returned `directive: pass` in `data` but never wrote
        `metadata["revision_directive"]`, which is the only key
        `response_build` reads. So `response_build` saw nothing then and sees
        nothing now.
        """
        context = _context(phi=0.9, entropy=0.1)
        gate._decide = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))

        await gate.execute(context)

        assert "revision_directive" not in context.metadata

    @pytest.mark.asyncio
    async def test_it_stays_fail_open(self, gate) -> None:
        gate._decide = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))

        result = await gate.execute(_context(phi=0.9))

        assert result.is_error() is False
        outcome = result.data["block_outcome"]
        assert outcome["operating_mode"] == "degraded"
        assert outcome["profiles"]["phionyx_pipeline"]["block_run_status"] == "failed"


class TestAbsentSignalsAreNotACleanCheck:
    @pytest.mark.asyncio
    async def test_a_turn_with_no_signals_records_what_it_stood_on(
        self, gate
    ) -> None:
        """`BlockContext.current_entropy` is a non-optional field defaulting to
        0.5, so this gate always has *something* to compare and the record can
        never be a blanket NOT_MEASURED. What it must not do is imply the value
        was measured this turn, so the source is named."""
        result = await gate.execute(_context())

        outcome = result.data["block_outcome"]
        detail = outcome["profiles"]["reference_detail"]
        assert detail["criteria_measured"] == "entropy"
        assert detail["entropy_source"] == "carried_state", (
            "no block computed entropy this turn; the 0.5 came from the "
            "context's own default and the record says so")
        assert result.data["directive"] == DIRECTIVE_PASS, (
            "the directive is unchanged — this migration corrects the record, "
            "not the behaviour")

    @pytest.mark.asyncio
    async def test_a_computed_entropy_is_named_as_such(self, gate) -> None:
        result = await gate.execute(_context(entropy=0.1, phi=0.9))

        detail = result.data["block_outcome"]["profiles"]["reference_detail"]
        assert detail["entropy_source"] == "metadata"

    @pytest.mark.asyncio
    async def test_the_record_names_which_criteria_were_absent(self, gate) -> None:
        """The five signals with no canonical producer become visible per turn,
        which is the evidence needed to decide whether to wire or drop them."""
        result = await gate.execute(_context(phi=0.9, entropy=0.1))

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "PASS"
        detail = outcome["profiles"]["reference_detail"]
        assert set(detail["criteria_measured"].split(",")) == {"phi", "entropy"}
        assert "coherence" in detail["criteria_absent"]
        assert "confidence" in detail["criteria_absent"]
        assert outcome["measured"]["items_checked"] == 2, (
            "two criteria had inputs; counting all eight would be the "
            "fabricated denominator MA-3.9 names")

    @pytest.mark.asyncio
    async def test_a_measured_negative_is_FAIL_with_the_directive(self, gate) -> None:
        result = await gate.execute(_context(entropy=0.99, phi=0.9))

        assert result.data["directive"] == "reject"
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "FAIL"
        assert "entropy" in outcome["reason"]


class TestTheDirectiveIsUnchanged:
    """Neutrality, case by case.

    Every default the old code used sat on the non-triggering side of its
    threshold — φ 0.5 against a 0.05 floor, coherence 1.0 against 0.50/0.30,
    confidence 1.0 against 0.35/0.50, conflict and drift 0.0 against 0.60. So a
    criterion with no input could not fire before either, and skipping it must
    produce the same directive.
    """

    @pytest.mark.parametrize("metadata,expected", [
        ({}, "pass"),
        ({"phi": 0.9, "entropy": 0.1}, "pass"),
        ({"entropy": 0.75, "phi": 0.9}, "damp"),
        ({"entropy": 0.90, "phi": 0.9}, "rewrite"),
        ({"entropy": 0.99, "phi": 0.9}, "reject"),
        ({"phi": 0.01, "entropy": 0.1}, "regenerate"),
        ({"ethics_result": {"risk_score": 0.9}, "phi": 0.9}, "reject"),
        ({"cep_flags": {"self_narrative": True}, "phi": 0.9}, "rewrite"),
    ])
    @pytest.mark.asyncio
    async def test_signals_that_do_reach_the_gate_decide_as_before(
        self, gate, metadata, expected
    ) -> None:
        result = await gate.execute(_context(**metadata))

        assert result.data["directive"] == expected

    @pytest.mark.asyncio
    async def test_an_absent_signal_cannot_change_the_directive(self, gate) -> None:
        """A criterion whose input is missing is skipped rather than defaulted;
        both routes must yield the same answer."""
        with_defaults = await gate.execute(
            _context(phi=0.9, entropy=0.1, coherence_qa_result={"coherence_score": 1.0},
                     confidence_result={"confidence": 1.0},
                     arbitration_result={"conflict_score": 0.0},
                     drift_result={"drift_score": 0.0}))
        without = await gate.execute(_context(phi=0.9, entropy=0.1))

        assert with_defaults.data["directive"] == without.data["directive"]

    def test_a_complete_snapshot_still_decides_the_old_way(self, gate) -> None:
        """`_decide` is called directly by the contract and Echoism tests with a
        hand-built snapshot; `present` defaults to every criterion so those
        callers are untouched."""
        snapshot = {"entropy": 0.99, "coherence": 1.0, "coherence_leak": False,
                    "phi": 1.0, "ethics_risk": 0.0, "ethics_enforced": False,
                    "confidence": 1.0, "conflict_score": 0.0,
                    "arbitration_strategy": None, "drift_score": 0.0,
                    "cep_flagged": False}

        assert gate._decide(snapshot).directive == "reject"
        assert gate._decide(snapshot, set(CRITERIA)).directive == "reject"
        assert gate._decide(snapshot, set()).directive == "pass", (
            "with nothing measured, no rule may fire")


class TestTheSignalReading:
    def test_the_confidence_payload_fallback_reads_a_field_that_exists(
        self, gate
    ) -> None:
        """Two defects, and the second was nearly missed.

        The branch was unreachable — `metadata.get(...) or {}` made an absent
        result an empty Mapping, which satisfied the isinstance test above it.
        And it read `W_final`, which **no object in this repository has**:
        `ConfidencePayload`'s field is `confidence_score` and
        `ArbitrationResult`'s is `w_final`. An earlier version of this test
        asserted the fallback worked by handing it a stub class with a
        `W_final` attribute — it verified the assumption, not the code. The real
        payload is used here.
        """
        from phionyx_core.contracts.v4.confidence_payload import ConfidencePayload

        context = _context(phi=0.9, entropy=0.1)
        context.v4_confidence = ConfidencePayload(confidence_score=0.2)

        state, present, _ = gate._extract_state(context)

        assert state["confidence"] == pytest.approx(0.2)
        assert "confidence" in present

    def test_w_final_is_read_because_that_is_what_the_producer_writes(
        self, gate
    ) -> None:
        """Repair 1. `confidence_fusion` writes `w_final`; this gate read
        `confidence_result`, which nothing writes, so both confidence rules
        were unreachable on every real turn."""
        state, present, _ = gate._extract_state(_context(w_final=0.2))

        assert state["confidence"] == pytest.approx(0.2)
        assert "confidence" in present

    def test_the_documented_key_still_wins_over_w_final(self, gate) -> None:
        """`confidence_result` is what the patent-claim tests supply; wiring
        `w_final` must not take that away from them."""
        state, _, _ = gate._extract_state(
            _context(confidence_result={"confidence": 0.9}, w_final=0.1))

        assert state["confidence"] == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_a_low_fused_confidence_now_reaches_the_directive(
        self, gate
    ) -> None:
        """The point of the repair: the rule fires."""
        result = await gate.execute(_context(w_final=0.2, phi=0.9, entropy=0.1))

        assert result.data["directive"] == "regenerate"
        assert "confidence" in result.data["block_outcome"][
            "profiles"]["reference_detail"]["criteria_measured"]

    @pytest.mark.asyncio
    async def test_the_flat_conflict_score_is_read(self, gate) -> None:
        """Repair 2, second half. `arbitration_resolve` writes `conflict_score`
        flat; this gate read `arbitration_result`, which nothing writes."""
        result = await gate.execute(
            _context(conflict_score=0.7, phi=0.9, entropy=0.1))

        assert result.data["directive"] == "rewrite"
        assert "conflict" in result.data["block_outcome"][
            "profiles"]["reference_detail"]["criteria_measured"]

    @pytest.mark.asyncio
    async def test_module_agreement_does_not_rewrite(self, gate) -> None:
        """The property that had to hold before this could be wired at all.

        Under the old `1 - HHI`, three agreeing modules scored 0.667 and would
        have crossed `conflict_rewrite`. Agreement now scores 0.0.
        """
        from phionyx_core.meta.arbitration_math import compute_conflict_score

        agreement = compute_conflict_score([0.9, 0.9, 0.9])
        result = await gate.execute(
            _context(conflict_score=agreement, phi=0.9, entropy=0.1))

        assert result.data["directive"] == "pass"

    @pytest.mark.asyncio
    async def test_a_safety_override_strategy_damps(self, gate) -> None:
        result = await gate.execute(
            _context(conflict_score=0.1, resolution_strategy="safety_override",
                     phi=0.9, entropy=0.1))

        assert result.data["directive"] == "damp"
        assert "arbitration_safety_override" in result.data["reasons"]

    @pytest.mark.asyncio
    async def test_an_absent_conflict_score_leaves_the_criterion_unmeasured(
        self, gate
    ) -> None:
        result = await gate.execute(_context(phi=0.9, entropy=0.1))

        detail = result.data["block_outcome"]["profiles"]["reference_detail"]
        assert "conflict" in detail["criteria_absent"]

    def test_both_ethics_key_names_are_still_read(self, gate) -> None:
        """`ethics_post_result` has no producer in the pipeline, but it is what
        the patent-claim tests supply and it is the documented name. Dropping it
        would have broken those tests and narrowed an SF1 C9 claim; choosing
        between the two names belongs to the key-naming decision, not here."""
        from_documented, present_a, _ = gate._extract_state(
            _context(ethics_post_result={"risk_score": 0.99}))
        from_pipeline, present_b, _ = gate._extract_state(
            _context(ethics_result={"risk_score": 0.99}))

        assert from_documented["ethics_risk"] == pytest.approx(0.99)
        assert from_pipeline["ethics_risk"] == pytest.approx(0.99)
        assert "ethics" in present_a and "ethics" in present_b

    def test_a_non_numeric_signal_is_absent_not_zero(self, gate) -> None:
        _, present, _ = gate._extract_state(
            _context(drift_result={"drift_score": "high"}))

        assert "drift" not in present

    def test_a_boolean_is_not_a_number(self, gate) -> None:
        """`isinstance(True, int)` is True in Python; a flag where a score
        belongs is a malformed signal, not a score of 1.0."""
        _, present, _ = gate._extract_state(
            _context(confidence_result={"confidence": True}))

        assert "confidence" not in present
