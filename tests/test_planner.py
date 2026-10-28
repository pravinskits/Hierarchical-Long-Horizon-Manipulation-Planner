import pytest
from src.hlmp.core.planner import HierarchicalPlanner
from src.hlmp.core.plan_models import PlannedSubgoal, Plan
from src.hlmp.core.task_state import TaskStateManager

def test_create_plan():
    planner = HierarchicalPlanner()
    plan = planner.create_plan("Move red cube to target")
    assert len(plan.subgoals) == 3
    assert plan.subgoals[0].skill == "PickSkill"
    assert plan.subgoals[0].id == "sg_001"
    assert not plan.subgoals[0].dependencies
    assert plan.subgoals[1].dependencies == ["sg_001"]
    
def test_validate_valid_plan():
    planner = HierarchicalPlanner()
    plan = planner.create_plan("Push block to edge")
    res = planner.validate_plan(plan)
    assert res.valid is True
    assert res.checked_subgoals == 2

def test_validate_unknown_skill():
    planner = HierarchicalPlanner()
    sg = PlannedSubgoal("sg_1", "FlySkill", {})
    plan = Plan("p1", "Fly", [sg], 0)
    res = planner.validate_plan(plan)
    assert res.valid is False
    assert any("Unknown skill" in e for e in res.errors)

def test_validate_circular_dependency():
    planner = HierarchicalPlanner()
    sg1 = PlannedSubgoal("sg_1", "PickSkill", {}, dependencies=["sg_2"])
    sg2 = PlannedSubgoal("sg_2", "MoveSkill", {}, dependencies=["sg_1"])
    plan = Plan("p1", "Cycle", [sg1, sg2], 0)
    res = planner.validate_plan(plan)
    assert res.valid is False
    assert any("Circular" in e for e in res.errors)
    
def test_validate_duplicate_id():
    planner = HierarchicalPlanner()
    sg1 = PlannedSubgoal("sg_1", "PickSkill", {})
    sg2 = PlannedSubgoal("sg_1", "MoveSkill", {})
    plan = Plan("p1", "Dup", [sg1, sg2], 0)
    res = planner.validate_plan(plan)
    assert res.valid is False
    assert any("Duplicate" in e for e in res.errors)

def test_plan_to_task_state():
    planner = HierarchicalPlanner()
    ts = TaskStateManager()
    plan = planner.create_plan("Move box to bin")
    planner.plan_to_task_state(plan, ts)
    assert len(ts.subgoals) == 3
    assert ts.subgoals[0].id == "sg_001"

def test_long_horizon():
    planner = HierarchicalPlanner()
    goal = "Move a to 1 and move b to 2 and move c to 3 and push d to 4"
    plan = planner.create_plan(goal)
    res = planner.validate_plan(plan)
    assert res.valid is True
    assert len(plan.subgoals) == 11
