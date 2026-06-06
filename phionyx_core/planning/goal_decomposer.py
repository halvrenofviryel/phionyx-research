"""
Goal Decomposer — v4 §4 (AGI Layer 4)
========================================

Decomposes high-level GoalObject into executable sub-goals
with dependency ordering.

Algorithm:
1. Analyze goal requirements
2. Identify prerequisite conditions (from causal graph)
3. Generate ordered sub-goals
4. Validate dependencies form a DAG

Integrates with:
- contracts/v4/goal_object.py (GoalObject, GoalPriority)
- contracts/v4/action_intent.py (ActionType for sub-goal actions)
- causality/causal_graph.py (for prerequisite analysis)
"""

import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
max_sub_goals = 20
default_complexity = 0.5


class SubGoalStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"       # All prerequisites met
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"   # Prerequisites not met


@dataclass
class SubGoal:
    """A decomposed sub-goal."""
    sub_goal_id: str
    name: str
    description: str = ""
    parent_goal_id: str = ""
    status: str = SubGoalStatus.PENDING.value
    priority: int = 0                  # Lower = higher priority (execution order)
    prerequisites: List[str] = field(default_factory=list)  # Sub-goal IDs this depends on
    action_type: str = "respond"       # ActionType from action_intent
    estimated_complexity: float = 0.5  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_ready(self) -> bool:
        return self.status == SubGoalStatus.READY.value

    @property
    def is_complete(self) -> bool:
        return self.status == SubGoalStatus.COMPLETED.value


@dataclass
class DecompositionPlan:
    """Full decomposition of a goal into sub-goals."""
    goal_id: str
    goal_name: str
    sub_goals: List[SubGoal]
    execution_order: List[str]  # Sub-goal IDs in execution order
    total_complexity: float
    estimated_steps: int

    def get_ready_goals(self, completed: Optional[Set[str]] = None) -> List[SubGoal]:
        """Get sub-goals whose prerequisites are all completed."""
        completed = completed or set()
        ready = []
        for sg in self.sub_goals:
            if sg.status in (SubGoalStatus.COMPLETED.value, SubGoalStatus.IN_PROGRESS.value):
                continue
            if all(p in completed for p in sg.prerequisites):
                ready.append(sg)
        return ready

    def mark_complete(self, sub_goal_id: str) -> None:
        """Mark a sub-goal as completed."""
        for sg in self.sub_goals:
            if sg.sub_goal_id == sub_goal_id:
                sg.status = SubGoalStatus.COMPLETED.value
                break

    @property
    def progress(self) -> float:
        """Completion percentage."""
        if not self.sub_goals:
            return 1.0
        completed = sum(1 for sg in self.sub_goals if sg.is_complete)
        return completed / len(self.sub_goals)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "sub_goals": [
                {
                    "id": sg.sub_goal_id,
                    "name": sg.name,
                    "status": sg.status,
                    "priority": sg.priority,
                    "prerequisites": sg.prerequisites,
                    "action_type": sg.action_type,
                    "complexity": sg.estimated_complexity,
                }
                for sg in self.sub_goals
            ],
            "execution_order": self.execution_order,
            "total_complexity": round(self.total_complexity, 2),
            "progress": round(self.progress, 2),
        }


class GoalDecomposer:
    """
    Decomposes goals into sub-goals with dependency ordering.

    Usage:
        decomposer = GoalDecomposer()
        plan = decomposer.decompose(
            goal_id="g1",
            goal_name="Improve system safety",
            requirements=["assess current risks", "implement mitigations", "verify"],
        )
        # Execute sub-goals in order
        for sg_id in plan.execution_order:
            ready = plan.get_ready_goals(completed={...})
    """

    def __init__(
        self,
        max_sub_goals: int = max_sub_goals,
        default_complexity: float = default_complexity,
    ):
        self.max_sub_goals = max_sub_goals
        self.default_complexity = default_complexity

    def decompose(
        self,
        goal_id: str,
        goal_name: str,
        requirements: List[str],
        dependencies: Optional[Dict[str, List[str]]] = None,
        action_types: Optional[Dict[str, str]] = None,
        complexities: Optional[Dict[str, float]] = None,
    ) -> DecompositionPlan:
        """
        Decompose a goal into sub-goals.

        Args:
            goal_id: Parent goal ID
            goal_name: Parent goal name
            requirements: List of requirement descriptions (become sub-goals)
            dependencies: {req_name: [depends_on_req_name, ...]}
            action_types: {req_name: ActionType string}
            complexities: {req_name: complexity 0-1}

        Returns:
            DecompositionPlan with ordered sub-goals
        """
        dependencies = dependencies or {}
        action_types = action_types or {}
        complexities = complexities or {}

        # Limit requirements
        reqs = requirements[:self.max_sub_goals]

        # Create sub-goals
        name_to_id: Dict[str, str] = {}
        sub_goals: List[SubGoal] = []

        for i, req in enumerate(reqs):
            sg_id = f"sg_{goal_id}_{i}"
            name_to_id[req] = sg_id

        for i, req in enumerate(reqs):
            sg_id = name_to_id[req]
            # Resolve prerequisites
            prereqs = []
            for dep_name in dependencies.get(req, []):
                if dep_name in name_to_id:
                    prereqs.append(name_to_id[dep_name])

            sub_goals.append(SubGoal(
                sub_goal_id=sg_id,
                name=req,
                parent_goal_id=goal_id,
                priority=i,
                prerequisites=prereqs,
                action_type=action_types.get(req, "respond"),
                estimated_complexity=complexities.get(req, self.default_complexity),
            ))

        # Compute execution order (topological sort)
        execution_order = self._topological_sort(sub_goals)

        # Total complexity
        total = sum(sg.estimated_complexity for sg in sub_goals)

        return DecompositionPlan(
            goal_id=goal_id,
            goal_name=goal_name,
            sub_goals=sub_goals,
            execution_order=execution_order,
            total_complexity=total,
            estimated_steps=len(sub_goals),
        )

    def decompose_with_causal_hints(
        self,
        goal_id: str,
        goal_name: str,
        requirements: List[str],
        causal_dependencies: List[tuple],
    ) -> DecompositionPlan:
        """
        Decompose using causal graph hints for dependency ordering.

        Args:
            causal_dependencies: List of (cause_req, effect_req) tuples
        """
        deps: Dict[str, List[str]] = {}
        for cause, effect in causal_dependencies:
            if effect not in deps:
                deps[effect] = []
            deps[effect].append(cause)

        return self.decompose(
            goal_id=goal_id,
            goal_name=goal_name,
            requirements=requirements,
            dependencies=deps,
        )

    def _topological_sort(self, sub_goals: List[SubGoal]) -> List[str]:
        """Sort sub-goals by dependency order."""
        id_to_sg = {sg.sub_goal_id: sg for sg in sub_goals}
        in_degree: Dict[str, int] = {sg.sub_goal_id: 0 for sg in sub_goals}

        for sg in sub_goals:
            for prereq in sg.prerequisites:
                if prereq in in_degree:
                    in_degree[sg.sub_goal_id] += 1

        queue = sorted(
            [sid for sid, d in in_degree.items() if d == 0],
            key=lambda sid: id_to_sg[sid].priority,
        )
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for sg in sub_goals:
                if current in sg.prerequisites:
                    in_degree[sg.sub_goal_id] -= 1
                    if in_degree[sg.sub_goal_id] == 0:
                        queue.append(sg.sub_goal_id)
            queue.sort(key=lambda sid: id_to_sg[sid].priority)

        # Add any remaining (circular dependency fallback)
        for sg in sub_goals:
            if sg.sub_goal_id not in order:
                order.append(sg.sub_goal_id)

        return order
