"""Keep / Revert / Park decision engine — Tier D (immutable by research agent).

This module is the core judgment layer of the Phionyx Research Engine.
It consumes scoring outputs and produces a deterministic, auditable
``Decision`` record.

Decision hierarchy (evaluated in strict priority order):
    1. Guardrail violation → REVERT   (absolute veto, no exceptions)
    2. CQS regressed       → REVERT
    3. CQS improved but below complexity tax → ARCHIVE (soft revert)
    4. Latency regression > 20 %      → PARK (held for human review)
    5. Decision score ≤ 0             → ARCHIVE (cost/latency offsets gains)
    6. Tier B edit                    → PARK   (requires human sign-off)
    7. All checks passed              → KEEP as *candidate*

Tier D is the evaluation lock: the research agent may read ``Decision``
objects but is prohibited from modifying this module.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .evaluation.scoring import compute_complexity_tax, compute_decision_score

# ---------------------------------------------------------------------------
# Decision record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """Immutable record of a keep / revert / park judgement.

    Attributes
    ----------
    action:
        One of ``"keep"``, ``"revert"``, or ``"park"``.

        * ``"keep"``   — experiment is accepted as a *candidate*; may be
                         promoted to baseline after human confirmation.
        * ``"revert"`` — experiment is discarded; baseline is unchanged.
        * ``"park"``   — experiment is held in a review queue; neither
                         accepted nor discarded until a human decides.

    status:
        One of ``"candidate"``, ``"rejected"``, or ``"archived"``.

        * ``"candidate"`` — passed all gates; eligible for promotion.
        * ``"rejected"``  — hard failure (guardrail violation or CQS
                            regression); not eligible for re-evaluation.
        * ``"archived"``  — soft failure (complexity tax not met or negative
                            decision score); may be reconsidered if context
                            changes.

    rationale:
        Human-readable explanation of why this decision was reached.
        Included verbatim in audit logs.

    guardrail_violations:
        List of guardrail violation strings (empty when action ≠ "revert"
        due to guardrails).

    cqs_delta:
        ``experiment_cqs − baseline_cqs``.  Negative = regression.

    decision_score:
        Weighted composite score from :func:`~evaluation.scoring.compute_decision_score`.
        Positive leans keep; negative leans revert.
    """

    action: str
    status: str
    rationale: str
    guardrail_violations: list[str]
    cqs_delta: float
    decision_score: float

    def __post_init__(self) -> None:
        valid_actions = {"keep", "revert", "park"}
        valid_statuses = {"candidate", "rejected", "archived"}
        if self.action not in valid_actions:
            raise ValueError(
                f"Decision.action must be one of {valid_actions}, got {self.action!r}"
            )
        if self.status not in valid_statuses:
            raise ValueError(
                f"Decision.status must be one of {valid_statuses}, got {self.status!r}"
            )


# ---------------------------------------------------------------------------
# Decision function
# ---------------------------------------------------------------------------


def decide(
    baseline_cqs: float,
    experiment_cqs: float,
    guardrail_violations: list[str],
    diff_lines: int,
    tier: str,
    latency_regression_pct: float = 0.0,
    cost_regression_pct: float = 0.0,
    lines_removed: int = 0,
) -> Decision:
    """Make a keep / revert / park judgement for a single experiment.

    This function is the core judgment of the research engine.  It is
    deliberately free of side-effects: given the same inputs it always
    returns the same ``Decision`` (fully deterministic and auditable).

    Parameters
    ----------
    baseline_cqs:
        CQS of the current accepted baseline, in ``[0.0, 1.0]``.
    experiment_cqs:
        CQS measured for the candidate experiment, in ``[0.0, 1.0]``.
    guardrail_violations:
        Output of :func:`~evaluation.scoring.check_guardrails`.  An empty
        list means all guardrails pass.
    diff_lines:
        Total lines changed (added + removed) in the experiment's patch.
    tier:
        Tier label of the code region being modified.  Tier ``"B"`` edits
        are auto-parked and require explicit human promotion; all other
        tiers (``"C"``, ``"D"``, etc.) follow the standard path.
    latency_regression_pct:
        P95 latency increase as a percentage (0 = no change).
    cost_regression_pct:
        Token / compute cost increase as a percentage (0 = no change).
    lines_removed:
        Lines removed by the patch (used to compute simplification bonus).

    Returns
    -------
    Decision
        Frozen, auditable decision record.

    Decision rules (in priority order)
    -----------------------------------
    1. **Guardrail violation → REVERT** (``status="rejected"``)
       Any entry in *guardrail_violations* triggers an unconditional revert.
       Guardrails have absolute veto power; no other metric can override them.

    2. **CQS regression → REVERT** (``status="rejected"``)
       ``experiment_cqs < baseline_cqs`` is a hard failure.

    3. **Below complexity tax → ARCHIVE** (``action="revert", status="archived"``)
       The experiment improved CQS but not enough to justify the size of the
       diff.  Logged for future reference; not eligible for auto-promotion.

    4. **Latency regression > 20 % → PARK** (``status="candidate"``)
       The quality gain is real but the performance cost is too high to
       auto-promote.  A human reviewer decides whether the trade-off is
       acceptable.

    5. **Decision score ≤ 0 → ARCHIVE** (``action="revert", status="archived"``)
       Latency, cost, and complexity penalties collectively outweigh the CQS
       improvement.

    6. **Tier B → PARK** (``status="candidate"``)
       Tier B regions are high-stakes (e.g., scheduling, arbitration).
       Even a clean quality improvement must pass through a human gate.

    7. **All checks passed → KEEP** (``status="candidate"``)
       The experiment is accepted as a candidate and may be promoted to
       baseline.
    """
    cqs_delta: float = experiment_cqs - baseline_cqs
    decision_score: float = compute_decision_score(
        cqs_delta=cqs_delta,
        latency_regression_pct=latency_regression_pct,
        cost_regression_pct=cost_regression_pct,
        diff_lines=diff_lines,
        lines_removed=lines_removed,
    )
    complexity_threshold: float = compute_complexity_tax(diff_lines)

    # ------------------------------------------------------------------
    # Rule 1: Guardrail violation → REVERT (absolute veto)
    # ------------------------------------------------------------------
    if guardrail_violations:
        return Decision(
            action="revert",
            status="rejected",
            rationale=f"Guardrail violations: {'; '.join(guardrail_violations)}",
            guardrail_violations=list(guardrail_violations),
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 2: CQS regression → REVERT
    # ------------------------------------------------------------------
    if cqs_delta < 0:
        return Decision(
            action="revert",
            status="rejected",
            rationale=f"CQS regressed by {abs(cqs_delta):.6f}",
            guardrail_violations=[],
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 3: CQS improved but below complexity tax → ARCHIVE
    # Infinite threshold (diff > 30 lines) always fails this check.
    # ------------------------------------------------------------------
    if math.isinf(complexity_threshold) or cqs_delta < complexity_threshold:
        if math.isinf(complexity_threshold):
            rationale = (
                f"Diff of {diff_lines} lines exceeds auto-promote limit (>30); "
                f"human review required (CQS delta={cqs_delta:.6f})"
            )
        else:
            rationale = (
                f"CQS improved by {cqs_delta:.6f} but below complexity "
                f"threshold {complexity_threshold:.6f} for {diff_lines} lines"
            )
        return Decision(
            action="revert",
            status="archived",
            rationale=rationale,
            guardrail_violations=[],
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 4: Latency regression > 20 % → PARK
    # ------------------------------------------------------------------
    if latency_regression_pct > 20.0:
        return Decision(
            action="park",
            status="candidate",
            rationale=(
                f"CQS improved by {cqs_delta:.6f} but latency increased "
                f"{latency_regression_pct:.1f}% (>20% threshold)"
            ),
            guardrail_violations=[],
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 5: Decision score ≤ 0 → ARCHIVE
    # Cost / latency / complexity penalties collectively offset CQS gains.
    # ------------------------------------------------------------------
    if decision_score <= 0:
        return Decision(
            action="revert",
            status="archived",
            rationale=(
                f"CQS improved by {cqs_delta:.6f} but decision score "
                f"{decision_score:.6f} \u2264 0 "
                f"(cost/latency/complexity offset gains)"
            ),
            guardrail_violations=[],
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 6: Tier B → PARK (requires human sign-off before promotion)
    # ------------------------------------------------------------------
    if tier == "B":
        return Decision(
            action="park",
            status="candidate",
            rationale=(
                f"CQS improved by {cqs_delta:.6f}, Tier B edit requires "
                f"human review before promotion"
            ),
            guardrail_violations=[],
            cqs_delta=cqs_delta,
            decision_score=decision_score,
        )

    # ------------------------------------------------------------------
    # Rule 7: All checks passed → KEEP as candidate
    # ------------------------------------------------------------------
    return Decision(
        action="keep",
        status="candidate",
        rationale=(
            f"CQS improved by {cqs_delta:.6f} "
            f"(score={decision_score:.6f}), "
            f"no guardrail violations, complexity justified"
        ),
        guardrail_violations=[],
        cqs_delta=cqs_delta,
        decision_score=decision_score,
    )
