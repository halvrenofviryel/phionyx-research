"""
Tests for Kill Switch Gate pipeline block.
"""

import pytest
from phionyx_core.pipeline.base import BlockContext, BlockResult
from phionyx_core.pipeline.blocks.kill_switch_gate import KillSwitchGateBlock
from phionyx_core.governance.kill_switch import KillSwitch, KillSwitchConfig


def _make_context(**kwargs) -> BlockContext:
    """Create a minimal BlockContext for testing."""
    defaults = dict(
        user_input="test input",
        card_type="dialogue",
        card_title="test",
        scene_context="",
        card_result="",
        metadata=kwargs.get("metadata", {}),
    )
    defaults.update(kwargs)
    return BlockContext(**defaults)


class TestKillSwitchGateBlock:
    """Pipeline block tests."""

    @pytest.mark.asyncio
    async def test_no_kill_switch_is_an_auditable_event_not_a_skip(self):
        """Rewritten 2026-08-02 (T1 gate review, founder-approved).

        This asserted `status == "skipped"`. "Skipped" means the block did not
        run; here it ran and found it had nothing to guard with — canonical
        block 1, the emergency stop, reporting as absent rather than as
        unavailable. The sibling gate, DeliberativeEthicsGateBlock, was given
        the same handling by the founder-directed credibility-floor fix.
        """
        result = await KillSwitchGateBlock(kill_switch=None).execute(
            _make_context())

        assert result.status == "ok"
        assert result.data["gate_unavailable"] is True
        assert result.data["kill_switch_triggered"] is False
        assert result.data["decision"] == "proceeded_unguarded"

    @pytest.mark.asyncio
    async def test_no_kill_switch_blocks_when_fail_closed(self):
        """The posture block_factory uses when KillSwitch cannot be imported."""
        result = await KillSwitchGateBlock(
            kill_switch=None, fail_closed=True).execute(_make_context())

        assert result.data["kill_switch_triggered"] is True
        assert result.data["early_exit"] is True
        assert result.data["decision"] == "blocked_gate_unavailable"
        assert "shutdown_message" in result.data

    @pytest.mark.asyncio
    async def test_safe_metrics_pass(self):
        ks = KillSwitch()
        block = KillSwitchGateBlock(kill_switch=ks)
        ctx = _make_context(metadata={})
        result = await block.execute(ctx)
        assert result.data["kill_switch_triggered"] is False
        assert result.data["early_exit"] is False

    @pytest.mark.asyncio
    async def test_high_ethics_risk_triggers_shutdown(self):
        ks = KillSwitch()
        block = KillSwitchGateBlock(kill_switch=ks)

        # Simulate ethics_result with high risk
        ctx = _make_context(metadata={
            "ethics_result": {"max_risk_score": 0.97},
        })
        result = await block.execute(ctx)
        assert result.data["kill_switch_triggered"] is True
        assert result.data["early_exit"] is True
        assert "shutdown_message" in result.data

    @pytest.mark.asyncio
    async def test_low_t_meta_triggers(self):
        ks = KillSwitch()
        block = KillSwitchGateBlock(kill_switch=ks)

        ctx = _make_context(metadata={
            "confidence_result": {"t_meta": 0.05},
        })
        result = await block.execute(ctx)
        assert result.data["kill_switch_triggered"] is True

    @pytest.mark.asyncio
    async def test_drift_accumulation(self):
        ks = KillSwitch()
        block = KillSwitchGateBlock(kill_switch=ks)

        # Accumulate 6 drifts (threshold is > 5)
        for i in range(6):
            ctx = _make_context(metadata={
                "drift_result": {"drift_detected": True},
            })
            result = await block.execute(ctx)

        assert result.data["kill_switch_triggered"] is True

    @pytest.mark.asyncio
    async def test_extracts_v4_confidence(self):
        ks = KillSwitch()
        block = KillSwitchGateBlock(kill_switch=ks)

        ctx = _make_context(metadata={
            "v4_confidence": {"t_meta": 0.08},
        })
        result = await block.execute(ctx)
        assert result.data["kill_switch_triggered"] is True

    @pytest.mark.asyncio
    async def test_block_id(self):
        block = KillSwitchGateBlock()
        assert block.block_id == "kill_switch_gate"
