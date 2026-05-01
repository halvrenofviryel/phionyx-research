"""Range validator — enforces parameter safe ranges."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RangeValidationResult:
    valid: bool
    violations: list[str]


def validate_range(
    param_name: str,
    value: Any,
    surface_params: list[dict],  # List of parameter defs from surfaces.yaml
) -> RangeValidationResult:
    """Validate that a parameter value is within its declared safe range.

    Every parameter in surfaces.yaml has range_min and range_max.
    Values outside this range are rejected before any edit is applied.
    """
    violations = []

    # Find parameter definition
    param_def = None
    for p in surface_params:
        if p["name"] == param_name:
            param_def = p
            break

    if param_def is None:
        violations.append(f"Parameter '{param_name}' not found in surface definition")
        return RangeValidationResult(valid=False, violations=violations)

    range_min = param_def.get("range_min", float("-inf"))
    range_max = param_def.get("range_max", float("inf"))
    param_type = param_def.get("type", "float")

    # Type check
    if param_type == "float":
        try:
            value = float(value)
        except (TypeError, ValueError):
            violations.append(f"Parameter '{param_name}' value '{value}' is not a valid float")
            return RangeValidationResult(valid=False, violations=violations)
    elif param_type == "int":
        try:
            value = int(value)
        except (TypeError, ValueError):
            violations.append(f"Parameter '{param_name}' value '{value}' is not a valid int")
            return RangeValidationResult(valid=False, violations=violations)

    # Range check
    if value < range_min:
        violations.append(
            f"Parameter '{param_name}' value {value} < range_min {range_min}"
        )
    if value > range_max:
        violations.append(
            f"Parameter '{param_name}' value {value} > range_max {range_max}"
        )

    # Step alignment check (optional, warn only)
    step = param_def.get("step")
    if step and param_type == "float":
        offset = (value - range_min) / step
        if abs(offset - round(offset)) > 1e-9:
            # Not a violation, just a note
            pass

    return RangeValidationResult(valid=len(violations) == 0, violations=violations)


def validate_constraint(
    param_name: str,
    value: Any,
    related_params: dict[str, Any],
    constraints: list[dict],
) -> RangeValidationResult:
    """Validate cross-parameter constraints (e.g., weights must sum to 1.0)."""
    violations = []

    for constraint in constraints:
        if constraint.get("type") == "sum_equals":
            params = constraint["params"]
            target = constraint["target"]
            total = sum(
                value if p == param_name else related_params.get(p, 0.0)
                for p in params
            )
            if abs(total - target) > 1e-6:
                violations.append(
                    f"Constraint '{constraint.get('name', 'sum')}': "
                    f"sum of {params} = {total:.6f}, expected {target}"
                )

    return RangeValidationResult(valid=len(violations) == 0, violations=violations)
