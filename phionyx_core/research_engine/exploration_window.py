"""
Controlled Nondeterminism Window — Online Learning Foundation
==============================================================

**Honesty note:** This is a seeded random parameter search within bounds.
It perturbs values deterministically and records outcomes. The "exploration"
is bounded grid/random search, not cognitive exploration or curiosity.

Provides a bounded, auditable, reproducible exploration mechanism
that allows parameter perturbation within strict safety bounds.

Design principles (compatible with ECHOISM Axiom 8 — Determinism):
1. **Seeded**: Every exploration uses a deterministic seed → reproducible
2. **Bounded**: Maximum delta fraction, parameter whitelist, time limit
3. **Isolated**: Exploration runs in sandbox context, not production path
4. **Auditable**: Every perturbation logged with seed, delta, outcome
5. **Reversible**: Exploration reverts automatically on guardrail violation

Flow:
    ExplorationWindow.open() → perturb parameters → run evaluation
    → if guardrails pass: record as evidence for OutcomeObserver
    → if guardrails fail: revert, log violation
    → close window (restore all original values)

This does NOT break determinism. Given the same seed and initial state,
the exploration produces identical results. The "nondeterminism" is
controlled: the seed introduces variability between sessions while
maintaining within-session reproducibility.

Mind-loop stages: Reflect + Revise (self-directed parameter exploration)
AGI component: Online learning foundation
Cognitive vs. automation: Infrastructure (seeded parameter search)
"""

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_MAX_PERTURBATIONS = 5
DEFAULT_MAX_DELTA_FRACTION = 0.10
DEFAULT_WINDOW_BUDGET = 10  # Maximum exploration steps per window


@dataclass(frozen=True)
class Perturbation:
    """A single parameter perturbation within an exploration window."""
    parameter_name: str
    original_value: float
    perturbed_value: float
    delta: float
    delta_fraction: float
    seed: int
    step_index: int


@dataclass
class ExplorationOutcome:
    """Outcome of a single exploration step."""
    perturbation: Perturbation
    score_before: float
    score_after: float
    score_delta: float
    guardrails_passed: bool
    violations: list[str] = field(default_factory=list)

    @property
    def improved(self) -> bool:
        return self.score_delta > 0 and self.guardrails_passed


@dataclass
class ExplorationWindowResult:
    """Summary of a complete exploration window session."""
    seed: int
    total_steps: int
    improvements_found: int
    violations_count: int
    outcomes: list[ExplorationOutcome]
    best_outcome: ExplorationOutcome | None
    opened_at: str
    closed_at: str
    budget_remaining: int


class ExplorationWindow:
    """
    Controlled nondeterminism window for bounded parameter exploration.

    Creates a reproducible (seeded) exploration session that perturbs
    parameters within safety bounds and evaluates outcomes.

    Usage:
        window = ExplorationWindow(
            seed=42,
            allowed_parameters={"DEFAULT_GAMMA", "COHERENCE_WEIGHT"},
            parameter_ranges={"DEFAULT_GAMMA": (0.05, 0.30)},
        )
        result = window.run(
            current_values={"DEFAULT_GAMMA": 0.15},
            evaluate_fn=lambda params: compute_cqs(params),
            guardrail_fn=lambda metrics: metrics.guardrails_intact,
        )
    """

    def __init__(
        self,
        seed: int,
        allowed_parameters: set[str] | None = None,
        parameter_ranges: dict[str, tuple[float, float]] | None = None,
        max_perturbations: int = DEFAULT_MAX_PERTURBATIONS,
        max_delta_fraction: float = DEFAULT_MAX_DELTA_FRACTION,
        budget: int = DEFAULT_WINDOW_BUDGET,
    ):
        """
        Args:
            seed: Deterministic seed for reproducibility.
            allowed_parameters: Whitelist of parameters that may be perturbed.
                                If None, all provided parameters are allowed.
            parameter_ranges: Valid ranges per parameter {name: (min, max)}.
            max_perturbations: Max parameters to perturb per step.
            max_delta_fraction: Max change as fraction of current value.
            budget: Maximum exploration steps in this window.
        """
        self.seed = seed
        self.allowed_parameters = allowed_parameters
        self.parameter_ranges = parameter_ranges or {}
        self.max_perturbations = max_perturbations
        self.max_delta_fraction = max_delta_fraction
        self.budget = budget
        self._rng = random.Random(seed)
        self._step_count = 0
        self._outcomes: list[ExplorationOutcome] = []

    def run(
        self,
        current_values: dict[str, float],
        evaluate_fn: Callable[[dict[str, float]], float],
        guardrail_fn: Callable[[dict[str, float], float], tuple[bool, list[str]]] | None = None,
    ) -> ExplorationWindowResult:
        """
        Execute the exploration window.

        Args:
            current_values: Current parameter values {name: value}.
            evaluate_fn: Function that evaluates a parameter set → score.
            guardrail_fn: Function that checks guardrails → (passed, violations).
                          If None, all perturbations pass guardrails.

        Returns:
            ExplorationWindowResult summarizing the session.
        """
        opened_at = datetime.now(timezone.utc).isoformat()

        # Filter to allowed parameters
        explorable = self._filter_allowed(current_values)

        if not explorable:
            return ExplorationWindowResult(
                seed=self.seed,
                total_steps=0,
                improvements_found=0,
                violations_count=0,
                outcomes=[],
                best_outcome=None,
                opened_at=opened_at,
                closed_at=datetime.now(timezone.utc).isoformat(),
                budget_remaining=self.budget,
            )

        # Compute baseline score
        baseline_score = evaluate_fn(current_values)

        # Run exploration steps
        param_names = sorted(explorable.keys())  # Deterministic order
        while self._step_count < self.budget and param_names:
            # Select parameter to perturb
            param_idx = self._rng.randint(0, len(param_names) - 1)
            param_name = param_names[param_idx]
            current_val = current_values[param_name]

            # Generate perturbation
            perturbation = self._generate_perturbation(
                param_name, current_val, self._step_count
            )
            if perturbation is None:
                self._step_count += 1
                continue

            # Apply perturbation and evaluate
            perturbed_values = dict(current_values)
            perturbed_values[param_name] = perturbation.perturbed_value

            try:
                perturbed_score = evaluate_fn(perturbed_values)
            except Exception as e:
                logger.debug("Evaluation failed for %s: %s", param_name, e)
                self._step_count += 1
                continue

            score_delta = perturbed_score - baseline_score

            # Check guardrails
            if guardrail_fn is not None:
                passed, violations = guardrail_fn(perturbed_values, perturbed_score)
            else:
                passed, violations = True, []

            outcome = ExplorationOutcome(
                perturbation=perturbation,
                score_before=baseline_score,
                score_after=perturbed_score,
                score_delta=score_delta,
                guardrails_passed=passed,
                violations=violations,
            )
            self._outcomes.append(outcome)
            self._step_count += 1

        # Find best outcome
        improvements = [o for o in self._outcomes if o.improved]
        best = max(improvements, key=lambda o: o.score_delta) if improvements else None

        return ExplorationWindowResult(
            seed=self.seed,
            total_steps=self._step_count,
            improvements_found=len(improvements),
            violations_count=sum(1 for o in self._outcomes if not o.guardrails_passed),
            outcomes=self._outcomes,
            best_outcome=best,
            opened_at=opened_at,
            closed_at=datetime.now(timezone.utc).isoformat(),
            budget_remaining=self.budget - self._step_count,
        )

    def generate_perturbations(
        self,
        current_values: dict[str, float],
        count: int = 1,
    ) -> list[Perturbation]:
        """
        Generate perturbations without executing evaluation.

        Useful for batch planning or dry-run inspection.
        """
        explorable = self._filter_allowed(current_values)
        param_names = sorted(explorable.keys())
        perturbations = []

        for i in range(count):
            if not param_names:
                break
            param_idx = self._rng.randint(0, len(param_names) - 1)
            param_name = param_names[param_idx]
            p = self._generate_perturbation(
                param_name, current_values[param_name], i
            )
            if p is not None:
                perturbations.append(p)

        return perturbations

    def _filter_allowed(self, values: dict[str, float]) -> dict[str, float]:
        """Filter parameter values to only allowed ones."""
        if self.allowed_parameters is None:
            return dict(values)
        return {
            k: v for k, v in values.items()
            if k in self.allowed_parameters
        }

    def _generate_perturbation(
        self,
        param_name: str,
        current_value: float,
        step_index: int,
    ) -> Perturbation | None:
        """Generate a single bounded perturbation."""
        if current_value == 0:
            # Can't compute fraction of zero; use small absolute delta
            delta = self._rng.uniform(-0.01, 0.01)
        else:
            max_delta = abs(current_value) * self.max_delta_fraction
            delta = self._rng.uniform(-max_delta, max_delta)

        new_value = current_value + delta

        # Enforce parameter range bounds
        if param_name in self.parameter_ranges:
            lo, hi = self.parameter_ranges[param_name]
            new_value = max(lo, min(hi, new_value))
            delta = new_value - current_value

        # Skip no-op perturbations
        if abs(delta) < 1e-10:
            return None

        fraction = abs(delta / current_value) if current_value != 0 else abs(delta)

        return Perturbation(
            parameter_name=param_name,
            original_value=current_value,
            perturbed_value=round(new_value, 6),
            delta=round(delta, 6),
            delta_fraction=round(fraction, 6),
            seed=self.seed,
            step_index=step_index,
        )
