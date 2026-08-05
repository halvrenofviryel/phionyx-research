"""AARM R5 — tamper-evidence, and the limit of what a receipt attests.

R5: *every action, its accumulated context, the policy decision, and the
execution outcome must be recorded in tamper-evident receipts that support
offline verification and incident reconstruction.*

The mechanism was already there — a SHA-256 content hash, an Ed25519 signature
over it, and a previous-hash link. What was missing was a test that anything
**breaks** when a record is altered after signing. The existing suite covered a
wrong ``previous_hash``, which is a broken *link*; it did not cover a mutated
*record*, which is the case R5 actually names.

Three things established here, and the third is the one that stops the other two
from being read as more than they are:

1. mutating a signed record's content invalidates its own hash
2. the stored signature then fails against the recomputed hash — offline, with
   only the record and a public key
3. none of that attests the decision was correct. A receipt is a notary.
"""

from __future__ import annotations

import pytest

from phionyx_core.contracts.v4.audit_record import AuditRecord
from phionyx_core.contracts.v4.principal import EstablishedBy, Principal
from phionyx_core.services.crypto.ed25519_signer import Ed25519Signer


def _signed(signer: Ed25519Signer, **kw) -> AuditRecord:
    """A record in the state a verifier would receive it: hashed, then signed."""
    defaults = dict(sequence_number=1, turn_id=1, event_type="turn_complete",
                    actor="agent", action="respond")
    defaults.update(kw)
    record = AuditRecord(**defaults)
    record.record_hash = record.compute_hash()
    record.signature = signer.sign(record.record_hash)
    record.signer_public_key = signer.public_key_hex
    return record


# --- 1. content mutation breaks the record's own hash ---------------------


@pytest.mark.parametrize(
    "field, tampered_value",
    [
        ("action", "delete_everything"),
        ("actor", "someone_else"),
        ("event_type", "routine_noop"),
        ("turn_id", 999),
        ("output_hash", "f" * 64),
    ],
)
def test_mutating_a_signed_record_invalidates_its_hash(field, tampered_value):
    signer = Ed25519Signer()
    record = _signed(signer)
    stored_hash = record.record_hash

    setattr(record, field, tampered_value)

    assert record.compute_hash() != stored_hash, (
        f"mutating {field!r} did not change the content hash — the field is "
        "outside the hash domain and is therefore not tamper-evident"
    )
    assert record.verify_chain() is False


def test_principal_mutation_is_covered_too():
    """The identity added for R6 sits inside the same hash domain."""
    signer = Ed25519Signer()
    record = _signed(
        signer,
        principal=Principal(service="phionyx", established_by=EstablishedBy.ASSERTED_BY_CALLER),
    )
    stored_hash = record.record_hash

    record.principal = Principal(
        service="phionyx", established_by=EstablishedBy.PLATFORM_ATTESTED
    )
    assert record.compute_hash() != stored_hash
    assert record.verify_chain() is False


# --- 2. offline verification fails, using only the record and a key -------


def test_signature_fails_against_the_recomputed_hash_after_tampering():
    """The offline check R5 asks for: no access to the producing system.

    A verifier holding only the record and the public key recomputes the hash
    from the content and checks the signature against it. Tampered content
    produces a hash the signature was never over.
    """
    signer = Ed25519Signer()
    record = _signed(signer)

    assert signer.verify(record.record_hash, record.signature) is True

    record.action = "something_else"
    recomputed = record.compute_hash()

    assert signer.verify(recomputed, record.signature) is False, (
        "the signature verified against a hash it was not made over"
    )


def test_a_tampered_record_in_the_middle_of_a_chain_breaks_it():
    signer = Ed25519Signer()
    r1 = _signed(signer, sequence_number=0, turn_id=0, event_type="genesis")
    r2 = _signed(signer, sequence_number=1, turn_id=1, previous_hash=r1.record_hash)
    r3 = _signed(signer, sequence_number=2, turn_id=2, previous_hash=r2.record_hash)

    assert r2.verify_chain(r1) is True
    assert r3.verify_chain(r2) is True

    r2.action = "quietly_changed"

    assert r2.verify_chain(r1) is False          # r2's own content no longer hashes to its stored hash
    assert r3.previous_hash == r2.record_hash    # the stale link still *looks* intact
    assert signer.verify(r2.compute_hash(), r2.signature) is False


# --- 3. what a receipt does NOT attest ------------------------------------


def test_a_valid_receipt_says_nothing_about_whether_the_decision_was_right():
    """Recorded as a test because the distinction is the module's own stated discipline.

    ``decision_receipt`` puts it plainly: *attests made + signed, NOT correct*.
    A record of a catastrophic decision verifies exactly as well as a record of a
    good one, and a reader who takes verification for endorsement has made an
    error the format cannot prevent.
    """
    signer = Ed25519Signer()
    catastrophic = _signed(signer, action="approved_an_irreversible_mistake")

    assert catastrophic.verify_chain() is True
    assert signer.verify(catastrophic.record_hash, catastrophic.signature) is True
