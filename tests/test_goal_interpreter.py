import pytest
from src.hlmp.core.goal_interpreter import GoalInterpreter

def test_interpret_move():
    gi = GoalInterpreter()
    res = gi.interpret("Move the red cube to the target")
    assert len(res) == 3
    assert res[0] == {"action": "pick", "object": "red_cube"}
    assert res[1] == {"action": "move", "object": "red_cube", "target": "target"}
    assert res[2] == {"action": "place", "object": "red_cube", "target": "target"}

def test_interpret_push():
    gi = GoalInterpreter()
    res = gi.interpret("Push the blue cube toward the edge")
    assert len(res) == 2
    assert res[0] == {"action": "move", "object": "blue_cube"}
    assert res[1] == {"action": "push", "object": "blue_cube", "target": "edge"}

def test_multi_object():
    gi = GoalInterpreter()
    res = gi.interpret("Move red cube to target and place blue cube beside it")
    assert len(res) == 6
    assert res[3] == {"action": "pick", "object": "blue_cube"}
    
def test_interpret_stack():
    gi = GoalInterpreter()
    res = gi.interpret("Stack the red cube on top of the blue cube")
    assert len(res) == 2
    assert res[0] == {"action": "pick", "object": "red_cube"}
    assert res[1] == {"action": "place", "object": "red_cube", "target": "blue_cube"}

def test_invalid_goal():
    gi = GoalInterpreter()
    with pytest.raises(ValueError):
        gi.interpret("Teach the robot to cook pasta")
