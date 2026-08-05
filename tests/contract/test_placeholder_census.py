"""A passing test that asserts nothing is worse than a missing one.

`assert True  # Placeholder` reports green. A skipped stub at least says it did
not run; a placeholder claims it ran and found nothing wrong. Counted on
2026-08-02, `tests/` held 4214 test functions and 179 placeholders — a `pass`
body, an `assert True`, or nothing but a docstring. After all four GDPR erasure
paths were written the same day, and after OD-14: 4299 and 121.

Most sit in ungated directories, which is why nobody had to look at them. Two
places matter:

- **`tests/regression`** is gated in CI and was 21/37; it is 16 after the five
  GDPR ones were written. The remaining placeholder names are still the
  project's own guarantees: `test_scenario_signature_tampering_detection`,
  `test_replay_determinism`, `test_policy_evaluation_consistency`.
- **GDPR right-to-erasure** had four test paths and none executed anything.
  All four were written on 2026-08-02 and the class that tracked them was
  deleted from this file, having fired once and done its job:
  `test_privacy/test_forget_right_execution.py` (12 tests),
  `regression/test_gdpr_regression.py` (6 real + 5 strict xfail),
  `test_privacy/test_gdpr_data_subject_rights.py` Article 17 (3 real + 4
  strict xfail) and `integration/core_bridge/test_gdpr_endpoints.py`
  (1 real + 5 strict xfail). The remaining concentration is
  `test_privacy` at 50/70 — Articles 13-16 and 18-22 of the same file, whose
  capabilities largely do not exist — and `test_school` at 52/52.

This file does not fix any of that. It pins the count so it cannot grow
quietly.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

TESTS_ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Measured 2026-08-02 at 179, lowered the same day to 121 as the four GDPR
#: erasure paths, the rest of the data-subject-rights file and then the 21
#: unconditionally-skipped stubs (OD-14) were written. Lower it whenever
#: placeholders are replaced by real assertions; raising it is a decision,
#: not a fix.
PLACEHOLDER_BUDGET = 121

#: Per-directory ceilings for the two that matter. `regression` is in CI, so a
#: placeholder added there ships as a green gate step.
GATED_BUDGETS = {"regression": 16, "integration": 1, "unit": 15, "test_contracts": 0}


def _is_placeholder(node: ast.AST) -> bool:
    """A body of `pass`, `assert True`, or only a docstring."""
    body = [
        stmt for stmt in node.body  # type: ignore[attr-defined]
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
    ]
    if not body:
        return True
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if (isinstance(stmt, ast.Assert) and isinstance(stmt.test, ast.Constant)
                and stmt.test.value is True):
            continue
        return False
    return True


def _census() -> dict[str, tuple[int, int]]:
    counts: dict[str, tuple[int, int]] = {}
    for directory in sorted(p for p in TESTS_ROOT.iterdir()
                            if p.is_dir() and not p.name.startswith("__")):
        total = placeholders = 0
        for path in directory.rglob("*.py"):
            if "__pycache__" in str(path):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name.startswith("test_")):
                    total += 1
                    placeholders += _is_placeholder(node)
        if total:
            counts[directory.name] = (total, placeholders)
    return counts


class TestThePlaceholderCountDoesNotGrow:
    def test_the_repository_total_is_within_budget(self) -> None:
        census = _census()
        placeholders = sum(p for _, p in census.values())

        assert placeholders <= PLACEHOLDER_BUDGET, (
            f"{placeholders} placeholder tests, budget {PLACEHOLDER_BUDGET}. "
            "A test whose body is `pass` or `assert True` reports green while "
            "measuring nothing. If these are new, write the assertion; if you "
            "are deliberately adding a stub, skip it so it does not claim to "
            "have passed.")

    @pytest.mark.parametrize("directory,budget", sorted(GATED_BUDGETS.items()))
    def test_a_gated_directory_does_not_gain_placeholders(
        self, directory: str, budget: int
    ) -> None:
        """These run in CI, so a placeholder here ships as a green gate step."""
        census = _census()
        if directory not in census:
            pytest.skip(f"{directory} holds no test functions")
        _, placeholders = census[directory]

        assert placeholders <= budget, (
            f"tests/{directory} has {placeholders} placeholders, budget {budget}")


class TestNoTestIsUnconditionallySkipped:
    """The sibling of the placeholder budget, added 2026-08-02 (OD-14).

    A placeholder claims it ran. An unconditional `@pytest.mark.skip` is more
    honest — it says it did not — but a permanent one on a test named for a
    security property is a guarantee nobody checks, and the name still reads
    like coverage in any listing of the suite.

    There were 21. Every reason followed one template: "X tests require Y
    mechanisms". Checked one at a time, eleven of those mechanisms existed —
    TimeManager, the decay formulas, EnvelopeValidator's four checks,
    SubagentChainV0's role invariants, `compute_handoff_signing_body` — and
    those tests were written. The nine genuine absences became
    `xfail(strict=True)` naming what is missing, so implementing one fails the
    build until the claim is revisited.

    `skipif` is untouched: skipping on a missing optional dependency or a
    platform is a real condition, evaluated every run.
    """

    def test_no_unconditional_skip_remains(self) -> None:
        offenders = []
        for path in sorted(TESTS_ROOT.rglob("test_*.py")):
            if "__pycache__" in str(path):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.ClassDef)):
                    continue
                for decorator in node.decorator_list:
                    rendered = ast.unparse(decorator)
                    if "mark.skip" in rendered and "skipif" not in rendered:
                        offenders.append(
                            f"{path.relative_to(TESTS_ROOT)}::{node.name}")

        assert offenders == [], (
            f"{len(offenders)} unconditionally-skipped tests: {offenders}. A "
            "permanent skip is a test name doing the work of a test. If the "
            "capability exists, write the assertion; if it does not, use "
            "xfail(strict=True) so the build tells you when it arrives. Use "
            "skipif for a real condition — an optional dependency, a platform.")
