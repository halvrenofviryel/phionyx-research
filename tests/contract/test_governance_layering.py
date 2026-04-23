"""Contract test: governance layering (ADR-0005).

Verifies the two non-negotiable import rules from ADR-0005:

1. ``phionyx_core/**`` must NOT import from ``phionyx_governance/``.
   Violating this reverses the core/bridge dependency direction and
   re-introduces the problem ADR-0002 solved.

2. ``phionyx_governance/**`` must NOT import from ``phionyx_bridge/``.
   ``phionyx_governance`` is a bridge-level package itself; it must
   not depend on the delivery layer (FastAPI-specific Echo Server code).

This is a static-AST gate: it parses each .py file and inspects
``Import`` / ``ImportFrom`` nodes plus string arguments to
``importlib.import_module`` calls. Docstring mentions of the forbidden
package are *not* flagged — only real imports.

Related: ``docs/adr/0005-governance-layering.md``.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        parts = path.parts
        if "__pycache__" in parts or "archive" in parts:
            continue
        yield path


def _module_top(name: str | None) -> str:
    return (name or "").split(".", 1)[0]


class _ImportCollector(ast.NodeVisitor):
    def __init__(self):
        self.imports: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import):  # noqa: N802
        for alias in node.names:
            self.imports.append((node.lineno, _module_top(alias.name)))

    def visit_ImportFrom(self, node: ast.ImportFrom):  # noqa: N802
        if node.module is not None:
            self.imports.append((node.lineno, _module_top(node.module)))

    def visit_Call(self, node: ast.Call):  # noqa: N802
        # Catch importlib.import_module("phionyx_X.…")
        func_name = (
            getattr(node.func, "attr", None)
            or getattr(node.func, "id", None)
        )
        if func_name == "import_module" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                self.imports.append((node.lineno, _module_top(first.value)))
        self.generic_visit(node)


def _find_import_violations(scan_root: Path, forbidden_top: str) -> list[tuple[Path, int, str]]:
    """Return (file, line_no, imported_module) for every real import of
    ``forbidden_top`` inside ``scan_root``."""
    violations: list[tuple[Path, int, str]] = []
    for path in _iter_python_files(scan_root):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        collector = _ImportCollector()
        collector.visit(tree)
        for lineno, top in collector.imports:
            if top == forbidden_top:
                violations.append((path, lineno, top))
    return violations


def _find_violations(scan_root: Path, forbidden_top: str):
    return _find_import_violations(scan_root, forbidden_top)


def _format(violations):
    return "\n".join(
        f"  {p.relative_to(REPO_ROOT)}:{ln}: imports `{mod}`"
        for p, ln, mod in violations[:10]
    )


def test_core_does_not_import_phionyx_governance():
    """ADR-0005 §3: phionyx_core/** must not import phionyx_governance."""
    violations = _find_violations(REPO_ROOT / "phionyx_core", "phionyx_governance")
    assert not violations, (
        f"phionyx_core imports phionyx_governance (ADR-0005 violation, "
        f"{len(violations)} occurrence(s)):\n{_format(violations)}"
    )


def test_phionyx_governance_does_not_import_phionyx_bridge():
    """ADR-0005 §3: phionyx_governance/** must not import phionyx_bridge."""
    violations = _find_violations(REPO_ROOT / "phionyx_governance", "phionyx_bridge")
    assert not violations, (
        f"phionyx_governance imports phionyx_bridge (ADR-0005 violation, "
        f"{len(violations)} occurrence(s)):\n{_format(violations)}"
    )


def test_core_does_not_import_phionyx_bridge():
    """ADR-0002 (restated): phionyx_core/** must not import phionyx_bridge."""
    violations = _find_violations(REPO_ROOT / "phionyx_core", "phionyx_bridge")
    assert not violations, (
        f"phionyx_core imports phionyx_bridge (ADR-0002 violation, "
        f"{len(violations)} occurrence(s)):\n{_format(violations)}"
    )


def test_core_does_not_import_delivery_frameworks():
    """ADR-0002 + .claude/rules/core-boundary.md: core must not import
    FastAPI, Uvicorn, Flask, Django, SQLAlchemy, anthropic, openai, litellm."""
    forbidden = (
        "fastapi", "uvicorn", "flask", "django",
        "sqlalchemy", "databases",
        "anthropic", "openai", "litellm",
    )
    all_violations = []
    for pkg in forbidden:
        all_violations.extend(_find_violations(REPO_ROOT / "phionyx_core", pkg))
    assert not all_violations, (
        f"phionyx_core imports a forbidden delivery-layer package "
        f"({len(all_violations)} occurrence(s)):\n{_format(all_violations)}"
    )
