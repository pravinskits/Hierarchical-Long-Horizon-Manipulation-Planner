from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

@dataclass
class PlannedSubgoal:
    id: str
    skill: str
    parameters: Dict[str, Any]
    preconditions: List[str] = field(default_factory=list)
    expected_outcome: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    status: str = "PENDING"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Plan:
    plan_id: str
    original_goal: str
    subgoals: List[PlannedSubgoal]
    created_at: float
    planner_type: str = "deterministic"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['subgoals'] = [sg.to_dict() for sg in self.subgoals]
        return d

@dataclass
class PlanValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked_subgoals: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
