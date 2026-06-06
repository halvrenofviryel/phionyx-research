"""
Complexity Budget Enforcement Engine
=====================================

Faz 2.3: Complexity Budget Enforcement - Tam Fonksiyonel

Gelişmiş complexity measurement ve enforcement servisi.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import re
import ast
import math

from phionyx_core.pipeline.blocks.complexity_budget import ComplexityMetrics, ComplexityBudget


@dataclass
class SimplificationSuggestion:
    """Suggestion for code simplification."""
    type: str  # "extract_function", "reduce_nesting", "split_class", "refactor"
    target: str  # What to modify
    description: str  # Detailed description
    priority: str  # "low", "medium", "high"
    estimated_impact: str  # "low", "medium", "high"


class ComplexityBudgetEngine:
    """
    Full-featured Complexity Budget Enforcement Engine.

    Provides:
    - Enhanced cyclomatic complexity calculation
    - Enhanced cognitive complexity calculation
    - Enhanced nesting depth calculation
    - Enhanced function length calculation
    - Budget configuration and enforcement
    - Simplification suggestion engine
    - Entropy integration
    """

    def __init__(self, budget: Optional[ComplexityBudget] = None):
        """
        Initialize complexity engine.

        Args:
            budget: ComplexityBudget configuration (optional)
        """
        self.budget = budget or ComplexityBudget()
        self.metrics_history: List[ComplexityMetrics] = []

    def measure_complexity_enhanced(self, code: str) -> ComplexityMetrics:
        """
        Enhanced complexity measurement.

        Args:
            code: Code string to measure

        Returns:
            ComplexityMetrics with all measurements
        """
        metrics = ComplexityMetrics()

        try:
            tree = ast.parse(code)

            # Enhanced cyclomatic complexity
            metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity_enhanced(tree)

            # Enhanced cognitive complexity
            metrics.cognitive_complexity = self._calculate_cognitive_complexity_enhanced(tree)

            # Enhanced nesting depth
            metrics.nesting_depth = self._calculate_max_nesting_depth_enhanced(tree)

            # Enhanced function length
            metrics.function_length = self._calculate_max_function_length_enhanced(tree)

            # Enhanced class complexity
            metrics.class_complexity = self._calculate_class_complexity_enhanced(tree)

        except SyntaxError:
            # Fallback to pattern-based estimation
            metrics.cyclomatic_complexity = self._estimate_cyclomatic_complexity_enhanced(code)
            metrics.cognitive_complexity = metrics.cyclomatic_complexity * 1.2  # Approximation
            metrics.nesting_depth = self._estimate_nesting_depth_enhanced(code)
            metrics.function_length = self._estimate_function_length_enhanced(code)
            metrics.class_complexity = self._estimate_class_complexity_enhanced(code)

        return metrics

    def _calculate_cyclomatic_complexity_enhanced(self, tree: ast.AST) -> int:
        """Enhanced cyclomatic complexity calculation."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, ast.If):
                complexity += 1
                # Check for elif chains
                if hasattr(node, 'orelse') and node.orelse:
                    for child in ast.walk(node.orelse):
                        if isinstance(child, ast.If):
                            complexity += 1
            elif isinstance(node, ast.While):
                complexity += 1
            elif isinstance(node, ast.For):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # Each additional condition adds complexity
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, ast.With):
                # Context managers can add complexity
                complexity += 0.5  # Round up

        return int(math.ceil(complexity))

    def _calculate_cognitive_complexity_enhanced(self, tree: ast.AST) -> int:
        """Enhanced cognitive complexity calculation."""
        complexity = 0
        nesting_level = 0

        def visit_node(node, level):
            nonlocal complexity, nesting_level
            current_complexity = 0

            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                nesting_level = level
                current_complexity = nesting_level + 1
                complexity += current_complexity

                # Visit children with increased nesting
                for child in ast.iter_child_nodes(node):
                    visit_node(child, level + 1)
            else:
                for child in ast.iter_child_nodes(node):
                    visit_node(child, level)

        visit_node(tree, 0)
        return complexity

    def _calculate_max_nesting_depth_enhanced(self, tree: ast.AST) -> int:
        """Enhanced maximum nesting depth calculation."""
        max_depth = 0

        def visit_node(node, depth):
            nonlocal max_depth
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                current_depth = depth + 1
                max_depth = max(max_depth, current_depth)
                for child in ast.iter_child_nodes(node):
                    visit_node(child, current_depth)
            else:
                for child in ast.iter_child_nodes(node):
                    visit_node(child, depth)

        visit_node(tree, 0)
        return max_depth

    def _calculate_max_function_length_enhanced(self, tree: ast.AST) -> int:
        """Enhanced maximum function length calculation."""
        max_length = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count all lines in function (including nested functions)
                start_line = node.lineno
                end_line = start_line

                # Find the last line in function body
                for child in ast.walk(node):
                    if hasattr(child, 'lineno'):
                        end_line = max(end_line, child.lineno)

                length = end_line - start_line + 1
                max_length = max(max_length, length)

        return max_length

    def _calculate_class_complexity_enhanced(self, tree: ast.AST) -> int:
        """Enhanced class complexity calculation."""
        max_complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))

                # Count attributes (including class variables)
                attributes = sum(1 for n in node.body if isinstance(n, ast.Assign))

                # Count properties
                properties = sum(1 for n in node.body if isinstance(n, ast.FunctionDef) and any(
                    isinstance(d, ast.Name) and d.id == 'property' for d in (n.decorator_list if hasattr(n, 'decorator_list') else [])
                ))

                # Calculate complexity: methods + attributes + properties
                complexity = methods + attributes + properties
                max_complexity = max(max_complexity, complexity)

        return max_complexity

    def _estimate_cyclomatic_complexity_enhanced(self, code: str) -> int:
        """Enhanced pattern-based cyclomatic complexity estimation."""
        complexity = 1  # Base

        # Count decision points
        complexity += len(re.findall(r'\bif\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\belif\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bwhile\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bfor\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bexcept\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\band\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bor\s+', code, re.IGNORECASE))
        complexity += len(re.findall(r'\btry\s*:', code, re.IGNORECASE))

        return complexity

    def _estimate_nesting_depth_enhanced(self, code: str) -> int:
        """Enhanced nesting depth estimation."""
        lines = code.split('\n')
        max_indent = 0

        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        # Convert to nesting level (assuming 4 spaces per level)
        return max_indent // 4

    def _estimate_function_length_enhanced(self, code: str) -> int:
        """Enhanced function length estimation."""
        # Count lines between function definitions
        func_pattern = r'def\s+\w+'
        func_matches = list(re.finditer(func_pattern, code))

        if not func_matches:
            return len(code.split('\n'))

        max_length = 0
        for i, match in enumerate(func_matches):
            start = match.start()
            end = func_matches[i + 1].start() if i + 1 < len(func_matches) else len(code)
            length = len(code[start:end].split('\n'))
            max_length = max(max_length, length)

        return max_length

    def _estimate_class_complexity_enhanced(self, code: str) -> int:
        """Enhanced class complexity estimation."""
        # Count methods and attributes
        methods = len(re.findall(r'def\s+\w+', code))
        attributes = len(re.findall(r'self\.\w+\s*=', code))
        properties = len(re.findall(r'@property', code))

        return methods + attributes + properties

    def check_budget_enhanced(
        self,
        metrics: ComplexityMetrics,
        budget: Optional[ComplexityBudget] = None
    ) -> Tuple[bool, List[str], List[SimplificationSuggestion]]:
        """
        Enhanced budget checking with suggestions.

        Args:
            metrics: ComplexityMetrics to check
            budget: ComplexityBudget (optional, uses self.budget if not provided)

        Returns:
            Tuple of (within_budget, violations, suggestions)
        """
        budget_to_use = budget or self.budget
        violations = []
        suggestions = []

        # Check each metric
        if metrics.cyclomatic_complexity > budget_to_use.max_cyclomatic:
            violations.append(f"Cyclomatic complexity ({metrics.cyclomatic_complexity}) exceeds budget ({budget_to_use.max_cyclomatic})")
            suggestions.append(SimplificationSuggestion(
                type="extract_function",
                target="complex_functions",
                description=f"Break down functions with cyclomatic complexity > {budget_to_use.max_cyclomatic} into smaller functions",
                priority="high",
                estimated_impact="high"
            ))

        if metrics.cognitive_complexity > budget_to_use.max_cognitive:
            violations.append(f"Cognitive complexity ({metrics.cognitive_complexity}) exceeds budget ({budget_to_use.max_cognitive})")
            suggestions.append(SimplificationSuggestion(
                type="reduce_nesting",
                target="nested_structures",
                description="Reduce nesting depth using early returns and guard clauses",
                priority="high",
                estimated_impact="medium"
            ))

        if metrics.nesting_depth > budget_to_use.max_nesting:
            violations.append(f"Nesting depth ({metrics.nesting_depth}) exceeds budget ({budget_to_use.max_nesting})")
            suggestions.append(SimplificationSuggestion(
                type="reduce_nesting",
                target="deeply_nested_code",
                description="Refactor nested structures into separate functions",
                priority="medium",
                estimated_impact="high"
            ))

        if metrics.function_length > budget_to_use.max_function_length:
            violations.append(f"Function length ({metrics.function_length} lines) exceeds budget ({budget_to_use.max_function_length})")
            suggestions.append(SimplificationSuggestion(
                type="extract_function",
                target="long_functions",
                description="Split long functions into smaller, focused functions",
                priority="medium",
                estimated_impact="medium"
            ))

        if metrics.class_complexity > budget_to_use.max_class_complexity:
            violations.append(f"Class complexity ({metrics.class_complexity}) exceeds budget ({budget_to_use.max_class_complexity})")
            suggestions.append(SimplificationSuggestion(
                type="split_class",
                target="large_classes",
                description="Split large classes into smaller, focused classes",
                priority="medium",
                estimated_impact="high"
            ))

        within_budget = len(violations) == 0

        return within_budget, violations, suggestions

    def calculate_entropy_impact(
        self,
        metrics: ComplexityMetrics,
        base_entropy: float = 0.5
    ) -> float:
        """
        Calculate entropy impact of complexity.

        Higher complexity → higher entropy (more uncertainty)

        Args:
            metrics: ComplexityMetrics
            base_entropy: Base entropy value

        Returns:
            Adjusted entropy value
        """
        # Normalize complexity metrics
        cyclomatic_norm = min(1.0, metrics.cyclomatic_complexity / 20.0)
        cognitive_norm = min(1.0, metrics.cognitive_complexity / 30.0)
        nesting_norm = min(1.0, metrics.nesting_depth / 5.0)

        # Weighted average
        complexity_score = (
            cyclomatic_norm * 0.4 +
            cognitive_norm * 0.3 +
            nesting_norm * 0.3
        )

        # Entropy increases with complexity
        entropy_boost = complexity_score * 0.2  # Max 0.2 boost
        adjusted_entropy = min(1.0, base_entropy + entropy_boost)

        return adjusted_entropy

    def generate_simplification_suggestions(
        self,
        code: str,
        metrics: ComplexityMetrics,
        budget: Optional[ComplexityBudget] = None
    ) -> List[SimplificationSuggestion]:
        """
        Generate simplification suggestions based on complexity metrics.

        Args:
            code: Code string
            metrics: ComplexityMetrics
            budget: ComplexityBudget (optional)

        Returns:
            List of SimplificationSuggestion
        """
        suggestions = []
        budget_to_use = budget or self.budget

        # Check for long functions
        if metrics.function_length > budget_to_use.max_function_length:
            suggestions.append(SimplificationSuggestion(
                type="extract_function",
                target="long_functions",
                description=f"Functions longer than {budget_to_use.max_function_length} lines should be split",
                priority="medium",
                estimated_impact="medium"
            ))

        # Check for deep nesting
        if metrics.nesting_depth > budget_to_use.max_nesting:
            suggestions.append(SimplificationSuggestion(
                type="reduce_nesting",
                target="deeply_nested_code",
                description=f"Nesting depth {metrics.nesting_depth} exceeds limit {budget_to_use.max_nesting}",
                priority="high",
                estimated_impact="high"
            ))

        # Check for complex classes
        if metrics.class_complexity > budget_to_use.max_class_complexity:
            suggestions.append(SimplificationSuggestion(
                type="split_class",
                target="large_classes",
                description=f"Class complexity {metrics.class_complexity} exceeds limit {budget_to_use.max_class_complexity}",
                priority="medium",
                estimated_impact="high"
            ))

        return suggestions


__all__ = [
    'ComplexityBudgetEngine',
    'SimplificationSuggestion',
]

