"""
Evaluation Report Generator
============================

Aggregates scoring data from Elo, Preference, and Calibration
into a structured evaluation report.

Roadmap Faz 2.3-2.4
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json

from .scoring import EloRating, PreferenceScorer, CalibrationMetrics
from .task_set import TaskSet


@dataclass
class PassFailCriteria:
    """Success criteria from the roadmap."""
    human_preference_threshold: float = 0.50
    accuracy_delta_min: float = -0.10
    calibration_error_max: float = 0.15
    governance_compliance_min: float = 1.00


@dataclass
class EvalResult:
    """Result for a single evaluation dimension."""
    metric_name: str
    value: float
    threshold: float
    passed: bool
    reasoning: str = ""


@dataclass
class EvalReport:
    """Complete evaluation report."""
    report_id: str
    generated_at: str
    task_set_name: str
    task_count: int
    evaluator_count: int
    results: List[EvalResult] = field(default_factory=list)
    elo_rankings: List[Dict[str, Any]] = field(default_factory=list)
    category_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    overall_pass: bool = False
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "task_set_name": self.task_set_name,
            "task_count": self.task_count,
            "evaluator_count": self.evaluator_count,
            "overall_pass": self.overall_pass,
            "results": [
                {
                    "metric": r.metric_name,
                    "value": round(r.value, 4),
                    "threshold": r.threshold,
                    "passed": r.passed,
                    "reasoning": r.reasoning,
                }
                for r in self.results
            ],
            "elo_rankings": self.elo_rankings,
            "category_breakdown": self.category_breakdown,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class EvalReportGenerator:
    """
    Generates comprehensive evaluation reports from scoring data.
    """

    def __init__(
        self,
        task_set: TaskSet,
        elo: EloRating,
        preference: PreferenceScorer,
        calibration: CalibrationMetrics,
        criteria: Optional[PassFailCriteria] = None,
    ):
        self.task_set = task_set
        self.elo = elo
        self.preference = preference
        self.calibration = calibration
        self.criteria = criteria or PassFailCriteria()

    def generate(
        self,
        report_id: str = "",
        phionyx_accuracy: float = 0.0,
        expert_accuracy: float = 0.0,
        governance_compliance: float = 1.0,
        evaluator_count: int = 0,
    ) -> EvalReport:
        """Generate a complete evaluation report."""
        if not report_id:
            report_id = f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        results = []

        # 1. Human Preference Score
        pref_score = self.preference.phionyx_preference_score()
        results.append(EvalResult(
            metric_name="Human Preference Score",
            value=pref_score,
            threshold=self.criteria.human_preference_threshold,
            passed=pref_score >= self.criteria.human_preference_threshold,
            reasoning=f"Phionyx preferred in {pref_score*100:.1f}% of evaluations",
        ))

        # 2. Accuracy Delta
        acc_delta = self.preference.accuracy_delta(phionyx_accuracy, expert_accuracy)
        results.append(EvalResult(
            metric_name="Accuracy Delta",
            value=acc_delta,
            threshold=self.criteria.accuracy_delta_min,
            passed=acc_delta >= self.criteria.accuracy_delta_min,
            reasoning=f"Phionyx accuracy {phionyx_accuracy:.1%} vs Expert {expert_accuracy:.1%}",
        ))

        # 3. Epistemic Calibration Error
        cal_error = self.calibration.calibration_error()
        results.append(EvalResult(
            metric_name="Epistemic Calibration Error",
            value=cal_error,
            threshold=self.criteria.calibration_error_max,
            passed=cal_error <= self.criteria.calibration_error_max,
            reasoning=f"ECE = {cal_error:.4f} (target < {self.criteria.calibration_error_max})",
        ))

        # 4. Governance Compliance
        results.append(EvalResult(
            metric_name="Governance Compliance",
            value=governance_compliance,
            threshold=self.criteria.governance_compliance_min,
            passed=governance_compliance >= self.criteria.governance_compliance_min,
            reasoning=f"Ethics framework compliance: {governance_compliance:.1%}",
        ))

        # Elo rankings
        elo_rankings = [
            {"player": player, "rating": round(rating, 1)}
            for player, rating in self.elo.rankings
        ]

        # Category breakdown from preference data
        category_breakdown = self._compute_category_breakdown()

        # Overall pass
        overall_pass = all(r.passed for r in results)

        # Summary
        passed_count = sum(1 for r in results if r.passed)
        summary = (
            f"{'PASSED' if overall_pass else 'FAILED'}: "
            f"{passed_count}/{len(results)} criteria met. "
            f"Phionyx preference: {pref_score*100:.1f}%, "
            f"Calibration error: {cal_error:.4f}, "
            f"Elo ranking: {elo_rankings[0]['player'] if elo_rankings else 'N/A'} leads."
        )

        return EvalReport(
            report_id=report_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            task_set_name=self.task_set.name,
            task_count=self.task_set.task_count,
            evaluator_count=evaluator_count,
            results=results,
            elo_rankings=elo_rankings,
            category_breakdown=category_breakdown,
            overall_pass=overall_pass,
            summary=summary,
        )

    def _compute_category_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Compute preference scores per task category."""
        from .task_set import TaskCategory
        from .scoring import PreferenceWinner

        breakdown: Dict[str, Dict[str, float]] = {}

        for category in TaskCategory:
            tasks = self.task_set.get_by_category(category)
            task_ids = {t.task_id for t in tasks}

            relevant_votes = [
                v for v in self.preference._votes if v.task_id in task_ids
            ]
            if not relevant_votes:
                continue

            total = sum(v.confidence for v in relevant_votes)
            if total == 0:
                continue

            phionyx_wins = sum(
                v.confidence for v in relevant_votes
                if v.winner == PreferenceWinner.C
            )
            expert_wins = sum(
                v.confidence for v in relevant_votes
                if v.winner == PreferenceWinner.A
            )
            kw_wins = sum(
                v.confidence for v in relevant_votes
                if v.winner == PreferenceWinner.B
            )

            breakdown[category.value] = {
                "phionyx": phionyx_wins / total,
                "expert": expert_wins / total,
                "knowledge_worker": kw_wins / total,
                "sample_size": len(relevant_votes),
            }

        return breakdown
