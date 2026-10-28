import pytest
from src.hlmp.core.planner import HybridPlanner
from src.hlmp.core.plan_models import Plan, PlannedSubgoal

class MockLLMPlanner:
    def __init__(self, plan_to_return):
        self.plan_to_return = plan_to_return
    def generate_plan(self, goal, scene):
        return self.plan_to_return

def test_llm_validation_fallback_on_unknown_skill():
    # Setup a mock LLM that hallucinates a skill
    bad_sg = PlannedSubgoal("sg_1", "FlySkill", {})
    bad_plan = Plan("p1", "Fly", [bad_sg], 0.0, "groq")
    
    hybrid = HybridPlanner({"llm": {"enabled": True}})
    hybrid.llm_planner = MockLLMPlanner(bad_plan)
    
    # When generating, it should reject "FlySkill" and fallback to deterministic
    plan = hybrid.create_plan("Move red cube to target")
    
    assert plan.planner_type == "deterministic"
    assert len(plan.subgoals) == 3 # the deterministic sequence
