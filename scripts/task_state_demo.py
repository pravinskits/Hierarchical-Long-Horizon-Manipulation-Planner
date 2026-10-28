"""
Demonstration script for Task State Management logic.
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.core.task_state import TaskStateManager
from src.hlmp.core.result import SkillResult

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("TaskStateDemo")
    
    manager = TaskStateManager(logger)
    
    # Create sample multi-step task
    manager.add_subgoal("sg_1", "PickSkill", {"target": "red_cube"})
    manager.add_subgoal("sg_2", "MoveSkill", {"target": "target_area"})
    manager.add_subgoal("sg_3", "PlaceSkill", {"target": "target_area"})
    manager.add_subgoal("sg_4", "PickSkill", {"target": "blue_cube"})
    manager.add_subgoal("sg_5", "PlaceSkill", {"target": "target_area"})
    
    logger.info("--- Initial State ---")
    print(manager.get_progress()["text"])
    
    # 1. Start and Complete sg_1
    manager.start_subgoal()
    success_res = SkillResult(success=True, skill_name="PickSkill", message="Picked red cube.")
    manager.complete_subgoal(success_res)
    
    # 2. Start and Complete sg_2
    manager.start_subgoal()
    success_res = SkillResult(success=True, skill_name="MoveSkill", message="Moved to area.")
    manager.complete_subgoal(success_res)
    
    # 3. Start, Fail, Retry, and Complete sg_3
    manager.start_subgoal()
    fail_res = SkillResult(success=False, skill_name="PlaceSkill", message="Missed target.")
    manager.fail_subgoal(fail_res)
    
    logger.info("--- State after failure ---")
    print(manager.get_progress()["text"])
    
    logger.info("Retrying failed subgoal...")
    manager.retry_subgoal()
    manager.start_subgoal() # Starts attempt 2
    success_res = SkillResult(success=True, skill_name="PlaceSkill", message="Placed red cube.")
    manager.complete_subgoal(success_res)
    
    # 4. Skip sg_4
    manager.skip_subgoal()
    
    # 5. Complete sg_5
    manager.start_subgoal()
    success_res = SkillResult(success=True, skill_name="PlaceSkill", message="Placed blue cube.")
    manager.complete_subgoal(success_res)
    
    logger.info("--- Final Task State ---")
    print(manager.get_progress()["text"])
    
    logger.info("--- JSON Export ---")
    print(manager.to_json())

if __name__ == "__main__":
    main()
