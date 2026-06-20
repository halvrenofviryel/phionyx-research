"""
AgentSlaMetrics — v4 Schema (F19)
=================================

A typed, pure SCHEMA for the six reviewer-required **AI Agent SLA metrics**. This is a
SCHEMA, **NOT a legal SLA contract** — it owns the *shape* of the measurements; legal SLA
contracts (binding guarantees, penalties, breach conditions) are explicitly deferred to v2.0.

The six metrics describe the **runtime evidence / governance layer's** operational behaviour —
**not model quality** (accuracy, latency, cost). They are governance-audit measurements
("evidence-grade audit substrate — mappings, not guarantees"), never compliance certifications.

Honesty discipline (binding — these belong in any reader-facing surface):
- **measurement, not guarantee** — a value is what the runtime *observed itself doing*, never a
  promise about future behaviour.
- **null != zero** — every metric is `Optional`. `None` means "not measurable for this period"
  (no data / source disabled); `0.0` is a *valid* rate. Never coerce missing data to `0.0`.
- **sample size matters** — rates are uninterpretable without `n_*`; always report them together.
- **per-metric limits** — each field's docstring states what it does NOT tell you.

Computation lives OUTSIDE core (`tools/claude_code_mcp/sla_metrics_aggregator.py`), reading
existing telemetry. Core owns only the schema (the F20 hybrid: pure contract in core, mechanism
in the dev-harness). Additive: a NEW standalone model; touches no existing v4 schema or hash
domain. Pure stdlib + pydantic — the Core import boundary is preserved.
"""

from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class MetricSource(str, Enum):
    """Which runtime subsystem a metric is observed from (provenance, not authority)."""
    GOVERNANCE_LOOP = "governance_loop"   # claim lifecycle (signed-record + observed-outcome)
    GATE_TELEMETRY = "gate_telemetry"     # response-gate directives + declaration coverage
    EVIDENCE_CHAIN = "evidence_chain"     # signed RGE envelope chain (verify + reconstruct)


#: Canonical source of each metric — the ONE subsystem its value is computed from (anti
#: double-source discipline: a rate has a single authoritative population, not two).
METRIC_SOURCES: Dict[str, MetricSource] = {
    "verified_completion_rate": MetricSource.GOVERNANCE_LOOP,
    "rejection_rate": MetricSource.GATE_TELEMETRY,
    "policy_gate_failure_rate": MetricSource.GATE_TELEMETRY,
    "replay_success_rate": MetricSource.EVIDENCE_CHAIN,
    "evidence_completeness_score": MetricSource.GATE_TELEMETRY,
    "mean_time_to_evidence_reconstruction_ms": MetricSource.EVIDENCE_CHAIN,
}


class AgentSlaMetrics(BaseModel):
    """The six reviewer-required AI Agent SLA metrics — a measurement schema, NOT a contract.

    Each rate is in ``[0, 1]``; MTTR is milliseconds ``>= 0``. Every metric is ``Optional``:
    ``None`` = "not measurable this period" (do not read as ``0.0``). Always interpret rates
    alongside the ``n_*`` sample sizes and the ``incomplete`` map.
    """

    # --- the six metrics (None when not measurable; 0.0 is a valid value, null is not) ---
    verified_completion_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description=("[governance_loop] governed claims that reached BOTH a signed record AND an "
                     "observed outcome / all governed claims. Limit: early-life values are LOW "
                     "because outcomes accumulate over time — not failure; NOT task accuracy."),
    )
    rejection_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description=("[gate_telemetry] gate decisions that rejected/asked-to-regenerate / all gate "
                     "decisions. Limit: a high value can mean a strict gate OR a noisy producer — "
                     "read with the false-discovery calibration, not alone."),
    )
    policy_gate_failure_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description=("[gate_telemetry] gate decisions that BLOCKED under policy / all gate "
                     "decisions (disjoint from rejection_rate: block vs reject/regenerate). Limit: "
                     "counts policy denials, NOT whether the denial was correct."),
    )
    replay_success_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description=("[evidence_chain] traces whose signed envelope chain verifies (hash chain + "
                     "schema + optional signature) on deterministic replay / all traces. Limit: "
                     "proves what was logged is UNFORGED, not that logging was COMPLETE."),
    )
    evidence_completeness_score: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description=("[gate_telemetry] mean declaration coverage (declared affected paths ∩ actual "
                     "git diff / git diff) across claims. Limit: declaration HONESTY, NOT ground-"
                     "truth correctness of the work."),
    )
    mean_time_to_evidence_reconstruction_ms: Optional[float] = Field(
        None, ge=0.0,
        description=("[evidence_chain] mean wall-clock ms to reconstruct + verify a trace's evidence "
                     "chain (MTTR). Limit: measured by the runtime over its OWN store; deployer is "
                     "responsible for archival, retention, and a tested reconstruction harness."),
    )

    # --- sample sizes (rates are uninterpretable without them) ---
    n_governed_claims: int = Field(0, ge=0, description="claims behind the completion/evidence rates")
    n_directives: int = Field(0, ge=0, description="gate decisions behind rejection/gate-failure rates")
    n_traces: int = Field(0, ge=0, description="traces behind replay-success + MTTR")

    # --- honesty + provenance ---
    incomplete: Dict[str, str] = Field(
        default_factory=dict,
        description="metric_name -> reason it is None (e.g. 'no labelled outcomes', 'persistence disabled')",
    )
    measurement_period_start: Optional[datetime] = None
    measurement_period_end: Optional[datetime] = None
    producer: str = Field(
        default="phionyx.sla_metrics/0.1",
        description="what computed this report (provenance label, not an authority claim)",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "verified_completion_rate": 0.62,
                "rejection_rate": 0.08,
                "policy_gate_failure_rate": 0.02,
                "replay_success_rate": 1.0,
                "evidence_completeness_score": 0.91,
                "mean_time_to_evidence_reconstruction_ms": 12.4,
                "n_governed_claims": 50,
                "n_directives": 120,
                "n_traces": 3,
                "incomplete": {},
                "producer": "phionyx.sla_metrics_aggregator/0.1",
            }
        }
