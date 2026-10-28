"""
Task State Management module.
"""

import time
import json
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from src.hlmp.core.result import SkillResult

class SubgoalStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

@dataclass
class Subgoal:
    id: str
    skill_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: SubgoalStatus = SubgoalStatus.PENDING
    attempts: int = 0
    start_time: float = 0.0
    completion_time: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TaskStateManager:
    """
    Manages the overall task state, subgoal lifecycles, and enforces state transitions.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.subgoals: List[Subgoal] = []
        self.current_subgoal_index: int = -1
        self.status: TaskStatus = TaskStatus.NOT_STARTED
        self.task_start_time: float = 0.0
        self.task_end_time: float = 0.0
        
    def add_subgoal(self, subgoal_id: str, skill_name: str, parameters: Dict[str, Any] = None) -> None:
        """Adds a new subgoal to the task sequence."""
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            raise InvalidStateTransitionError("Cannot add subgoals to a completed or failed task.")
            
        sg = Subgoal(id=subgoal_id, skill_name=skill_name, parameters=parameters or {})
        self.subgoals.append(sg)
        
        if self.current_subgoal_index == -1:
            self.current_subgoal_index = 0
            
    def get_current_subgoal(self) -> Optional[Subgoal]:
        """Returns the current subgoal if one exists and the task is not complete."""
        if 0 <= self.current_subgoal_index < len(self.subgoals):
            return self.subgoals[self.current_subgoal_index]
        return None
        
    def start_subgoal(self) -> Subgoal:
        """Starts the current subgoal."""
        sg = self.get_current_subgoal()
        if not sg:
            raise InvalidStateTransitionError("No current subgoal to start.")
            
        if sg.status not in (SubgoalStatus.PENDING, SubgoalStatus.FAILED):
            raise InvalidStateTransitionError(f"Cannot start subgoal from state {sg.status}")
            
        if self.status == TaskStatus.NOT_STARTED:
            self.status = TaskStatus.RUNNING
            self.task_start_time = time.time()
            
        sg.status = SubgoalStatus.RUNNING
        sg.attempts += 1
        sg.start_time = time.time()
        sg.error_message = ""
        self.logger.info(f"Started subgoal: {sg.id} (Attempt {sg.attempts})")
        return sg

    def complete_subgoal(self, result: SkillResult) -> None:
        """Marks the current running subgoal as successful."""
        sg = self.get_current_subgoal()
        if not sg or sg.status != SubgoalStatus.RUNNING:
            raise InvalidStateTransitionError("Can only complete a RUNNING subgoal.")
            
        if not result.success:
            raise ValueError("Cannot complete a subgoal with a failed SkillResult. Use fail_subgoal.")
            
        sg.status = SubgoalStatus.SUCCESS
        sg.completion_time = time.time()
        sg.metadata = result.metadata
        self.logger.info(f"Completed subgoal: {sg.id}")
        
        self._advance_task()
        
    def fail_subgoal(self, result: SkillResult) -> None:
        """Marks the current running subgoal as failed."""
        sg = self.get_current_subgoal()
        if not sg or sg.status != SubgoalStatus.RUNNING:
            raise InvalidStateTransitionError("Can only fail a RUNNING subgoal.")
            
        if result.success:
            raise ValueError("Cannot fail a subgoal with a successful SkillResult. Use complete_subgoal.")
            
        sg.status = SubgoalStatus.FAILED
        sg.completion_time = time.time()
        sg.error_message = result.message
        sg.metadata = result.metadata
        self.logger.warning(f"Failed subgoal: {sg.id} | Reason: {sg.error_message}")
        
    def skip_subgoal(self) -> None:
        """Skips a pending or failed subgoal and advances to the next."""
        sg = self.get_current_subgoal()
        if not sg:
            raise InvalidStateTransitionError("No current subgoal to skip.")
            
        if sg.status not in (SubgoalStatus.PENDING, SubgoalStatus.FAILED):
            raise InvalidStateTransitionError(f"Cannot skip subgoal from state {sg.status}")
            
        sg.status = SubgoalStatus.SKIPPED
        sg.completion_time = time.time()
        self.logger.info(f"Skipped subgoal: {sg.id}")
        self._advance_task()
        
    def retry_subgoal(self) -> None:
        """Retries a failed subgoal (essentially sets it up to be started again)."""
        sg = self.get_current_subgoal()
        if not sg or sg.status != SubgoalStatus.FAILED:
            raise InvalidStateTransitionError("Can only retry a FAILED subgoal.")
        self.logger.info(f"Preparing to retry subgoal: {sg.id}")
        
    def _advance_task(self) -> None:
        """Advances the current subgoal index. If at the end, marks task completed."""
        self.current_subgoal_index += 1
        if self.current_subgoal_index >= len(self.subgoals):
            self.status = TaskStatus.COMPLETED
            self.task_end_time = time.time()
            self.logger.info("All subgoals finished. Task COMPLETED.")
            
    def get_pending_subgoals(self) -> List[Subgoal]:
        return [sg for sg in self.subgoals if sg.status == SubgoalStatus.PENDING]
        
    def get_completed_subgoals(self) -> List[Subgoal]:
        return [sg for sg in self.subgoals if sg.status == SubgoalStatus.SUCCESS]
        
    def get_failed_subgoals(self) -> List[Subgoal]:
        return [sg for sg in self.subgoals if sg.status == SubgoalStatus.FAILED]
        
    def is_task_complete(self) -> bool:
        return self.status == TaskStatus.COMPLETED
        
    def is_task_failed(self) -> bool:
        return self.status == TaskStatus.FAILED
        
    def get_progress(self) -> Dict[str, Any]:
        """Returns a summary of the current task progress."""
        total = len(self.subgoals)
        completed = len(self.get_completed_subgoals())
        skipped = len([sg for sg in self.subgoals if sg.status == SubgoalStatus.SKIPPED])
        
        progress = 0.0 if total == 0 else ((completed + skipped) / total) * 100.0
        
        return {
            "completed": completed,
            "skipped": skipped,
            "total": total,
            "percentage": round(progress, 2),
            "status": self.status.value,
            "text": f"Task progress:\n{completed + skipped} / {total} subgoals completed\n{progress:.2f}%"
        }
        
    def reset(self) -> None:
        """Resets the task state manager completely."""
        self.subgoals = []
        self.current_subgoal_index = -1
        self.status = TaskStatus.NOT_STARTED
        self.task_start_time = 0.0
        self.task_end_time = 0.0
        self.logger.info("TaskStateManager reset.")
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete task state to a dictionary."""
        return {
            "status": self.status.value,
            "task_start_time": self.task_start_time,
            "task_end_time": self.task_end_time,
            "current_subgoal_index": self.current_subgoal_index,
            "progress": self.get_progress(),
            "subgoals": [sg.to_dict() for sg in self.subgoals]
        }
        
    def to_json(self) -> str:
        """Serializes the complete task state to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
