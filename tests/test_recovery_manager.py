import pytest
import logging
from src.hlmp.core.task_state import TaskStateManager
from src.hlmp.recovery.recovery_manager import RecoveryManager
from src.hlmp.recovery.recovery_strategy import RecoveryStrategy
from src.hlmp.recovery.models import FailureEvent, FailureType

@pytest.fixture
def manager():
    return RecoveryManager({"recovery": {"max_attempts": 3, "escalation_enabled": True}})

def create_event(ftype):
    return FailureEvent(
        failure_type=ftype,
        skill_name="TestSkill",
        subgoal_id="sg1",
        timestamp=0.0,
        message="Test"
    )

def test_grasp_failure_escalation(manager):
    event = create_event(FailureType.GRASP_FAILURE)
    
    d1 = manager.determine_strategy(event, 1)
    assert d1.strategy == RecoveryStrategy.REGRASP
    
    d2 = manager.determine_strategy(event, 2)
    assert d2.strategy == RecoveryStrategy.REPOSITION
    
    d3 = manager.determine_strategy(event, 3)
    assert d3.strategy == RecoveryStrategy.REPLAN

def test_timeout_retry(manager):
    event = create_event(FailureType.TIMEOUT)
    d1 = manager.determine_strategy(event, 1)
    assert d1.strategy == RecoveryStrategy.RETRY

def test_max_attempts_abort(manager):
    event = create_event(FailureType.GRASP_FAILURE)
    d4 = manager.determine_strategy(event, 4)
    assert d4.strategy == RecoveryStrategy.ABORT

def test_invalid_action_replan(manager):
    event = create_event(FailureType.INVALID_ACTION)
    d1 = manager.determine_strategy(event, 1)
    assert d1.strategy == RecoveryStrategy.REPLAN

def test_execution_integration(manager):
    ts = TaskStateManager()
    ts.add_subgoal("sg1", "Move")
    ts.start_subgoal()
    
    from src.hlmp.core.result import SkillResult
    ts.fail_subgoal(SkillResult(False, "Move", "Failed"))
    
    event = create_event(FailureType.TARGET_NOT_REACHED)
    dec = manager.determine_strategy(event, 1)
    res = manager.execute_recovery(dec, ts)
    
    assert res.success is True
