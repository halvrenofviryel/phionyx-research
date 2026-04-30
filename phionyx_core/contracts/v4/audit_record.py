"""
AuditRecord — v4 Schema §3.10
================================

Extends existing PedagogyLogger + audit_layer with Ed25519 signing,
hash chain for immutability, and structured audit trail.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditRecord(BaseModel):
    """
    v4 AuditRecord schema.

    Extends audit_layer block output with cryptographic integrity:
    - Ed25519 digital signature
    - Hash chain linking (previous_hash → current_hash)
    - Append-only guarantee
    """
    record_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique audit record identifier"
    )
    sequence_number: int = Field(
        ..., ge=0,
        description="Monotonic sequence number in audit chain"
    )

    # Hash chain
    previous_hash: str = Field(
        default="0" * 64,
        description="SHA-256 hash of previous audit record (genesis = 0*64)"
    )
    record_hash: str | None = Field(
        None,
        description="SHA-256 hash of this record's content"
    )

    # Signature (Ed25519)
    signature: str | None = Field(
        None,
        description="Ed25519 signature of record_hash (hex-encoded)"
    )
    signer_public_key: str | None = Field(
        None,
        description="Public key of signer (hex-encoded)"
    )

    # Audit content
    turn_id: int = Field(
        ..., ge=0,
        description="Turn ID this record covers"
    )
    event_type: str = Field(
        ...,
        description="Audit event type (e.g., 'turn_complete', 'ethics_trigger', 'state_snapshot')"
    )
    actor: str = Field(
        default="system",
        description="Actor that caused this event"
    )
    action: str = Field(
        default="",
        description="Action description"
    )

    # Snapshot data
    state_snapshot: dict[str, Any] | None = Field(
        None,
        description="State snapshot at audit time"
    )
    input_hash: str | None = Field(
        None,
        description="SHA-256 of input that triggered this event"
    )
    output_hash: str | None = Field(
        None,
        description="SHA-256 of output produced"
    )

    # Explainability
    decision_trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Decision trace for explainability"
    )
    block_results: dict[str, Any] | None = Field(
        None,
        description="Pipeline block results summary"
    )

    # Timestamps
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Metadata
    schema_version: str = Field(default="4.0.0")
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Patent-claim traceability (v4.1.0 additive extension — not part of
    # hash-chained content to preserve existing hash-chain continuity).
    # Populated with the tuple of SF/Claim refs touched during the turn
    # (union of claim_refs across executed PipelineBlocks). See
    # docs/publications/patents/ukipo/BLOCK_CLAIM_IMPROVEMENT_PLAN_V2.md.
    claim_refs: list[str] = Field(
        default_factory=list,
        description=(
            "UKIPO patent-claim references this turn exercised, e.g. "
            "['SF1:C4', 'SF1:C15', 'SF2:C1']. Optional; empty list when "
            "upstream blocks do not advertise claim_refs. Not included in "
            "compute_hash() so existing audit hash chains remain valid."
        ),
    )
    revision_directive: dict[str, Any] | None = Field(
        default=None,
        description=(
            "When response_revision_gate emitted a non-'pass' directive for "
            "this turn, the full directive payload is captured here for "
            "regulatory audit. Not included in compute_hash() — see "
            "claim_refs field rationale."
        ),
    )

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of record content (excluding hash and signature)."""
        content = {
            "record_id": self.record_id,
            "sequence_number": self.sequence_number,
            "previous_hash": self.previous_hash,
            "turn_id": self.turn_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "action": self.action,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "timestamp": self.timestamp.isoformat(),
        }
        content_bytes = json.dumps(content, sort_keys=True).encode("utf-8")
        return hashlib.sha256(content_bytes).hexdigest()

    def verify_chain(self, previous_record: Optional["AuditRecord"] = None) -> bool:
        """Verify hash chain integrity."""
        if previous_record is not None:
            if previous_record.record_hash != self.previous_hash:
                return False
        computed = self.compute_hash()
        if self.record_hash is not None and computed != self.record_hash:
            return False
        return True

    model_config = ConfigDict(json_schema_extra={'example': {'sequence_number': 42, 'turn_id': 5, 'event_type': 'turn_complete', 'actor': 'system'}})
