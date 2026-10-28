import pytest
from src.hlmp.llm.schemas import LLMSubgoalSchema, LLMPlanSchema, SchemaValidationError

def test_valid_schema():
    sg = LLMSubgoalSchema(
        id="sg_1",
        skill="MoveSkill",
        parameters={"target": "red"},
        preconditions=["robot_free"],
        expected_outcome=["at_target"],
        dependencies=[],
        priority=1
    )
    plan = LLMPlanSchema(goal="test", subgoals=[sg])
    assert plan.goal == "test"
    assert plan.subgoals[0].id == "sg_1"

def test_missing_required_field():
    with pytest.raises(TypeError):
        LLMSubgoalSchema(id="sg_1") # missing skill

def test_invalid_type():
    with pytest.raises(SchemaValidationError):
        LLMSubgoalSchema(id="sg_1", skill="MoveSkill", priority="high")
        
def test_from_dict():
    data = {
        "goal": "Test",
        "subgoals": [{"id": "s1", "skill": "Pick"}]
    }
    plan = LLMPlanSchema.from_dict(data)
    assert plan.goal == "Test"
