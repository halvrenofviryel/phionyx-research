"""
Tests for GoalDecomposer — v4 §4 (AGI Layer 4)
================================================
"""

import pytest
from phionyx_core.planning.goal_decomposer import (
    GoalDecomposer,
    SubGoal,
    SubGoalStatus,
    DecompositionPlan,
)


# ── Basic Decomposition ──

def test_decompose_simple():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Test Goal", ["step A", "step B", "step C"])
    assert plan.goal_id == "g1"
    assert len(plan.sub_goals) == 3
    assert plan.estimated_steps == 3

def test_decompose_empty():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Empty", [])
    assert len(plan.sub_goals) == 0
    assert plan.progress == 1.0

def test_decompose_max_limit():
    d = GoalDecomposer(max_sub_goals=2)
    plan = d.decompose("g1", "Limited", ["a", "b", "c", "d"])
    assert len(plan.sub_goals) == 2


# ── Dependencies ──

def test_dependencies():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "With Deps",
        ["assess", "implement", "verify"],
        dependencies={"implement": ["assess"], "verify": ["implement"]},
    )
    assess = [sg for sg in plan.sub_goals if sg.name == "assess"][0]
    implement = [sg for sg in plan.sub_goals if sg.name == "implement"][0]
    verify = [sg for sg in plan.sub_goals if sg.name == "verify"][0]
    assert assess.sub_goal_id in implement.prerequisites
    assert implement.sub_goal_id in verify.prerequisites

def test_execution_order_respects_deps():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "Ordered",
        ["verify", "implement", "assess"],
        dependencies={"implement": ["assess"], "verify": ["implement"]},
    )
    order = plan.execution_order
    ids = {sg.name: sg.sub_goal_id for sg in plan.sub_goals}
    assert order.index(ids["assess"]) < order.index(ids["implement"])
    assert order.index(ids["implement"]) < order.index(ids["verify"])


# ── Action Types & Complexity ──

def test_custom_action_types():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "Actions",
        ["store data", "respond"],
        action_types={"store data": "store_memory", "respond": "respond"},
    )
    store = [sg for sg in plan.sub_goals if sg.name == "store data"][0]
    assert store.action_type == "store_memory"

def test_custom_complexities():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "Complex",
        ["easy", "hard"],
        complexities={"easy": 0.1, "hard": 0.9},
    )
    assert plan.total_complexity == pytest.approx(1.0)


# ── Ready Goals ──

def test_get_ready_goals_no_deps():
    d = GoalDecomposer()
    plan = d.decompose("g1", "No Deps", ["a", "b", "c"])
    ready = plan.get_ready_goals()
    assert len(ready) == 3  # All ready when no deps

def test_get_ready_goals_with_deps():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "Deps",
        ["assess", "implement"],
        dependencies={"implement": ["assess"]},
    )
    assess = [sg for sg in plan.sub_goals if sg.name == "assess"][0]
    implement = [sg for sg in plan.sub_goals if sg.name == "implement"][0]
    ready = plan.get_ready_goals()
    ready_ids = [r.sub_goal_id for r in ready]
    assert assess.sub_goal_id in ready_ids
    assert implement.sub_goal_id not in ready_ids  # Blocked

def test_get_ready_after_completion():
    d = GoalDecomposer()
    plan = d.decompose(
        "g1", "Deps",
        ["assess", "implement"],
        dependencies={"implement": ["assess"]},
    )
    assess = [sg for sg in plan.sub_goals if sg.name == "assess"][0]
    ready = plan.get_ready_goals(completed={assess.sub_goal_id})
    ready_names = [r.name for r in ready]
    assert "implement" in ready_names


# ── Progress ──

def test_progress_zero():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Test", ["a", "b"])
    assert plan.progress == pytest.approx(0.0)

def test_progress_half():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Test", ["a", "b"])
    plan.mark_complete(plan.sub_goals[0].sub_goal_id)
    assert plan.progress == pytest.approx(0.5)

def test_progress_full():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Test", ["a", "b"])
    for sg in plan.sub_goals:
        plan.mark_complete(sg.sub_goal_id)
    assert plan.progress == pytest.approx(1.0)


# ── Causal Hints ──

def test_decompose_with_causal_hints():
    d = GoalDecomposer()
    plan = d.decompose_with_causal_hints(
        "g1", "Causal",
        ["analyze", "fix", "test"],
        causal_dependencies=[("analyze", "fix"), ("fix", "test")],
    )
    order = plan.execution_order
    ids = {sg.name: sg.sub_goal_id for sg in plan.sub_goals}
    assert order.index(ids["analyze"]) < order.index(ids["fix"])
    assert order.index(ids["fix"]) < order.index(ids["test"])


# ── Serialization ──

def test_to_dict():
    d = GoalDecomposer()
    plan = d.decompose("g1", "Test", ["a", "b"])
    data = plan.to_dict()
    assert data["goal_id"] == "g1"
    assert len(data["sub_goals"]) == 2
    assert "execution_order" in data
    assert "progress" in data


# ── SubGoal Properties ──

def test_subgoal_is_ready():
    sg = SubGoal(sub_goal_id="1", name="test", status=SubGoalStatus.READY.value)
    assert sg.is_ready is True

def test_subgoal_is_complete():
    sg = SubGoal(sub_goal_id="1", name="test", status=SubGoalStatus.COMPLETED.value)
    assert sg.is_complete is True
