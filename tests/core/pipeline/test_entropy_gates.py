"""
Entropy Gate Tests — Sprint 3
================================

Evidence target:
- Pre-gate: high entropy → warning injected into context
- Pre-gate: normal entropy → pass-through
- Post-gate: high entropy + low coherence → flagged
- Post-gate: normal → pass
- Gates no longer bypass when service is None
"""

import pytest
from phionyx_core.pipeline.blocks.entropy_amplitude_pre_gate import EntropyAmplitudePreGateBlock
from phionyx_core.pipeline.blocks.entropy_amplitude_post_gate import EntropyAmplitudePostGateBlock
from phionyx_core.pipeline.base import BlockContext


# --- Pre-gate tests ---


@pytest.mark.asyncio
async def test_pre_gate_high_entropy_injects_warning():
    """High entropy (>0.8) → uncertainty warning injected into context string."""
    block = EntropyAmplitudePreGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.9,
        metadata={"enhanced_context_string": "Base context."},
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert result.data["gate_action"] == "warning_injected"
    assert "HIGH UNCERTAINTY" in result.data["enhanced_context_string"]


@pytest.mark.asyncio
async def test_pre_gate_normal_entropy_passes():
    """Normal entropy (<=0.8) → pass-through, no warning."""
    block = EntropyAmplitudePreGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"enhanced_context_string": "Base context."},
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert result.data["gate_action"] == "pass"
    assert "HIGH UNCERTAINTY" not in result.data["enhanced_context_string"]


@pytest.mark.asyncio
async def test_pre_gate_boundary_entropy_passes():
    """Entropy at exactly 0.8 → pass (threshold is >0.8)."""
    block = EntropyAmplitudePreGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.8,
        metadata={"enhanced_context_string": "Base context."},
    )
    result = await block.execute(ctx)
    assert result.data["gate_action"] == "pass"


@pytest.mark.asyncio
async def test_pre_gate_no_longer_skips_without_service():
    """Pre-gate should NOT skip when gate service is None (inline fallback)."""
    block = EntropyAmplitudePreGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={},
    )
    skip_reason = block.should_skip(ctx)
    assert skip_reason is None, "Pre-gate should never skip (has inline fallback)"


# --- Post-gate tests ---


@pytest.mark.asyncio
async def test_post_gate_high_entropy_low_coherence_flagged():
    """High entropy + low coherence → flagged."""
    block = EntropyAmplitudePostGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "physics_state": {"entropy": 0.9, "phi": 0.3},
            "coherence_qa_result": {"coherence_score": 0.5},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert result.data["gate_action"] == "flagged"
    assert ctx.metadata.get("entropy_gate_warning") is True


@pytest.mark.asyncio
async def test_post_gate_normal_passes():
    """Normal entropy → pass."""
    block = EntropyAmplitudePostGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "physics_state": {"entropy": 0.5, "phi": 0.5},
        },
    )
    result = await block.execute(ctx)
    assert result.is_success()
    assert result.data["gate_action"] == "pass"


@pytest.mark.asyncio
async def test_post_gate_high_entropy_high_coherence_passes():
    """High entropy but high coherence → pass (both conditions must be met)."""
    block = EntropyAmplitudePostGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "physics_state": {"entropy": 0.9},
            "coherence_qa_result": {"coherence_score": 0.9},
        },
    )
    result = await block.execute(ctx)
    assert result.data["gate_action"] == "pass"


@pytest.mark.asyncio
async def test_post_gate_empty_physics_state():
    """Empty physics_state → the gate does not fire, and does not claim a pass.

    This asserted ``gate_action == "pass"`` until 2026-08-02. There was nothing
    to compare against either threshold, so "pass" was a verdict the block had
    not reached — the shape the P-4 migration removes. The *behaviour* is
    unchanged and still asserted below: the turn is not flagged and the block
    reports success, so the pipeline continues.
    """
    block = EntropyAmplitudePostGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={"physics_state": {}},
    )
    result = await block.execute(ctx)
    assert result.data["gate_action"] == "not_measured"
    assert result.is_success()
    assert ctx.metadata.get("entropy_gate_warning") is None
    assert result.data["block_outcome"]["measurement_status"] == "NOT_MEASURED"


@pytest.mark.asyncio
async def test_post_gate_no_longer_skips_without_service():
    """Post-gate should NOT skip when gate service is None."""
    block = EntropyAmplitudePostGateBlock(gate=None)
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={},
    )
    skip_reason = block.should_skip(ctx)
    assert skip_reason is None, "Post-gate should never skip (has inline fallback)"
