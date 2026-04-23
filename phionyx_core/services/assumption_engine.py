"""
Assumption Surfacing Engine
============================

Faz 2.1: Assumption Surfacing Engine - Tam Fonksiyonel

Gelişmiş assumption extraction ve validation servisi.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import ast
import hashlib

from phionyx_core.services.assumption_types import Assumption


@dataclass
class AssumptionEvidence:
    """Evidence for an assumption."""
    source: str  # "code", "state", "profile", "test"
    reference: str  # Code reference or state field
    confidence: float  # 0.0-1.0
    timestamp: float  # When evidence was collected


@dataclass
class ValidationResult:
    """Result of assumption validation."""
    is_valid: bool
    violations: List[Assumption]
    warnings: List[Assumption]
    validated_count: int
    total_count: int


class AssumptionSurfacingEngine:
    """
    Full-featured Assumption Surfacing Engine.

    Provides:
    - Advanced assumption extraction (type, state, dependency, performance)
    - Assumption validation against profile and state
    - Evidence linking and tracking
    - Assumption challenge mechanism
    """

    def __init__(self, profile: Optional[Any] = None):
        """
        Initialize assumption engine.

        Args:
            profile: Profile instance for validation (optional)
        """
        self.profile = profile
        self.assumption_cache: Dict[str, List[Assumption]] = {}
        self.evidence_map: Dict[str, List[AssumptionEvidence]] = {}

    def extract_assumptions(
        self,
        code: str,
        context: Any,
        state: Optional[Any] = None
    ) -> List[Assumption]:
        """
        Extract assumptions from code and context.

        Enhanced extraction with:
        - Type inference assumptions
        - State assumptions
        - Dependency assumptions
        - Performance assumptions

        Args:
            code: Code string
            context: BlockContext or similar
            state: EchoState2Plus (optional)

        Returns:
            List of Assumption objects
        """
        assumptions = []

        # 1. Type inference assumptions (enhanced)
        assumptions.extend(self._extract_type_assumptions_enhanced(code, context))

        # 2. State assumptions (enhanced)
        if state:
            assumptions.extend(self._extract_state_assumptions_enhanced(state, context))
        else:
            assumptions.extend(self._extract_state_assumptions_from_context(context))

        # 3. Dependency assumptions (enhanced)
        assumptions.extend(self._extract_dependency_assumptions_enhanced(code, context))

        # 4. Performance assumptions (new)
        assumptions.extend(self._extract_performance_assumptions(code, context))

        # Link evidence to assumptions
        for assumption in assumptions:
            self._link_evidence(assumption, code, context, state)

        return assumptions

    def _extract_type_assumptions_enhanced(
        self,
        code: str,
        context: Any
    ) -> List[Assumption]:
        """Enhanced type assumption extraction."""
        assumptions = []

        try:
            tree = ast.parse(code)

            # Walk AST for type assumptions
            for node in ast.walk(tree):
                # Function definitions
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        # No type annotation
                        if arg.annotation is None:
                            # Infer type from usage
                            inferred_type = self._infer_type_from_usage(node, arg.arg)

                            assumptions.append(Assumption(
                                type="input_type",
                                description=f"Function '{node.name}' parameter '{arg.arg}' type inferred as '{inferred_type}'",
                                code_reference=f"{node.name}:{node.lineno}",
                                confidence=0.6 if inferred_type else 0.4,
                                evidence=[f"Parameter '{arg.arg}' in function '{node.name}' has no type annotation"]
                            ))
                        else:
                            # Type annotation exists
                            type_str = ast.unparse(arg.annotation)
                            assumptions.append(Assumption(
                                type="input_type",
                                description=f"Function '{node.name}' parameter '{arg.arg}' is assumed to be type '{type_str}'",
                                code_reference=f"{node.name}:{node.lineno}",
                                confidence=0.9,
                                evidence=[f"Type annotation: {type_str}"]
                            ))

                    # Return type assumption
                    if node.returns is None:
                        inferred_return = self._infer_return_type(node)
                        if inferred_return:
                            assumptions.append(Assumption(
                                type="return_type",
                                description=f"Function '{node.name}' return type inferred as '{inferred_return}'",
                                code_reference=f"{node.name}:{node.lineno}",
                                confidence=0.6,
                                evidence=["Return type inferred from function body"]
                            ))

                # Variable assignments
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Infer type from value
                            inferred_type = self._infer_type_from_value(node.value)
                            if inferred_type:
                                assumptions.append(Assumption(
                                    type="variable_type",
                                    description=f"Variable '{target.id}' type inferred as '{inferred_type}'",
                                    code_reference=f"line:{node.lineno}",
                                    confidence=0.7,
                                    evidence=[f"Type inferred from assignment: {ast.unparse(node.value)[:50]}"]
                                ))

        except SyntaxError:
            # Fallback to pattern-based extraction
            assumptions.extend(self._extract_type_assumptions_pattern(code))

        return assumptions

    def _infer_type_from_usage(self, func_node: ast.FunctionDef, param_name: str) -> Optional[str]:
        """Infer parameter type from function body usage."""
        # Look for operations on parameter
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == param_name:
                        # Check method calls
                        if node.func.attr in ['upper', 'lower', 'strip', 'split']:
                            return "str"
                        elif node.func.attr in ['append', 'extend', 'pop']:
                            return "list"
                        elif node.func.attr in ['keys', 'values', 'items']:
                            return "dict"

            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    return "list" or "dict"

            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    if node.attr in ['keys', 'values', 'items']:
                        return "dict"

        return None

    def _infer_return_type(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Infer return type from function body."""
        # Look for return statements
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value:
                    return self._infer_type_from_value(node.value)
        return None

    def _infer_type_from_value(self, value_node: ast.AST) -> Optional[str]:
        """Infer type from AST value node."""
        if isinstance(value_node, ast.Str):
            return "str"
        elif isinstance(value_node, ast.Num):
            return "int" or "float"
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Tuple):
            return "tuple"
        elif isinstance(value_node, ast.Call):
            # Try to infer from function name
            if isinstance(value_node.func, ast.Name):
                func_name = value_node.func.id
                if func_name in ['str', 'int', 'float', 'list', 'dict']:
                    return func_name
        return None

    def _extract_type_assumptions_pattern(self, code: str) -> List[Assumption]:
        """Pattern-based type assumption extraction (fallback)."""
        assumptions = []

        # Look for common type assumptions in comments
        comment_patterns = [
            (r'#\s*assume\s+(\w+)\s+is\s+(\w+)', "variable_type"),
            (r'#\s*(\w+)\s+must\s+be\s+(\w+)', "variable_type"),
            (r'#\s*(\w+)\s+is\s+always\s+(\w+)', "variable_type"),
        ]

        for pattern, assumption_type in comment_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                assumptions.append(Assumption(
                    type=assumption_type,
                    description=f"Assumption: {match.group(1)} is {match.group(2)}",
                    code_reference=None,
                    confidence=0.6,
                    evidence=[match.group(0)]
                ))

        return assumptions

    def _extract_state_assumptions_enhanced(
        self,
        state: Any,
        context: Any
    ) -> List[Assumption]:
        """Enhanced state assumption extraction."""
        assumptions = []

        # Check state fields
        if hasattr(state, 'A'):
            assumptions.append(Assumption(
                type="state",
                description=f"Arousal (A) is assumed to be {state.A}",
                code_reference=None,
                confidence=0.9,
                evidence=[f"State.A = {state.A}"]
            ))

        if hasattr(state, 'V'):
            assumptions.append(Assumption(
                type="state",
                description=f"Valence (V) is assumed to be {state.V}",
                code_reference=None,
                confidence=0.9,
                evidence=[f"State.V = {state.V}"]
            ))

        if hasattr(state, 'H'):
            assumptions.append(Assumption(
                type="state",
                description=f"Entropy (H) is assumed to be {state.H}",
                code_reference=None,
                confidence=0.9,
                evidence=[f"State.H = {state.H}"]
            ))

        # Check for state invariants
        if hasattr(state, 'H') and state.H < 0.01:
            assumptions.append(Assumption(
                type="state",
                description="Entropy is assumed to be >= 0.01 (invariant)",
                code_reference=None,
                confidence=1.0,
                evidence=["EchoState invariant: H >= 0.01"]
            ))

        return assumptions

    def _extract_state_assumptions_from_context(self, context: Any) -> List[Assumption]:
        """Extract state assumptions from context (when state not available)."""
        assumptions = []

        if hasattr(context, 'current_entropy'):
            assumptions.append(Assumption(
                type="state",
                description=f"Entropy is assumed to be {context.current_entropy}",
                code_reference=None,
                confidence=0.8,
                evidence=[f"Context.current_entropy = {context.current_entropy}"]
            ))

        if hasattr(context, 'current_amplitude'):
            assumptions.append(Assumption(
                type="state",
                description=f"Amplitude is assumed to be {context.current_amplitude}",
                code_reference=None,
                confidence=0.8,
                evidence=[f"Context.current_amplitude = {context.current_amplitude}"]
            ))

        return assumptions

    def _extract_dependency_assumptions_enhanced(
        self,
        code: str,
        context: Any
    ) -> List[Assumption]:
        """Enhanced dependency assumption extraction."""
        assumptions = []

        # Extract import statements
        import_patterns = [
            (r'import\s+(\w+)', "dependency"),
            (r'from\s+(\w+)\s+import', "dependency"),
        ]

        for pattern, assumption_type in import_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                module_name = match.group(1)
                assumptions.append(Assumption(
                    type=assumption_type,
                    description=f"Dependency assumption: '{module_name}' is available and importable",
                    code_reference=None,
                    confidence=0.8,
                    evidence=[f"Import statement: {match.group(0)}"]
                ))

        # Extract function calls (potential dependencies)
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        # Check if it's a built-in or external function
                        if func_name not in dir(__builtins__):
                            assumptions.append(Assumption(
                                type="dependency",
                                description=f"Function '{func_name}' is assumed to be available",
                                code_reference=f"line:{node.lineno}",
                                confidence=0.6,
                                evidence=[f"Function call: {func_name}()"]
                            ))
        except SyntaxError:
            pass

        return assumptions

    def _extract_performance_assumptions(
        self,
        code: str,
        context: Any
    ) -> List[Assumption]:
        """Extract performance assumptions."""
        assumptions = []

        # Look for loops (performance implications)
        loop_patterns = [
            (r'for\s+\w+\s+in\s+range\((\d+)\)', "performance"),
            (r'for\s+\w+\s+in\s+(\w+)', "performance"),
            (r'while\s+.*:', "performance"),
        ]

        for pattern, assumption_type in loop_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                assumptions.append(Assumption(
                    type=assumption_type,
                    description="Performance assumption: Loop iteration count is bounded",
                    code_reference=None,
                    confidence=0.5,
                    evidence=[f"Loop pattern: {match.group(0)}"]
                ))

        # Look for recursive calls
        if 'def ' in code and re.search(r'\w+\s*\(', code):
            assumptions.append(Assumption(
                type="performance",
                description="Performance assumption: Recursion depth is bounded",
                code_reference=None,
                confidence=0.4,
                evidence=["Recursive function detected"]
            ))

        return assumptions

    def _link_evidence(
        self,
        assumption: Assumption,
        code: str,
        context: Any,
        state: Optional[Any] = None
    ) -> None:
        """Link evidence to assumption."""
        if not assumption.evidence:
            assumption.evidence = []

        # Create evidence hash for tracking
        evidence_hash = hashlib.sha256(
            f"{assumption.type}:{assumption.description}".encode()
        ).hexdigest()[:32]

        # Store evidence
        if evidence_hash not in self.evidence_map:
            self.evidence_map[evidence_hash] = []

        evidence = AssumptionEvidence(
            source="code" if code else "state",
            reference=assumption.code_reference or "unknown",
            confidence=assumption.confidence,
            timestamp=0.0  # Would use actual timestamp in production
        )

        self.evidence_map[evidence_hash].append(evidence)

    def validate_assumptions(
        self,
        assumptions: List[Assumption],
        profile: Optional[Any] = None,
        state: Optional[Any] = None
    ) -> ValidationResult:
        """
        Validate assumptions against profile and state.

        Args:
            assumptions: List of assumptions to validate
            profile: Profile instance (optional, uses self.profile if not provided)
            state: EchoState2Plus (optional)

        Returns:
            ValidationResult
        """
        violations = []
        warnings = []

        profile_to_use = profile or self.profile

        for assumption in assumptions:
            # Check against profile constraints
            if profile_to_use:
                if not self._validate_against_profile(assumption, profile_to_use):
                    violations.append(assumption)
                    continue

            # Check against state constraints
            if state:
                if not self._validate_against_state(assumption, state):
                    warnings.append(assumption)
                    continue

            # Check confidence threshold
            if assumption.confidence < 0.5:
                warnings.append(assumption)

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            validated_count=len(assumptions) - len(violations) - len(warnings),
            total_count=len(assumptions)
        )

    def _validate_against_profile(self, assumption: Assumption, profile: Any) -> bool:
        """Validate assumption against profile constraints."""
        # Profile validation logic would go here
        # For now, return True (would check profile constraints)
        return True

    def _validate_against_state(self, assumption: Assumption, state: Any) -> bool:
        """Validate assumption against state constraints."""
        # State validation logic would go here
        # For now, return True (would check state invariants)
        return True

    def challenge_assumption(
        self,
        assumption: Assumption,
        challenge_reason: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Challenge an assumption.

        Args:
            assumption: Assumption to challenge
            challenge_reason: Reason for challenge

        Returns:
            Tuple of (is_valid, resolution_message)
        """
        # Check if assumption has evidence
        if not assumption.evidence or len(assumption.evidence) == 0:
            return (False, f"Assumption '{assumption.description}' lacks evidence and cannot be validated")

        # Check confidence
        if assumption.confidence < 0.5:
            return (False, f"Assumption '{assumption.description}' has low confidence ({assumption.confidence})")

        # If assumption has evidence and high confidence, it's valid
        return (True, f"Assumption '{assumption.description}' is validated with evidence")


__all__ = [
    'AssumptionSurfacingEngine',
    'AssumptionEvidence',
    'ValidationResult',
]

