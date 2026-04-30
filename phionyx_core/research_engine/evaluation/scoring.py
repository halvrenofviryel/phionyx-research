"""Evaluation scoring — Tier D (immutable by research agent).

CQS (Composite Quality Score) is an internal quality metric. It is not
an industry-standard benchmark.

CQS uses geometric mean so no single weak component can be hidden
by strong components. This prevents metric hacking.

Tier D is the evaluation lock: the research agent may read these results
but is prohibited from modifying this module or its logic. All scoring
decisions are auditable and deterministic.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Primary metric components
# ---------------------------------------------------------------------------

#: The six required components for the Composite Quality Score.
#: Order is significant for audit-log readability but not for computation.
_CQS_REQUIRED_COMPONENTS: list[str] = [
    "task_completion_accuracy",
    "determinism_consistency",
    "reasoning_chain_validity",
    "policy_compliance_rate",
    "response_coherence",
    "trace_completeness",
]

# ---------------------------------------------------------------------------
# CQS — Composite Quality Score
# ---------------------------------------------------------------------------


def compute_cqs(components: dict[str, float]) -> float:
    """Compute Composite Quality Score using geometric mean.

    Parameters
    ----------
    components:
        A mapping of metric name → value in ``[0.0, 1.0]``.  The six
        required keys are:

        * ``task_completion_accuracy``
        * ``determinism_consistency``
        * ``reasoning_chain_validity``
        * ``policy_compliance_rate``
        * ``response_coherence``
        * ``trace_completeness``

        Missing keys default to ``0.0``.

    Returns
    -------
    float
        Geometric mean of the six components, in ``[0.0, 1.0]``.
        Returns ``0.0`` immediately if any component is exactly ``0.0``.

    Raises
    ------
    ValueError
        If any component value falls outside ``[0.0, 1.0]``.

    Notes
    -----
    Geometric mean was chosen over arithmetic mean deliberately: a single
    weak component drags the entire score down, preventing the research
    agent from gaming the metric by trading one dimension against another.
    For example, an agent cannot compensate for poor determinism by
    inflating trace completeness.
    """
    values: list[float] = []
    for key in _CQS_REQUIRED_COMPONENTS:
        v = components.get(key, 0.0)
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                f"CQS component '{key}' has value {v!r} which is outside [0.0, 1.0]"
            )
        values.append(v)

    # Short-circuit: any zero collapses the geometric mean to zero.
    if any(v == 0.0 for v in values):
        return 0.0

    return math.prod(values) ** (1.0 / len(values))


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


def check_guardrails(metrics: dict[str, float]) -> list[str]:
    """Check guardrail metrics and return a list of violation descriptions.

    Guardrails carry **veto power**: a non-empty violation list blocks
    promotion to *candidate* status even when CQS has improved.  The
    decision engine enforces this unconditionally (Rule 1 in ``decide()``).

    Parameters
    ----------
    metrics:
        Flat metric dictionary.  Keys not present default to their
        "passing" sentinel value (0.0 for rates, 1.0 for coverage ratios,
        0 for counts).

    Returns
    -------
    List[str]
        Human-readable violation descriptions.  An empty list means all
        guardrails pass.

    Guardrail definitions
    ---------------------
    +---------------------------+----------+-----------------------------------------------+
    | Metric                    | Operator | Threshold                                     |
    +===========================+==========+===============================================+
    | governance_violation_rate | >        | 0.0  (zero tolerance)                         |
    +---------------------------+----------+-----------------------------------------------+
    | determinism_consistency   | <        | 0.96 (96 % minimum)                           |
    +---------------------------+----------+-----------------------------------------------+
    | state_hash_consistency    | <        | 0.95 (95 % minimum)                           |
    +---------------------------+----------+-----------------------------------------------+
    | audit_coverage            | <        | 0.98 (98 % minimum)                           |
    +---------------------------+----------+-----------------------------------------------+
    | gold_task_regressions     | >        | 0    (zero regressions on gold tasks)         |
    +---------------------------+----------+-----------------------------------------------+
    """
    violations: list[str] = []

    # --- Governance: zero tolerance -------------------------------------------
    gvr = metrics.get("governance_violation_rate", 0.0)
    if gvr > 0.0:
        violations.append(
            f"governance_violation_rate={gvr:.4f} > 0.0"
        )

    # --- Determinism: must stay at or above 96 % ------------------------------
    # Default to 1.0 (fully passing) so that a missing key does not trigger a
    # spurious violation.  A caller that genuinely measured 0 % determinism
    # must supply the key explicitly.
    det = metrics.get("determinism_consistency", 1.0)
    if det < 0.96:
        violations.append(f"determinism_consistency={det:.4f} < 0.96")

    # --- State hash consistency: must stay at or above 95 % ------------------
    shc = metrics.get("state_hash_consistency", 1.0)
    if shc < 0.95:
        violations.append(f"state_hash_consistency={shc:.4f} < 0.95")

    # --- Audit coverage: must stay at or above 98 % --------------------------
    ac = metrics.get("audit_coverage", 1.0)
    if ac < 0.98:
        violations.append(f"audit_coverage={ac:.4f} < 0.98")

    # --- Gold task regressions: must be zero ----------------------------------
    gtr = int(metrics.get("gold_task_regressions", 0))
    if gtr > 0:
        violations.append(f"gold_task_regressions={gtr} > 0")

    return violations


# ---------------------------------------------------------------------------
# Complexity tax
# ---------------------------------------------------------------------------


def compute_complexity_tax(diff_lines: int) -> float:
    """Return the minimum CQS delta required to justify an edit of *diff_lines*.

    Larger edits carry more risk (merge conflicts, review burden, unexpected
    interactions) and must justify themselves with proportionally larger
    quality improvements.

    Parameters
    ----------
    diff_lines:
        Total lines changed (added + removed) in the diff.  Non-positive
        values are treated as zero (no-op edit).

    Returns
    -------
    float
        Minimum required CQS delta.  Returns ``float('inf')`` for diffs
        larger than 30 lines — these require human review and cannot be
        auto-promoted.

    Complexity tiers
    ----------------
    +-------------+---------+------------------------------------------+
    | Lines       | Tax     | Rationale                                |
    +=============+=========+==========================================+
    | ≤ 0         | 0.000   | No-op                                    |
    +-------------+---------+------------------------------------------+
    | 1 – 5       | 0.005   | Trivial one-liner; minimal barrier       |
    +-------------+---------+------------------------------------------+
    | 6 – 15      | 0.010   | Small refactor; 1 % improvement required |
    +-------------+---------+------------------------------------------+
    | 16 – 30     | 0.020   | Medium change; 2 % improvement required  |
    +-------------+---------+------------------------------------------+
    | > 30        | ∞       | Large edit — human review mandatory      |
    +-------------+---------+------------------------------------------+
    """
    if diff_lines <= 0:
        return 0.0
    if diff_lines <= 5:
        return 0.005
    if diff_lines <= 15:
        return 0.010
    if diff_lines <= 30:
        return 0.020
    # Anything larger cannot be auto-promoted; the caller must flag this.
    return float("inf")


# ---------------------------------------------------------------------------
# Composite decision score
# ---------------------------------------------------------------------------


def compute_decision_score(
    cqs_delta: float,
    latency_regression_pct: float,
    cost_regression_pct: float,
    diff_lines: int,
    lines_removed: int = 0,
) -> float:
    """Compute a single signed score that summarises whether to keep or revert.

    A positive score leans *keep*; a negative score leans *revert*.  The
    decision engine uses this as a secondary signal after guardrail and CQS
    checks (Rules 4–5 in ``decide()``).

    Parameters
    ----------
    cqs_delta:
        Experiment CQS minus baseline CQS.  Can be negative.
    latency_regression_pct:
        Percentage increase in P95 latency (0 = no change, 20 = 20 % slower).
        Negative values (improvements) are clamped to 0 — latency wins are
        accounted for implicitly through lower cost/complexity.
    cost_regression_pct:
        Percentage increase in token/compute cost.  Same clamping as latency.
    diff_lines:
        Total lines changed (added + removed).
    lines_removed:
        Lines removed by the edit.  Simplification (net removal) earns a
        bonus because smaller code is easier to audit and maintain.

    Returns
    -------
    float
        Signed decision score.

    Score formula
    -------------
    ::

        score = (cqs_delta * 1.0)
              - max(0, latency_regression_pct / 100) * 0.3
              - max(0, cost_regression_pct   / 100) * 0.2
              - complexity_tax                       * 0.2
              + simplification_bonus                 * 0.3

    where ``simplification_bonus = 0.002 * max(0, lines_removed - diff_lines)``.

    Weights rationale
    -----------------
    * Quality (1.0) outweighs all regressions combined — CQS improvement
      is the primary signal.
    * Latency (0.3) matters more than cost (0.2) because it affects the
      human user directly.
    * Complexity (0.2) penalises large diffs to discourage speculative
      over-engineering.
    * Simplification (0.3) rewards shrinking the codebase — a deleted line
      is a line that cannot regress.
    """
    complexity = compute_complexity_tax(diff_lines)
    # Guard against inf * 0.2 producing NaN in edge cases where complexity
    # is infinite but the caller still wants a numeric score for logging.
    complexity_penalty = 0.0 if math.isinf(complexity) else complexity * 0.2

    simplification_bonus = 0.002 * max(0, lines_removed - diff_lines)

    score = (
        cqs_delta * 1.0
        - max(0.0, latency_regression_pct / 100.0) * 0.3
        - max(0.0, cost_regression_pct / 100.0) * 0.2
        - complexity_penalty
        + simplification_bonus * 0.3
    )
    return score
