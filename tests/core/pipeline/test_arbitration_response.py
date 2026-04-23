"""
Arbitration → Response Tests — Sprint 5
==========================================

Evidence target:
- No conflict → normal response
- Safety override → safety note appended
- Arbitration needed but non-safety strategy → no modification
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
async def test_no_conflict_normal_response():
    """No arbitration result → narrative unchanged."""
    builder = MockBuilder()
    block = ResponseBuildBlock(builder=builder)
    original = "Clear answer."
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


@pytest.mark.asyncio
async def test_safety_override_appends_note():
    """Safety override → safety note appended."""
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
            "arbitration_result": {
                "arbitration_needed": True,
                "resolution_strategy": "safety_override",
            },
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert "additional safety considerations" in builder.last_narrative


@pytest.mark.asyncio
async def test_non_safety_strategy_no_modification():
    """Arbitration needed with non-safety strategy → no modification."""
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
            "arbitration_result": {
                "arbitration_needed": True,
                "resolution_strategy": "confidence_weighted",
            },
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative == original


@pytest.mark.asyncio
async def test_arbitration_not_needed_no_modification():
    """Arbitration not needed → no modification."""
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
            "arbitration_result": {
                "arbitration_needed": False,
            },
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert builder.last_narrative == original
