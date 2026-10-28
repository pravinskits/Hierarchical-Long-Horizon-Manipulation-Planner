import time
import uuid
import logging
import random
from typing import Dict, Any, List
from .models import ExperimentResult
from src.hlmp.core.planner import HierarchicalPlanner
from src.hlmp.core.task_state import TaskStateManager, TaskStatus, SubgoalStatus
from src.hlmp.experiments.scenarios import ScenarioGenerator
from src.hlmp.recovery.recovery_manager import RecoveryManager
from src.hlmp.recovery.models import FailureEvent, FailureType

class BenchmarkRunner:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def run_single_experiment(self, system: str, horizon: int, failure_rate: float, seed: int) -> ExperimentResult:
        start_time = time.time()
        random.seed(seed)
        
        gen = ScenarioGenerator(seed)
        goal = gen.generate_long_horizon(horizon)
        
        planner = HierarchicalPlanner(self.logger)
        plan = planner.create_plan(goal)
        
        # Limit to exact horizon for accurate tests
        if len(plan.subgoals) > horizon:
            plan.subgoals = plan.subgoals[:horizon]
        elif len(plan.subgoals) < horizon:
            # Duplicate to match horizon
            while len(plan.subgoals) < horizon:
                plan.subgoals.append(plan.subgoals[-1])
        
        ts = TaskStateManager()
        planner.plan_to_task_state(plan, ts)
        
        rm = RecoveryManager({})
        
        res = ExperimentResult(
            experiment_id=uuid.uuid4().hex,
            timestamp=start_time,
            system=system,
            scenario="auto_generated",
            seed=seed,
            horizon=horizon,
            failure_rate=failure_rate,
            task_success=False,
            completed_subgoals=0,
            total_subgoals=len(plan.subgoals),
            failure_count=0
        )
        
        self.logger.info(f"EXPERIMENT_START | sys={system} hor={horizon} fail={failure_rate} seed={seed}")
        
        from src.hlmp.core.result import SkillResult
        
        while ts.status in (TaskStatus.NOT_STARTED, TaskStatus.RUNNING):
            sg = ts.get_current_subgoal()
            if not sg:
                break
                
            if sg.status in (SubgoalStatus.PENDING, SubgoalStatus.FAILED):
                ts.start_subgoal()
                
            is_failure = random.random() < failure_rate
            
            if not is_failure:
                ts.complete_subgoal(SkillResult(skill_name=sg.skill_name, success=True, message="Mock success"))
                res.completed_subgoals += 1
            else:
                self.logger.warning("FAILURE_INJECTED")
                ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message="Injected simulation failure"))
                res.failure_count += 1
                res.injected_failure_count += 1
                
                if system == "OPEN_LOOP":
                    ts.status = TaskStatus.FAILED
                    res.abort_reason = "Open loop failure"
                    break
                elif system == "HIERARCHICAL_NO_RECOVERY":
                    ts.status = TaskStatus.FAILED
                    res.abort_reason = "No recovery configured"
                    break
                elif system == "HIERARCHICAL_SIMPLE_RETRY":
                    res.recovery_attempts += 1
                    if sg.attempts < 3:
                        ts.retry_subgoal()
                        res.successful_recoveries += 1
                    else:
                        ts.status = TaskStatus.FAILED
                        res.abort_reason = "Max retries exceeded"
                        break
                elif system == "FULL_ADAPTIVE_RECOVERY":
                    res.recovery_attempts += 1
                    event = FailureEvent(failure_type=FailureType.GRASP_FAILURE, skill_name=sg.skill_name, subgoal_id=sg.id, timestamp=1.0, message="Mock")
                    decision = rm.process_failure(event, ts)
                    if decision.success:
                        res.successful_recoveries += 1
                        ts.retry_subgoal()
                    else:
                        ts.status = TaskStatus.FAILED
                        res.abort_reason = "Adaptive recovery aborted"
                        break
                        
        res.task_success = (ts.status == TaskStatus.COMPLETED)
        res.task_status = ts.status.value
        res.execution_time = time.time() - start_time
        
        self.logger.info(f"EXPERIMENT_COMPLETE | Success: {res.task_success}")
        return res
