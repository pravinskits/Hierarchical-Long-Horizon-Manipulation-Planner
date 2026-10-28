"""
Demonstration script for Adaptive Recovery Management.
"""

import os
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.core.result import SkillResult
from src.hlmp.core.task_state import TaskStateManager
from src.hlmp.recovery import FailureDetector, RecoveryManager, FailureType, FailureEvent

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("RecoveryDemo")
    
    config = {
        "recovery": {
            "enabled": True,
            "max_attempts": 3,
            "escalation_enabled": True
        }
    }
    
    detector = FailureDetector(config, logger)
    manager = RecoveryManager(config, logger)
    task_state = TaskStateManager(logger)
    
    # 1-4. System startup & simulation setup
    logger.info("1-4. System setup and workspace creation initialized.\n")
    task_state.add_subgoal("sg_1", "PickSkill", {"target": "red_cube"})
    
    # 5-6. Execute Pick and intentionally cause grasp failure
    print("TASK STARTED\n--------------")
    print("Subgoal: Pick red cube")
    task_state.start_subgoal()
    
    simulated_result = SkillResult(
        success=False,
        skill_name="PickSkill",
        message="Failed to lift object."
    )
    task_state.fail_subgoal(simulated_result)
    
    # 7. Failure Detector
    context = {"subgoal_id": "sg_1"}
    event = detector.evaluate(simulated_result, context)
    
    if event:
        print("\nSKILL FAILURE\n--------------")
        print(f"Failure: {event.failure_type.value}")
        print(f"Confidence: {event.confidence:.2f}")
        
        # 8-10. Recovery Manager
        print("\nRECOVERY PIPELINE\n-----------------")
        result = manager.process_failure(event, task_state)
        
        print("\nRECOVERY RESULT\n---------------")
        print(f"Success: {result.success}")
        
        # 11-12. Continue Task
        if result.success:
            print("\nTASK CONTINUES\n--------------")
            
        print("\nRECOVERY HISTORY\n----------------")
        print(json.dumps(manager.history, indent=2))

if __name__ == "__main__":
    main()
