"""State-leak redaction is reachable again, without a 47th canonical block.

`coherence_qa` was canonical in v2.4.0, dropped in v2.5.0 with no successor
mapping and no recorded rationale, and archived in 709a0b04. Three runtime
consumers kept waiting for its output:

- `response_build` swaps in `redacted_text` when `leak_detected`;
- `echo_orchestrator` has a redaction branch keyed on `block_id ==
  "coherence_qa"`, which no contract version can reach;
- `response_revision_gate` has 3 of its 17 rules on coherence.

Nineteen test files supplied `coherence_qa_result` by hand, so
tests/unit/core/pipeline/test_coherence_enforcement.py passed on input nothing
produced — a control that read as present because its tests were green.

The capability now runs inside `ethics_post_response` (canonical 21), which is
the designated post-generation content check and sits before the gate. The
canonical count stays at 46, which matters because it is cited in published
papers, books and posts.

These tests assert the *path*, not the patterns: that a leak detected at block
21 reaches block 41's decision and block 42's redaction.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.ethics_post_response import EthicsPostResponseBlock
from phionyx_core.pipeline.blocks.response_revision_gate import (
    ResponseRevisionGateBlock,
)

LEAKING = "Sure — my phi is 0.85 right now, so I can help."
CLEAN = "Sure, I can help with that."


def _context(**metadata) -> BlockContext:
    return BlockContext(user_input="t", card_type="", card_title="",
                        scene_context="", card_result="", metadata=metadata)


class TestBlockTwentyOneProducesIt:
    @pytest.mark.asyncio
    async def test_a_leak_is_detected_and_redacted(self) -> None:
        context = _context(narrative_text=LEAKING)

        result = await EthicsPostResponseBlock().execute(context)

        qa = result.data["coherence_qa_result"]
        assert qa["leak_detected"] is True
        assert "phi is 0.85" not in qa["redacted_text"]
        assert context.metadata["coherence_qa_result"] is qa

    @pytest.mark.asyncio
    async def test_clean_text_is_not_flagged(self) -> None:
        result = await EthicsPostResponseBlock().execute(
            _context(narrative_text=CLEAN))

        assert result.data["coherence_qa_result"]["leak_detected"] is False

    @pytest.mark.asyncio
    async def test_coherence_runs_even_with_no_ethics_evaluator(self) -> None:
        """The reason it is placed before the early returns: on a turn where
        ethics cannot run, the redaction control must still work."""
        result = await EthicsPostResponseBlock().execute(
            _context(narrative_text=LEAKING))

        assert result.data["coherence_qa_result"]["leak_detected"] is True
        assert result.data["ethics_result"] is None

    @pytest.mark.asyncio
    async def test_no_narrative_is_not_a_clean_scan(self) -> None:
        result = await EthicsPostResponseBlock().execute(_context())

        assert result.data["coherence_qa_result"] is None
        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "NOT_MEASURED"
        assert "coherence" in outcome["profiles"]["reference_detail"][
            "criteria_absent"]


class TestTheRecordNamesWhichCriterionWasMeasured:
    @pytest.mark.asyncio
    async def test_a_leak_is_FAIL_and_says_so(self) -> None:
        result = await EthicsPostResponseBlock().execute(
            _context(narrative_text=LEAKING))

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "FAIL"
        assert "coherence" in outcome["reason"]
        detail = outcome["profiles"]["reference_detail"]
        assert detail["criteria_measured"] == "coherence"
        assert detail["criteria_absent"] == "ethics"

    @pytest.mark.asyncio
    async def test_items_checked_counts_only_evaluated_criteria(self) -> None:
        """One criterion had an input; a denominator of 2 would be MA-3.9's
        fabricated denominator."""
        result = await EthicsPostResponseBlock().execute(
            _context(narrative_text=CLEAN))

        assert result.data["block_outcome"]["measured"]["items_checked"] == 1

    @pytest.mark.asyncio
    async def test_both_criteria_measured_counts_two(self) -> None:
        class _Clear:
            def check_ethics_post_response(self, **_kwargs):
                return {"status": "ok"}

        result = await EthicsPostResponseBlock(processor=_Clear()).execute(
            _context(narrative_text=CLEAN, frame={"user_input": "x"}))

        outcome = result.data["block_outcome"]
        assert outcome["measurement_status"] == "PASS"
        assert outcome["measured"]["items_checked"] == 2
        assert set(outcome["profiles"]["reference_detail"][
            "criteria_measured"].split(",")) == {"ethics", "coherence"}

    @pytest.mark.asyncio
    async def test_a_clean_scan_does_not_mask_an_ethics_failure(self) -> None:
        """PASS only if every evaluated criterion passed."""
        class _Enforcing:
            def check_ethics_post_response(self, **_kwargs):
                return {"status": "blocked", "enforced": True}

        result = await EthicsPostResponseBlock(processor=_Enforcing()).execute(
            _context(narrative_text=CLEAN, frame={"user_input": "x"}))

        assert result.data["block_outcome"]["measurement_status"] == "FAIL"


class TestItReachesBlockFortyOne:
    @pytest.mark.asyncio
    async def test_a_leak_now_drives_the_revision_directive(self) -> None:
        """The three coherence rules in response_revision_gate have never been
        able to fire. Block 21 runs before block 41, which is why it hosts this.
        """
        context = _context(narrative_text=LEAKING, phi=0.9, entropy=0.1)
        post = await EthicsPostResponseBlock().execute(context)
        context.metadata.update(
            {k: v for k, v in post.data.items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        assert gate.data["directive"] == "rewrite"
        assert "coherence_leak_detected" in gate.data["reasons"]
        assert "coherence" in gate.data["block_outcome"][
            "profiles"]["reference_detail"]["criteria_measured"]

    @pytest.mark.asyncio
    async def test_a_clean_turn_leaves_the_directive_alone(self) -> None:
        context = _context(narrative_text=CLEAN, phi=0.9, entropy=0.1)
        post = await EthicsPostResponseBlock().execute(context)
        context.metadata.update(
            {k: v for k, v in post.data.items() if k != "block_outcome"})

        gate = await ResponseRevisionGateBlock().execute(context)

        assert gate.data["directive"] == "pass"


class TestItReachesBlockFortyTwo:
    @pytest.mark.asyncio
    async def test_response_build_swaps_in_the_redacted_text(self) -> None:
        """response_build:86-91 has always had this branch and has never been
        able to take it."""
        from phionyx_core.pipeline.blocks.response_build import ResponseBuildBlock

        class _EchoBuilder:
            """Returns whatever narrative it is handed, so the assertion is
            about what response_build passed in, not about the builder."""

            def build_response(self, frame, narrative_response, physics_state,
                               **_kwargs):
                return {"narrative_response": narrative_response}

        context = _context(narrative_text=LEAKING, frame={"user_input": "x"},
                           physics_state={"phi": 0.9})
        post = await EthicsPostResponseBlock().execute(context)
        context.metadata.update(
            {k: v for k, v in post.data.items() if k != "block_outcome"})

        built = await ResponseBuildBlock(builder=_EchoBuilder()).execute(context)

        blob = str(built.data)
        assert "phi is 0.85" not in blob, (
            "response_build:86-91 should have swapped in redacted_text")
        assert "Sure" in blob
