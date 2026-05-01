"""
Outcome Observer — PRE → LearningUpdate Bridge
================================================

**Honesty note:** This is a threshold-based rule application module, not
outcome-driven learning. It counts consistent experiment decisions and
generates proposals when a fixed threshold (3+) is reached. There is no
belief update or model revision — it applies a counting rule.

Observes PRE experiment outcomes and generates LearningUpdate proposals
when sufficient evidence accumulates for a parameter change.

Flow:
    PRE ExperimentRecord → OutcomeObserver.observe() → evidence accumulation
    → when 3+ consistent keep decisions → generate LearningUpdate
    → feed to LearningGateService for zone classification + approval

This is the "bridge layer" between research experimentation and
parameter learning. Without it, PRE experiments and the learning gate
are decoupled.

Mind-loop stages: Reflect + Revise (outcome-based learning)
AGI component: Self-directed parameter revision
Cognitive vs. automation: Infrastructure (threshold-based proposal generation)
"""

import logging
from dataclasses import dataclass, field

from phionyx_core.contracts.v4.learning_update import (
    LearningGateDecision,
    LearningUpdate,
)
from phionyx_core.research_engine.schemas import ExperimentRecord

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

MIN_CONSISTENT_EXPERIMENTS = 3
CQS_DELTA_THRESHOLD = 0.005
MAX_DELTA_FRACTION = 0.20


@dataclass
class ParameterEvidence:
    """Accumulated evidence for a single parameter."""
    parameter_name: str
    surface_file: str
    tier: str
    experiments: list[dict] = field(default_factory=list)

    @property
    def keep_count(self) -> int:
        return sum(1 for e in self.experiments if e["decision"] == "keep")

    @property
    def consistent_direction(self) -> bool:
        """All kept experiments propose same direction of change."""
        kept = [e for e in self.experiments if e["decision"] == "keep"]
        if len(kept) < 2:
            return len(kept) == 1
        directions = [e["cqs_delta"] > 0 for e in kept]
        return all(directions) or not any(directions)

    @property
    def avg_cqs_delta(self) -> float:
        kept = [e for e in self.experiments if e["decision"] == "keep"]
        if not kept:
            return 0.0
        return sum(e["cqs_delta"] for e in kept) / len(kept)

    @property
    def best_value(self) -> float | None:
        """Best proposed value from kept experiments (highest CQS delta)."""
        kept = [e for e in self.experiments if e["decision"] == "keep"]
        if not kept:
            return None
        best = max(kept, key=lambda e: e["cqs_delta"])
        return best["proposed_value"]

    @property
    def current_value(self) -> float | None:
        """Current value from the most recent experiment."""
        if not self.experiments:
            return None
        return self.experiments[-1]["current_value"]


@dataclass
class OutcomeObserverResult:
    """Result of processing a batch of experiment records."""
    total_observed: int
    parameters_tracked: int
    updates_proposed: int
    proposed_updates: list[LearningUpdate]


class OutcomeObserver:
    """
    Observes PRE experiment outcomes and proposes LearningUpdates.

    Accumulates evidence per parameter. When a parameter has enough
    consistent positive experiments, generates a LearningUpdate proposal
    for the learning gate.

    Usage:
        observer = OutcomeObserver()
        for record in experiment_records:
            observer.observe(record)
        result = observer.propose_updates()
        for update in result.proposed_updates:
            gate_service.evaluate_updates([update])
    """

    def __init__(
        self,
        min_experiments: int = MIN_CONSISTENT_EXPERIMENTS,
        cqs_delta_threshold: float = CQS_DELTA_THRESHOLD,
        max_delta_fraction: float = MAX_DELTA_FRACTION,
        tier_zone_map: dict[str, str] | None = None,
    ):
        """
        Args:
            min_experiments: Minimum consistent keep decisions before proposing.
            cqs_delta_threshold: Minimum |CQS delta| to consider significant.
            max_delta_fraction: Maximum allowed change as fraction of current.
            tier_zone_map: Mapping from tier to boundary zone.
        """
        self.min_experiments = min_experiments
        self.cqs_delta_threshold = cqs_delta_threshold
        self.max_delta_fraction = max_delta_fraction
        self.tier_zone_map = tier_zone_map or {
            "A": "adaptive",
            "B": "gated",
            "C": "gated",
            "D": "immutable",
        }
        self._evidence: dict[str, ParameterEvidence] = {}
        self._proposed_params: set = set()

    def observe(self, record: ExperimentRecord) -> None:
        """
        Record an experiment outcome for evidence accumulation.

        Args:
            record: Completed PRE experiment record.
        """
        param_name = record.hypothesis.parameter_name
        if param_name not in self._evidence:
            self._evidence[param_name] = ParameterEvidence(
                parameter_name=param_name,
                surface_file=record.surface_file,
                tier=record.tier,
            )

        self._evidence[param_name].experiments.append({
            "experiment_id": record.experiment_id,
            "decision": record.decision,
            "cqs_delta": record.cqs_delta,
            "baseline_cqs": record.baseline_cqs,
            "experiment_cqs": record.experiment_cqs,
            "current_value": record.hypothesis.old_value,
            "proposed_value": record.hypothesis.new_value,
            "guardrail_passed": len(record.guardrail_violations) == 0,
            "timestamp": record.timestamp,
        })

    def observe_batch(self, records: list[ExperimentRecord]) -> None:
        """Observe multiple experiment records."""
        for record in records:
            self.observe(record)

    def propose_updates(self) -> OutcomeObserverResult:
        """
        Generate LearningUpdate proposals for parameters with sufficient evidence.

        A proposal is generated when:
        1. Parameter has >= min_experiments "keep" decisions
        2. All kept experiments agree on direction (consistent)
        3. Average |CQS delta| exceeds threshold
        4. All experiments passed guardrails
        5. Parameter has not already been proposed in this session

        Returns:
            OutcomeObserverResult with proposed LearningUpdates.
        """
        proposals: list[LearningUpdate] = []

        for param_name, evidence in sorted(self._evidence.items()):
            if param_name in self._proposed_params:
                continue

            if not self._is_ready(evidence):
                continue

            update = self._create_update(evidence)
            if update is not None:
                proposals.append(update)
                self._proposed_params.add(param_name)

        return OutcomeObserverResult(
            total_observed=sum(
                len(e.experiments) for e in self._evidence.values()
            ),
            parameters_tracked=len(self._evidence),
            updates_proposed=len(proposals),
            proposed_updates=proposals,
        )

    def get_evidence(self, parameter_name: str) -> ParameterEvidence | None:
        """Get accumulated evidence for a parameter."""
        return self._evidence.get(parameter_name)

    def get_all_evidence(self) -> dict[str, ParameterEvidence]:
        """Get all accumulated evidence."""
        return dict(self._evidence)

    def reset(self) -> None:
        """Clear all accumulated evidence and proposals."""
        self._evidence.clear()
        self._proposed_params.clear()

    def _is_ready(self, evidence: ParameterEvidence) -> bool:
        """Check if evidence meets proposal criteria."""
        if evidence.keep_count < self.min_experiments:
            return False

        if not evidence.consistent_direction:
            logger.debug(
                "Parameter %s has inconsistent direction, skipping",
                evidence.parameter_name,
            )
            return False

        if abs(evidence.avg_cqs_delta) < self.cqs_delta_threshold:
            logger.debug(
                "Parameter %s avg CQS delta %.6f below threshold %.6f",
                evidence.parameter_name,
                evidence.avg_cqs_delta,
                self.cqs_delta_threshold,
            )
            return False

        # All kept experiments must have passed guardrails
        kept = [e for e in evidence.experiments if e["decision"] == "keep"]
        if not all(e["guardrail_passed"] for e in kept):
            return False

        return True

    def _create_update(self, evidence: ParameterEvidence) -> LearningUpdate | None:
        """Create a LearningUpdate from accumulated evidence."""
        current = evidence.current_value
        proposed = evidence.best_value

        if current is None or proposed is None:
            return None

        # Compute delta
        try:
            delta = float(proposed) - float(current)
        except (TypeError, ValueError):
            delta = None

        # Check max delta fraction
        if delta is not None and current != 0:
            fraction = abs(delta) / abs(float(current))
            if fraction > self.max_delta_fraction:
                logger.debug(
                    "Parameter %s delta fraction %.2f exceeds max %.2f, capping",
                    evidence.parameter_name,
                    fraction,
                    self.max_delta_fraction,
                )
                # Cap the proposed value
                direction = 1.0 if delta > 0 else -1.0
                proposed = float(current) + direction * abs(float(current)) * self.max_delta_fraction

        # Build evidence entries
        kept = [e for e in evidence.experiments if e["decision"] == "keep"]
        evidence_entries = [
            {
                "experiment_id": e["experiment_id"],
                "cqs_before": e["baseline_cqs"],
                "cqs_after": e["experiment_cqs"],
                "cqs_delta": e["cqs_delta"],
                "guardrail_passed": e["guardrail_passed"],
                "timestamp": e["timestamp"],
            }
            for e in kept
        ]

        # Resolve boundary zone from tier
        zone = self.tier_zone_map.get(evidence.tier, "gated")

        return LearningUpdate(
            target_parameter=evidence.parameter_name,
            current_value=current,
            proposed_value=proposed,
            delta=delta,
            boundary_zone=zone,
            gate_decision=LearningGateDecision.PENDING,
            gate_reason="Proposed by OutcomeObserver from PRE evidence",
            source_module="outcome_observer",
            evidence=evidence_entries,
            min_experiments=self.min_experiments,
            cqs_delta_threshold=self.cqs_delta_threshold,
            rollback_procedure="auto",
            metadata={
                "surface_file": evidence.surface_file,
                "tier": evidence.tier,
                "keep_count": evidence.keep_count,
                "avg_cqs_delta": evidence.avg_cqs_delta,
            },
        )
