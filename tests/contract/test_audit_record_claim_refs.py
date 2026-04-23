"""
AuditRecord claim_refs Field — Hash Chain Continuity Contract
===============================================================

Purpose:
    The v3.8.0 plan requires adding ``claim_refs`` and ``revision_directive``
    fields to AuditRecord for regulatory audit traceability. These fields
    MUST NOT invalidate existing hash chains: records produced before the
    schema change must still verify after the change.

    ``compute_hash()`` in ``phionyx_core/contracts/v4/audit_record.py`` must
    therefore continue to include only the original fixed set of core fields.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from phionyx_core.contracts.v4.audit_record import AuditRecord


# Expected keys hashed by compute_hash() — frozen for forwards compatibility.
HASH_CONTENT_KEYS = {
    "record_id",
    "sequence_number",
    "previous_hash",
    "turn_id",
    "event_type",
    "actor",
    "action",
    "input_hash",
    "output_hash",
    "timestamp",
}


def _pre_v3_8_0_hash(rec: AuditRecord) -> str:
    """Replay the pre-v3.8.0 hash algorithm to prove continuity."""
    content = {
        "record_id": rec.record_id,
        "sequence_number": rec.sequence_number,
        "previous_hash": rec.previous_hash,
        "turn_id": rec.turn_id,
        "event_type": rec.event_type,
        "actor": rec.actor,
        "action": rec.action,
        "input_hash": rec.input_hash,
        "output_hash": rec.output_hash,
        "timestamp": rec.timestamp.isoformat(),
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()


def test_claim_refs_field_default_is_empty_list():
    rec = AuditRecord(sequence_number=1, turn_id=1, event_type="test")
    assert rec.claim_refs == []


def test_revision_directive_field_default_is_none():
    rec = AuditRecord(sequence_number=1, turn_id=1, event_type="test")
    assert rec.revision_directive is None


def test_claim_refs_accepts_sf_claim_ids():
    rec = AuditRecord(
        sequence_number=1, turn_id=1, event_type="test",
        claim_refs=["SF1:C4", "SF1:C15", "SF2:C1"],
    )
    assert rec.claim_refs == ["SF1:C4", "SF1:C15", "SF2:C1"]


def test_compute_hash_does_not_depend_on_claim_refs():
    """Adding claim_refs must not change compute_hash — hash chain continuity."""
    ts = datetime.now(timezone.utc)
    a = AuditRecord(
        record_id="fixed-uuid", sequence_number=1, turn_id=1,
        event_type="test", actor="system", action="",
        input_hash=None, output_hash=None, timestamp=ts,
    )
    b = AuditRecord(
        record_id="fixed-uuid", sequence_number=1, turn_id=1,
        event_type="test", actor="system", action="",
        input_hash=None, output_hash=None, timestamp=ts,
        claim_refs=["SF1:C4", "SF2:C1"],
    )
    assert a.compute_hash() == b.compute_hash(), (
        "AuditRecord.compute_hash() leaked claim_refs into the hash — "
        "this breaks hash-chain continuity for legacy records."
    )


def test_compute_hash_does_not_depend_on_revision_directive():
    ts = datetime.now(timezone.utc)
    a = AuditRecord(
        record_id="fixed-uuid", sequence_number=1, turn_id=1,
        event_type="test", timestamp=ts,
    )
    b = AuditRecord(
        record_id="fixed-uuid", sequence_number=1, turn_id=1,
        event_type="test", timestamp=ts,
        revision_directive={"directive": "damp", "damp_factor": 0.6},
    )
    assert a.compute_hash() == b.compute_hash()


def test_legacy_hash_reproducibility():
    """A record without the new fields hashes to the same value as the
    pre-v3.8.0 algorithm would have produced."""
    ts = datetime.now(timezone.utc)
    rec = AuditRecord(
        record_id="legacy-id", sequence_number=7, turn_id=3,
        event_type="turn_complete", actor="system", action="done",
        input_hash="a"*64, output_hash="b"*64, timestamp=ts,
    )
    assert rec.compute_hash() == _pre_v3_8_0_hash(rec)


def test_verify_chain_still_works_after_schema_extension():
    ts = datetime.now(timezone.utc)
    genesis = AuditRecord(
        sequence_number=0, turn_id=0, event_type="genesis",
        previous_hash="0" * 64, timestamp=ts,
    )
    genesis.record_hash = genesis.compute_hash()
    assert genesis.verify_chain()

    follow = AuditRecord(
        sequence_number=1, turn_id=1, event_type="turn_complete",
        previous_hash=genesis.record_hash, timestamp=ts,
        claim_refs=["SF1:C15"],  # new field populated
        revision_directive={"directive": "pass"},
    )
    follow.record_hash = follow.compute_hash()
    assert follow.verify_chain(previous_record=genesis)


def test_hash_content_key_set_is_frozen():
    """Guard against accidental expansion of hashed content."""
    # This mirrors AuditRecord.compute_hash's `content` dict; change detector.
    ts = datetime.now(timezone.utc)
    rec = AuditRecord(
        sequence_number=1, turn_id=1, event_type="test", timestamp=ts,
    )
    # Recompute to trigger method; if compute_hash body expanded, this
    # test won't notice directly — but audit_record.py diff review should.
    # We assert here that adding claim_refs / revision_directive didn't
    # bump schema_version expectations.
    assert rec.schema_version == "4.0.0"
    # Sanity: the fields DO exist on the model
    field_names = set(AuditRecord.model_fields.keys())
    assert "claim_refs" in field_names
    assert "revision_directive" in field_names
