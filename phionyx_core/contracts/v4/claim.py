"""
Claim — v4 Schema §3.14 (L2→L3 §1)
===================================

A typed, auditable record of ONE governed claim across the self-governance
lifecycle. The single object that ties a ``claim_id`` from creation through
gate decision, signed record, and observed outcome — so lifecycle-COMPLETION
(not merely invocation coverage) is measurable.

Realized THROUGH the existing 46-block path, not a new pipeline: the lifecycle
stages map to ``intent_classification`` → ``context_retrieval_rag`` →
``knowledge_boundary_check`` → ``response_revision_gate`` → ``audit_layer`` →
``outcome_feedback`` (the AGI mind-loop). This contract is the explicit join key
the two producers (gate telemetry + envelope chain) previously lacked — the same
gap the §4 trace-alignment fix exposed.

``is_lifecycle_complete()`` is the L3 headline predicate that replaces
invocation-coverage: a claim is complete only when it reached a signed record
AND an observed outcome — not when the gate was merely invoked.

Pure stdlib + pydantic (Core import boundary preserved). Does NOT touch the
frozen ``audit_record.py`` hash chain.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timezone
import hashlib

from pydantic import BaseModel, Field


class LifecycleStage(str, Enum):
    """The governed-claim lifecycle — a naming of the mind-loop, in order."""
    CREATED = "claim_created"                   # Perceive
    EVIDENCE_DECLARED = "evidence_declared"     # UpdateMemory
    EVIDENCE_VERIFIED = "evidence_verified"     # UpdateSelf/WorldModel
    GATE_DECISION = "gate_decision"             # Plan/Act
    SIGNED_RECORD = "signed_record_persisted"   # Act (durable trace)
    OUTCOME_OBSERVED = "outcome_observed"       # Reflect+Revise


class ClaimType(str, Enum):
    """What kind of assertion the claim makes."""
    FIXED = "fixed"
    TESTED = "tested"
    REVIEWED = "reviewed"
    SAFE_TO_COMMIT = "safe_to_commit"
    PUBLISHED = "published"
    DEPLOYED = "deployed"
    OTHER = "other"


class Claim(BaseModel):
    """A governed claim tracked across its lifecycle.

    The completion predicate is deliberately strict: a claim that was gated but
    whose outcome never closed is *incomplete*, not *covered*. That is the L3
    move — from "did we govern the act?" to "did the governance close the loop?".
    """
    claim_id: str = Field(..., description="Stable id — sha256[:16] of the claim text")
    claim_type: ClaimType = Field(default=ClaimType.OTHER)
    assertion: Optional[str] = Field(None, description="What is being claimed")

    # Join keys across the two producers (gate telemetry + envelope chain) — the
    # gap the §4 trace-alignment fix exposed; this contract carries BOTH.
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    turn_index: Optional[int] = Field(None, ge=0)

    # Lifecycle progress
    stages_reached: List[LifecycleStage] = Field(default_factory=list)

    # Per-stage evidence (optional; filled as the claim progresses)
    declared_scope: Dict[str, Any] = Field(default_factory=dict)
    observed_scope: Dict[str, Any] = Field(default_factory=dict)
    faithfulness: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="declaration_coverage — declaration-HONESTY, NOT correctness")
    gate_directive: Optional[str] = None
    signed_envelope_ref: Optional[str] = None
    outcome_label: Optional[str] = Field(None, description="tp | fp | tn | fn | unknown")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def compute_id(claim_text: str) -> str:
        """Stable claim_id from the claim text (matches the gate's claim_hash)."""
        return hashlib.sha256((claim_text or "").encode("utf-8")).hexdigest()[:16]

    def mark(self, stage: LifecycleStage) -> "Claim":
        """Record that the claim reached `stage` (idempotent). Returns self."""
        if stage not in self.stages_reached:
            self.stages_reached.append(stage)
        return self

    def reached(self, stage: LifecycleStage) -> bool:
        return stage in self.stages_reached

    def is_lifecycle_complete(self) -> bool:
        """L3 headline predicate: a signed record AND an observed outcome.

        This is what replaces invocation-coverage — a gate call alone is not a
        completed lifecycle.
        """
        return (LifecycleStage.SIGNED_RECORD in self.stages_reached
                and LifecycleStage.OUTCOME_OBSERVED in self.stages_reached)

    class Config:
        json_schema_extra = {
            "example": {
                "claim_id": "a1b2c3d4e5f6a7b8",
                "claim_type": "fixed",
                "assertion": "the label-feed cross-session bug is fixed",
                "stages_reached": [
                    "claim_created", "evidence_verified", "gate_decision",
                    "signed_record_persisted", "outcome_observed",
                ],
                "gate_directive": "pass",
                "outcome_label": "tp",
            }
        }


def lifecycle_completion(claims: List[Claim]) -> Dict[str, Any]:
    """L3 headline metric — the fraction of governed claims that CLOSED the loop.

    Returns the completion ratio plus the honest funnel (how many reached each
    stage), so a low number reads as 'the loop is young / outcomes still
    accumulating', never as failure. Crucially this is NOT invocation coverage:
    a claim that only reached `gate_decision` is counted as governed-but-open.

    Honest caveat (binding): early in the loop's life, completion is LOW because
    `outcome_observed` accumulates from real outcomes over time (the §4 calibration
    feed) and `signed_record_persisted` began only once envelope persistence shipped
    (§5/P6). Report completion WITH the funnel, never the ratio alone.
    """
    n = len(claims)
    funnel = {stage.value: sum(1 for c in claims if c.reached(stage)) for stage in LifecycleStage}
    complete = sum(1 for c in claims if c.is_lifecycle_complete())
    return {
        "n_governed_claims": n,
        "n_lifecycle_complete": complete,
        "lifecycle_completion": round(complete / n, 3) if n else None,
        "funnel": funnel,
        "caveat": ("lifecycle-completion (signed record AND observed outcome), NOT invocation "
                   "coverage; low early-life completion = outcomes still accumulating, not failure"),
    }
