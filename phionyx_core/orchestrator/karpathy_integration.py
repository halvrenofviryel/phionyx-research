"""
Karpathy Features End-to-End Integration
========================================

Faz 3.2: End-to-End Integration

Tüm Karpathy özelliklerinin birlikte çalışması için orchestration.
"""

from dataclasses import dataclass
from typing import Any

from phionyx_core.pipeline.base import BlockContext
from phionyx_core.services.assumption_challenge_module import AssumptionChallengeModule
from phionyx_core.services.assumption_engine import AssumptionSurfacingEngine
from phionyx_core.services.clarification_engine import ClarificationRequestEngine
from phionyx_core.services.complexity_engine import ComplexityBudgetEngine
from phionyx_core.services.dead_code_pruner import DeadCodePruner
from phionyx_core.services.inconsistency_engine import InconsistencyDetectionEngine
from phionyx_core.services.inline_plan_engine import InlinePlanEngine
from phionyx_core.services.orthogonal_change_guard import OrthogonalChangeGuard
from phionyx_core.services.pushback_engine import PushBackEngine
from phionyx_core.services.success_criteria_engine import SuccessCriteriaEngine
from phionyx_core.services.tradeoff_engine import TradeOffElicitationEngine


@dataclass
class KarpathyPipelineResult:
    """Result of Karpathy pipeline execution."""
    assumptions: list[Any]
    inconsistencies: list[Any]
    complexity_metrics: dict[str, Any] | None
    push_back_result: Any | None
    success_criteria_result: Any | None
    trade_offs: Any | None
    plan: Any | None
    clarifications: list[Any]
    dead_code: list[Any]
    orthogonal_changes: list[Any]
    assumption_challenges: list[Any]
    evidence_chain: list[dict[str, Any]]
    audit_trail: list[dict[str, Any]]


class KarpathyPipelineOrchestrator:
    """
    End-to-end orchestrator for all Karpathy features.

    Provides:
    - Pipeline orchestration
    - State consistency
    - Governance workflow
    - Evidence chain
    - Audit trail
    """

    def __init__(
        self,
        assumption_engine: AssumptionSurfacingEngine | None = None,
        inconsistency_engine: InconsistencyDetectionEngine | None = None,
        complexity_engine: ComplexityBudgetEngine | None = None,
        pushback_engine: PushBackEngine | None = None,
        success_criteria_engine: SuccessCriteriaEngine | None = None,
        tradeoff_engine: TradeOffElicitationEngine | None = None,
        plan_engine: InlinePlanEngine | None = None,
        clarification_engine: ClarificationRequestEngine | None = None,
        dead_code_pruner: DeadCodePruner | None = None,
        orthogonal_guard: OrthogonalChangeGuard | None = None,
        challenge_module: AssumptionChallengeModule | None = None
    ):
        """Initialize orchestrator with all engines."""
        self.assumption_engine = assumption_engine or AssumptionSurfacingEngine()
        self.inconsistency_engine = inconsistency_engine or InconsistencyDetectionEngine()
        self.complexity_engine = complexity_engine or ComplexityBudgetEngine()
        self.pushback_engine = pushback_engine
        self.success_criteria_engine = success_criteria_engine or SuccessCriteriaEngine()
        self.tradeoff_engine = tradeoff_engine or TradeOffElicitationEngine()
        self.plan_engine = plan_engine or InlinePlanEngine()
        self.clarification_engine = clarification_engine or ClarificationRequestEngine()
        self.dead_code_pruner = dead_code_pruner or DeadCodePruner()
        self.orthogonal_guard = orthogonal_guard or OrthogonalChangeGuard()
        self.challenge_module = challenge_module or AssumptionChallengeModule()

        self.evidence_chain: list[dict[str, Any]] = []
        self.audit_trail: list[dict[str, Any]] = []

    async def execute_karpathy_pipeline(
        self,
        context: BlockContext,
        code: str | None = None,
        requirements: list[dict[str, Any]] | None = None
    ) -> KarpathyPipelineResult:
        """
        Execute complete Karpathy pipeline.

        Args:
            context: BlockContext
            code: Code string (optional)
            requirements: Requirements list (optional)

        Returns:
            KarpathyPipelineResult
        """
        # Extract code if not provided
        if not code:
            code = self._extract_code_from_context(context)

        # 1. Assumption Surfacing
        assumptions = []
        if code:
            assumptions = self.assumption_engine.extract_assumptions(code, context)
            self._add_to_evidence_chain("assumptions", assumptions)
            self._add_to_audit_trail("assumption_extraction", {"count": len(assumptions)})

        # 2. Assumption Challenge
        assumption_challenges = []
        if assumptions:
            assumption_challenges = self.challenge_module.challenge_assumptions(assumptions)
            self._add_to_evidence_chain("assumption_challenges", assumption_challenges)

        # 3. Inconsistency Detection
        inconsistencies = []
        coherence_metrics = None
        if code:
            inconsistencies, coherence_metrics = self.inconsistency_engine.detect_inconsistencies(
                code=code,
                plan=context.metadata.get("plan") if context.metadata else None,
                tests=context.metadata.get("tests") if context.metadata else None,
                requirements=requirements
            )
            self._add_to_evidence_chain("inconsistencies", inconsistencies)
            self._add_to_audit_trail("inconsistency_detection", {"count": len(inconsistencies)})

        # 4. Complexity Budget
        complexity_metrics = None
        if code:
            metrics = self.complexity_engine.measure_complexity_enhanced(code)
            within_budget, violations, suggestions = self.complexity_engine.check_budget_enhanced(metrics)
            complexity_metrics = {
                "metrics": metrics,
                "within_budget": within_budget,
                "violations": violations,
                "suggestions": suggestions
            }
            self._add_to_evidence_chain("complexity", complexity_metrics)

        # 5. Push-back Evaluation
        push_back_result = None
        if self.pushback_engine:
            push_back_result = self.pushback_engine.evaluate_push_back(
                context=context,
                requirements=requirements
            )
            self._add_to_evidence_chain("push_back", push_back_result)

        # 6. Trade-off Elicitation
        trade_offs = None
        if requirements:
            alternatives = self.tradeoff_engine.generate_alternatives(
                requirement=str(requirements),
                constraints=None
            )
            trade_offs = self.tradeoff_engine.generate_tradeoff_table(alternatives)
            self._add_to_evidence_chain("trade_offs", trade_offs)

        # 7. Inline Plan Generation
        plan = None
        if requirements:
            plan = self.plan_engine.generate_plan(
                requirement=str(requirements),
                context=context.metadata if context.metadata else None
            )
            self._add_to_evidence_chain("plan", plan)

        # 8. Clarification Requests
        clarifications = []
        if context.user_input:
            clarifications = self.clarification_engine.detect_confusion(
                user_input=context.user_input,
                context=context.metadata if context.metadata else None
            )
            self._add_to_evidence_chain("clarifications", clarifications)

        # 9. Dead Code Detection
        dead_code = []
        if code:
            dead_code = self.dead_code_pruner.detect_dead_code(code)
            self._add_to_evidence_chain("dead_code", dead_code)

        # 10. Orthogonal Change Detection
        orthogonal_changes = []
        if code:
            orthogonal_changes = self.orthogonal_guard.check_orthogonal_changes(
                code=code,
                context=context.metadata if context.metadata else None
            )
            self._add_to_evidence_chain("orthogonal_changes", orthogonal_changes)

        # 11. Success Criteria (if available)
        success_criteria_result = None
        if context.metadata and "success_criteria" in context.metadata:
            criteria = context.metadata["success_criteria"]
            evaluation_result, test_codes = self.success_criteria_engine.orchestrate_workflow(
                criteria=criteria,
                code=code
            )
            success_criteria_result = {
                "evaluation": evaluation_result,
                "test_codes": test_codes
            }
            self._add_to_evidence_chain("success_criteria", success_criteria_result)

        return KarpathyPipelineResult(
            assumptions=assumptions,
            inconsistencies=inconsistencies,
            complexity_metrics=complexity_metrics,
            push_back_result=push_back_result,
            success_criteria_result=success_criteria_result,
            trade_offs=trade_offs,
            plan=plan,
            clarifications=clarifications,
            dead_code=dead_code,
            orthogonal_changes=orthogonal_changes,
            assumption_challenges=assumption_challenges,
            evidence_chain=self.evidence_chain,
            audit_trail=self.audit_trail
        )

    def _extract_code_from_context(self, context: BlockContext) -> str:
        """Extract code from context."""
        if context.metadata and "generated_code" in context.metadata:
            return context.metadata["generated_code"]

        # Try to extract from user input
        code_blocks = []
        if context.user_input:
            import re
            python_blocks = re.findall(r'```python\s*(.*?)```', context.user_input, re.DOTALL)
            code_blocks.extend(python_blocks)

        return "\n\n".join(code_blocks) if code_blocks else ""

    def _add_to_evidence_chain(self, step: str, data: Any) -> None:
        """Add to evidence chain."""
        self.evidence_chain.append({
            "step": step,
            "data": data,
            "timestamp": None  # Would use actual timestamp in production
        })

    def _add_to_audit_trail(self, action: str, details: dict[str, Any]) -> None:
        """Add to audit trail."""
        self.audit_trail.append({
            "action": action,
            "details": details,
            "timestamp": None  # Would use actual timestamp in production
        })

    def get_evidence_chain(self) -> list[dict[str, Any]]:
        """Get complete evidence chain."""
        return self.evidence_chain

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Get complete audit trail."""
        return self.audit_trail


__all__ = [
    'KarpathyPipelineOrchestrator',
    'KarpathyPipelineResult',
]

