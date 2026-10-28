import pytest
from src.hlmp.recovery.failure_classifier import FailureClassifier
from src.hlmp.recovery.models import FailureType
from src.hlmp.core.result import SkillResult

@pytest.fixture
def classifier():
    return FailureClassifier({"recovery": {"max_skill_duration": 5.0}})

def test_no_failure(classifier):
    res = SkillResult(True, "MoveSkill", "OK")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.NONE

def test_grasp_failure(classifier):
    res = SkillResult(False, "PickSkill", "Missed")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.GRASP_FAILURE
    assert "detached" in event.observed_state.lower()

def test_placement_failure(classifier):
    res = SkillResult(False, "PlaceSkill", "Failed to reach target.")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.PLACEMENT_FAILURE

def test_placement_tolerance_failure(classifier):
    res = SkillResult(False, "PlaceSkill", "Placement tolerance exceeded: dist=0.131")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.PLACEMENT_FAILURE

def test_push_approach_failure(classifier):
    res = SkillResult(False, "PushSkill", "Failed to approach object for pushing.")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.TARGET_NOT_REACHED

def test_timeout(classifier):
    res = SkillResult(False, "MoveSkill", "Timeout reached")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.TIMEOUT

def test_execution_error(classifier):
    res = SkillResult(False, "UnknownSkill", "Some weird crash")
    event = classifier.classify(res, {})
    assert event.failure_type == FailureType.EXECUTION_ERROR
