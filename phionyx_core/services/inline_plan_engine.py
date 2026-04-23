"""
Inline Plan Mode Engine
=======================

Faz 3.1: Kalan Özellikler

Kod üretiminden önce plan üretir ve adım ayrıştırması yapar.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PlanStep:
    """Plan step definition."""
    id: str
    order: int
    description: str
    dependencies: List[str] = None  # IDs of steps that must complete before this
    estimated_time: Optional[float] = None  # In minutes
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class Plan:
    """Plan definition."""
    id: str
    title: str
    description: str
    steps: List[PlanStep]
    total_estimated_time: Optional[float] = None
    status: str = "draft"  # "draft", "approved", "executing", "completed"


class InlinePlanEngine:
    """
    Full-featured Inline Plan Mode Engine.

    Provides:
    - Plan generation from requirements
    - Step decomposition
    - Dependency resolution
    - Plan execution tracking
    """

    def __init__(self):
        """Initialize inline plan engine."""
        self.plan_cache: Dict[str, Plan] = {}

    def generate_plan(
        self,
        requirement: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """
        Generate plan from requirement.

        Args:
            requirement: Requirement description
            context: Additional context (optional)

        Returns:
            Plan with decomposed steps
        """
        # Decompose requirement into steps
        steps = self._decompose_requirement(requirement, context)

        # Calculate total estimated time
        total_time = sum(step.estimated_time or 0 for step in steps)

        plan = Plan(
            id=f"plan_{len(self.plan_cache)}",
            title=f"Plan for: {requirement[:50]}...",
            description=requirement,
            steps=steps,
            total_estimated_time=total_time
        )

        # Store in cache
        self.plan_cache[plan.id] = plan

        return plan

    def _decompose_requirement(
        self,
        requirement: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[PlanStep]:
        """Decompose requirement into steps."""
        steps = []

        # Common step patterns
        step_patterns = [
            ("analysis", "Analyze requirements and constraints", 15),
            ("design", "Design solution architecture", 30),
            ("implementation", "Implement core functionality", 60),
            ("testing", "Write and execute tests", 30),
            ("documentation", "Document code and API", 20),
            ("review", "Code review and refinement", 15),
        ]

        # Generate steps based on requirement complexity
        requirement_length = len(requirement)
        num_steps = min(6, max(3, requirement_length // 50))

        for i, (step_type, step_desc, estimated_time) in enumerate(step_patterns[:num_steps]):
            step = PlanStep(
                id=f"step_{i+1}",
                order=i+1,
                description=f"{step_desc} for: {requirement[:30]}...",
                dependencies=[f"step_{i}"] if i > 0 else [],
                estimated_time=estimated_time,
                status="pending"
            )
            steps.append(step)

        return steps

    def update_step_status(
        self,
        plan_id: str,
        step_id: str,
        status: str
    ) -> bool:
        """
        Update step status.

        Args:
            plan_id: Plan ID
            step_id: Step ID
            status: New status

        Returns:
            True if updated successfully
        """
        plan = self.plan_cache.get(plan_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                return True

        return False

    def get_execution_order(self, plan: Plan) -> List[PlanStep]:
        """
        Get execution order considering dependencies.

        Args:
            plan: Plan

        Returns:
            List of steps in execution order
        """
        # Topological sort based on dependencies
        executed = set()
        result = []

        while len(result) < len(plan.steps):
            progress = False

            for step in plan.steps:
                if step.id in executed:
                    continue

                # Check if all dependencies are executed
                if all(dep in executed for dep in step.dependencies):
                    result.append(step)
                    executed.add(step.id)
                    progress = True

            if not progress:
                # Circular dependency or missing dependency
                # Add remaining steps in order
                for step in plan.steps:
                    if step.id not in executed:
                        result.append(step)
                        executed.add(step.id)
                break

        return result


__all__ = [
    'InlinePlanEngine',
    'Plan',
    'PlanStep',
]

