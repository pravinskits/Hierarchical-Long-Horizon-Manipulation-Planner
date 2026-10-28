from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TaskCreateRequest(BaseModel):
    goal: str = Field(..., description="The high-level goal for the manipulation task.")

class TaskResponse(BaseModel):
    task_id: str
    goal: str
    status: str

class PlanRequest(BaseModel):
    planner: str = Field(default="deterministic", description="The planner to use: 'deterministic' or 'groq'.")

class SubgoalSchema(BaseModel):
    id: str
    skill_name: str
    parameters: Dict[str, Any]
    status: str
    attempts: int
    error_message: Optional[str] = ""

class PlanResponse(BaseModel):
    task_id: str
    planner: str
    subgoals: List[SubgoalSchema]

class TaskStateResponse(BaseModel):
    task_id: str
    goal: str
    status: str
    progress_percentage: float
    current_subgoal: Optional[SubgoalSchema] = None
    completed_subgoals: List[SubgoalSchema]
    pending_subgoals: List[SubgoalSchema]
    failed_subgoals: List[SubgoalSchema]

class ExecuteResponse(BaseModel):
    task_id: str
    status: str
    message: str

class FailureEventResponse(BaseModel):
    id: int
    task_id: str
    timestamp: float
    skill_name: str
    subgoal_id: str
    failure_type: str
    message: str

class RecoveryEventResponse(BaseModel):
    id: int
    task_id: str
    timestamp: float
    strategy: str
    failure_type: str
    success: bool

class AbortRequest(BaseModel):
    reason: Optional[str] = "User requested abort"

class AbortResponse(BaseModel):
    task_id: str
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    simulation_available: bool
    llm_enabled: bool

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Dict[str, Any]
