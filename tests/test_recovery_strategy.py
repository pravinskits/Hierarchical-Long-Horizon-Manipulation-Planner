import pytest
from src.hlmp.recovery.recovery_strategy import RecoveryStrategy, RecoveryDecision
from src.hlmp.recovery.models import FailureType

def test_decision_serialization():
    dec = RecoveryDecision(
        strategy=RecoveryStrategy.REGRASP,
        failure_type=FailureType.GRASP_FAILURE,
        subgoal_id="sg1",
        reason="Test",
        confidence=0.9,
        attempt_number=1
    )
    d = dec.to_dict()
    assert d["strategy"] == "REGRASP"
    assert d["failure_type"] == "GRASP_FAILURE"
    assert d["attempt_number"] == 1
