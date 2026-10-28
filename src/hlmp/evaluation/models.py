from dataclasses import dataclass, field, asdict
from typing import Dict, Any

@dataclass
class ExperimentResult:
    experiment_id: str
    timestamp: float
    system: str
    scenario: str
    seed: int
    horizon: int
    failure_rate: float
    task_success: bool
    completed_subgoals: int
    total_subgoals: int
    failure_count: int
    failure_types: Dict[str, int] = field(default_factory=dict)
    injected_failure_count: int = 0
    natural_failure_count: int = 0
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    execution_time: float = 0.0
    task_status: str = "UNKNOWN"
    abort_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
