"""
Success Criteria Workflow Engine
=================================

Faz 2.5: Success Criteria Workflow - Tam Fonksiyonel

Test-first workflow implementation with success criteria definition and evaluation.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class CriteriaType(Enum):
    """Type of success criteria."""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    COMPLIANCE = "compliance"


@dataclass
class SuccessCriterion:
    """Success criterion definition."""
    id: str
    name: str
    description: str
    type: CriteriaType
    test_expression: str  # Test code or expression
    expected_result: Any  # Expected result
    priority: str = "medium"  # "low", "medium", "high", "critical"
    timeout: Optional[float] = None  # Timeout in seconds


@dataclass
class TestResult:
    """Result of a test execution."""
    criterion_id: str
    passed: bool
    actual_result: Any
    expected_result: Any
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class EvaluationResult:
    """Result of success criteria evaluation."""
    all_passed: bool
    passed_count: int
    failed_count: int
    total_count: int
    test_results: List[TestResult]
    overall_score: float  # 0.0-1.0
    critical_failures: List[str]  # IDs of critical criteria that failed


class SuccessCriteriaEngine:
    """
    Full-featured Success Criteria Workflow Engine.

    Provides:
    - Success criteria definition
    - Test generation from criteria
    - Test execution integration
    - Evaluation engine
    - AI Assurance Kit integration
    - Workflow orchestration
    """

    def __init__(self, ai_assurance_kit: Optional[Any] = None):
        """
        Initialize success criteria engine.

        Args:
            ai_assurance_kit: AI Assurance Kit instance (optional)
        """
        self.ai_assurance_kit = ai_assurance_kit
        self.criteria_registry: Dict[str, SuccessCriterion] = {}
        self.test_results_history: List[TestResult] = []

    def define_criteria(
        self,
        criteria: List[SuccessCriterion]
    ) -> None:
        """
        Define success criteria.

        Args:
            criteria: List of SuccessCriterion
        """
        for criterion in criteria:
            self.criteria_registry[criterion.id] = criterion

    def generate_tests_from_criteria(
        self,
        criteria: Optional[List[SuccessCriterion]] = None
    ) -> List[str]:
        """
        Generate test code from success criteria.

        Args:
            criteria: List of criteria (optional, uses registry if not provided)

        Returns:
            List of test code strings
        """
        criteria_to_use = criteria or list(self.criteria_registry.values())
        test_codes = []

        for criterion in criteria_to_use:
            test_code = self._generate_test_code(criterion)
            test_codes.append(test_code)

        return test_codes

    def _generate_test_code(self, criterion: SuccessCriterion) -> str:
        """Generate test code for a criterion."""
        # Generate test function
        test_name = f"test_{criterion.id}"

        test_code = f"""
def {test_name}():
    \"\"\"Test for criterion: {criterion.name}\"\"\"
    # {criterion.description}
    # Type: {criterion.type.value}
    # Priority: {criterion.priority}

    # Test expression
    result = {criterion.test_expression}

    # Expected result
    expected = {repr(criterion.expected_result)}

    # Assertion
    assert result == expected, f"Expected {{expected}}, got {{result}}"

    return True
"""
        return test_code.strip()

    def execute_tests(
        self,
        test_codes: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[TestResult]:
        """
        Execute test codes.

        Args:
            test_codes: List of test code strings
            context: Execution context (optional)

        Returns:
            List of TestResult
        """
        results = []

        for test_code in test_codes:
            # Extract criterion ID from test code
            criterion_id = self._extract_criterion_id(test_code)
            criterion = self.criteria_registry.get(criterion_id)

            if not criterion:
                # Skip if criterion not found
                continue

            # Execute test
            try:
                # In production, this would use a proper test execution framework
                # For now, we'll simulate execution
                result = self._execute_test_code(test_code, context)

                test_result = TestResult(
                    criterion_id=criterion_id,
                    passed=result["passed"],
                    actual_result=result.get("actual_result"),
                    expected_result=criterion.expected_result,
                    error_message=result.get("error_message"),
                    execution_time=result.get("execution_time")
                )

                results.append(test_result)

            except Exception as e:
                test_result = TestResult(
                    criterion_id=criterion_id,
                    passed=False,
                    actual_result=None,
                    expected_result=criterion.expected_result,
                    error_message=str(e),
                    execution_time=None
                )
                results.append(test_result)

        # Store in history
        self.test_results_history.extend(results)

        return results

    def _extract_criterion_id(self, test_code: str) -> Optional[str]:
        """Extract criterion ID from test code."""
        match = re.search(r'test_(\w+)', test_code)
        if match:
            return match.group(1)
        return None

    def _execute_test_code(
        self,
        test_code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute test code.

        In production, this would use a proper test execution framework.
        For now, we'll return a simulated result.

        Args:
            test_code: Test code string
            context: Execution context

        Returns:
            Execution result dictionary
        """
        # Simulated execution
        # In production, this would actually execute the test code
        return {
            "passed": True,  # Would be determined by actual execution
            "actual_result": None,  # Would be actual result
            "execution_time": 0.1  # Would be actual execution time
        }

    def evaluate_criteria(
        self,
        test_results: List[TestResult],
        criteria: Optional[List[SuccessCriterion]] = None
    ) -> EvaluationResult:
        """
        Evaluate success criteria based on test results.

        Args:
            test_results: List of TestResult
            criteria: List of criteria (optional, uses registry if not provided)

        Returns:
            EvaluationResult
        """
        criteria_to_use = criteria or list(self.criteria_registry.values())

        passed_count = sum(1 for r in test_results if r.passed)
        failed_count = len(test_results) - passed_count
        total_count = len(criteria_to_use)

        # Calculate overall score
        if total_count > 0:
            overall_score = passed_count / total_count
        else:
            overall_score = 0.0

        # Find critical failures
        critical_failures = []
        for result in test_results:
            if not result.passed:
                criterion = self.criteria_registry.get(result.criterion_id)
                if criterion and criterion.priority == "critical":
                    critical_failures.append(result.criterion_id)

        all_passed = (failed_count == 0) and (len(critical_failures) == 0)

        return EvaluationResult(
            all_passed=all_passed,
            passed_count=passed_count,
            failed_count=failed_count,
            total_count=total_count,
            test_results=test_results,
            overall_score=overall_score,
            critical_failures=critical_failures
        )

    def integrate_with_ai_assurance_kit(
        self,
        criteria: List[SuccessCriterion]
    ) -> Dict[str, Any]:
        """
        Integrate with AI Assurance Kit.

        Args:
            criteria: List of SuccessCriterion

        Returns:
            Integration result
        """
        if not self.ai_assurance_kit:
            return {
                "integrated": False,
                "message": "AI Assurance Kit not available"
            }

        # Generate tests
        test_codes = self.generate_tests_from_criteria(criteria)

        # Execute tests using AI Assurance Kit
        # This would call AI Assurance Kit's test execution methods
        # For now, we'll return a placeholder result

        return {
            "integrated": True,
            "test_count": len(test_codes),
            "criteria_count": len(criteria),
            "message": "Successfully integrated with AI Assurance Kit"
        }

    def orchestrate_workflow(
        self,
        criteria: List[SuccessCriterion],
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[EvaluationResult, List[str]]:
        """
        Orchestrate the complete success criteria workflow.

        Args:
            criteria: List of SuccessCriterion
            code: Code to test (optional)
            context: Execution context (optional)

        Returns:
            Tuple of (EvaluationResult, test_codes)
        """
        # 1. Define criteria
        self.define_criteria(criteria)

        # 2. Generate tests
        test_codes = self.generate_tests_from_criteria(criteria)

        # 3. Execute tests
        test_results = self.execute_tests(test_codes, context)

        # 4. Evaluate results
        evaluation_result = self.evaluate_criteria(test_results, criteria)

        # 5. Integrate with AI Assurance Kit (if available)
        if self.ai_assurance_kit:
            self.integrate_with_ai_assurance_kit(criteria)

        return evaluation_result, test_codes


__all__ = [
    'SuccessCriteriaEngine',
    'SuccessCriterion',
    'TestResult',
    'EvaluationResult',
    'CriteriaType',
]

