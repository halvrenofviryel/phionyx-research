"""
Trust → Response Integration Tests — Sprint 4
================================================

Evidence target:
- Trusted context → normal response
- Untrusted context → disclaimer prepended
- No trust result → no change (default trusted)
"""

import pytest
from phionyx_core.pipeline.blocks.response_build import ResponseBuildBlock
from phionyx_core.pipeline.base import BlockContext


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
async def test_trusted_context_normal_response():
    """Trusted context → narrative unchanged."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "Here is your answer."
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
            "trust_result": {"is_trusted": True, "direct_trust": 0.9},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative == original


@pytest.mark.asyncio
async def test_untrusted_context_disclaimer_prepended():
    """Untrusted context → disclaimer prepended to narrative."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "Here is your answer."
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
            "trust_result": {"is_trusted": False, "direct_trust": 0.2},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative.startswith("[Note: Response generated in reduced-trust context]")
    assert original in builder.last_narrative


@pytest.mark.asyncio
async def test_no_trust_result_no_change():
    """No trust_result in metadata → narrative unchanged (default trusted)."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "Normal response."
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
