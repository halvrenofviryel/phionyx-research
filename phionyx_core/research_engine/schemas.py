"""Pydantic v2 schemas for the Phionyx Research Engine.

All record types are immutable (frozen=True) so they can be safely cached,
hashed, and passed across async boundaries without defensive copying.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# MetricVector
# ---------------------------------------------------------------------------

class MetricVector(BaseModel):
    """A complete snapshot of system quality captured by a benchmark run.

    Primary CQS components (used in geometric mean):
        task_completion_accuracy, determinism_consistency,
        reasoning_chain_validity, policy_compliance_rate,
        response_coherence, trace_completeness

    Supporting / guardrail metrics (not in CQS geometric mean):
        governance_violation_rate, avg_latency_ms, phi_stability_variance,
        state_hash_consistency, p95_latency_ms, token_cost_per_task
    """

    model_config = ConfigDict(frozen=True)

    # --- Primary CQS components -------------------------------------------
    task_completion_accuracy: float
    determinism_consistency: float
    reasoning_chain_validity: float
    policy_compliance_rate: float
    response_coherence: float
    trace_completeness: float

    # --- Guardrail / operational metrics ------------------------------------
    governance_violation_rate: float
    avg_latency_ms: float
    phi_stability_variance: float
    state_hash_consistency: float = 1.0

    # --- Optional extended metrics ------------------------------------------
    p95_latency_ms: float | None = None
    token_cost_per_task: float | None = None

    # --- Computed properties ------------------------------------------------

    @property
    def cqs(self) -> float:
        """Composite Quality Score — geometric mean of the six primary components.

        Returns a value in [0, 1]. Any component equal to 0 collapses the
        entire score to 0, which is intentional: a zero on any pillar is a
        hard failure.
        """
        components = [
            self.task_completion_accuracy,
            self.determinism_consistency,
            self.reasoning_chain_validity,
            self.policy_compliance_rate,
            self.response_coherence,
            self.trace_completeness,
        ]
        # Clamp to [0, 1] before computing to guard against upstream errors
        clamped = [max(0.0, min(1.0, c)) for c in components]
        product = math.prod(clamped)
        return product ** (1.0 / 6.0)

    @property
    def guardrails_intact(self) -> bool:
        """True iff all hard safety constraints are satisfied.

        Conditions (all must hold):
        - governance_violation_rate == 0.0  (zero tolerance)
        - determinism_consistency  >= 0.96
        - state_hash_consistency   >= 0.95
        """
        return (
            self.governance_violation_rate == 0.0
            and self.determinism_consistency >= 0.96
            and self.state_hash_consistency >= 0.95
        )


# ---------------------------------------------------------------------------
# Hypothesis
# ---------------------------------------------------------------------------

class Hypothesis(BaseModel):
    """A single proposed change to a surface parameter.

    The engine generates one Hypothesis per experiment, applies it, benchmarks,
    and then decides keep / revert / park / crash.
    """

    model_config = ConfigDict(frozen=True)

    parameter_name: str
    surface_file: str
    tier: Literal["A", "B", "C"]
    old_value: Any
    new_value: Any
    expected_metric: str
    expected_delta: float
    reasoning: str
    edit_size_estimate: int  # estimated lines changed


# ---------------------------------------------------------------------------
# ExperimentRecord
# ---------------------------------------------------------------------------

class ExperimentRecord(BaseModel):
    """Full audit record for one completed experiment.

    Written to the audit store regardless of decision so the entire
    session history is reconstructible from disk.
    """

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    timestamp: str          # ISO 8601
    session_id: str
    surface_file: str
    tier: str
    hypothesis: Hypothesis
    baseline_cqs: float
    experiment_cqs: float
    cqs_delta: float
    baseline_metrics: MetricVector
    experiment_metrics: MetricVector
    decision: Literal["keep", "revert", "park", "crash"]
    rationale: str
    git_commit: str | None
    diff_lines_changed: int
    benchmark_suite: str
    benchmark_duration_seconds: float
    guardrail_violations: list[str]
    status: Literal["rejected", "archived", "candidate", "promoted", "gold"]


# ---------------------------------------------------------------------------
# BaselineSnapshot
# ---------------------------------------------------------------------------

class BaselineSnapshot(BaseModel):
    """Immutable record of the system state at session start.

    Used as the reference point for all cqs_delta calculations within a
    session. Stored to disk so interrupted sessions can resume correctly.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: str          # ISO 8601
    git_commit: str
    metrics: MetricVector
    surface_values: dict[str, Any]


# ---------------------------------------------------------------------------
# SessionReport
# ---------------------------------------------------------------------------

class SessionReport(BaseModel):
    """Summary written at the end of every research session.

    experiments contains experiment IDs only — full records live in the
    audit store and are linked by ID.
    """

    model_config = ConfigDict(frozen=True)

    session_id: str
    start_time: str         # ISO 8601
    end_time: str           # ISO 8601
    total_experiments: int
    kept: int
    reverted: int
    parked: int
    crashed: int
    best_cqs_delta: float
    stop_reason: str
    experiments: list[str]  # experiment IDs


# ---------------------------------------------------------------------------
# Surface parameter catalogue
# ---------------------------------------------------------------------------

class SurfaceParameter(BaseModel):
    """A single tunable parameter on a surface file.

    The engine will only propose values within [range_min, range_max]
    stepping by *step*.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    type: Literal["float", "int"]
    current: float
    range_min: float
    range_max: float
    step: float


class Surface(BaseModel):
    """Descriptor for one file that the engine is permitted to modify.

    Tier controls how aggressively the engine explores:
        A — core physics / governance  (smallest diffs, highest bar)
        B — bridge adapters / pipeline blocks
        C — heuristics / weights / prompts
        D — config / templates (largest permitted diffs)

    review_required=True surfaces are parked rather than auto-promoted.
    """

    model_config = ConfigDict(frozen=True)

    file: str
    tier: Literal["A", "B", "C", "D"]
    parameters: list[SurfaceParameter]
    max_lines_changed: int
    review_required: bool = False
