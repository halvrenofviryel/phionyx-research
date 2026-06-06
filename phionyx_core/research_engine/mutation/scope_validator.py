"""Scope validator — enforces Tier A/B/C/D edit permissions."""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    violations: List[str]


def validate_scope(
    file_path: str,
    diff_lines: int,
    tier: str,
    surfaces: List[dict],  # Parsed from surfaces.yaml
) -> ValidationResult:
    """Validate that the proposed edit is within scope.

    Rules:
    - File must be listed in surfaces
    - File's tier must match or be more permissive than declared
    - Diff size must be within tier limits
    - Tier D files cannot be edited at all
    - Tier C files can only have proposals (no actual edits)
    """
    violations = []

    # Find the surface definition for this file
    surface = None
    for s in surfaces:
        if s["file"] == file_path:
            surface = s
            break

    if surface is None:
        violations.append(f"File '{file_path}' is not listed in surfaces.yaml")
        return ValidationResult(valid=False, violations=violations)

    # Check tier
    surface_tier = surface.get("tier", "D")

    if surface_tier == "D":
        violations.append(f"File '{file_path}' is Tier D (immutable)")
        return ValidationResult(valid=False, violations=violations)

    if surface_tier == "C" and tier != "C":
        violations.append(
            f"File '{file_path}' is Tier C (proposal only), "
            f"but edit was attempted as Tier {tier}"
        )
        return ValidationResult(valid=False, violations=violations)

    # Check diff size
    max_lines = surface.get("max_lines_changed", 5)
    if diff_lines > max_lines:
        violations.append(
            f"Diff size {diff_lines} exceeds max {max_lines} "
            f"for Tier {surface_tier} surface '{file_path}'"
        )

    return ValidationResult(valid=len(violations) == 0, violations=violations)
