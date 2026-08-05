"""AARM R6 — identity binding, and the honest limit of what binding buys.

R6: *every action receipt MUST be cryptographically bound to an agent identity.*

Before ``Principal`` existed, records carried an ``actor`` string inside the hash
domain. That gives integrity — the value cannot be altered after signing — but
integrity of a field is not assurance of an identity, and the evidence map scored
R6 ``partial`` for exactly that reason.

These tests establish three separate things, and the third is the one that keeps
this from being an over-claim:

1. a record WITHOUT a principal hashes exactly as it did before the field
   existed, so no existing chain moves
2. a record WITH a principal puts it inside the hash domain, so mutating the
   identity breaks verification — this is the binding
3. binding is not verification. A principal established by assertion is still a
   claim, and the model says so rather than letting a reader assume otherwise.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from phionyx_core.contracts.v4.audit_record import AuditRecord
from phionyx_core.contracts.v4.decision_receipt import DecisionReceipt
from phionyx_core.contracts.v4.principal import UNVERIFIED, EstablishedBy, Principal

BASE = dict(
    record_id="r1",
    sequence_number=1,
    previous_hash="0" * 64,
    turn_id=1,
    event_type="turn_complete",
    actor="agent",
    action="respond",
)


def _asserted(**kw) -> Principal:
    kw.setdefault("established_by", EstablishedBy.ASSERTED_BY_CALLER)
    return Principal(**kw)


# --- 1. no existing chain moves ------------------------------------------


def test_record_without_principal_hashes_exactly_as_before():
    """The pre-change hash, recomputed here from the ten fields that always existed.

    If this ever fails, every previously signed record in every chain has been
    invalidated by a schema change, which is the worst possible outcome of an
    additive field.
    """
    record = AuditRecord(**BASE)
    pre_change_content = {
        "record_id": record.record_id,
        "sequence_number": record.sequence_number,
        "previous_hash": record.previous_hash,
        "turn_id": record.turn_id,
        "event_type": record.event_type,
        "actor": record.actor,
        "action": record.action,
        "input_hash": record.input_hash,
        "output_hash": record.output_hash,
        "timestamp": record.timestamp.isoformat(),
    }
    expected = hashlib.sha256(
        json.dumps(pre_change_content, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert record.compute_hash() == expected


# --- 2. the binding itself -----------------------------------------------


def test_adding_a_principal_changes_the_hash():
    without = AuditRecord(**BASE).compute_hash()
    with_ = AuditRecord(**BASE, principal=_asserted(service="phionyx")).compute_hash()
    assert with_ != without


@pytest.mark.parametrize(
    "field, value",
    [
        ("service", "someone-else"),
        ("human", "another-operator"),
        ("session", "a-different-session"),
        ("attestation_ref", "a-forged-pointer"),
    ],
)
def test_identity_mutation_invalidates_the_hash(field, value):
    """The R6 test the evidence map recorded as absent. Mutate the identity, break the hash."""
    original = AuditRecord(**BASE, principal=_asserted(service="phionyx"))
    signed_hash = original.compute_hash()

    mutated = {"service": "phionyx", field: value}
    tampered = AuditRecord(**BASE, principal=_asserted(**mutated))
    assert tampered.compute_hash() != signed_hash, (
        f"mutating principal.{field} did not change the record hash — "
        "the identity is carried but not bound"
    )


def test_escalating_established_by_invalidates_the_hash():
    """Upgrading a claimed identity to a verified one must not be free.

    This is the attack the field exists to stop: a record whose identity was
    asserted, relabelled after the fact as platform-attested.
    """
    honest = AuditRecord(**BASE, principal=_asserted(service="phionyx")).compute_hash()
    flattering = AuditRecord(
        **BASE,
        principal=Principal(
            service="phionyx", established_by=EstablishedBy.PLATFORM_ATTESTED
        ),
    ).compute_hash()
    assert flattering != honest


# --- 3. binding is not verification --------------------------------------


def test_asserted_identity_reports_itself_as_unverified():
    assert _asserted(service="phionyx").is_verified is False
    assert EstablishedBy.ASSERTED_BY_CALLER in UNVERIFIED
    assert EstablishedBy.NOT_ESTABLISHED in UNVERIFIED


def test_established_by_is_required():
    """A principal without it is the ambiguity the model exists to remove."""
    with pytest.raises(Exception):
        Principal(service="phionyx")  # type: ignore[call-arg]


def test_decision_receipt_can_carry_a_principal():
    receipt = DecisionReceipt(directive="block", principal=_asserted(service="phionyx"))
    assert receipt.principal is not None
    assert receipt.principal.is_verified is False


def test_a_receipt_without_a_principal_says_nothing_rather_than_something_weak():
    """None is 'not answered', which is distinct from 'answered weakly'."""
    assert DecisionReceipt(directive="block").principal is None
