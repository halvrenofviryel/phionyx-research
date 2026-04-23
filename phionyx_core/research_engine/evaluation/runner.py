"""Benchmark runner — executes test suites and captures real metrics.

Tier D (immutable by research agent). The runner is the evaluation lock.
It must produce the same results for the same code state.

v2: Multi-suite strategy — runs separate suites for each metric dimension
and aggregates into a single MetricVector. No more hardcoded placeholders.
"""
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkResult:
    success: bool
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_seconds: float
    raw_output: str
    metrics: dict[str, Any]
    failed_test_ids: tuple[str, ...] = ()


def _load_gold_test_ids(repo_dir: Path) -> set[str]:
    """Load the gold test ID set from fixtures."""
    gold_file = (
        repo_dir / "phionyx_core" / "research_engine"
        / "fixtures" / "gold" / "gold_test_ids.json"
    )
    if not gold_file.exists():
        return set()
    with open(gold_file) as f:
        return set(json.load(f))


def _parse_junit_xml(xml_path: Path) -> dict[str, str]:
    """Parse JUnit XML → {test_node_id: "passed"|"failed"|"skipped"|"error"}."""
    results: dict[str, str] = {}
    if not xml_path.exists():
        return results
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return results

    for tc in tree.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        parts = classname.split(".")
        file_parts = []
        class_parts = []
        found_test_file = False
        for p in parts:
            if found_test_file:
                class_parts.append(p)
            elif p.startswith("test_"):
                file_parts.append(p + ".py")
                found_test_file = True
            else:
                file_parts.append(p)
        if file_parts:
            file_path = "/".join(file_parts)
            if class_parts:
                node_id = f"{file_path}::{'::'.join(class_parts)}::{name}"
            else:
                node_id = f"{file_path}::{name}"
        else:
            node_id = f"{classname}::{name}"

        if tc.find("failure") is not None:
            results[node_id] = "failed"
        elif tc.find("error") is not None:
            results[node_id] = "error"
        elif tc.find("skipped") is not None:
            results[node_id] = "skipped"
        else:
            results[node_id] = "passed"
    return results


SUITE_MAP: dict[str, str] = {
    "core_v1": "tests/behavioral_eval/",
    "determinism": "tests/behavioral_eval/test_determinism_stress.py",
    "governance": "tests/behavioral_eval/test_governance_redteam.py",
    "pipeline": "tests/behavioral_eval/test_pipeline_invariants.py",
    "physics": "tests/benchmarks/test_physics_sensitivity.py",
    "bridge": "tests/unit/bridge/",
    "core_unit": "tests/unit/core/",
    "full": "tests/",
}

COMPOSITE_SUITES: list[str] = ["core_v1", "determinism", "governance", "physics"]


class BenchmarkRunner:
    """Runs benchmark suites and captures real metrics.

    v2: multi-suite composite runs, JUnit XML parsing, gold task regression detection.
    """

    def __init__(self, repo_dir: str = ".", timeout: int = 300):
        self._repo = Path(repo_dir).resolve()
        self._timeout = timeout
        self._gold_ids = _load_gold_test_ids(self._repo)

    def run_suite(self, suite_name: str = "core_v1") -> BenchmarkResult:
        """Run a single benchmark suite."""
        test_path = SUITE_MAP.get(suite_name, suite_name)
        return self._run_pytest(test_path, suite_name)

    def run_composite(self) -> BenchmarkResult:
        """Run multiple suites and aggregate into a single MetricVector."""
        all_test_results: dict[str, str] = {}
        suite_results: dict[str, dict] = {}
        total_duration = 0.0
        raw_parts: list[str] = []
        overall_success = True

        for suite in COMPOSITE_SUITES:
            result = self.run_suite(suite)
            total_duration += result.duration_seconds
            raw_parts.append(f"=== {suite} ===\n{result.raw_output}")
            suite_results[suite] = {
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "errors": result.errors,
                "total": result.total_tests,
                "duration": result.duration_seconds,
            }
            if not result.success:
                overall_success = False
            xml_path = self._repo / "data" / "research_engine" / f"junit_{suite}.xml"
            test_map = _parse_junit_xml(xml_path)
            all_test_results.update(test_map)

        metrics = self._aggregate_metrics(suite_results, all_test_results)
        total_passed = sum(s["passed"] for s in suite_results.values())
        total_failed = sum(s["failed"] for s in suite_results.values())
        total_skipped = sum(s["skipped"] for s in suite_results.values())
        total_errors = sum(s["errors"] for s in suite_results.values())
        total_tests = sum(s["total"] for s in suite_results.values())
        failed_ids = tuple(
            tid for tid, status in all_test_results.items()
            if status in ("failed", "error")
        )

        return BenchmarkResult(
            success=overall_success,
            total_tests=total_tests,
            passed=total_passed,
            failed=total_failed,
            skipped=total_skipped,
            errors=total_errors,
            duration_seconds=total_duration,
            raw_output="\n".join(raw_parts)[-3000:],
            metrics=metrics,
            failed_test_ids=failed_ids,
        )

    def _run_pytest(self, test_path: str, suite_name: str) -> BenchmarkResult:
        """Execute pytest for a single suite."""
        junit_xml = self._repo / "data" / "research_engine" / f"junit_{suite_name}.xml"
        junit_xml.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    str(test_path),
                    f"--junitxml={junit_xml}",
                    "--tb=short", "-q", "--no-header",
                ],
                cwd=self._repo,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            duration = time.time() - start_time
            raw = result.stdout + "\n" + result.stderr
            passed, failed, skipped, errors = self._parse_pytest_summary(result.stdout)
            total = passed + failed + skipped + errors
            test_map = _parse_junit_xml(junit_xml)
            failed_ids = tuple(
                tid for tid, status in test_map.items()
                if status in ("failed", "error")
            )
            metrics = self._compute_single_suite_metrics(
                passed, failed, skipped, errors, total, duration
            )
            return BenchmarkResult(
                success=result.returncode == 0,
                total_tests=total,
                passed=passed, failed=failed,
                skipped=skipped, errors=errors,
                duration_seconds=duration,
                raw_output=raw[-2000:],
                metrics=metrics,
                failed_test_ids=failed_ids,
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return BenchmarkResult(
                success=False, total_tests=0,
                passed=0, failed=0, skipped=0, errors=1,
                duration_seconds=duration,
                raw_output=f"Benchmark timed out after {self._timeout}s",
                metrics=self._empty_metrics(),
            )
        except Exception as e:
            duration = time.time() - start_time
            return BenchmarkResult(
                success=False, total_tests=0,
                passed=0, failed=0, skipped=0, errors=1,
                duration_seconds=duration,
                raw_output=f"Benchmark error: {e}",
                metrics=self._empty_metrics(),
            )

    def _aggregate_metrics(
        self,
        suite_results: dict[str, dict],
        all_test_results: dict[str, str],
    ) -> dict[str, Any]:
        """Aggregate metrics from multiple suite runs.

        v3: Blends binary pass rates (50%) with continuous quality probe
        metrics (50%) to break the flat CQS landscape.
        """
        core = suite_results.get("core_v1", {})
        core_runnable = core.get("total", 0) - core.get("skipped", 0)
        core_pass_rate = (
            core.get("passed", 0) / core_runnable if core_runnable > 0 else 0.0
        )

        det = suite_results.get("determinism", {})
        det_runnable = det.get("total", 0) - det.get("skipped", 0)
        det_pass_rate = (
            det.get("passed", 0) / det_runnable if det_runnable > 0 else 0.0
        )

        gov = suite_results.get("governance", {})
        gov_runnable = gov.get("total", 0) - gov.get("skipped", 0)
        gov_pass_rate = (
            gov.get("passed", 0) / gov_runnable if gov_runnable > 0 else 0.0
        )
        gov_fail_rate = (
            gov.get("failed", 0) / gov_runnable if gov_runnable > 0 else 0.0
        )

        phys = suite_results.get("physics", {})
        phys_runnable = phys.get("total", 0) - phys.get("skipped", 0)
        phys_pass_rate = (
            phys.get("passed", 0) / phys_runnable if phys_runnable > 0 else 0.0
        )

        total_runnable = sum(
            s.get("total", 0) - s.get("skipped", 0)
            for s in suite_results.values()
        )
        total_duration = sum(
            s.get("duration", 0) for s in suite_results.values()
        )

        gold_regressions = 0
        if self._gold_ids:
            for gold_id in self._gold_ids:
                status = all_test_results.get(gold_id)
                if status in ("failed", "error"):
                    gold_regressions += 1

        # ── Quality Probe: continuous metrics from Phionyx modules ──
        continuous: dict[str, float] = {}
        try:
            from phionyx_core.research_engine.evaluation.quality_probe import (
                QualityProbe,
            )
            probe = QualityProbe(str(self._repo))
            continuous = probe.probe()
        except Exception:
            pass  # Fall back to pure binary rates

        def _blend(binary: float, key: str) -> float:
            """50-50 blend of binary pass rate and ONE continuous metric."""
            if key in continuous:
                return 0.5 * binary + 0.5 * continuous[key]
            return binary

        def _blend3(binary: float, key1: str, key2: str) -> float:
            """Blend binary with up to 2 continuous metrics (equal weight)."""
            vals = [continuous[k] for k in (key1, key2) if k in continuous]
            if vals:
                cont_avg = sum(vals) / len(vals)
                return 0.5 * binary + 0.5 * cont_avg
            return binary

        return {
            # CQS components: 4 blended + 2 unblended (guardrail-checked)
            # Each probe domain gets dedicated CQS slot for signal strength:
            #   memory → task_completion + reasoning_chain
            #   causality → response_coherence
            #   formulas → policy_compliance + trace_completeness
            #   physics constants → phi_stability_variance
            "task_completion_accuracy": _blend(
                phys_pass_rate, "memory_cluster_quality",
            ),
            # determinism_consistency is checked by guardrails (< 0.96 → veto)
            # so we keep it as pure binary to avoid false guardrail violations
            "determinism_consistency": det_pass_rate,
            "reasoning_chain_validity": _blend(
                core_pass_rate, "memory_consolidation_rate",
            ),
            "policy_compliance_rate": _blend3(
                gov_pass_rate,
                "memory_promotion_rate",
                "formula_base_floor_effect",
            ),
            "response_coherence": _blend3(
                0.5 * phys_pass_rate + 0.5 * core_pass_rate,
                "causality_mean_effective_strength",
                "formula_entropy_sensitivity",
            ),
            "trace_completeness": _blend3(
                core_pass_rate,
                "physics_resonance_quality",
                "formula_recovery_strength",
            ),
            "governance_violation_rate": gov_fail_rate,
            "avg_latency_ms": (
                (total_duration / total_runnable * 1000)
                if total_runnable > 0
                else 0.0
            ),
            "phi_stability_variance": continuous.get(
                "physics_stability", 0.0
            ),
            "state_hash_consistency": det_pass_rate,
            "gold_task_regressions": gold_regressions,
            "total_tests": sum(
                s.get("total", 0) for s in suite_results.values()
            ),
            "passed": sum(
                s.get("passed", 0) for s in suite_results.values()
            ),
            "failed": sum(
                s.get("failed", 0) for s in suite_results.values()
            ),
            "skipped": sum(
                s.get("skipped", 0) for s in suite_results.values()
            ),
            "errors": sum(
                s.get("errors", 0) for s in suite_results.values()
            ),
            "quality_probe": continuous,
            "suite_breakdown": {
                name: {
                    "pass_rate": s.get("passed", 0)
                    / max(1, s.get("total", 0) - s.get("skipped", 0)),
                    **s,
                }
                for name, s in suite_results.items()
            },
        }

    def _compute_single_suite_metrics(
        self, passed: int, failed: int, skipped: int,
        errors: int, total: int, duration: float,
    ) -> dict[str, Any]:
        """Compute basic metrics for a single suite run."""
        runnable = total - skipped
        pass_rate = passed / runnable if runnable > 0 else 0.0
        return {
            "task_completion_accuracy": pass_rate,
            "determinism_consistency": pass_rate,
            "reasoning_chain_validity": pass_rate,
            "policy_compliance_rate": pass_rate,
            "response_coherence": pass_rate,
            "trace_completeness": pass_rate,
            "governance_violation_rate": 1.0 - pass_rate,
            "avg_latency_ms": (duration / runnable * 1000) if runnable > 0 else 0.0,
            "phi_stability_variance": 0.0,
            "state_hash_consistency": pass_rate,
            "total_tests": total,
            "passed": passed, "failed": failed,
            "skipped": skipped, "errors": errors,
        }

    def _parse_pytest_summary(self, stdout: str) -> tuple[int, int, int, int]:
        """Parse pytest summary line for counts."""
        passed = failed = skipped = errors = 0
        for line in stdout.strip().split("\n"):
            line = line.strip()
            m_passed = re.search(r"(\d+) passed", line)
            m_failed = re.search(r"(\d+) failed", line)
            m_skipped = re.search(r"(\d+) skipped", line)
            m_errors = re.search(r"(\d+) error", line)
            if m_passed:
                passed = int(m_passed.group(1))
            if m_failed:
                failed = int(m_failed.group(1))
            if m_skipped:
                skipped = int(m_skipped.group(1))
            if m_errors:
                errors = int(m_errors.group(1))
        return passed, failed, skipped, errors

    def _empty_metrics(self) -> dict[str, Any]:
        """Return empty metrics for failed/crashed benchmarks."""
        return {
            "task_completion_accuracy": 0.0,
            "determinism_consistency": 0.0,
            "reasoning_chain_validity": 0.0,
            "policy_compliance_rate": 0.0,
            "response_coherence": 0.0,
            "trace_completeness": 0.0,
            "governance_violation_rate": 1.0,
            "avg_latency_ms": 0.0,
            "phi_stability_variance": 0.0,
            "state_hash_consistency": 0.0,
            "gold_task_regressions": 0,
            "total_tests": 0,
            "passed": 0, "failed": 0,
            "skipped": 0, "errors": 0,
        }
