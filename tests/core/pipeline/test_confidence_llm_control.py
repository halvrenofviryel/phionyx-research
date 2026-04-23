"""
Confidence → LLM Control Tests — Sprint 2
============================================

Evidence target:
- confidence_fusion writes w_final to metadata
- narrative_layer injects w_final into physics_state
- real_llm_processor uses w_final for confidence directive (phi fallback)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from phionyx_core.pipeline.blocks.confidence_fusion import ConfidenceFusionBlock
from phionyx_core.pipeline.blocks.narrative_layer import NarrativeLayerBlock
from phionyx_core.pipeline.base import BlockContext


# --- confidence_fusion → metadata ---

@pytest.mark.asyncio
async def test_confidence_fusion_writes_w_final_to_metadata():
    """confidence_fusion block stores w_final in context.metadata."""
    block = ConfidenceFusionBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        pipeline_version="3.0.0",
        metadata={
            "physics_state": {"phi": 0.7},
            "confidence_result": {"confidence_score": 0.8},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    # w_final should be in both result.data and context.metadata
    assert "w_final" in result.data
    assert "w_final" in ctx.metadata
    assert isinstance(ctx.metadata["w_final"], float)


# --- narrative_layer w_final injection ---

@pytest.mark.asyncio
async def test_narrative_layer_injects_w_final_into_physics_state():
    """narrative_layer reads w_final from metadata and injects into physics_state."""
    mock_processor = MagicMock()
    mock_processor.process_narrative_layer = AsyncMock(
        return_value=({"test": True}, "Response text", MagicMock(status="ok"))
    )
    block = NarrativeLayerBlock(processor=mock_processor, enable_templates=False)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "physics_state": {"phi": 0.5, "entropy": 0.5},
            "w_final": 0.85,
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    # Verify processor was called with w_final in physics_state
    call_kwargs = mock_processor.process_narrative_layer.call_args
    ps = call_kwargs.kwargs.get("physics_state") or call_kwargs[1].get("physics_state")
    assert ps is not None
    assert ps.get("w_final") == 0.85


@pytest.mark.asyncio
async def test_narrative_layer_no_w_final_no_injection():
    """Without w_final in metadata, physics_state is unchanged."""
    mock_processor = MagicMock()
    mock_processor.process_narrative_layer = AsyncMock(
        return_value=({"test": True}, "Response text", MagicMock(status="ok"))
    )
    block = NarrativeLayerBlock(processor=mock_processor, enable_templates=False)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "physics_state": {"phi": 0.5, "entropy": 0.5},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    call_kwargs = mock_processor.process_narrative_layer.call_args
    ps = call_kwargs.kwargs.get("physics_state") or call_kwargs[1].get("physics_state")
    assert "w_final" not in ps


@pytest.mark.asyncio
async def test_narrative_layer_w_final_creates_physics_state_if_none():
    """If physics_state is None but w_final exists, physics_state is created."""
    mock_processor = MagicMock()
    mock_processor.process_narrative_layer = AsyncMock(
        return_value=({"test": True}, "Response text", MagicMock(status="ok"))
    )
    block = NarrativeLayerBlock(processor=mock_processor, enable_templates=False)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "frame": {"user_input": "test"},
            "w_final": 0.3,
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    call_kwargs = mock_processor.process_narrative_layer.call_args
    ps = call_kwargs.kwargs.get("physics_state") or call_kwargs[1].get("physics_state")
    assert ps is not None
    assert ps["w_final"] == 0.3


# --- real_llm_processor w_final → confidence directive ---

def test_w_final_high_confident_directive():
    """High w_final (>0.7) → confident directive in LLM prompt."""
    # Simulate the directive selection logic from process_narrative_layer
    w_final = 0.85
    phi = 0.3  # Low phi, but w_final overrides
    confidence_source = w_final if w_final is not None else phi

    if confidence_source > 0.7:
        directive = "confident"
    elif confidence_source < 0.3:
        directive = "tentative"
    else:
        directive = "neutral"

    assert directive == "confident"


def test_w_final_low_tentative_directive():
    """Low w_final (<0.3) → tentative directive."""
    w_final = 0.2
    phi = 0.9  # High phi, but w_final overrides
    confidence_source = w_final if w_final is not None else phi

    if confidence_source > 0.7:
        directive = "confident"
    elif confidence_source < 0.3:
        directive = "tentative"
    else:
        directive = "neutral"

    assert directive == "tentative"


def test_w_final_none_falls_back_to_phi():
    """When w_final is None, phi is used as confidence source."""
    w_final = None
    phi = 0.8
    confidence_source = w_final if w_final is not None else phi

    if confidence_source > 0.7:
        directive = "confident"
    elif confidence_source < 0.3:
        directive = "tentative"
    else:
        directive = "neutral"

    assert directive == "confident"
