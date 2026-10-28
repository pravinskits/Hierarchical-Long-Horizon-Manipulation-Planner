"""
Recovery Strategy and Models.
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from .models import FailureType

class RecoveryStrategy(str, Enum):
    RETRY = "RETRY"
    REPOSITION = "REPOSITION"
    REGRASP = "REGRASP"
    ADJUST_TARGET = "ADJUST_TARGET"
    REPLAN = "REPLAN"
    SKIP = "SKIP"
    ABORT = "ABORT"

@dataclass
class RecoveryDecision:
    strategy: RecoveryStrategy
    failure_type: FailureType
    subgoal_id: str
    reason: str
    confidence: float
    attempt_number: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['strategy'] = self.strategy.value
        d['failure_type'] = self.failure_type.value if self.failure_type else "UNKNOWN"
        return d

@dataclass
class RecoveryResult:
    success: bool
    strategy: RecoveryStrategy
    message: str
    duration: float = 0.0
    previous_failure: Optional[str] = None
    state_before: Dict[str, Any] = field(default_factory=dict)
    state_after: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['strategy'] = self.strategy.value
        return d
