"""Tests for the three runtime deployment profiles (portfolio redesign, 2026-06-07).

Proves the profiles reference REAL canonical blocks, keep the safety/record floor,
and compose correctly — and that the embedded canonical list does not drift from
the contract.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from phionyx_core.profiles.runtime_profiles import (
    CANONICAL_BLOCKS_V3_8_0,
    RUNTIME_PROFILES,
    APPLICATION_PROFILE_MAP,
    compose,
    get_runtime_profile,
    profiles_for_application,
)

REPO = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())


def test_embedded_canonical_matches_contract():
    """The embedded 46-block list must equal the contract (no silent drift)."""
    d = json.loads((REPO / "phionyx_core/contracts/telemetry/canonical_blocks_v3_8_0.json").read_text())
    blocks = None
    for k in ("blocks", "canonical_blocks", "order", "block_order"):
        if k in d:
            raw = d[k]
            blocks = [b if isinstance(b, str) else (b.get("name") or b.get("block_id") or b.get("id")) for b in raw]
            break
    if blocks is None:
        for v in d.values():
            if isinstance(v, list) and len(v) > 20:
                blocks = [b if isinstance(b, str) else (b.get("name") or b.get("block_id") or b.get("id")) for b in v]
                break
    assert blocks is not None, "could not locate block list in contract"
    assert len(CANONICAL_BLOCKS_V3_8_0) == 46
    assert set(CANONICAL_BLOCKS_V3_8_0) == set(blocks), "embedded canonical list drifted from contract"


@pytest.mark.parametrize("name", list(RUNTIME_PROFILES))
def test_profile_validates(name):
    """Every profile references only real blocks and keeps the safety/record floor."""
    p = RUNTIME_PROFILES[name]
    p.validate()  # raises on unknown block or missing floor
    assert set(p.active_blocks) <= set(CANONICAL_BLOCKS_V3_8_0)
    # active + bypassed partition the canonical 46
    assert set(p.active_blocks) | set(p.bypassed_blocks) == set(CANONICAL_BLOCKS_V3_8_0)
    assert not (set(p.active_blocks) & set(p.bypassed_blocks))


def test_governance_profiles_keep_safety_and_record_floor():
    """Evidence/Abstention/SafetyGate must never bypass kill_switch/input_safety/audit."""
    for name in ("evidence", "abstention_boundary", "safety_gate"):
        active = set(get_runtime_profile(name).active_blocks)
        assert {"kill_switch_gate", "input_safety_gate", "audit_layer"} <= active


def test_evidence_runtime_is_notary_not_mindloop():
    """Evidence Runtime bypasses the mind-loop/heavy-physics (value-study thesis)."""
    ev = get_runtime_profile("evidence")
    bypassed = set(ev.bypassed_blocks)
    for mindloop in ("causal_graph_update", "counterfactual_analysis", "goal_decomposition",
                     "world_state_snapshot", "memory_consolidation", "ukf_predict"):
        assert mindloop in bypassed
    # but the notary core is active
    assert {"audit_layer", "outcome_feedback", "learning_gate"} <= set(ev.active_blocks)


def test_safety_gate_is_fail_closed_and_inline():
    p = get_runtime_profile("safety_gate")
    assert p.fail_closed is True
    assert p.execution_mode == "inline"
    assert {"deliberative_ethics_gate", "action_intent_gate"} <= set(p.active_blocks)


def test_abstention_boundary_is_fail_closed_and_inline():
    # D-pillar: the abstention profile declares the abstain/proceed decision must
    # gate the response inline (the contract the enforcement leans on).
    p = get_runtime_profile("abstention_boundary")
    assert p.fail_closed is True
    assert p.execution_mode == "inline"
    assert "knowledge_boundary_check" in set(p.active_blocks)


def test_full_cognition_is_all_46():
    assert set(get_runtime_profile("full_cognition").active_blocks) == set(CANONICAL_BLOCKS_V3_8_0)


def test_compose_unions_active_blocks():
    composed = compose("safety_gate", "evidence")
    assert set(get_runtime_profile("evidence").active_blocks) <= composed
    assert set(get_runtime_profile("safety_gate").active_blocks) <= composed
    assert "deliberative_ethics_gate" in composed  # from safety_gate
    assert "learning_gate" in composed             # from evidence


def test_every_application_maps_to_valid_profiles():
    for app_key in APPLICATION_PROFILE_MAP:
        profs = profiles_for_application(app_key)
        assert len(profs) >= 1
        for p in profs:
            assert p.name in RUNTIME_PROFILES


def test_npc_studio_uses_full_cognition_products_need_affect():
    """NPC Studio is the type where the physics/affect IS the product."""
    names = [p.name for p in profiles_for_application("product_npc_studio")]
    assert "full_cognition" in names
    # coding agents, by contrast, are evidence-only (notary, not police)
    assert [p.name for p in profiles_for_application("T1_coding_agents")] == ["evidence"]


# ── reconciliation with the pre-existing profile files (founder ask 2026-06-07) ──

@pytest.mark.parametrize(
    "name", ["trace_school_rpg", "npc_studio", "scenario_generator", "edu", "game", "clinical", "sdk_default"]
)
def test_load_profile_builtins_resolve(name):
    """The module-config layer (profiles.load_profile) now works without external YAML."""
    from phionyx_core.profiles import load_profile
    p = load_profile(name)
    assert p.name == name
    # configs are valid (pydantic) and carry the persona's governance intent
    assert p.governance.audit_level in ("MINIMAL", "STANDARD", "VERBOSE")


def test_product_bindings_link_all_three_layers():
    """Each product binds runtime (layer 1) + module (layer 2) + physics (layer 3)."""
    from phionyx_core.profiles import load_profile
    from phionyx_core.profiles.runtime_profiles import PRODUCT_PROFILE_BINDINGS
    from phionyx_core.physics.profiles import ProfileLoader as PhysLoader
    phys = set(PhysLoader()._profiles.keys())
    for b in PRODUCT_PROFILE_BINDINGS.values():
        for r in b.runtime_profiles:
            assert r in RUNTIME_PROFILES                       # layer 1 valid
        assert load_profile(b.module_profile).name == b.module_profile  # layer 2 loadable
        assert b.physics_profile in phys                       # layer 3 is a real physics profile


def test_school_rpg_is_gdpr_strict():
    """The School RPG module profile is the strict one (FULL PII scrub, VERBOSE audit)."""
    from phionyx_core.profiles import load_profile
    p = load_profile("trace_school_rpg")
    assert p.governance.pii_mode == "FULL"
    assert p.governance.audit_level == "VERBOSE"


def test_execution_modes_invariant_I6():
    """Reviewer I6: gating profiles run inline; the evidence notary may run hybrid."""
    assert get_runtime_profile("safety_gate").execution_mode == "inline"
    assert get_runtime_profile("abstention_boundary").execution_mode == "inline"
    assert get_runtime_profile("evidence").execution_mode == "hybrid"
    # every profile declares a valid mode
    for p in RUNTIME_PROFILES.values():
        assert p.execution_mode in ("inline", "async", "hybrid")
