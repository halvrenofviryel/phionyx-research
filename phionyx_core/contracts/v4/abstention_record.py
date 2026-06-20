"""
AbstentionRecord — v4 Schema (D-pillar, §9 item 3)
==================================================

A typed, signable record of ONE calibrated abstention decision: when the runtime
is outside its evidence boundary and chooses to hedge / ask / defer / refuse
rather than answer. This is the artifact the Abstention & Boundary runtime
profile (Category D) promises — "calibrated abstention decision + reason,
recorded" — and it is how D's decision flows into C's signed chain.

Additive, mirroring ``claim.py``: pure stdlib + pydantic, and it does NOT touch
the frozen ``audit_record.py`` hash chain. The actual signing/chaining is done by
the companion envelope writer (RFC 8785 JCS canonical JSON → SHA-256 chain →
signature); this contract owns only the SHAPE and the canonical content.

Data-minimisation (binding): the record stores ``query_hash`` (never the raw
query), numeric calibration signals, the decision enum, and a SHORT policy-basis
reason — never free-text user disclosure.
"""

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

ABSTENTION_RECORD_SCHEMA = "phionyx.abstention_record.v1"

_REASON_MAX = 200


class AbstentionDecision(str, Enum):
    """The calibrated abstention spectrum (value study Profile B vocabulary)."""

    PROCEED = "proceed"   # within boundary — answered
    HEDGE = "hedge"       # answered with an explicit caveat
    ASK = "ask"           # ask the user for missing information
    DEFER = "defer"       # hand off to a human (HITL)
    REFUSE = "refuse"     # decline to answer


# The pipeline detector's enum is {proceed, hedge, admit_ignorance, refuse}.
# Map it onto the study's {proceed, hedge, ask, defer, refuse}. `admit_ignorance`
# ("I don't know") maps to DEFER so the human-handoff distinction the T6 artifact
# requires is preserved rather than collapsed into a bare refuse.
_RECOMMENDATION_TO_DECISION = {
    "proceed": AbstentionDecision.PROCEED,
    "hedge": AbstentionDecision.HEDGE,
    "admit_ignorance": AbstentionDecision.DEFER,
    "refuse": AbstentionDecision.REFUSE,
}


def recommendation_to_decision(recommendation: str) -> AbstentionDecision:
    """Map a KnowledgeBoundary recommendation to the abstention decision enum."""
    return _RECOMMENDATION_TO_DECISION.get(
        (recommendation or "").strip().lower(), AbstentionDecision.HEDGE
    )


class AbstentionRecord(BaseModel):
    """A signable record of one calibrated abstention decision.

    ``previous_hash`` / ``record_hash`` / ``signature`` are filled by the
    envelope writer at persist time; the contract leaves them ``None``.
    """

    schema_id: str = Field(default=ABSTENTION_RECORD_SCHEMA)

    # Data-minimised reference to the query — a hash, never the raw text.
    query_hash: str = Field(..., description="sha256[:16] of the query text")

    decision: AbstentionDecision = Field(...)
    enforced: bool = Field(
        default=False,
        description="True if the decision actually gated the turn (fail_closed on); "
        "False if recorded as advisory (default-off)",
    )

    # Calibration signals (all in [0,1]).
    ood_score: float = Field(..., ge=0.0, le=1.0)
    retrieval_coverage: float = Field(..., ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="calibrated confidence (from confidence_fusion / trust), "
        "NOT the raw boundary_score",
    )
    boundary_score: float | None = Field(default=None, ge=0.0, le=1.0)

    reason: str = Field(default="", description="short policy-basis reason (truncated)")

    # OOD provenance — for replaying the embedding-backed decision against the
    # exact frozen reference set.
    ood_source: str | None = None
    model_id: str | None = None
    corpus_version: str | None = None

    # Join keys across the gate-telemetry and envelope-chain producers.
    trace_id: str | None = None
    session_id: str | None = None
    turn_index: int | None = Field(default=None, ge=0)

    # Integrity (chain link) — populated by the envelope writer, not the contract.
    previous_hash: str | None = None
    record_hash: str | None = None
    signature: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def query_hash_of(query_text: str) -> str:
        """Data-minimised query reference (matches the gate's claim/query hashing)."""
        return hashlib.sha256((query_text or "").encode("utf-8")).hexdigest()[:16]

    def content_for_hash(self) -> dict[str, Any]:
        """Canonical content the chain hashes — excludes the integrity fields and
        the wall-clock ``created_at`` so the record is replay-stable
        (decision-keyed determinism). Feed this to the JCS canonicaliser."""
        return {
            "schema_id": self.schema_id,
            "query_hash": self.query_hash,
            "decision": self.decision.value,
            "enforced": self.enforced,
            "ood_score": self.ood_score,
            "retrieval_coverage": self.retrieval_coverage,
            "novelty_score": self.novelty_score,
            "confidence": self.confidence,
            "boundary_score": self.boundary_score,
            "reason": self.reason,
            "ood_source": self.ood_source,
            "model_id": self.model_id,
            "corpus_version": self.corpus_version,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
        }

    @classmethod
    def from_boundary(
        cls,
        *,
        query_text: str,
        recommendation: str,
        ood_score: float,
        retrieval_coverage: float,
        confidence: float,
        novelty_score: float = 0.0,
        boundary_score: float | None = None,
        reason: str = "",
        enforced: bool = False,
        ood_source: str | None = None,
        model_id: str | None = None,
        corpus_version: str | None = None,
        trace_id: str | None = None,
        session_id: str | None = None,
        turn_index: int | None = None,
    ) -> "AbstentionRecord":
        """Build an AbstentionRecord from a knowledge-boundary decision.

        ``reason`` is truncated to keep the record data-minimised (no free-text
        user disclosure leaks into a signable artifact)."""
        return cls(
            query_hash=cls.query_hash_of(query_text),
            decision=recommendation_to_decision(recommendation),
            enforced=enforced,
            ood_score=max(0.0, min(1.0, ood_score)),
            retrieval_coverage=max(0.0, min(1.0, retrieval_coverage)),
            novelty_score=max(0.0, min(1.0, novelty_score)),
            confidence=max(0.0, min(1.0, confidence)),
            boundary_score=boundary_score,
            reason=(reason or "")[:_REASON_MAX],
            ood_source=ood_source,
            model_id=model_id,
            corpus_version=corpus_version,
            trace_id=trace_id,
            session_id=session_id,
            turn_index=turn_index,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "schema_id": ABSTENTION_RECORD_SCHEMA,
                "query_hash": "a1b2c3d4e5f6a7b8",
                "decision": "defer",
                "enforced": True,
                "ood_score": 0.82,
                "retrieval_coverage": 0.18,
                "confidence": 0.31,
                "reason": "outside evidence boundary: low retrieval coverage",
            }
        }
