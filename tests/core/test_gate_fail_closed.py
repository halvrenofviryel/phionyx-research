"""Negative tests for the gate fail-closed credibility-floor fix.

Founder-directed (value study §9 P0, 2026-06-07): an unavailable or crashing
safety/ethics scorer must NOT silently pass content through when the deployment
profile demands fail-closed — and even in the default (fail-open) mode the event
must be recorded as an auditable ``gate_unavailable`` signal.

These prove rejection works (the testing-evidence rule for gate modules):
fail_closed=True BLOCKS/DEFERS; fail_closed=False passes but flags.
"""
from __future__ import annotations

import pytest

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.pipeline.blocks.input_safety_gate import InputSafetyGateBlock
from phionyx_core.pipeline.blocks.deliberative_ethics_gate import DeliberativeEthicsGateBlock


def _ctx(metadata=None, user_input="please do something potentially harmful"):
    return BlockContext(
        user_input=user_input, card_type="shadow", card_title="t", card_result="",
        scene_context="", current_entropy=0.5, pipeline_version="3.8.0",
        metadata=metadata or {},
    )


class _RaisingProc:
    async def process_safety(self, *a, **k):
        raise RuntimeError("safety scorer crashed")


class _RaisingEthics:
    def deliberate(self, *a, **k):
        raise RuntimeError("ethics engine crashed")


HIGH_RISK = {"harm_risk": 0.9, "manipulation_risk": 0.8,
             "boundary_violation_risk": 0.7, "attachment_risk": 0.1}


# ───────────────────────── input_safety_gate ─────────────────────────

@pytest.mark.asyncio
@pytest.mark.adversarial
async def test_input_safety_no_processor_fail_closed_blocks():
    """No safety processor + fail_closed → BLOCK (early exit), enforced + auditable."""
    r = await InputSafetyGateBlock(processor=None, fail_closed=True).execute(_ctx())
    assert r.data["early_exit"] is True
    assert r.data["is_blocked"] is True
    assert r.data["gate_unavailable"] is True
    assert r.data["enforced"] is True
    assert r.data["decision"] == "blocked"


@pytest.mark.asyncio
async def test_input_safety_no_processor_fail_open_passes_but_flags():
    """No processor + default (fail-open) → passes, but ALWAYS flagged auditable."""
    r = await InputSafetyGateBlock(processor=None, fail_closed=False).execute(_ctx())
    assert r.data["early_exit"] is False
    assert r.data["is_blocked"] is False
    assert r.data["gate_unavailable"] is True          # never silent
    assert r.data["enforced"] is False
    assert r.data["decision"] == "passed_unverified"


@pytest.mark.asyncio
@pytest.mark.adversarial
async def test_input_safety_processor_raises_fail_closed_blocks():
    """A crashing safety scorer must NOT pass content through under fail_closed."""
    ctx = _ctx(metadata={"frame": {"user_input": "x"}})
    r = await InputSafetyGateBlock(processor=_RaisingProc(), fail_closed=True).execute(ctx)
    assert r.data["early_exit"] is True
    assert r.data["is_blocked"] is True
    assert r.data["gate_unavailable"] is True
    assert "safety_check_exception" in r.data["reason"]


@pytest.mark.asyncio
async def test_input_safety_processor_raises_fail_open_flags():
    """A crashing scorer under fail-open still records the gate_unavailable event."""
    ctx = _ctx(metadata={"frame": {"user_input": "x"}})
    r = await InputSafetyGateBlock(processor=_RaisingProc(), fail_closed=False).execute(ctx)
    assert r.data["is_blocked"] is False
    assert r.data["gate_unavailable"] is True
    assert r.data["decision"] == "passed_unverified"


# ───────────────────────── deliberative_ethics_gate ─────────────────────────

@pytest.mark.asyncio
@pytest.mark.adversarial
async def test_ethics_scorer_raises_fail_closed_defers_to_human():
    """A crashing ethics scorer on an elevated-risk turn must DEFER, not proceed."""
    ctx = _ctx(metadata={"ethics_result": dict(HIGH_RISK)})
    r = await DeliberativeEthicsGateBlock(deliberative_ethics=_RaisingEthics(), fail_closed=True).execute(ctx)
    assert r.status == "ok"                              # pipeline must act on the verdict
    assert r.data["final_verdict"] == "DEFER_TO_HUMAN"
    assert r.data["defer_to_human"] is True
    assert r.data["early_exit"] is True
    assert r.data["gate_unavailable"] is True
    assert r.data["enforced"] is True


@pytest.mark.asyncio
async def test_ethics_scorer_raises_fail_open_flags_not_silent():
    """Default mode proceeds but records gate_unavailable (no longer status=error+silent)."""
    ctx = _ctx(metadata={"ethics_result": dict(HIGH_RISK)})
    r = await DeliberativeEthicsGateBlock(deliberative_ethics=_RaisingEthics(), fail_closed=False).execute(ctx)
    assert r.data["gate_unavailable"] is True
    assert r.data["early_exit"] is False
    assert r.data["final_verdict"] == "ERROR_UNVERIFIED"
    assert r.data["decision"] == "passed_unverified"


@pytest.mark.asyncio
async def test_ethics_un_injected_still_denies_high_risk():
    """Regression: the un-injected heuristic STILL denies high-risk (fail-safe, unchanged)."""
    ctx = _ctx(metadata={"ethics_result": dict(HIGH_RISK)})
    r = await DeliberativeEthicsGateBlock(deliberative_ethics=None).execute(ctx)
    assert r.data["final_verdict"] == "DENY"
    assert r.data["early_exit"] is True
