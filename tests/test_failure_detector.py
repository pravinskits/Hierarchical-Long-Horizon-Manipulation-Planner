import pytest
import logging
from src.hlmp.recovery.failure_detector import FailureDetector
from src.hlmp.recovery.models import FailureType
from src.hlmp.core.result import SkillResult

def test_evaluate_success():
    detector = FailureDetector({})
    res = SkillResult(True, "PickSkill", "OK")
    event = detector.evaluate(res, {})
    assert event is None

def test_evaluate_failure():
    detector = FailureDetector({})
    res = SkillResult(False, "PickSkill", "Failed")
    event = detector.evaluate(res, {"subgoal_id": "sg1"})
    
    assert event is not None
    assert event.failure_type == FailureType.GRASP_FAILURE
    assert event.subgoal_id == "sg1"
    
def test_event_serialization():
    detector = FailureDetector({})
    res = SkillResult(False, "PickSkill", "Failed")
    event = detector.evaluate(res, {"subgoal_id": "sg1"})
    
    d = event.to_dict()
    assert d["failure_type"] == "GRASP_FAILURE"
    assert d["skill_name"] == "PickSkill"
