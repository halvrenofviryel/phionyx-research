"""Main experiment loop — Tier D (immutable by research agent).

This is the Phionyx equivalent of Karpathy's autoresearch loop.
It orchestrates: hypothesis → validate → edit → benchmark → decide → keep/revert.
"""
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .decision import decide
from .evaluation.runner import BenchmarkRunner
from .evaluation.scoring import check_guardrails, compute_cqs
from .governance.budget_monitor import BudgetMonitor
from .audit.logger import AuditLogger
from .store.experiment_store import ExperimentStore
from .store.baseline_store import BaselineStore
from .rollback.git_manager import GitManager
from .rollback.config_snapshot import ConfigSnapshot
from .mutation.planner import create_plan
from .mutation.scope_validator import validate_scope
from .mutation.range_validator import validate_range

logger = logging.getLogger(__name__)


def _generate_experiment_id(surface: str, seq: int) -> str:
    """Generate a unique experiment ID."""
    ts = time.strftime("%Y%m%d-%H%M%S")
    surface_short = Path(surface).stem[:20]
    return f"exp-{ts}-{surface_short}-{seq:03d}"


def _generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _apply_parameter_edit(file_path: str, param_name: str, old_value: Any, new_value: Any) -> bool:
    """Apply a single parameter value change to a file.

    Finds the line containing the parameter assignment and replaces the value.
    Returns True if the edit was applied, False if the parameter was not found.
    """
    path = Path(file_path)
    if not path.exists():
        return False

    content = path.read_text()

    # Match patterns like: param_name = value  or  "param_name": value
    # Python assignment: `param_name = 1.15`
    pattern_py = rf"^(\s*{re.escape(param_name)}\s*=\s*){re.escape(str(old_value))}"
    replaced, count = re.subn(pattern_py, rf"\g<1>{new_value}", content, flags=re.MULTILINE)

    if count > 0:
        path.write_text(replaced)
        return True

    # Dict entry: `"param_name": 1.15` or `'param_name': 1.15`
    pattern_dict = rf'(["\']){re.escape(param_name)}\1\s*:\s*{re.escape(str(old_value))}'
    replaced, count = re.subn(
        pattern_dict,
        rf'"{param_name}": {new_value}',
        content,
    )

    if count > 0:
        path.write_text(replaced)
        return True

    return False


def _check_stop_file(data_dir: str) -> bool:
    """Check if a STOP file exists (human override)."""
    return Path(data_dir).joinpath("STOP").exists()


def run_session(
    config: EngineConfig | None = None,
    surface_file: str = "phionyx_core/physics/constants.py",
    suite_name: str = "core_v1",
    strategy: str = "grid",
    surfaces: list[dict] | None = None,
    parameters: list[dict] | None = None,
    dry_run: bool = False,
) -> dict:
    """Run an experiment session.

    This is the main entry point for the research engine.
    It runs the experiment loop until budget is exhausted or
    no more hypotheses remain.

    Args:
        config: Engine configuration (uses defaults if None)
        surface_file: File to optimize
        suite_name: Benchmark suite to run
        strategy: Hypothesis strategy ("grid", "random", "boundary", "all")
        surfaces: Surface definitions (parsed from surfaces.yaml)
        parameters: Parameter definitions for the surface
        dry_run: If True, do not actually edit files or run benchmarks

    Returns:
        Session report as dict
    """
    if config is None:
        config = EngineConfig()

    session_id = _generate_session_id()

    # Initialize components
    budget = BudgetMonitor(
        max_experiments=config.session.max_experiments,
        max_session_seconds=config.session.max_session_seconds,
        max_consecutive_failures=config.session.max_consecutive_failures,
    )
    audit = AuditLogger(config.audit_dir)
    store = ExperimentStore(config.data_dir)
    baseline_store = BaselineStore(config.data_dir)
    git = GitManager()
    snapshots = ConfigSnapshot(config.data_dir)
    runner = BenchmarkRunner(timeout=config.session.benchmark_timeout_seconds)

    # Log session start
    audit.log_session_start(session_id, {
        "surface_file": surface_file,
        "suite_name": suite_name,
        "strategy": strategy,
        "max_experiments": config.session.max_experiments,
        "max_session_seconds": config.session.max_session_seconds,
    })

    # Default surfaces/parameters if not provided
    if surfaces is None:
        surfaces = [{"file": surface_file, "tier": "A", "max_lines_changed": 5}]
    if parameters is None:
        parameters = []

    # Get already-tried values from experiment history
    already_tried = {}
    for param in parameters:
        tried = store.get_tried_values(surface_file, param["name"])
        if tried:
            already_tried[param["name"]] = tried

    # Generate mutation plan
    plan = create_plan(
        surface_file=surface_file,
        tier="A",  # v1: only Tier A
        parameters=parameters,
        already_tried=already_tried,
        strategy=strategy,
    )

    # Run baseline if no baseline exists
    if not baseline_store.exists() and not dry_run:
        logger.info("[PRE] Running baseline composite benchmark...")
        baseline_result = runner.run_composite()
        baseline_cqs = compute_cqs(baseline_result.metrics)
        if baseline_cqs > 0:
            baseline_store.save({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "git_commit": git.get_current_commit(),
                "metrics": {**baseline_result.metrics, "cqs": baseline_cqs},
                "surface_values": {p["name"]: p["current"] for p in parameters},
            })
            logger.info("[PRE] Baseline CQS: %.6f (tests: %d/%d)", baseline_cqs, baseline_result.passed, baseline_result.total_tests)
        else:
            logger.error("[PRE] Baseline CQS is zero — cannot proceed.")
            audit.log_session_end(session_id, {"error": "Baseline CQS zero"})
            return {"error": "Baseline CQS zero", "session_id": session_id}

    # Session tracking
    results = {
        "session_id": session_id,
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "experiments": [],
        "kept": 0,
        "reverted": 0,
        "parked": 0,
        "crashed": 0,
        "best_cqs_delta": 0.0,
        "stop_reason": "",
    }

    experiment_seq = 0

    # === MAIN LOOP ===
    while True:
        # 1. Check budget
        budget_status = budget.check()
        if budget_status.exhausted:
            results["stop_reason"] = budget_status.reason
            logger.info("[PRE] Budget exhausted: %s", budget_status.reason)
            break

        # 2. Check stop file
        if _check_stop_file(config.data_dir):
            results["stop_reason"] = "STOP file detected"
            logger.info("[PRE] STOP file detected. Ending session.")
            break

        # 3. Get next hypothesis
        hypothesis = plan.next()
        if hypothesis is None:
            results["stop_reason"] = "No more hypotheses"
            logger.info("[PRE] No more hypotheses. Ending session.")
            break

        experiment_seq += 1
        exp_id = _generate_experiment_id(surface_file, experiment_seq)

        logger.info("[PRE] Experiment %d: %s %s → %s (%s)",
                    experiment_seq, hypothesis.parameter_name,
                    hypothesis.old_value, hypothesis.new_value, hypothesis.strategy)

        # 4. Validate scope
        scope_result = validate_scope(surface_file, 1, "A", surfaces)
        if not scope_result.valid:
            logger.warning("[PRE] Scope validation failed: %s", scope_result.violations)
            budget.consume_experiment(success=False)
            continue

        # 5. Validate range
        range_result = validate_range(
            hypothesis.parameter_name,
            hypothesis.new_value,
            [{"name": p["name"], "range_min": p["range_min"],
              "range_max": p["range_max"], "type": p.get("type", "float")}
             for p in parameters],
        )
        if not range_result.valid:
            logger.warning("[PRE] Range validation failed: %s", range_result.violations)
            budget.consume_experiment(success=False)
            continue

        if dry_run:
            logger.debug("[PRE] DRY RUN: Would edit %s: %s = %s",
                         surface_file, hypothesis.parameter_name, hypothesis.new_value)
            budget.consume_experiment(success=True)
            continue

        # 6. Snapshot baseline
        _snap_path = snapshots.snapshot(exp_id, [surface_file])

        # 7. Apply mutation
        audit.log_experiment_start(exp_id, {
            "parameter": hypothesis.parameter_name,
            "old_value": hypothesis.old_value,
            "new_value": hypothesis.new_value,
            "strategy": hypothesis.strategy,
        })

        edit_success = _apply_parameter_edit(
            surface_file, hypothesis.parameter_name,
            hypothesis.old_value, hypothesis.new_value,
        )

        if not edit_success:
            logger.warning("[PRE] Failed to apply edit. Skipping.")
            snapshots.restore(exp_id)
            snapshots.cleanup(exp_id)
            budget.consume_experiment(success=False)
            continue

        # 8. Git commit
        git_result = git.commit_experiment(
            exp_id,
            f"{hypothesis.parameter_name}: {hypothesis.old_value} → {hypothesis.new_value}",
            [surface_file],
        )

        if not git_result.success:
            logger.warning("[PRE] Git commit failed: %s", git_result.error)
            snapshots.restore(exp_id)
            snapshots.cleanup(exp_id)
            budget.consume_experiment(success=False)
            continue

        # 9. Run benchmarks
        logger.info("[PRE] Running composite benchmark...")
        bench_result = runner.run_composite()

        if not bench_result.success and bench_result.total_tests == 0:
            # Crash — revert
            logger.error("[PRE] Benchmark crashed. Reverting.")
            git.revert_last_commit()
            snapshots.restore(exp_id)
            snapshots.cleanup(exp_id)

            audit.log_experiment_complete(
                exp_id, "crash", "rejected", "Benchmark crashed",
                0.0, bench_result.metrics,
            )
            store.append({
                "experiment_id": exp_id, "session_id": session_id,
                "surface_file": surface_file, "tier": "A",
                "hypothesis": {"parameter_name": hypothesis.parameter_name,
                               "old_value": hypothesis.old_value,
                               "new_value": hypothesis.new_value,
                               "strategy": hypothesis.strategy},
                "decision": "crash", "status": "rejected",
                "rationale": "Benchmark crashed",
                "cqs_delta": 0.0,
            })
            results["crashed"] += 1
            budget.consume_experiment(success=False)
            continue

        # 10. Capture metrics and evaluate
        baseline = baseline_store.load()
        baseline_cqs = baseline["metrics"]["cqs"] if baseline else 0.0
        experiment_cqs = compute_cqs(bench_result.metrics)
        guardrail_violations = check_guardrails(bench_result.metrics)

        # 11. Decide
        decision = decide(
            baseline_cqs=baseline_cqs,
            experiment_cqs=experiment_cqs,
            guardrail_violations=guardrail_violations,
            diff_lines=1,
            tier="A",
        )

        cqs_delta = experiment_cqs - baseline_cqs

        logger.info("[PRE] CQS: %.6f → %.6f (delta=%+.6f) → %s",
                    baseline_cqs, experiment_cqs, cqs_delta, decision.action.upper())

        # 12. Execute decision
        if decision.action == "keep":
            # Update baseline
            baseline_store.save({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "git_commit": git.get_current_commit(),
                "metrics": {**bench_result.metrics, "cqs": experiment_cqs},
                "surface_values": {
                    **(baseline.get("surface_values", {}) if baseline else {}),
                    hypothesis.parameter_name: hypothesis.new_value,
                },
            })
            results["kept"] += 1
            if cqs_delta > results["best_cqs_delta"]:
                results["best_cqs_delta"] = cqs_delta
            budget.consume_experiment(success=True)

        elif decision.action == "revert":
            git.revert_last_commit()
            snapshots.restore(exp_id)
            results["reverted"] += 1
            budget.consume_experiment(success=False)

        elif decision.action == "park":
            # Keep the commit but don't update baseline
            results["parked"] += 1
            budget.consume_experiment(success=True)

        snapshots.cleanup(exp_id)

        # 13. Log
        audit.log_experiment_complete(
            exp_id, decision.action, decision.status, decision.rationale,
            cqs_delta, bench_result.metrics,
        )
        store.append({
            "experiment_id": exp_id, "session_id": session_id,
            "surface_file": surface_file, "tier": "A",
            "hypothesis": {"parameter_name": hypothesis.parameter_name,
                           "old_value": hypothesis.old_value,
                           "new_value": hypothesis.new_value,
                           "strategy": hypothesis.strategy,
                           "reasoning": hypothesis.reasoning},
            "baseline_cqs": baseline_cqs,
            "experiment_cqs": experiment_cqs,
            "cqs_delta": cqs_delta,
            "decision": decision.action,
            "status": decision.status,
            "rationale": decision.rationale,
            "git_commit": git.get_current_commit(),
            "diff_lines_changed": 1,
            "benchmark_suite": suite_name,
            "benchmark_duration_seconds": bench_result.duration_seconds,
            "guardrail_violations": decision.guardrail_violations,
            "metrics": bench_result.metrics,
        })

        results["experiments"].append(exp_id)

        # Update hypothesis old_value for subsequent experiments
        # (so the next edit replaces the NEW current value)
        if decision.action == "keep":
            for h in plan.hypotheses:
                if h.parameter_name == hypothesis.parameter_name:
                    # HypothesisPlan is a regular (non-frozen) dataclass,
                    # so direct attribute assignment is safe.
                    h.old_value = hypothesis.new_value

    # === END LOOP ===

    results["end_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results["total_experiments"] = len(results["experiments"])

    audit.log_session_end(session_id, results)

    # Log summary
    logger.info("=" * 60)
    logger.info("[PRE] Session Complete: %s", session_id)
    logger.info("  Total experiments: %d", results['total_experiments'])
    logger.info("  Kept: %d", results['kept'])
    logger.info("  Reverted: %d", results['reverted'])
    logger.info("  Parked: %d", results['parked'])
    logger.info("  Crashed: %d", results['crashed'])
    logger.info("  Best CQS delta: %+.6f", results['best_cqs_delta'])
    logger.info("  Stop reason: %s", results['stop_reason'])
    logger.info("=" * 60)

    return results
