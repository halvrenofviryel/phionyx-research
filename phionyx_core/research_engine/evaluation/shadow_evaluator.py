"""Shadow evaluator — blind evaluation for gold promotion.

Provides independent validation that the main experiment loop does NOT see.
Three evaluation dimensions:

1. Gold re-verification: Re-run the 31 gold tests to catch delayed regressions
2. Holdout suite: Run adversarial/ambiguous tests NOT in composite suites
3. Temporal stability: Re-run composite benchmark N times, measure variance

This module is Tier B (modifiable with human review).
"""
import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from phionyx_core.research_engine.evaluation.runner import (
    BenchmarkRunner,
    _load_gold_test_ids,
)
from phionyx_core.research_engine.evaluation.scoring import compute_cqs

# Holdout suites — tests NOT in the main composite benchmark
HOLDOUT_SUITES: dict[str, str] = {
    "adversarial": "tests/behavioral_eval/test_adversarial_scenarios.py",
    "ambiguous": "tests/behavioral_eval/test_ambiguous_scenarios.py",
    "long_horizon": "tests/behavioral_eval/test_long_horizon_hard.py",
    "deceptive": "tests/behavioral_eval/test_multi_agent_deceptive.py",
    "world_continuity": "tests/behavioral_eval/test_world_model_continuity.py",
}

# Thresholds for shadow evaluation pass/fail
SHADOW_THRESHOLDS = {
    "gold_regression_max": 0,        # Zero tolerance on gold tests
    "holdout_pass_rate_min": 0.85,   # 85% holdout pass rate
    "temporal_cv_max": 0.05,         # 5% coefficient of variation max
    "cqs_drift_max": 0.02,           # 2% max CQS drift from stored value
}


@dataclass
class ShadowReport:
    """Complete shadow evaluation report for an experiment."""

    experiment_id: str
    timestamp: str
    verdict: str  # "pass", "fail", "partial"

    # Gold re-verification
    gold_regressions: int = 0
    gold_total: int = 0
    gold_pass: bool = True

    # Holdout suite
    holdout_pass_rate: float = 0.0
    holdout_total: int = 0
    holdout_passed: int = 0
    holdout_failed: int = 0
    holdout_suites: dict[str, dict[str, Any]] = field(default_factory=dict)
    holdout_pass: bool = True

    # Temporal stability
    temporal_runs: int = 0
    temporal_cqs_values: list[float] = field(default_factory=list)
    temporal_mean: float = 0.0
    temporal_stdev: float = 0.0
    temporal_cv: float = 0.0  # coefficient of variation
    temporal_pass: bool = True

    # CQS drift
    stored_cqs: float = 0.0
    shadow_cqs: float = 0.0
    cqs_drift: float = 0.0
    drift_pass: bool = True

    # Duration
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "verdict": self.verdict,
            "gold": {
                "regressions": self.gold_regressions,
                "total": self.gold_total,
                "pass": self.gold_pass,
            },
            "holdout": {
                "pass_rate": self.holdout_pass_rate,
                "total": self.holdout_total,
                "passed": self.holdout_passed,
                "failed": self.holdout_failed,
                "suites": self.holdout_suites,
                "pass": self.holdout_pass,
            },
            "temporal": {
                "runs": self.temporal_runs,
                "cqs_values": self.temporal_cqs_values,
                "mean": self.temporal_mean,
                "stdev": self.temporal_stdev,
                "cv": self.temporal_cv,
                "pass": self.temporal_pass,
            },
            "drift": {
                "stored_cqs": self.stored_cqs,
                "shadow_cqs": self.shadow_cqs,
                "drift": self.cqs_drift,
                "pass": self.drift_pass,
            },
            "duration_seconds": self.duration_seconds,
        }


class ShadowEvaluator:
    """Blind evaluation layer for gold promotion decisions.

    Runs tests and benchmarks that the main experiment loop does NOT see,
    providing independent validation of experiment quality.
    """

    def __init__(
        self,
        repo_dir: str = ".",
        data_dir: str = "data/research_engine",
        temporal_runs: int = 3,
        timeout: int = 300,
    ):
        self._repo = Path(repo_dir).resolve()
        self._data_dir = Path(data_dir)
        self._reports_dir = self._data_dir / "shadow_reports"
        self._reports_dir.mkdir(parents=True, exist_ok=True)
        self._temporal_runs = temporal_runs
        self._runner = BenchmarkRunner(repo_dir=repo_dir, timeout=timeout)
        self._gold_ids = _load_gold_test_ids(self._repo)

    def evaluate(
        self,
        experiment_id: str,
        stored_cqs: float = 0.0,
        skip_holdout: bool = False,
        skip_temporal: bool = False,
    ) -> ShadowReport:
        """Run comprehensive shadow evaluation for an experiment.

        Returns a ShadowReport with verdict: pass/fail/partial.
        """
        start = time.time()
        report = ShadowReport(
            experiment_id=experiment_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            verdict="pending",
            stored_cqs=stored_cqs,
        )

        # 1. Gold re-verification
        self._verify_gold(report)

        # 2. Holdout suite
        if not skip_holdout:
            self._run_holdout(report)

        # 3. Temporal stability
        if not skip_temporal:
            self._check_temporal_stability(report)

        # 4. CQS drift check (uses temporal mean if available)
        if report.temporal_cqs_values:
            report.shadow_cqs = report.temporal_mean
        elif not skip_temporal:
            # Run a single composite to get current CQS
            result = self._runner.run_composite()
            report.shadow_cqs = compute_cqs(result.metrics)
        else:
            report.shadow_cqs = stored_cqs

        if stored_cqs > 0:
            report.cqs_drift = abs(report.shadow_cqs - stored_cqs) / stored_cqs
            report.drift_pass = report.cqs_drift <= SHADOW_THRESHOLDS["cqs_drift_max"]

        # Compute verdict
        checks = [report.gold_pass, report.drift_pass]
        if not skip_holdout:
            checks.append(report.holdout_pass)
        if not skip_temporal:
            checks.append(report.temporal_pass)

        if all(checks):
            report.verdict = "pass"
        elif report.gold_pass and report.drift_pass:
            report.verdict = "partial"
        else:
            report.verdict = "fail"

        report.duration_seconds = time.time() - start

        # Persist report
        self._save_report(report)

        return report

    def _verify_gold(self, report: ShadowReport) -> None:
        """Re-run gold tests and check for regressions."""
        report.gold_total = len(self._gold_ids)
        if not self._gold_ids:
            report.gold_pass = True
            return

        # Run composite benchmark (needed for gold test results)
        result = self._runner.run_composite()
        gold_regressions = result.metrics.get("gold_task_regressions", 0)
        report.gold_regressions = gold_regressions
        report.gold_pass = gold_regressions <= SHADOW_THRESHOLDS["gold_regression_max"]

    def _run_holdout(self, report: ShadowReport) -> None:
        """Run holdout test suites not seen during main experiment loop."""
        total_passed = 0
        total_failed = 0
        total_tests = 0

        for suite_name, suite_path in HOLDOUT_SUITES.items():
            test_path = self._repo / suite_path
            if not test_path.exists():
                continue

            result = self._runner.run_suite(suite_name)
            suite_info = {
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "total": result.total_tests,
                "duration": result.duration_seconds,
            }
            report.holdout_suites[suite_name] = suite_info
            runnable = result.total_tests - result.skipped
            total_passed += result.passed
            total_failed += result.failed
            total_tests += runnable

        report.holdout_total = total_tests
        report.holdout_passed = total_passed
        report.holdout_failed = total_failed
        report.holdout_pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
        report.holdout_pass = (
            report.holdout_pass_rate >= SHADOW_THRESHOLDS["holdout_pass_rate_min"]
        )

    def _check_temporal_stability(self, report: ShadowReport) -> None:
        """Run composite benchmark N times and measure CQS variance."""
        cqs_values: list[float] = []
        for _ in range(self._temporal_runs):
            result = self._runner.run_composite()
            cqs = compute_cqs(result.metrics)
            cqs_values.append(cqs)

        report.temporal_runs = len(cqs_values)
        report.temporal_cqs_values = cqs_values

        if len(cqs_values) >= 2:
            report.temporal_mean = statistics.mean(cqs_values)
            report.temporal_stdev = statistics.stdev(cqs_values)
            report.temporal_cv = (
                report.temporal_stdev / report.temporal_mean
                if report.temporal_mean > 0
                else 0.0
            )
        elif cqs_values:
            report.temporal_mean = cqs_values[0]
            report.temporal_stdev = 0.0
            report.temporal_cv = 0.0

        report.temporal_pass = report.temporal_cv <= SHADOW_THRESHOLDS["temporal_cv_max"]

    def _save_report(self, report: ShadowReport) -> None:
        """Persist shadow report to disk."""
        report_path = self._reports_dir / f"{report.experiment_id}.json"
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

    def load_report(self, experiment_id: str) -> ShadowReport | None:
        """Load a previously saved shadow report."""
        report_path = self._reports_dir / f"{experiment_id}.json"
        if not report_path.exists():
            return None
        try:
            with open(report_path) as f:
                data = json.load(f)
            return self._dict_to_report(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_reports(self) -> list[dict[str, Any]]:
        """List all shadow evaluation reports (summary)."""
        reports = []
        if not self._reports_dir.exists():
            return reports
        for path in sorted(self._reports_dir.glob("*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                reports.append({
                    "experiment_id": data["experiment_id"],
                    "timestamp": data["timestamp"],
                    "verdict": data["verdict"],
                    "shadow_cqs": data["drift"]["shadow_cqs"],
                    "gold_pass": data["gold"]["pass"],
                    "holdout_pass": data["holdout"]["pass"],
                    "temporal_pass": data["temporal"]["pass"],
                    "drift_pass": data["drift"]["pass"],
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return reports

    @staticmethod
    def _dict_to_report(data: dict[str, Any]) -> ShadowReport:
        """Reconstruct ShadowReport from dict."""
        gold = data.get("gold", {})
        holdout = data.get("holdout", {})
        temporal = data.get("temporal", {})
        drift = data.get("drift", {})
        return ShadowReport(
            experiment_id=data["experiment_id"],
            timestamp=data["timestamp"],
            verdict=data["verdict"],
            gold_regressions=gold.get("regressions", 0),
            gold_total=gold.get("total", 0),
            gold_pass=gold.get("pass", True),
            holdout_pass_rate=holdout.get("pass_rate", 0.0),
            holdout_total=holdout.get("total", 0),
            holdout_passed=holdout.get("passed", 0),
            holdout_failed=holdout.get("failed", 0),
            holdout_suites=holdout.get("suites", {}),
            holdout_pass=holdout.get("pass", True),
            temporal_runs=temporal.get("runs", 0),
            temporal_cqs_values=temporal.get("cqs_values", []),
            temporal_mean=temporal.get("mean", 0.0),
            temporal_stdev=temporal.get("stdev", 0.0),
            temporal_cv=temporal.get("cv", 0.0),
            temporal_pass=temporal.get("pass", True),
            stored_cqs=drift.get("stored_cqs", 0.0),
            shadow_cqs=drift.get("shadow_cqs", 0.0),
            cqs_drift=drift.get("drift", 0.0),
            drift_pass=drift.get("pass", True),
            duration_seconds=data.get("duration_seconds", 0.0),
        )
