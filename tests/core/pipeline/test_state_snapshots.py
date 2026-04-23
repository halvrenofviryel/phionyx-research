"""
State Snapshot Tests — Sprint 6 (SF1 Claim 15, 17)
=====================================================

Evidence target:
- Physics update → pre-update snapshot stored
- Coherence violation → snapshot reference stored with pre_physics_snapshot
- Clean execution → no violation snapshot
"""

import pytest
from unittest.mock import MagicMock
from phionyx_core.pipeline.blocks.state_update_physics import StateUpdatePhysicsBlock
from phionyx_core.pipeline.blocks.archive.coherence_qa import CoherenceQaBlock
from phionyx_core.pipeline.base import BlockContext


# --- state_update_physics snapshot tests ---


@pytest.mark.asyncio
async def test_physics_update_stores_pre_snapshot():
    """Physics update stores pre-update snapshot in metadata."""
    block = StateUpdatePhysicsBlock(updater=None)
    us = MagicMock()
    us.phi = 0.7
    us.entropy = 0.3
    us.valence = 0.0
    us.arousal = 0.5
    us.narrative_drive = 0.5
    us.coherence = 0.8

    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "unified_state": us,
            "physics_state": {"phi": 0.5, "entropy": 0.6, "valence": -0.1},
        },
    )
    await block.execute(ctx)
    snapshot = ctx.metadata.get("_state_snapshot_pre_physics")
    assert snapshot is not None
    assert snapshot["phi"] == 0.5
    assert snapshot["entropy"] == 0.6
    assert snapshot["valence"] == -0.1


@pytest.mark.asyncio
async def test_snapshot_reflects_pre_update_not_post():
    """Snapshot contains the state BEFORE update, not after."""
    block = StateUpdatePhysicsBlock(updater=None)
    us = MagicMock()
    us.phi = 0.9
    us.entropy = 0.1
    us.valence = 0.5
    us.arousal = 0.8
    us.narrative_drive = 0.5
    us.coherence = 0.8

    original_phi = 0.4
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "unified_state": us,
            "physics_state": {"phi": original_phi, "entropy": 0.5},
        },
    )
    result = await block.execute(ctx)
    snapshot = ctx.metadata["_state_snapshot_pre_physics"]
    updated_ps = result.data["physics_state"]

    # Snapshot should have original value
    assert snapshot["phi"] == original_phi
    # Updated physics should have new value from unified_state
    assert updated_ps["phi"] == 0.9


# --- coherence_qa violation snapshot tests ---


@pytest.mark.asyncio
async def test_coherence_violation_stores_snapshot_reference():
    """Coherence violation stores snapshot reference with pre_physics_snapshot."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "narrative_text": "My phi is 0.85 and entropy is 0.3",
            "_state_snapshot_pre_physics": {"phi": 0.5, "entropy": 0.5},
        },
    )
    await block.execute(ctx)
    violation_snapshot = ctx.metadata.get("_state_snapshot_coherence_violation")
    assert violation_snapshot is not None
    assert violation_snapshot["violation_count"] > 0
    assert violation_snapshot["coherence_score"] < 1.0
    assert violation_snapshot["pre_physics_snapshot"] == {"phi": 0.5, "entropy": 0.5}


@pytest.mark.asyncio
async def test_clean_response_no_violation_snapshot():
    """Clean response → no violation snapshot stored."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "narrative_text": "Hello! How can I help you today?",
        },
    )
    await block.execute(ctx)
    assert "_state_snapshot_coherence_violation" not in ctx.metadata


@pytest.mark.asyncio
async def test_violation_snapshot_without_pre_physics():
    """Violation snapshot works even when no pre_physics_snapshot exists."""
    block = CoherenceQaBlock()
    ctx = BlockContext(
        user_input="test",
        card_type="shadow",
        card_title="test",
        card_result="",
        scene_context="",
        current_entropy=0.5,
        metadata={
            "narrative_text": "Debug: phi=0.85",
        },
    )
    await block.execute(ctx)
    violation_snapshot = ctx.metadata.get("_state_snapshot_coherence_violation")
    assert violation_snapshot is not None
    assert violation_snapshot["pre_physics_snapshot"] is None
