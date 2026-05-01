"""Mutation planner — deterministic hypothesis generation.

v1 uses grid search and random search. NO LLM-based hypothesis generation.
Karpathy observed: "agents' ideas are bad out of the box."
Deterministic strategies produce more systematic, interpretable results.

The LLM role in v1 is limited to interpreting results, not generating hypotheses.
"""
import random
from dataclasses import dataclass, field


@dataclass
class HypothesisPlan:
    parameter_name: str
    surface_file: str
    tier: str
    old_value: float
    new_value: float
    strategy: str  # "grid", "random", "boundary"
    reasoning: str


def _frange(start: float, stop: float, step: float) -> list[float]:
    """Generate float range, avoiding floating point issues."""
    result = []
    current = start
    while current <= stop + step * 0.01:
        result.append(round(current, 10))
        current += step
    return result


def generate_grid_hypotheses(
    param_name: str,
    surface_file: str,
    tier: str,
    current_value: float,
    range_min: float,
    range_max: float,
    step: float,
    already_tried: set[float] | None = None,
) -> list[HypothesisPlan]:
    """Generate hypotheses by systematic grid search.

    Tries every value in [range_min, range_max] with given step,
    skipping the current value and already-tried values.
    Orders by distance from current value (try nearby first).
    """
    if already_tried is None:
        already_tried = set()

    candidates = _frange(range_min, range_max, step)
    # Remove current value and already tried
    candidates = [
        v for v in candidates
        if abs(v - current_value) > step * 0.01 and v not in already_tried
    ]
    # Sort by distance from current (try nearby first)
    candidates.sort(key=lambda v: abs(v - current_value))

    return [
        HypothesisPlan(
            parameter_name=param_name,
            surface_file=surface_file,
            tier=tier,
            old_value=current_value,
            new_value=v,
            strategy="grid",
            reasoning=(
                f"Grid search: try {param_name}={v} "
                f"(delta={v - current_value:+.4f} from current {current_value})"
            ),
        )
        for v in candidates
    ]


def generate_random_hypotheses(
    param_name: str,
    surface_file: str,
    tier: str,
    current_value: float,
    range_min: float,
    range_max: float,
    count: int = 5,
    seed: int | None = None,
) -> list[HypothesisPlan]:
    """Generate hypotheses by random sampling within range."""
    rng = random.Random(seed)

    return [
        HypothesisPlan(
            parameter_name=param_name,
            surface_file=surface_file,
            tier=tier,
            old_value=current_value,
            new_value=round(rng.uniform(range_min, range_max), 4),
            strategy="random",
            reasoning=f"Random exploration of {param_name} within [{range_min}, {range_max}]",
        )
        for _ in range(count)
    ]


def generate_boundary_hypotheses(
    param_name: str,
    surface_file: str,
    tier: str,
    current_value: float,
    range_min: float,
    range_max: float,
    step: float,
) -> list[HypothesisPlan]:
    """Generate hypotheses at boundary values and extremes.

    Tests: min, max, min+step, max-step, midpoint.
    Boundary testing reveals if the parameter has monotonic or non-monotonic effects.
    """
    midpoint = round((range_min + range_max) / 2, 10)
    candidates = [
        range_min,
        range_min + step,
        midpoint,
        range_max - step,
        range_max,
    ]
    # Remove current and duplicates
    seen: set[float] = set()
    unique = []
    for v in candidates:
        v = round(v, 10)
        if abs(v - current_value) > step * 0.01 and v not in seen:
            seen.add(v)
            unique.append(v)

    return [
        HypothesisPlan(
            parameter_name=param_name,
            surface_file=surface_file,
            tier=tier,
            old_value=current_value,
            new_value=v,
            strategy="boundary",
            reasoning=f"Boundary test: {param_name}={v} (min={range_min}, max={range_max})",
        )
        for v in unique
    ]


@dataclass
class MutationPlan:
    """Complete mutation plan for an experiment session."""
    surface_file: str
    hypotheses: list[HypothesisPlan] = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return len(self.hypotheses)

    def next(self) -> HypothesisPlan | None:
        if self.hypotheses:
            return self.hypotheses.pop(0)
        return None


def _interleave(per_param: list[list[HypothesisPlan]]) -> list[HypothesisPlan]:
    """Round-robin interleave hypothesis lists from different parameters.

    Ensures all parameters get explored even with small experiment budgets.
    Example: [A1,A2,A3], [B1,B2] -> [A1,B1,A2,B2,A3]
    """
    result: list[HypothesisPlan] = []
    max_len = max((len(h) for h in per_param), default=0)
    for i in range(max_len):
        for param_hyps in per_param:
            if i < len(param_hyps):
                result.append(param_hyps[i])
    return result


def create_plan(
    surface_file: str,
    tier: str,
    parameters: list[dict],
    already_tried: dict[str, set[float]] | None = None,
    strategy: str = "grid",  # "grid", "random", "boundary", "all"
    seed: int | None = None,
) -> MutationPlan:
    """Create a mutation plan for an experiment session.

    Generates hypotheses for all parameters in the surface,
    using the specified strategy. Hypotheses are interleaved
    across parameters (round-robin) so each parameter gets
    explored even with limited experiment budgets.
    """
    if already_tried is None:
        already_tried = {}

    per_param: list[list[HypothesisPlan]] = []

    for param in parameters:
        param_tried = already_tried.get(param["name"], set())
        param_hyps: list[HypothesisPlan] = []

        if strategy in ("grid", "all"):
            param_hyps.extend(generate_grid_hypotheses(
                param["name"], surface_file, tier,
                param["current"], param["range_min"], param["range_max"],
                param["step"], param_tried,
            ))

        if strategy in ("boundary", "all"):
            param_hyps.extend(generate_boundary_hypotheses(
                param["name"], surface_file, tier,
                param["current"], param["range_min"], param["range_max"],
                param["step"],
            ))

        if strategy in ("random", "all"):
            param_hyps.extend(generate_random_hypotheses(
                param["name"], surface_file, tier,
                param["current"], param["range_min"], param["range_max"],
                seed=seed,
            ))

        per_param.append(param_hyps)

    interleaved = _interleave(per_param)
    return MutationPlan(surface_file=surface_file, hypotheses=interleaved)
