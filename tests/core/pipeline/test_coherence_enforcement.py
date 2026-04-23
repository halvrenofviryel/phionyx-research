"""
Coherence Enforcement Tests
=============================

Sprint 2: Proves that coherence_qa redacted_text is actually used
by response_build when state leak is detected.

Evidence target:
- State leak → redacted text used in response
- Clean response → original preserved
- coherence_score stored in metadata
- Orchestrator applies redaction to narrative_text
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from phionyx_core.pipeline.blocks.archive.coherence_qa import CoherenceQaBlock
from phionyx_core.pipeline.blocks.response_build import ResponseBuildBlock
from phionyx_core.pipeline.base import BlockContext, BlockResult


# --- CoherenceQaBlock tests ---


@pytest.mark.asyncio
async def test_leak_detected_produces_redacted_text():
    """When narrative contains state leak, redacted_text is produced."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": "Hello! My phi is 0.85 and entropy is 0.3. How are you?"},
    )
    result = await block.execute(ctx)
    assert result.is_success()
    qa = result.data["qa_result"]
    assert qa["leak_detected"] is True
    assert qa["redacted_text"] is not None
    assert "phi is 0.85" not in qa["redacted_text"]
    assert "entropy is 0.3" not in qa["redacted_text"]


@pytest.mark.asyncio
async def test_clean_response_no_redaction():
    """Clean response without leaks → no redaction, high score."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": "Hello! I'm doing great. How can I help you today?"},
    )
    result = await block.execute(ctx)
    assert result.is_success()
    qa = result.data["qa_result"]
    assert qa["leak_detected"] is False
    assert qa["redacted_text"] is None
    assert qa["coherence_score"] == 1.0


@pytest.mark.asyncio
async def test_multiple_leaks_all_redacted():
    """Multiple state leaks → all redacted."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "narrative_text": "phi is 0.85. entropy is 0.3. valence is 0.6. arousal is 0.7. "
                             "But anyway, hello!"
        },
    )
    result = await block.execute(ctx)
    qa = result.data["qa_result"]
    assert qa["leak_detected"] is True
    assert qa["violation_count"] >= 4
    assert "phi is 0.85" not in qa["redacted_text"]
    assert "entropy is 0.3" not in qa["redacted_text"]
    assert "valence is 0.6" not in qa["redacted_text"]
    assert "arousal is 0.7" not in qa["redacted_text"]
    # Non-leak text should survive
    assert "hello" in qa["redacted_text"].lower()


@pytest.mark.asyncio
async def test_coherence_score_decreases_with_violations():
    """More violations → lower coherence score."""
    block = CoherenceQaBlock()
    # Single violation
    ctx1 = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": "My phi is 0.85."},
    )
    r1 = await block.execute(ctx1)
    score1 = r1.data["qa_result"]["coherence_score"]

    # Multiple violations
    ctx2 = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": "phi is 0.85. entropy is 0.3. valence is 0.6."},
    )
    r2 = await block.execute(ctx2)
    score2 = r2.data["qa_result"]["coherence_score"]

    assert score2 < score1, f"More violations should yield lower score: {score2} >= {score1}"


@pytest.mark.asyncio
async def test_coherence_qa_result_stored_in_metadata():
    """coherence_qa_result should be stored in context.metadata."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": "phi is 0.85. Hello!"},
    )
    await block.execute(ctx)
    assert "coherence_qa_result" in ctx.metadata
    assert ctx.metadata["coherence_qa_result"]["leak_detected"] is True


# --- ResponseBuildBlock coherence integration tests ---


class MockBuilder:
    """Mock response builder that captures narrative_response."""

    def __init__(self):
        self.last_narrative = None

    def build_response(self, narrative_response="", **kwargs):
        self.last_narrative = narrative_response
        return {
            "narrative": narrative_response,
            "physics": kwargs.get("physics_state", {}),
        }


@pytest.mark.asyncio
async def test_response_build_uses_redacted_text_on_leak():
    """When coherence_qa detected leak, response_build uses redacted text."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "narrative_text": "My phi is 0.85 and I am fine.",
            "physics_state": {"phi": 0.5, "entropy": 0.5},
            "coherence_qa_result": {
                "leak_detected": True,
                "redacted_text": "I am fine.",
                "coherence_score": 0.6,
                "violations": ["phi is 0.85"],
                "violation_count": 1,
            },
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    # Builder should receive the redacted text, not the original
    assert builder.last_narrative == "I am fine."
    assert "phi is 0.85" not in builder.last_narrative


@pytest.mark.asyncio
async def test_response_build_keeps_original_when_no_leak():
    """No leak → original narrative preserved."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "I'm here to help you with anything!"
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "narrative_text": original,
            "physics_state": {"phi": 0.5, "entropy": 0.5},
            "coherence_qa_result": {
                "leak_detected": False,
                "redacted_text": None,
                "coherence_score": 1.0,
                "violations": [],
                "violation_count": 0,
            },
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative == original


@pytest.mark.asyncio
async def test_response_build_no_coherence_result_uses_original():
    """No coherence_qa_result at all → original narrative used."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "Hello world"
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "narrative_text": original,
            "physics_state": {"phi": 0.5},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative == original


# --- Full chain: CoherenceQA → ResponseBuild ---


@pytest.mark.asyncio
async def test_full_chain_leak_to_redacted_response():
    """Full chain: leaked narrative → coherence_qa detects → response_build uses redacted."""
    leaky_text = "Sure! My phi is 0.92 and entropy is 0.15. Let me help you with that."

    # Step 1: Run coherence QA
    qa_block = CoherenceQaBlock()
    qa_ctx = BlockContext(
        user_input="help me",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": leaky_text},
    )
    qa_result = await qa_block.execute(qa_ctx)
    qa_data = qa_result.data["qa_result"]

    # Verify leak detected
    assert qa_data["leak_detected"] is True
    assert qa_data["redacted_text"] is not None

    # Step 2: Feed into response_build
    builder = MockBuilder()
    rb_block = ResponseBuildBlock(builder=builder)
    rb_ctx = BlockContext(
        user_input="help me",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "help me"},
            "narrative_text": leaky_text,
            "physics_state": {"phi": 0.5},
            "coherence_qa_result": qa_data,
        },
    )
    rb_result = await rb_block.execute(rb_ctx)

    # Verify redacted text used
    assert rb_result.is_success()
    assert "phi is 0.92" not in builder.last_narrative
    assert "entropy is 0.15" not in builder.last_narrative
    # Non-leak content preserved
    assert "help" in builder.last_narrative.lower()


@pytest.mark.asyncio
async def test_full_chain_clean_response_passes_through():
    """Full chain: clean narrative → no redaction → original preserved."""
    clean_text = "I'd be happy to help you learn about Python programming!"

    # Step 1: Run coherence QA
    qa_block = CoherenceQaBlock()
    qa_ctx = BlockContext(
        user_input="teach me python",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"narrative_text": clean_text},
    )
    qa_result = await qa_block.execute(qa_ctx)
    qa_data = qa_result.data["qa_result"]

    # Verify no leak
    assert qa_data["leak_detected"] is False

    # Step 2: Feed into response_build
    builder = MockBuilder()
    rb_block = ResponseBuildBlock(builder=builder)
    rb_ctx = BlockContext(
        user_input="teach me python",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "teach me python"},
            "narrative_text": clean_text,
            "physics_state": {"phi": 0.5},
            "coherence_qa_result": qa_data,
        },
    )
    rb_result = await rb_block.execute(rb_ctx)

    assert rb_result.is_success()
    assert builder.last_narrative == clean_text
