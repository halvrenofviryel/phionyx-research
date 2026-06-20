"""
LearningDecisionRecord — v4 Schema (P1 / VLDR v1)
=================================================

The signed, replayable record of ONE learning-gate decision — a
**Verified Learning Decision Record (VLDR)**. Fulfils Learning Gate
Contract v1.0 §7 (audit trail: every decision produces a record) and
§6 (rollback writes an audit record).

Honesty discipline (binding, mirrors ``DecisionReceipt``):
- **attests made + chained, NOT correct** — a record proves a gate
  decision was taken and hash-chained; it does NOT attest the change
  was beneficial. The gate is a notary for self-modification, not an
  oracle of improvement.
- **data-minimised** — parameter values are stored as short ``repr``
  strings, never raw objects; evidence is summarised to a count + the
  measured ΔCQS, not raw payloads.
- **Core owns the SHAPE only.** Persistence + Ed25519 signing into the
  live RGE v0.2 envelope chain lives in the bridge/MCP adapter — Core
  cannot import the envelope store (see ``decision_receipt.py``). The
  in-core ``InMemoryLearningRecordPort`` hash-chains records
  deterministically so Core is replay-testable standalone; the RGE
  adapter later overwrites ``signature_alg`` + ``envelope_hash`` without
  changing this shape.

Determinism (Echoism: decision/parameter-keyed, not clock-keyed): the
signing body in ``canonical_signing_body`` EXCLUDES the wall-clock
timestamp and the sink-set integrity fields. Two runtimes that take the
same decision with the same ``prev_record_hash`` produce byte-identical
signing bodies — the record reproduces the *decision*, not the clock.

Mind-loop stage: Reflect+Revise (controlled self-modification record).
AGI label: governance/audit capability expansion (the record is
infrastructure). The closed, evidence-bound, reversible self-modification
loop it enables is the cognitive claim — and that claim is gated on the
replay-from-record test, not on this shape existing.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LearningDecisionRecord(BaseModel):
    """One learning-gate decision (or rollback), data-minimised + hash-chainable."""

    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # what was decided
    update_id: str = Field(..., description="LearningUpdate.update_id this record attests")
    target_parameter: str = Field(..., description="Parameter path the decision concerns")
    boundary_zone: str = Field(..., description="immutable | gated | adaptive")
    gate_decision: str = Field(..., description="approved | rejected | pending | deferred")
    gate_reason: str = Field(default="", description="Human-readable reason for the decision")

    # evidence summary (data-minimised — counts/deltas, not raw payloads)
    evidence_count: int = Field(default=0, ge=0)
    cqs_delta: Optional[float] = Field(
        default=None, description="Mean measured ΔCQS across evidence, if available"
    )

    # value provenance: truncated repr is a HUMAN PREVIEW only; the full-value hash is
    # what the canonical body binds, so a 128-char repr collision cannot swap values
    # without breaking the record hash (⑦ integrity fix).
    original_value_repr: Optional[str] = Field(default=None)
    proposed_value_repr: Optional[str] = Field(default=None)
    original_value_hash: Optional[str] = Field(default=None, description="sha256 of full repr(value)")
    proposed_value_hash: Optional[str] = Field(default=None, description="sha256 of full repr(value)")

    # rollback facts (Contract v1.0 §6)
    rollback: bool = Field(default=False, description="True if this record attests a rollback")
    restored: bool = Field(default=False, description="True if the original value was restored")
    restored_value_repr: Optional[str] = Field(default=None)

    # integrity / chain (in-core hash chain; RGE adapter upgrades alg + envelope_hash)
    timestamp_utc: Optional[str] = Field(default=None, description="ISO-8601 UTC (NOT signed)")
    prev_record_hash: Optional[str] = Field(default=None, description="Hash of the prior record")
    record_hash: Optional[str] = Field(default=None, description="sha256: of the signing body")
    signature_alg: str = Field(default="unsigned", description="unsigned | sha256-chain | Ed25519")
    envelope_hash: Optional[str] = Field(
        default=None, description="RGE envelope integrity.current, set by the bridge adapter"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    def canonical_signing_body(self) -> bytes:
        """Deterministic canonical-JSON bytes of the governance facts.

        Excludes ``record_id``, ``record_hash``, ``envelope_hash``,
        ``signature_alg``, ``timestamp_utc`` and ``metadata`` — i.e. the
        clock and the sink-set integrity fields. Includes
        ``prev_record_hash`` so the body is chain-bound and tamper-evident.
        """
        # Bind on the FULL-value hashes, not the truncated reprs (⑦): truncation is
        # display-only and must not be able to change the record hash.
        body = {
            "boundary_zone": self.boundary_zone,
            "cqs_delta": self.cqs_delta,
            "evidence_count": self.evidence_count,
            "gate_decision": self.gate_decision,
            "gate_reason": self.gate_reason,
            "original_value_hash": self.original_value_hash,
            "prev_record_hash": self.prev_record_hash,
            "proposed_value_hash": self.proposed_value_hash,
            "restored": self.restored,
            "rollback": self.rollback,
            "target_parameter": self.target_parameter,
            "update_id": self.update_id,
        }
        return json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")

    def compute_hash(self) -> str:
        """Return ``sha256:<hex>`` over the canonical signing body."""
        return "sha256:" + hashlib.sha256(self.canonical_signing_body()).hexdigest()

    class Config:
        json_schema_extra = {
            "example": {
                "update_id": "b1e2-...",
                "target_parameter": "physics.gamma",
                "boundary_zone": "adaptive",
                "gate_decision": "approved",
                "gate_reason": "Adaptive zone — evidence criteria met, within bounds",
                "evidence_count": 3,
                "cqs_delta": 0.012,
                "original_value_repr": "0.15",
                "proposed_value_repr": "0.18",
                "signature_alg": "sha256-chain",
                "record_hash": "sha256:" + "a" * 64,
            }
        }
