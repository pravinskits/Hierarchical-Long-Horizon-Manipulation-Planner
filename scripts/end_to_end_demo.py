import os
import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.config import load_config
from src.hlmp.core.planner import HierarchicalPlanner
from src.hlmp.core.task_state import TaskStateManager, TaskStatus
from src.hlmp.core.result import SkillResult
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.robot import RobotArm
from src.hlmp.skills import get_skill_class
from src.hlmp.recovery.failure_detector import FailureDetector
from src.hlmp.recovery.failure_classifier import FailureClassifier
from src.hlmp.recovery.recovery_manager import RecoveryManager
from src.hlmp.recovery.models import FailureType

def main():
    print("========================================")
    print("PHASE 13: END-TO-END RESEARCH DEMONSTRATION")
    print("========================================")
    
    # Setup
    config = load_config(str(Path(__file__).parent.parent / "config" / "settings.yaml"))
    
    logger = logging.getLogger("EndToEndDemo")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("[EVENT] TASK_START")

    from src.hlmp.sim.scene import SceneManager
    from src.hlmp.sim.objects import ObjectManager

    # 1. Start required backend/simulation components
    logger.info("Initializing Simulation...")
    env = SimulationEnvironment(config, logger, headless=False)
    env.connect()
    
    scene_mgr = SceneManager(config, logger, env.client_id)
    scene_mgr.build_scene()
    
    obj_mgr = ObjectManager(config, logger, env.client_id)
    obj_mgr.populate_from_config()
    
    robot = RobotArm(config, logger, env.client_id)
    robot.load()
    robot.reset_to_initial()
    
    detector = FailureDetector(config, logger)
    recovery_manager = RecoveryManager(config, logger)
    
    # 2. Create a task from a natural-language goal
    goal = "Move the red cube to the target area and move the blue cube to the target area"
    logger.info(f"Natural-language goal: '{goal}'")
    
    # 3. Generate a hierarchical plan
    logger.info("Generating Hierarchical Plan...")
    planner = HierarchicalPlanner(logger)
    plan = planner.create_plan(goal)
    logger.info("[EVENT] PLAN_GENERATED")
    
    # 4. Validate the plan (done inside create_plan)
    
    # 5. Create TaskStateManager state
    ts = TaskStateManager(logger)
    planner.plan_to_task_state(plan, ts)
    
    logger.info("Task State Manager initialized with subgoals:")
    for sg in ts.subgoals:
        logger.info(f"  - {sg.id}: {sg.skill_name} {sg.parameters}")

    # Track metrics
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "goal": goal,
        "events": []
    }

    def log_event(event_type, details=""):
        logger.info(f"[EVENT] {event_type} - {details}")
        log_data["events"].append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "details": details
        })

    # 6. Execute the plan
    last_constraint_id = -1
    import pybullet as p
    
    while ts.status in (TaskStatus.NOT_STARTED, TaskStatus.RUNNING):
        sg = ts.get_current_subgoal()
        if not sg:
            break
            
        if sg.status.value in ("PENDING", "FAILED"):
            ts.start_subgoal()
            
        log_event("SUBGOAL_START", f"{sg.skill_name} {sg.parameters}")
        
        skill_class = get_skill_class(sg.skill_name)
        skill = skill_class(env, robot, config, logger)
        
        # Determine if we should inject a failure for demonstration
        inject_failure = False
        if "Pick" in sg.skill_name and "blue_cube" in sg.parameters.values() and sg.attempts == 1:
            log_event("FAILURE_INJECTED", "CONTROLLED EXPERIMENTAL FAILURE for pick skill")
            inject_failure = True
            
        try:
            # Resolve parameters
            exec_params = {}
            for k, v in sg.parameters.items():
                if isinstance(v, str):
                    if v in obj_mgr.objects:
                        obj_id = obj_mgr.objects[v]
                        exec_params["object_id"] = obj_id
                        pos, _ = p.getBasePositionAndOrientation(obj_id, physicsClientId=env.client_id)
                        exec_params["target_pos"] = list(pos)
                    elif "target" in v:
                        exec_params["target_pos"] = config["sim"]["objects"]["target_area"]["pos"]
                        
            if "Place" in sg.skill_name:
                exec_params["constraint_id"] = last_constraint_id
                
            if "Move" in sg.skill_name and "object_id" in exec_params:
                del exec_params["object_id"]
            
            print(f"DEBUG exec_params for {sg.skill_name}: {exec_params}")
            # 7. Execute actual skill outcome
            result = skill.execute(**exec_params)
            
            if hasattr(result, 'metadata') and "constraint_id" in result.metadata:
                last_constraint_id = result.metadata["constraint_id"]
            
            # Inject Failure if required
            if inject_failure:
                result.success = False
                result.message = "Failed to secure grasp on object"
                result.info = {"reason": "collision"}
                log_event("SUBGOAL_FAILURE", f"Controlled failure applied to {sg.skill_name}")
                
            # Detect actual skill outcomes
            context = {"force_failure": inject_failure}
            failure_event = detector.evaluate(result, context)
            
            if failure_event:
                log_event("FAILURE_DETECTED", f"Detector caught failure in {sg.skill_name}")
                log_event("FAILURE_CLASSIFIED", f"Type: {failure_event.failure_type.value}, Conf: {failure_event.confidence}")
                
                ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message=failure_event.message))
                
                # Select RecoveryDecision
                log_event("RECOVERY_START", f"Requesting recovery for {failure_event.failure_type.value}")
                recovery_result = recovery_manager.process_failure(failure_event, ts)
                
                log_event("RECOVERY_DECISION", f"Strategy chosen: {recovery_result.strategy.value}")
                
                if recovery_result.success:
                    log_event("RECOVERY_SUCCESS", "Adaptive recovery resolved the issue.")
                else:
                    log_event("RECOVERY_FAILED", "Adaptive recovery could not resolve the issue.")
                    ts.status = TaskStatus.FAILED
                    break
            else:
                ts.complete_subgoal(result)
                log_event("SUBGOAL_SUCCESS", f"{sg.skill_name} completed successfully")
                
        except Exception as e:
            ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message=str(e)))
            ts.status = TaskStatus.FAILED
            break

    # 10. Complete or abort the task based on actual state
    if ts.status == TaskStatus.COMPLETED:
        log_event("TASK_COMPLETE", "All subgoals achieved successfully.")
    else:
        log_event("TASK_FAILED", "Task could not be completed.")

    # 11. Print final metrics
    print("\n========================================")
    print("FINAL METRICS")
    print("========================================")
    print(f"Task Status: {ts.status.value}")
    prog = ts.get_progress()
    print(f"Subgoal Completion Rate: {prog['completed']}/{prog['total']} ({prog['percentage']*100:.1f}%)")
    print(f"Total Failure Events: {len(ts.get_failed_subgoals())}")
    
    # 12. Save structured execution log
    os.makedirs("results/raw", exist_ok=True)
    log_file = f"results/raw/end_to_end_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"\nStructured execution log saved to: {log_file}")
    
    env.disconnect()

if __name__ == "__main__":
    main()
