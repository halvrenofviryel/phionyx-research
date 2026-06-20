"""Contract test for the Claim lifecycle object (v4 §3.14, L2→L3 §1).

Binds the L3 headline predicate: a claim is lifecycle-COMPLETE only when it
reached a signed record AND an observed outcome — not when the gate was merely
invoked. This is what replaces invocation-coverage.
"""
import pytest

from phionyx_core.contracts.v4 import Claim, ClaimType, LifecycleStage, lifecycle_completion


def test_claim_id_stable_and_short():
    assert Claim.compute_id("x") == Claim.compute_id("x")
    assert len(Claim.compute_id("x")) == 16


def test_lifecycle_complete_requires_signed_record_and_outcome():
    c = Claim(claim_id="a", claim_type=ClaimType.FIXED)
    c.mark(LifecycleStage.CREATED).mark(LifecycleStage.GATE_DECISION)
    assert not c.is_lifecycle_complete()          # gated but not closed → INCOMPLETE (the L3 point)
    c.mark(LifecycleStage.SIGNED_RECORD)
    assert not c.is_lifecycle_complete()          # signed but no outcome → still incomplete
    c.mark(LifecycleStage.OUTCOME_OBSERVED)
    assert c.is_lifecycle_complete()


def test_mark_is_idempotent():
    c = Claim(claim_id="a").mark(LifecycleStage.CREATED).mark(LifecycleStage.CREATED)
    assert c.stages_reached.count(LifecycleStage.CREATED) == 1


def test_lifecycle_completion_aggregator():
    done = Claim(claim_id="c").mark(LifecycleStage.SIGNED_RECORD).mark(LifecycleStage.OUTCOME_OBSERVED)
    open_claim = Claim(claim_id="o").mark(LifecycleStage.GATE_DECISION)
    rep = lifecycle_completion([done, open_claim])
    assert rep["n_governed_claims"] == 2
    assert rep["n_lifecycle_complete"] == 1
    assert rep["lifecycle_completion"] == 0.5
    assert rep["funnel"]["gate_decision"] == 1
    assert rep["funnel"]["outcome_observed"] == 1
    assert "NOT invocation coverage" in rep["caveat"]


def test_lifecycle_completion_empty():
    rep = lifecycle_completion([])
    assert rep["n_governed_claims"] == 0 and rep["lifecycle_completion"] is None


def test_faithfulness_is_bounded_0_1():
    with pytest.raises(Exception):
        Claim(claim_id="a", faithfulness=1.5)


def test_join_keys_carried():
    c = Claim(claim_id="a", trace_id="T", session_id="S", turn_index=3)
    assert c.trace_id == "T" and c.session_id == "S" and c.turn_index == 3
