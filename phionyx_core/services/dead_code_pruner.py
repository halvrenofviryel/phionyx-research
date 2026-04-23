"""
Dead Code Pruner
================

Faz 3.1: Kalan Özellikler

Dead code detection and removal suggestions.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re
import ast


@dataclass
class DeadCodeItem:
    """Dead code item."""
    type: str  # "function", "class", "variable", "import"
    name: str
    location: str  # File:line
    reason: str
    confidence: float  # 0.0-1.0
    suggestion: str


class DeadCodePruner:
    """
    Full-featured Dead Code Pruner.

    Provides:
    - Dead code detection
    - Unused function/class detection
    - Unused import detection
    - Removal suggestions
    """

    def __init__(self):
        """Initialize dead code pruner."""
        self.detected_items: List[DeadCodeItem] = []

    def detect_dead_code(
        self,
        code: str,
        entry_points: Optional[List[str]] = None
    ) -> List[DeadCodeItem]:
        """
        Detect dead code in codebase.

        Args:
            code: Code string to analyze
            entry_points: List of entry point function/class names (optional)

        Returns:
            List of DeadCodeItem
        """
        dead_items = []

        try:
            tree = ast.parse(code)

            # Extract all defined functions and classes
            defined_functions = self._extract_functions(tree)
            defined_classes = self._extract_classes(tree)
            _defined_variables = self._extract_variables(tree)
            imports = self._extract_imports(tree)

            # Extract all usages
            function_calls = self._extract_function_calls(tree)
            class_instantiations = self._extract_class_instantiations(tree)
            variable_usages = self._extract_variable_usages(tree)

            # Check for unused functions
            entry_points_set = set(entry_points or [])
            for func in defined_functions:
                if func["name"] not in function_calls and func["name"] not in entry_points_set:
                    dead_items.append(DeadCodeItem(
                        type="function",
                        name=func["name"],
                        location=f"line:{func['line']}",
                        reason="Function is defined but never called",
                        confidence=0.8,
                        suggestion=f"Remove unused function '{func['name']}' or add it to entry points"
                    ))

            # Check for unused classes
            for cls in defined_classes:
                if cls["name"] not in class_instantiations:
                    dead_items.append(DeadCodeItem(
                        type="class",
                        name=cls["name"],
                        location=f"line:{cls['line']}",
                        reason="Class is defined but never instantiated",
                        confidence=0.7,
                        suggestion=f"Remove unused class '{cls['name']}' or use it somewhere"
                    ))

            # Check for unused imports
            for imp in imports:
                if imp["name"] not in function_calls and imp["name"] not in variable_usages:
                    dead_items.append(DeadCodeItem(
                        type="import",
                        name=imp["name"],
                        location=f"line:{imp['line']}",
                        reason="Import is not used",
                        confidence=0.9,
                        suggestion=f"Remove unused import '{imp['name']}'"
                    ))

        except SyntaxError:
            # Fallback to pattern-based detection
            dead_items.extend(self._detect_dead_code_pattern(code))

        self.detected_items.extend(dead_items)
        return dead_items

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno
                })
        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno
                })
        return classes

    def _extract_variables(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract variable definitions."""
        variables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            "name": target.id,
                            "line": node.lineno
                        })
        return variables

    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "name": alias.name,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({
                        "name": alias.name,
                        "line": node.lineno
                    })
        return imports

    def _extract_function_calls(self, tree: ast.AST) -> Set[str]:
        """Extract function calls."""
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        return calls

    def _extract_class_instantiations(self, tree: ast.AST) -> Set[str]:
        """Extract class instantiations."""
        instantiations = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    instantiations.add(node.func.id)
        return instantiations

    def _extract_variable_usages(self, tree: ast.AST) -> Set[str]:
        """Extract variable usages."""
        usages = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                usages.add(node.id)
        return usages

    def _detect_dead_code_pattern(self, code: str) -> List[DeadCodeItem]:
        """Pattern-based dead code detection (fallback)."""
        dead_items = []

        # Detect unused function definitions
        func_pattern = r'def\s+(\w+)\s*\('
        func_matches = list(re.finditer(func_pattern, code))

        for match in func_matches:
            func_name = match.group(1)
            # Check if function is called
            call_pattern = rf'\b{func_name}\s*\('
            if not re.search(call_pattern, code[match.end():]):
                dead_items.append(DeadCodeItem(
                    type="function",
                    name=func_name,
                    location=f"line:{code[:match.start()].count(chr(10)) + 1}",
                    reason="Function is defined but never called",
                    confidence=0.6,
                    suggestion=f"Remove unused function '{func_name}'"
                ))

        return dead_items


__all__ = [
    'DeadCodePruner',
    'DeadCodeItem',
]

