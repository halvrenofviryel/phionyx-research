"""
NoveltyClearance — v4 Schema (Adversarial Governance Hardening v1 / "C")
=======================================================================

A signed record that an independent reviewer has examined a **high-novelty change** that the
escalate-on-novelty tripwire (phi collapse) flagged, and cleared (or denied) it. This is the
mechanism that lets a *reviewed* high-novelty change pass the gate **legitimately** — instead of
shrinking/fragmenting the change to dilute the novelty veto (novelty-laundering, the Goodhart move
documented in the AGI_TO_ASI analysis §III.3).

Two ASI-resistant properties are **formal invariants** (enforced at construction, not by policy):
  1. **Actor/Reviewer separation (collusion counter, §III.3):** ``reviewer_id != actor_id``. An
     agent cannot clear its own escalation — by construction, not by goodwill.
  2. **Decision-keyed integrity:** the hash binds the change_ref + actor + reviewer + decision and
     EXCLUDES the wall-clock, so a clearance is replay-reproducible and tamper-evident (Echoism).

Honesty discipline (mirrors VLDR/GER): attests reviewed + signed, NOT correct. A clearance proves
an independent party took responsibility for the review; it does not prove the change is good.

Core owns the SHAPE + the invariants + ``is_valid_for``. Persistence into the signed RGE chain +
the gate read-side live in the bridge/MCP companion (Core cannot import the envelope store).
"""

from __future__ import annotations

import hashlib
import json
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class ClearanceDecision(str, Enum):
    CLEARED = "cleared"   # the reviewed high-novelty change may pass
    DENIED = "denied"     # the change is refused; must be revised


class NoveltyClearance(BaseModel):
    """An independent reviewer's signed clearance/denial of a flagged high-novelty change."""

    clearance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    change_ref: str = Field(..., min_length=1, description="Stable ref of the change (claim/diff hash)")
    actor_id: str = Field(..., min_length=1, description="Identity that PRODUCED the change")
    reviewer_id: str = Field(..., min_length=1, description="Identity that REVIEWED it (must differ)")
    decision: ClearanceDecision = Field(...)
    novelty_score: Optional[float] = Field(
        default=None, description="The phi/novelty signal that triggered escalation"
    )
    review_note: str = Field(default="", description="Reviewer's stated basis (governance text)")

    # integrity / chain (same discipline as VLDR/GER; clock excluded from the signed body)
    timestamp_utc: Optional[str] = Field(default=None)
    prev_record_hash: Optional[str] = Field(default=None)
    record_hash: Optional[str] = Field(default=None)
    signature_alg: str = Field(default="unsigned")
    envelope_hash: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _enforce_actor_reviewer_separation(self) -> "NoveltyClearance":
        if self.actor_id == self.reviewer_id:
            raise ValueError(
                "actor_id must differ from reviewer_id — an agent cannot clear its own "
                "escalation (collusion counter, AGI_TO_ASI §III.3)"
            )
        return self

    def canonical_signing_body(self) -> bytes:
        """Decision-keyed canonical-JSON bytes (excludes clearance_id, hashes, clock)."""
        body = {
            "actor_id": self.actor_id,
            "change_ref": self.change_ref,
            "decision": self.decision.value,
            "novelty_score": self.novelty_score,
            "prev_record_hash": self.prev_record_hash,
            "review_note": self.review_note,
            "reviewer_id": self.reviewer_id,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    def compute_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_signing_body()).hexdigest()

    def is_valid_for(self, change_ref: str, actor_id: str) -> bool:
        """True iff this is a CLEARED, independent clearance for exactly this change.

        The gate read-side calls this: a high-novelty change is allowed only when a clearance
        exists that (a) is CLEARED, (b) matches the change_ref, (c) was issued for this actor,
        and (d) by a different reviewer. (a)–(d) together are the legitimacy condition; (d) is
        already guaranteed by the constructor invariant but re-checked here defensively.
        """
        return (
            self.decision == ClearanceDecision.CLEARED
            and self.change_ref == change_ref
            and self.actor_id == actor_id
            and self.reviewer_id != self.actor_id
        )


__all__ = ["NoveltyClearance", "ClearanceDecision"]
