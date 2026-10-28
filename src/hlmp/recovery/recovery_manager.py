"""
Adaptive Recovery Manager Engine.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from src.hlmp.core.task_state import TaskStateManager
from src.hlmp.recovery.models import FailureEvent, FailureType
from src.hlmp.recovery.recovery_strategy import RecoveryStrategy, RecoveryDecision, RecoveryResult

class RecoveryManager:
    """
    Determines and executes recovery strategies based on failure events and task states.
    """
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config.get("recovery", {})
        self.logger = logger or logging.getLogger(__name__)
        self.max_attempts = self.config.get("max_attempts", 3)
        self.escalation_enabled = self.config.get("escalation_enabled", True)
        self.history: List[Dict[str, Any]] = []
        
    def process_failure(self, event: FailureEvent, task_state: TaskStateManager) -> RecoveryResult:
        """
        Main entry point for recovery processing.
        """
        self.logger.info("RECOVERY_START")
        
        # 1. Determine attempts
        subgoal = task_state.get_current_subgoal()
        attempt_num = subgoal.attempts if subgoal else 1
        
        # 2. Select Strategy
        decision = self.determine_strategy(event, attempt_num)
        self.logger.info(f"RECOVERY_DECISION | Strategy: {decision.strategy.value} | Reason: {decision.reason} | Attempt: {decision.attempt_number}/{self.max_attempts}")
        
        # 3. Execute
        result = self.execute_recovery(decision, task_state)
        
        # 4. Record history
        record = {
            "failure": event.failure_type.value,
            "strategy": decision.strategy.value,
            "attempt": decision.attempt_number,
            "success": result.success
        }
        self.history.append(record)
        
        if result.success:
            self.logger.info(f"RECOVERY_SUCCESS | {result.message}")
        else:
            self.logger.warning(f"RECOVERY_FAILURE | {result.message}")
            if decision.strategy == RecoveryStrategy.ABORT:
                self.logger.error("TASK_ABORT")
                
        return result

    def determine_strategy(self, event: FailureEvent, attempt_num: int) -> RecoveryDecision:
        """
        Deterministic escalating recovery policy.
        """
        strategy = RecoveryStrategy.ABORT
        reason = "Maximum attempts exceeded."
        
        if attempt_num > self.max_attempts:
            return self._build_decision(strategy, event, attempt_num, reason)
            
        ftype = event.failure_type
        
        if ftype in (FailureType.GRASP_FAILURE, FailureType.OBJECT_SLIPPED):
            if attempt_num == 1:
                strategy, reason = RecoveryStrategy.REGRASP, "Object was not attached to the gripper"
            elif attempt_num == 2 and self.escalation_enabled:
                strategy, reason = RecoveryStrategy.REPOSITION, "Escalating to reposition before regrasp"
            else:
                strategy, reason = RecoveryStrategy.REPLAN, "Multiple grasp failures, replanning required"
                self.logger.warning("RECOVERY_ESCALATION to REPLAN")
                
        elif ftype == FailureType.PLACEMENT_FAILURE:
            if attempt_num == 1:
                strategy, reason = RecoveryStrategy.RETRY, "Minor placement error, retrying"
            elif attempt_num == 2:
                strategy, reason = RecoveryStrategy.REPOSITION, "Escalating to reposition before placement"
            else:
                strategy, reason = RecoveryStrategy.REPLAN, "Multiple placement failures"
                
        elif ftype == FailureType.TARGET_NOT_REACHED:
            strategy, reason = RecoveryStrategy.REPOSITION, "Repositioning to reach target"
            if attempt_num >= 2:
                strategy, reason = RecoveryStrategy.ADJUST_TARGET, "Adjusting target tolerances/position"
                
        elif ftype == FailureType.TIMEOUT:
            strategy, reason = RecoveryStrategy.RETRY, "Retrying timed-out action"
            if attempt_num >= 2:
                strategy, reason = RecoveryStrategy.ABORT, "Repeated timeout, aborting"
                
        elif ftype == FailureType.COLLISION:
            strategy, reason = RecoveryStrategy.REPOSITION, "Repositioning to clear collision"
            
        elif ftype == FailureType.INVALID_ACTION:
            strategy, reason = RecoveryStrategy.REPLAN, "Invalid action requires replanning"
            
        else: # UNKNOWN, EXECUTION_ERROR, etc.
            strategy, reason = RecoveryStrategy.REPLAN, "Unknown failure requires replanning"
            
        return self._build_decision(strategy, event, attempt_num, reason)
        
    def _build_decision(self, strategy: RecoveryStrategy, event: FailureEvent, attempt: int, reason: str) -> RecoveryDecision:
        return RecoveryDecision(
            strategy=strategy,
            failure_type=event.failure_type,
            subgoal_id=event.subgoal_id,
            reason=reason,
            confidence=event.confidence,
            attempt_number=attempt,
            timestamp=time.time()
        )
        
    def execute_recovery(self, decision: RecoveryDecision, task_state: TaskStateManager) -> RecoveryResult:
        """
        Executes the strategy and updates task state.
        """
        start_time = time.time()
        success = False
        message = ""
        
        if decision.strategy in (RecoveryStrategy.RETRY, RecoveryStrategy.REGRASP, RecoveryStrategy.REPOSITION, RecoveryStrategy.ADJUST_TARGET):
            task_state.retry_subgoal()
            success = True
            message = f"Successfully executed {decision.strategy.value} action."
            
        elif decision.strategy == RecoveryStrategy.SKIP:
            task_state.skip_subgoal()
            success = True
            message = "Skipped problematic subgoal."
            
        elif decision.strategy == RecoveryStrategy.REPLAN:
            success = False
            message = "Replanning requested but not implemented."
            
        elif decision.strategy == RecoveryStrategy.ABORT:
            success = False
            message = "Task aborted."
            
        duration = time.time() - start_time
        
        return RecoveryResult(
            success=success,
            strategy=decision.strategy,
            message=message,
            duration=duration,
            previous_failure=decision.failure_type.value
        )
