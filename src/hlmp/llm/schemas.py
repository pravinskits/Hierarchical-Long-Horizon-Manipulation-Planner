from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

class MissingAPIKey(Exception):
    pass

class LLMConnectionError(Exception):
    pass

class LLMTimeoutError(Exception):
    pass

class InvalidLLMResponse(Exception):
    pass

class SchemaValidationError(Exception):
    pass

class UnsupportedLLMPlan(Exception):
    pass

@dataclass
class LLMSubgoalSchema:
    id: str
    skill: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    expected_outcome: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    
    def __post_init__(self):
        if not isinstance(self.id, str):
            raise SchemaValidationError("id must be a string")
        if not isinstance(self.skill, str):
            raise SchemaValidationError("skill must be a string")
        if not isinstance(self.priority, int):
            raise SchemaValidationError("priority must be an int")

@dataclass
class LLMPlanSchema:
    goal: str
    subgoals: List[LLMSubgoalSchema]
    
    def __post_init__(self):
        if not isinstance(self.goal, str):
            raise SchemaValidationError("goal must be a string")
        if not isinstance(self.subgoals, list):
            raise SchemaValidationError("subgoals must be a list")
            
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMPlanSchema':
        if "goal" not in data or "subgoals" not in data:
            raise SchemaValidationError("Missing required fields")
        try:
            subgoals = [LLMSubgoalSchema(**sg) for sg in data["subgoals"]]
        except TypeError as e:
            raise SchemaValidationError(f"Invalid subgoal format: {e}")
            
        return cls(goal=data["goal"], subgoals=subgoals)
