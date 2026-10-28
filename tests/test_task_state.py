"""
Tests for TaskStateManager.
"""

import pytest
import logging
import json
from src.hlmp.core.task_state import TaskStateManager, SubgoalStatus, TaskStatus, InvalidStateTransitionError
from src.hlmp.core.result import SkillResult

@pytest.fixture
def manager():
    logger = logging.getLogger("test_logger")
    return TaskStateManager(logger)

def test_task_creation_and_addition(manager):
    assert manager.status == TaskStatus.NOT_STARTED
    manager.add_subgoal("sg1", "Move")
    manager.add_subgoal("sg2", "Pick")
    assert len(manager.subgoals) == 2
    assert manager.get_current_subgoal().id == "sg1"

def test_valid_state_transitions(manager):
    manager.add_subgoal("sg1", "Move")
    
    # PENDING -> RUNNING
    sg = manager.start_subgoal()
    assert sg.status == SubgoalStatus.RUNNING
    assert manager.status == TaskStatus.RUNNING
    
    # RUNNING -> SUCCESS
    manager.complete_subgoal(SkillResult(success=True, skill_name="Move", message="OK"))
    assert manager.subgoals[0].status == SubgoalStatus.SUCCESS
    assert manager.status == TaskStatus.COMPLETED

def test_invalid_state_transitions(manager):
    manager.add_subgoal("sg1", "Move")
    
    # Cannot complete a pending subgoal
    with pytest.raises(InvalidStateTransitionError):
        manager.complete_subgoal(SkillResult(True, "Move", "OK"))
        
    manager.start_subgoal()
    
    # Cannot skip a running subgoal
    with pytest.raises(InvalidStateTransitionError):
        manager.skip_subgoal()
        
    # Cannot fail with a successful result
    with pytest.raises(ValueError):
        manager.fail_subgoal(SkillResult(True, "Move", "OK"))
        
    # Cannot complete with a failed result
    with pytest.raises(ValueError):
        manager.complete_subgoal(SkillResult(False, "Move", "Fail"))

def test_failure_and_retry(manager):
    manager.add_subgoal("sg1", "Move")
    manager.start_subgoal()
    manager.fail_subgoal(SkillResult(False, "Move", "Failed"))
    
    assert manager.get_current_subgoal().status == SubgoalStatus.FAILED
    assert manager.get_current_subgoal().attempts == 1
    
    manager.retry_subgoal()
    manager.start_subgoal() # attempt 2
    
    assert manager.get_current_subgoal().status == SubgoalStatus.RUNNING
    assert manager.get_current_subgoal().attempts == 2

def test_progress_and_json(manager):
    manager.add_subgoal("sg1", "Move")
    manager.add_subgoal("sg2", "Move")
    
    manager.start_subgoal()
    manager.complete_subgoal(SkillResult(True, "Move", "OK"))
    
    prog = manager.get_progress()
    assert prog["completed"] == 1
    assert prog["total"] == 2
    assert prog["percentage"] == 50.0
    
    json_str = manager.to_json()
    data = json.loads(json_str)
    assert data["status"] == "RUNNING"
    assert len(data["subgoals"]) == 2
