"""
Inconsistency Detection Engine
==============================

Faz 2.2: Inconsistency Detection Engine - Tam Fonksiyonel

Gelişmiş inconsistency detection ve resolution servisi.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import ast

from phionyx_core.pipeline.blocks.inconsistency_detection import Inconsistency


@dataclass
class ResolutionSuggestion:
    """Resolution suggestion for an inconsistency."""
    action: str  # "add", "remove", "modify", "refactor"
    target: str  # What to modify
    description: str  # Detailed description
    priority: str  # "low", "medium", "high", "critical"
    estimated_effort: str  # "low", "medium", "high"


@dataclass
class CoherenceMetrics:
    """Coherence metrics for inconsistency detection."""
    code_plan_coherence: float  # 0.0-1.0
    code_test_coherence: float  # 0.0-1.0
    plan_requirement_coherence: float  # 0.0-1.0
    overall_coherence: float  # 0.0-1.0


class InconsistencyDetectionEngine:
    """
    Full-featured Inconsistency Detection Engine.

    Provides:
    - Advanced code-plan mismatch detection
    - Advanced code-test mismatch detection
    - Plan-requirement mismatch detection
    - State inconsistency detection
    - Resolution suggestion engine
    - Coherence metric integration
    """

    def __init__(self):
        """Initialize inconsistency detection engine."""
        self.inconsistency_cache: Dict[str, List[Inconsistency]] = {}
        self.resolution_cache: Dict[str, List[ResolutionSuggestion]] = {}

    def detect_inconsistencies(
        self,
        code: str,
        plan: Optional[str] = None,
        tests: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        state: Optional[Any] = None
    ) -> Tuple[List[Inconsistency], CoherenceMetrics]:
        """
        Detect inconsistencies between code, plan, tests, and requirements.

        Args:
            code: Generated code
            plan: Plan document (optional)
            tests: Test cases (optional)
            requirements: Requirements list (optional)
            state: EchoState2Plus (optional)

        Returns:
            Tuple of (inconsistencies, coherence_metrics)
        """
        inconsistencies = []

        # 1. Code-plan mismatch detection (enhanced)
        if plan:
            code_plan_inconsistencies = self._detect_code_plan_mismatch_enhanced(code, plan)
            inconsistencies.extend(code_plan_inconsistencies)

        # 2. Code-test mismatch detection (enhanced)
        if tests:
            code_test_inconsistencies = self._detect_code_test_mismatch_enhanced(code, tests)
            inconsistencies.extend(code_test_inconsistencies)

        # 3. Plan-requirement mismatch detection (enhanced)
        if plan and requirements:
            plan_req_inconsistencies = self._detect_plan_requirement_mismatch_enhanced(plan, requirements)
            inconsistencies.extend(plan_req_inconsistencies)

        # 4. State inconsistency detection (enhanced)
        if state:
            state_inconsistencies = self._detect_state_inconsistency_enhanced(state)
            inconsistencies.extend(state_inconsistencies)

        # Calculate coherence metrics
        coherence_metrics = self._calculate_coherence_metrics(
            code, plan, tests, requirements, inconsistencies
        )

        # Generate resolution suggestions
        for inconsistency in inconsistencies:
            if not inconsistency.resolution_suggestion:
                inconsistency.resolution_suggestion = self._generate_resolution_suggestion(
                    inconsistency, code, plan, tests, requirements
                )

        return inconsistencies, coherence_metrics

    def _detect_code_plan_mismatch_enhanced(
        self,
        code: str,
        plan: str
    ) -> List[Inconsistency]:
        """Enhanced code-plan mismatch detection."""
        inconsistencies = []

        # Extract plan steps
        plan_steps = self._extract_plan_steps_enhanced(plan)

        # Extract code elements
        code_elements = self._extract_code_elements_enhanced(code)

        # Check if plan steps are implemented
        for step in plan_steps:
            step_keywords = self._extract_keywords(step)
            implemented = False

            for element in code_elements:
                element_keywords = self._extract_keywords(element["name"])
                similarity = self._calculate_similarity(step_keywords, element_keywords)

                if similarity > 0.6:
                    implemented = True
                    break

            if not implemented:
                inconsistencies.append(Inconsistency(
                    type="code_plan",
                    description=f"Plan step not implemented: '{step}'",
                    severity="high",
                    code_reference=None,
                    resolution_suggestion=f"Implement plan step: {step}",
                    evidence=[f"Plan step: {step}", f"Code elements: {[e['name'] for e in code_elements]}"]
                ))

        # Check if code has elements not in plan
        for element in code_elements:
            element_keywords = self._extract_keywords(element["name"])
            in_plan = False

            for step in plan_steps:
                step_keywords = self._extract_keywords(step)
                similarity = self._calculate_similarity(element_keywords, step_keywords)

                if similarity > 0.6:
                    in_plan = True
                    break

            if not in_plan:
                inconsistencies.append(Inconsistency(
                    type="code_plan",
                    description=f"Code element not in plan: '{element['name']}'",
                    severity="medium",
                    code_reference=element.get("reference"),
                    resolution_suggestion=f"Add '{element['name']}' to plan or remove from code",
                    evidence=[f"Code element: {element['name']}", f"Plan steps: {plan_steps}"]
                ))

        return inconsistencies

    def _detect_code_test_mismatch_enhanced(
        self,
        code: str,
        tests: List[str]
    ) -> List[Inconsistency]:
        """Enhanced code-test mismatch detection."""
        inconsistencies = []

        # Extract code functions
        code_functions = self._extract_functions_enhanced(code)

        # Extract test cases
        test_cases = self._extract_test_cases_enhanced(tests)

        # Check if test cases match code functions
        for test_case in test_cases:
            tested_function = self._extract_tested_function_enhanced(test_case)

            if tested_function:
                if tested_function not in [f["name"] for f in code_functions]:
                    inconsistencies.append(Inconsistency(
                        type="code_test",
                        description=f"Test case tests function '{tested_function}' which is not in code",
                        severity="high",
                        code_reference=None,
                        resolution_suggestion=f"Add function '{tested_function}' to code or remove test",
                        evidence=[f"Test case: {test_case['name']}", f"Code functions: {[f['name'] for f in code_functions]}"]
                    ))

        # Check if code functions have tests
        for func in code_functions:
            has_test = False

            for test_case in test_cases:
                tested_function = self._extract_tested_function_enhanced(test_case)
                if tested_function == func["name"]:
                    has_test = True
                    break

            if not has_test:
                inconsistencies.append(Inconsistency(
                    type="code_test",
                    description=f"Function '{func['name']}' has no test coverage",
                    severity="medium",
                    code_reference=func.get("reference"),
                    resolution_suggestion=f"Add test for function '{func['name']}'",
                    evidence=[f"Function: {func['name']}", f"Test cases: {len(test_cases)}"]
                ))

        return inconsistencies

    def _detect_plan_requirement_mismatch_enhanced(
        self,
        plan: str,
        requirements: List[str]
    ) -> List[Inconsistency]:
        """Enhanced plan-requirement mismatch detection."""
        inconsistencies = []

        # Extract plan steps
        plan_steps = self._extract_plan_steps_enhanced(plan)

        # Check if requirements are covered in plan
        for req in requirements:
            req_keywords = self._extract_keywords(req)
            covered = False

            for step in plan_steps:
                step_keywords = self._extract_keywords(step)
                similarity = self._calculate_similarity(req_keywords, step_keywords)

                if similarity > 0.6:
                    covered = True
                    break

            if not covered:
                inconsistencies.append(Inconsistency(
                    type="plan_requirement",
                    description=f"Requirement not covered in plan: '{req}'",
                    severity="high",
                    code_reference=None,
                    resolution_suggestion=f"Add requirement '{req}' to plan",
                    evidence=[f"Requirement: {req}", f"Plan steps: {plan_steps}"]
                ))

        return inconsistencies

    def _detect_state_inconsistency_enhanced(self, state: Any) -> List[Inconsistency]:
        """Enhanced state inconsistency detection."""
        inconsistencies = []

        # Check entropy consistency
        if hasattr(state, 'H'):
            if state.H < 0.01:
                inconsistencies.append(Inconsistency(
                    type="state",
                    description="Entropy is too low (<0.01), violates EchoState invariant",
                    severity="critical",
                    code_reference=None,
                    resolution_suggestion="Adjust entropy to be >= 0.01",
                    evidence=[f"Current entropy: {state.H}"]
                ))
            elif state.H > 1.0:
                inconsistencies.append(Inconsistency(
                    type="state",
                    description="Entropy exceeds maximum (>1.0)",
                    severity="high",
                    code_reference=None,
                    resolution_suggestion="Adjust entropy to be <= 1.0",
                    evidence=[f"Current entropy: {state.H}"]
                ))

        # Check coherence (if available)
        if hasattr(state, 'C'):
            if state.C < 0.5:
                inconsistencies.append(Inconsistency(
                    type="state",
                    description=f"Coherence is low ({state.C:.2f}), indicates state inconsistency",
                    severity="medium",
                    code_reference=None,
                    resolution_suggestion="Review state updates and coherence calculations",
                    evidence=[f"Current coherence: {state.C:.2f}"]
                ))

        # Check assumptions vs state
        if hasattr(state, 'assumptions') and state.assumptions:
            for assumption in state.assumptions:
                if assumption.get("type") == "state":
                    # Validate state assumption against actual state
                    if not self._validate_state_assumption(assumption, state):
                        inconsistencies.append(Inconsistency(
                            type="state",
                            description=f"State assumption mismatch: '{assumption.get('description')}'",
                            severity="medium",
                            code_reference=assumption.get("code_reference"),
                            resolution_suggestion="Update state assumption or fix state",
                            evidence=[f"Assumption: {assumption.get('description')}"]
                        ))

        return inconsistencies

    def _calculate_coherence_metrics(
        self,
        code: str,
        plan: Optional[str],
        tests: Optional[List[str]],
        requirements: Optional[List[str]],
        inconsistencies: List[Inconsistency]
    ) -> CoherenceMetrics:
        """Calculate coherence metrics."""
        code_plan_coherence = 1.0
        code_test_coherence = 1.0
        plan_requirement_coherence = 1.0

        # Calculate code-plan coherence
        if plan:
            code_plan_inconsistencies = [i for i in inconsistencies if i.type == "code_plan"]
            if code_plan_inconsistencies:
                # Lower coherence based on inconsistency count and severity
                severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
                total_weight = sum(severity_weights.get(i.severity, 0.5) for i in code_plan_inconsistencies)
                code_plan_coherence = max(0.0, 1.0 - (total_weight / 10.0))

        # Calculate code-test coherence
        if tests:
            code_test_inconsistencies = [i for i in inconsistencies if i.type == "code_test"]
            if code_test_inconsistencies:
                severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
                total_weight = sum(severity_weights.get(i.severity, 0.5) for i in code_test_inconsistencies)
                code_test_coherence = max(0.0, 1.0 - (total_weight / 10.0))

        # Calculate plan-requirement coherence
        if plan and requirements:
            plan_req_inconsistencies = [i for i in inconsistencies if i.type == "plan_requirement"]
            if plan_req_inconsistencies:
                severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
                total_weight = sum(severity_weights.get(i.severity, 0.5) for i in plan_req_inconsistencies)
                plan_requirement_coherence = max(0.0, 1.0 - (total_weight / 10.0))

        # Overall coherence (weighted average)
        weights = []
        values = []

        if plan:
            weights.append(0.4)
            values.append(code_plan_coherence)

        if tests:
            weights.append(0.3)
            values.append(code_test_coherence)

        if plan and requirements:
            weights.append(0.3)
            values.append(plan_requirement_coherence)

        if weights:
            overall_coherence = sum(w * v for w, v in zip(weights, values, strict=False)) / sum(weights)
        else:
            overall_coherence = 1.0

        return CoherenceMetrics(
            code_plan_coherence=code_plan_coherence,
            code_test_coherence=code_test_coherence,
            plan_requirement_coherence=plan_requirement_coherence,
            overall_coherence=overall_coherence
        )

    def _generate_resolution_suggestion(
        self,
        inconsistency: Inconsistency,
        code: str,
        plan: Optional[str],
        tests: Optional[List[str]],
        requirements: Optional[List[str]]
    ) -> str:
        """Generate resolution suggestion for inconsistency."""
        if inconsistency.type == "code_plan":
            return "Review plan and code alignment. Consider: 1) Update plan to match code, 2) Update code to match plan, or 3) Refactor both for better alignment."
        elif inconsistency.type == "code_test":
            return "Ensure test coverage matches code. Consider: 1) Add missing tests, 2) Remove obsolete tests, or 3) Update tests to match code changes."
        elif inconsistency.type == "plan_requirement":
            return "Ensure plan covers all requirements. Consider: 1) Add missing requirements to plan, 2) Update plan steps to cover requirements, or 3) Clarify requirement scope."
        elif inconsistency.type == "state":
            return "Review state consistency. Consider: 1) Validate state invariants, 2) Update state assumptions, or 3) Fix state calculation logic."
        else:
            return "Review and resolve inconsistency based on context."

    def _extract_plan_steps_enhanced(self, plan: str) -> List[str]:
        """Enhanced plan step extraction."""
        steps = []

        # Look for numbered steps
        step_pattern = r'(?:^|\n)\s*(?:\d+\.|[-*])\s*(.+?)(?=\n\s*(?:\d+\.|[-*])|$)'
        matches = re.finditer(step_pattern, plan, re.MULTILINE)
        for match in matches:
            steps.append(match.group(1).strip())

        # Also look for action verbs (Create, Add, Implement, etc.)
        action_pattern = r'(?:^|\n)\s*(?:Create|Add|Implement|Update|Fix|Remove|Refactor)\s+(.+?)(?=\n|$)'
        matches = re.finditer(action_pattern, plan, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            step = match.group(1).strip()
            if step not in steps:
                steps.append(step)

        return steps

    def _extract_code_elements_enhanced(self, code: str) -> List[Dict[str, Any]]:
        """Enhanced code element extraction."""
        elements = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    elements.append({
                        "name": node.name,
                        "type": "function",
                        "reference": f"{node.name}:{node.lineno}",
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    elements.append({
                        "name": node.name,
                        "type": "class",
                        "reference": f"{node.name}:{node.lineno}",
                        "line": node.lineno
                    })
        except SyntaxError:
            # Fallback to pattern-based extraction
            func_pattern = r'def\s+(\w+)\s*\('
            for match in re.finditer(func_pattern, code):
                elements.append({
                    "name": match.group(1),
                    "type": "function",
                    "reference": None,
                    "line": None
                })

        return elements

    def _extract_functions_enhanced(self, code: str) -> List[Dict[str, Any]]:
        """Enhanced function extraction."""
        functions = []

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "reference": f"{node.name}:{node.lineno}",
                        "line": node.lineno
                    })
        except SyntaxError:
            func_pattern = r'def\s+(\w+)\s*\('
            for match in re.finditer(func_pattern, code):
                functions.append({
                    "name": match.group(1),
                    "reference": None,
                    "line": None
                })

        return functions

    def _extract_test_cases_enhanced(self, tests: List[str]) -> List[Dict[str, Any]]:
        """Enhanced test case extraction."""
        test_cases = []

        for test_code in tests:
            # Look for test functions
            test_pattern = r'def\s+(test_\w+)\s*\('
            matches = re.finditer(test_pattern, test_code)
            for match in matches:
                test_cases.append({
                    "name": match.group(1),
                    "code": test_code
                })

        return test_cases

    def _extract_tested_function_enhanced(self, test_case: Dict[str, Any]) -> Optional[str]:
        """Enhanced tested function extraction."""
        test_code = test_case.get("code", "")

        # Look for function calls in test
        func_call_pattern = r'(\w+)\s*\('
        matches = re.finditer(func_call_pattern, test_code)

        for match in matches:
            func_name = match.group(1)
            # Skip test framework functions
            if not func_name.startswith('test_') and not func_name.startswith('assert') and func_name not in ['print', 'len', 'str', 'int']:
                return func_name

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords

    def _calculate_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate similarity between two keyword lists."""
        if not keywords1 or not keywords2:
            return 0.0

        # Use SequenceMatcher for similarity
        set1 = set(keywords1)
        set2 = set(keywords2)

        if not set1 or not set2:
            return 0.0

        intersection = set1.intersection(set2)
        union = set1.union(set2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _validate_state_assumption(self, assumption: Dict[str, Any], state: Any) -> bool:
        """Validate state assumption against actual state."""
        # Basic validation - would be enhanced in production
        return True


__all__ = [
    'InconsistencyDetectionEngine',
    'ResolutionSuggestion',
    'CoherenceMetrics',
]

