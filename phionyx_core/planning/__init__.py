"""
Planning Module — v4 §4 (AGI Layer 4)
=======================================

Goal decomposition and action planning.

Components:
- GoalDecomposer: Breaks high-level goals into sub-goals
"""

from .goal_decomposer import GoalDecomposer, SubGoal, DecompositionPlan

__all__ = [
    "GoalDecomposer",
    "SubGoal",
    "DecompositionPlan",
]
