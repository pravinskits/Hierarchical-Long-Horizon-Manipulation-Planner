"""
Failure detection models.
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

class FailureType(str, Enum):
    NONE = "NONE"
    OBJECT_NOT_DETECTED = "OBJECT_NOT_DETECTED"
    GRASP_FAILURE = "GRASP_FAILURE"
    OBJECT_SLIPPED = "OBJECT_SLIPPED"
    TARGET_NOT_REACHED = "TARGET_NOT_REACHED"
    PLACEMENT_FAILURE = "PLACEMENT_FAILURE"
    COLLISION = "COLLISION"
    POSITION_ERROR = "POSITION_ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_ACTION = "INVALID_ACTION"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    UNKNOWN = "UNKNOWN"

@dataclass
class FailureEvent:
    failure_type: FailureType
    skill_name: str
    subgoal_id: str
    timestamp: float
    message: str
    expected_state: str = ""
    observed_state: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['failure_type'] = self.failure_type.value
        return d
