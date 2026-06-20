"""Phase 1 — runtime profile bypass wiring into the orchestrator (2026-06-07).

Proves the env-driven runtime profile resolves to the right ACTIVE block set,
never bypasses the safety/record floor or always-on blocks, fails safe on a bad
profile, and is a no-op (None) when unset — so default execution is unchanged.

The bypass itself reuses the orchestrator's EXISTING skip mechanism
(echo_orchestrator skip_reason loop); this tests the resolver that feeds it.
"""
from __future__ import annotations

import pytest

from phionyx_core.orchestrator.echo_orchestrator import EchoOrchestrator

FLOOR_AND_ALWAYS_ON = {
    "kill_switch_gate", "input_safety_gate", "audit_layer",
    "response_build", "phi_computation", "entropy_computation",
}


def test_unset_is_noop(monkeypatch):
    """No env → (None, None) → orchestrator runs ALL blocks (default unchanged)."""
    monkeypatch.delenv("PHIONYX_RUNTIME_PROFILE", raising=False)
    name, active = EchoOrchestrator._resolve_runtime_profile()
    assert name is None and active is None


def test_evidence_profile_bypasses_mindloop_keeps_floor(monkeypatch):
    monkeypatch.setenv("PHIONYX_RUNTIME_PROFILE", "evidence")
    name, active = EchoOrchestrator._resolve_runtime_profile()
    assert name == "evidence"
    # floor + always-on always present
    assert FLOOR_AND_ALWAYS_ON <= active
    # the notary core is active
    assert {"audit_layer", "outcome_feedback", "learning_gate"} <= active
    # mind-loop / heavy physics is policy-bypassed (NOT in the active set)
    for bypassed in ("causal_graph_update", "counterfactual_analysis",
                     "goal_decomposition", "memory_consolidation", "ukf_predict"):
        assert bypassed not in active


def test_compose_two_profiles(monkeypatch):
    monkeypatch.setenv("PHIONYX_RUNTIME_PROFILE", "evidence,safety_gate")
    name, active = EchoOrchestrator._resolve_runtime_profile()
    assert name == "evidence,safety_gate"
    assert "deliberative_ethics_gate" in active   # from safety_gate
    assert "learning_gate" in active              # from evidence
    assert FLOOR_AND_ALWAYS_ON <= active


def test_bad_profile_fails_safe(monkeypatch):
    """Unknown profile must run all blocks (None), never silently bypass."""
    monkeypatch.setenv("PHIONYX_RUNTIME_PROFILE", "does_not_exist")
    name, active = EchoOrchestrator._resolve_runtime_profile()
    assert name is None and active is None


def test_full_cognition_keeps_all_46(monkeypatch):
    from phionyx_core.profiles.runtime_profiles import CANONICAL_BLOCKS_V3_8_0
    monkeypatch.setenv("PHIONYX_RUNTIME_PROFILE", "full_cognition")
    _, active = EchoOrchestrator._resolve_runtime_profile()
    assert set(CANONICAL_BLOCKS_V3_8_0) <= active
