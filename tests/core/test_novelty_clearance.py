"""
NoveltyClearance tests (Adversarial Governance Hardening v1 / "C")
=================================================================

The clearance is the legitimate alternative to novelty-laundering: a reviewed high-novelty
change passes ONLY with an independent, signed clearance. Key ASI-resistant property tested
here: an agent cannot clear its own escalation (actor != reviewer, enforced at construction).
"""

import pytest

from phionyx_core.contracts.v4.novelty_clearance import NoveltyClearance, ClearanceDecision


def _clearance(**kw):
    base = dict(
        change_ref="sha256:abc",
        actor_id="claude",
        reviewer_id="founder",
        decision=ClearanceDecision.CLEARED,
    )
    base.update(kw)
    return NoveltyClearance(**base)


# ── formal invariant: no self-clearance (collusion counter) ──────────────────

def test_actor_cannot_clear_self():
    with pytest.raises(ValueError):
        NoveltyClearance(
            change_ref="sha256:abc",
            actor_id="claude",
            reviewer_id="claude",          # SAME identity → must be rejected
            decision=ClearanceDecision.CLEARED,
        )


def test_independent_clearance_constructs():
    c = _clearance()
    assert c.reviewer_id != c.actor_id
    assert c.decision == ClearanceDecision.CLEARED


# ── is_valid_for: the gate legitimacy condition ──────────────────────────────

def test_valid_for_matching_change_and_actor():
    c = _clearance(change_ref="sha256:X", actor_id="claude")
    assert c.is_valid_for("sha256:X", "claude") is True


def test_invalid_for_wrong_change():
    c = _clearance(change_ref="sha256:X")
    assert c.is_valid_for("sha256:OTHER", "claude") is False


def test_invalid_for_wrong_actor():
    c = _clearance(actor_id="claude")
    assert c.is_valid_for(c.change_ref, "someone_else") is False


def test_denied_is_not_valid():
    c = _clearance(decision=ClearanceDecision.DENIED)
    assert c.is_valid_for(c.change_ref, c.actor_id) is False


# ── decision-keyed, tamper-evident hash ──────────────────────────────────────

def test_hash_excludes_clock():
    a = _clearance(timestamp_utc="2026-06-13T00:00:00Z")
    b = _clearance(timestamp_utc="2026-06-13T23:59:59Z")
    assert a.compute_hash() == b.compute_hash()


def test_hash_changes_with_decision():
    a = _clearance(decision=ClearanceDecision.CLEARED)
    b = _clearance(decision=ClearanceDecision.DENIED)
    assert a.compute_hash() != b.compute_hash()
