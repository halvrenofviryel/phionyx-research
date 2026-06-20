"""
DecisionReceipt — v4 Schema (F18)
=================================

The data-minimised, safe-to-surface shape of ONE governed decision read back from the signed
evidence chain — an **AI decision receipt**. It is what a forensics-lite query (F18) returns when
you resolve an F20 evidence id, filter decisions by directive, or render a trace timeline.

Honesty discipline (binding):
- **attests made + signed, NOT correct** — a receipt proves a decision was recorded and the
  envelope is cryptographically chained/signed; it does NOT attest the decision was *right* or the
  output *true*. F18 is a notary, not a truth oracle.
- **data-minimised** — NO raw user text, NO raw model/tool output. Only the directive, the
  runtime's STATED policy reason (governance text, not user content), policy-basis names, evidence
  link *kinds* (not raw refs), and hashes/flags. Raw payloads stay inside the signing envelope.
- **read-only** — a receipt is a *view*; F18 never mutates the chain.

Like its F19/F20 siblings, this module owns only the SHAPE. The query functions that read the live
RGE v0.2 envelope chain and build receipts live in the `phionyx-mcp-server` companion (core can not
import the envelope store). Additive: a NEW standalone model touching no existing v4 schema or hash
domain. Pure stdlib + pydantic — the Core import boundary is preserved.
"""

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class DecisionReceipt(BaseModel):
    """One governed decision, read back from the signed evidence chain (data-minimised).

    The ``directive`` vocabulary is the durable signed record's (RGE ``runtime_decision``:
    release / block / defer / redact) — deliberately a free string here so core stays
    vocabulary-agnostic and forward-compatible.
    """

    # citable handle (F20) + chain position
    evidence_id: Optional[str] = Field(
        None, description="F20 evidence id (phionyx:trace:<date>:sha256:<hex>) for this decision")
    trace_id: Optional[str] = None
    turn_index: Optional[int] = Field(None, ge=0)
    timestamp_utc: Optional[str] = Field(None, description="ISO-8601 UTC of the decision")

    # the decision itself (governance facts only — no raw user/output text)
    directive: Optional[str] = Field(
        None, description="the recorded decision (e.g. release|block|defer|redact)")
    decision_reason: Optional[str] = Field(
        None, description="the runtime's STATED policy reason — governance text, NOT user content")
    policy_basis: List[str] = Field(
        default_factory=list, description="gate/policy names that backed the decision")
    redacted: bool = Field(False, description="whether the output was redacted/blocked")
    evidence_link_kinds: List[str] = Field(
        default_factory=list,
        description="KINDS of evidence linked (retrieval/tool_call/memory/policy/...), NOT raw refs")

    # trust-boundary + integrity flags
    descriptor_change_detected: Optional[bool] = Field(
        None, description="MCP tool-descriptor rug-pull flag, if recorded")
    anomaly: Optional[bool] = Field(None, description="runtime anomaly flag, if recorded")
    signature_alg: Optional[str] = Field(
        None, description="envelope signature algorithm (e.g. Ed25519, demo-hmac, unsigned)")
    chain_verified: Optional[bool] = Field(
        None, description="result of verify_chain on the trace at read time (None = not checked)")

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "evidence_id": "phionyx:trace:2026-06-10:sha256:" + "a" * 64,
                "trace_id": "trace-460c36a336fd43e6",
                "turn_index": 7,
                "timestamp_utc": "2026-06-10T15:23:45Z",
                "directive": "block",
                "decision_reason": "blocked by the deliberative ethics gate",
                "policy_basis": ["input_safety_gate", "deliberative_ethics"],
                "redacted": True,
                "evidence_link_kinds": ["policy"],
                "anomaly": False,
                "signature_alg": "Ed25519",
                "chain_verified": True,
            }
        }
