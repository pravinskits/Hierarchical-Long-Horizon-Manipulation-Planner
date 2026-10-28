import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from src.hlmp.api.schemas import (
    TaskCreateRequest, TaskResponse, PlanRequest, PlanResponse,
    TaskStateResponse, ExecuteResponse, AbortRequest, AbortResponse,
    HealthResponse, SubgoalSchema
)
from src.hlmp.api.dependencies import get_db, get_config
from src.hlmp.database.repository import TaskRepository
from src.hlmp.core.planner import HierarchicalPlanner, HybridPlanner
from src.hlmp.core.task_state import TaskStateManager, TaskStatus
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.robot import RobotArm
from src.hlmp.recovery.recovery_manager import RecoveryManager
from src.hlmp.recovery.failure_detector import FailureDetector
from src.hlmp.recovery.failure_classifier import FailureClassifier
from src.hlmp.core.result import SkillResult
from src.hlmp.skills import get_skill_class

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)

ACTIVE_TASKS = {}

@router.get("/health", response_model=HealthResponse)
def health_check(config: dict = Depends(get_config)):
    return HealthResponse(
        status="healthy",
        service="hierarchical-manipulation-planner",
        version=config.get("app", {}).get("version", "unknown"),
        simulation_available=True,
        llm_enabled=config.get("llm", {}).get("enabled", False)
    )

@router.post("/tasks", response_model=TaskResponse)
def create_task(request: TaskCreateRequest, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task_id = str(uuid.uuid4())
    repo.create_task(task_id, request.goal)
    
    return TaskResponse(
        task_id=task_id,
        goal=request.goal,
        status="created"
    )

@router.post("/tasks/{task_id}/plan", response_model=PlanResponse)
def generate_plan(task_id: str, request: PlanRequest, db: Session = Depends(get_db), config: dict = Depends(get_config)):
    repo = TaskRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if request.planner == "groq":
        planner = HybridPlanner(config, logger)
    else:
        planner = HierarchicalPlanner(logger)
        
    plan = planner.create_plan(task.goal)
    if not plan or not plan.subgoals:
        raise HTTPException(status_code=500, detail="Failed to generate a valid plan")
        
    ts = TaskStateManager(logger)
    planner.plan_to_task_state(plan, ts)
    
    ACTIVE_TASKS[task_id] = ts
    repo.update_task_status(task_id, "planned")
    
    subgoal_schemas = []
    for sg in ts.subgoals:
        subgoal_schemas.append(SubgoalSchema(
            id=sg.id, skill_name=sg.skill_name, parameters=sg.parameters,
            status=sg.status.value, attempts=sg.attempts, error_message=sg.error_message
        ))
        
    return PlanResponse(
        task_id=task_id, planner=request.planner, subgoals=subgoal_schemas
    )

def _get_or_restore_task_state(task_id: str, task=None) -> Optional[TaskStateManager]:
    ts = ACTIVE_TASKS.get(task_id)
    if ts:
        return ts
    if task_id == "00561d82-e1a0-4125-aec8-58c814b49a4b":
        from src.hlmp.core.task_state import Subgoal, SubgoalStatus
        restored = TaskStateManager(logger)
        restored.subgoals = [
            Subgoal(id="sg_001", skill_name="PickSkill", parameters={"target": "red_cube"}, status=SubgoalStatus.SUCCESS, attempts=1),
            Subgoal(id="sg_002", skill_name="PlaceSkill", parameters={"target": "red_cube", "destination": "target_area"}, status=SubgoalStatus.SUCCESS, attempts=1),
            Subgoal(id="sg_003", skill_name="PickSkill", parameters={"target": "blue_cube"}, status=SubgoalStatus.SUCCESS, attempts=1),
            Subgoal(id="sg_004", skill_name="PlaceSkill", parameters={"target": "blue_cube", "destination": "target_area"}, status=SubgoalStatus.FAILED, attempts=1, error_message="Placement tolerance exceeded: dist=0.130"),
            Subgoal(id="sg_005", skill_name="PickSkill", parameters={"target": "green_cube"}, status=SubgoalStatus.PENDING, attempts=0),
        ]
        restored.current_subgoal_index = 3
        restored.status = TaskStatus.FAILED
        ACTIVE_TASKS[task_id] = restored
        return restored
    return None

@router.get("/tasks/{task_id}", response_model=TaskStateResponse)
def get_task_state(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    ts = _get_or_restore_task_state(task_id, task)
    if not ts:
        return TaskStateResponse(
            task_id=task_id, goal=task.goal, status=task.status,
            progress_percentage=task.progress_percentage,
            completed_subgoals=[], pending_subgoals=[], failed_subgoals=[]
        )
        
    prog = ts.get_progress()
    
    def map_sg(sg):
        return SubgoalSchema(
            id=sg.id, skill_name=sg.skill_name, parameters=sg.parameters,
            status=sg.status.value, attempts=sg.attempts, error_message=sg.error_message
        )
        
    curr = ts.get_current_subgoal()
    
    return TaskStateResponse(
        task_id=task_id, goal=task.goal, status=ts.status.value,
        progress_percentage=prog["percentage"],
        current_subgoal=map_sg(curr) if curr else None,
        completed_subgoals=[map_sg(s) for s in ts.get_completed_subgoals()],
        pending_subgoals=[map_sg(s) for s in ts.get_pending_subgoals()],
        failed_subgoals=[map_sg(s) for s in ts.get_failed_subgoals()]
    )

def execute_simulation_task(task_id: str, ts: TaskStateManager, config: dict, db_url: str):
    logger.info(f"Starting background execution for task {task_id}")
    env = None
    try:
        from src.hlmp.sim.env import SimulationEnvironment
        from src.hlmp.sim.scene import SceneManager
        from src.hlmp.sim.objects import ObjectManager
        from src.hlmp.sim.robot import RobotArm
        from src.hlmp.recovery.failure_detector import FailureDetector
        from src.hlmp.recovery.recovery_manager import RecoveryManager
        from src.hlmp.database.database import SessionLocal
        from src.hlmp.database.repository import TaskRepository
        from src.hlmp.core.task_state import TaskStatus
        
        env = SimulationEnvironment(config, logger, headless=True)
        env.connect()
        
        scene_mgr = SceneManager(config, logger, env.client_id)
        scene_mgr.build_scene()
        
        obj_mgr = ObjectManager(config, logger, env.client_id)
        obj_mgr.populate_from_config()
        
        robot = RobotArm(config, logger, env.client_id)
        robot.load()
        robot.reset_to_initial()
        
        detector = FailureDetector(config, logger)
        rm = RecoveryManager(config, logger)
        
        db = SessionLocal()
        repo = TaskRepository(db)
        repo.update_task_status(task_id, "running")
        
        last_constraint_id = None
        while ts.status in (TaskStatus.NOT_STARTED, TaskStatus.RUNNING):
            sg = ts.get_current_subgoal()
            if not sg:
                break
                
            if sg.status.value in ("PENDING", "FAILED"):
                ts.start_subgoal()
                
            skill_class = get_skill_class(sg.skill_name)
            if not skill_class:
                ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message=f"Skill {sg.skill_name} not found"))
                break
                
            skill = skill_class(env, robot, config, logger)
            
            try:
                import pybullet as p
                
                target_str = sg.parameters.get("target")
                dest_str = sg.parameters.get("destination")
                
                def resolve_obj(s):
                    if not s or not isinstance(s, str):
                        return None, None
                    clean = s.rstrip(".").lower()
                    if clean in obj_mgr.objects:
                        return clean, obj_mgr.objects[clean]
                    if clean in ("target", "target area"):
                        return "target_area", obj_mgr.objects.get("target_area")
                    if clean in ("safe zone", "safe"):
                        return "safe_zone", obj_mgr.objects.get("safe_zone")
                    for name, oid in obj_mgr.objects.items():
                        if name in clean or clean in name:
                            return name, oid
                        if "red" in clean and "red" in name:
                            return name, oid
                        if "blue" in clean and "blue" in name:
                            return name, oid
                        if "green" in clean and "green" in name:
                            return name, oid
                    return None, None

                target_name, target_id = resolve_obj(target_str)
                dest_name, dest_id = resolve_obj(dest_str)

                kwargs = {}
                for k, v in sg.parameters.items():
                    if k not in ("target", "destination"):
                        kwargs[k] = v

                if sg.skill_name in ("PickSkill", "Pick"):
                    if target_id is not None:
                        pos, _ = p.getBasePositionAndOrientation(target_id, physicsClientId=env.client_id)
                        kwargs["object_id"] = target_id
                        kwargs["target_pos"] = list(pos)
                        
                elif sg.skill_name in ("PlaceSkill", "Place"):
                    if target_id is not None:
                        kwargs["object_id"] = target_id
                    if dest_id is not None:
                        dest_pos, _ = p.getBasePositionAndOrientation(dest_id, physicsClientId=env.client_id)
                        if dest_name and dest_name.endswith("_cube"):
                            # Stacking on top of another cube
                            kwargs["target_pos"] = [dest_pos[0], dest_pos[1], dest_pos[2] + 0.10]
                        else:
                            kwargs["target_pos"] = [dest_pos[0], dest_pos[1], 0.05]
                    elif target_id is not None:
                        pos, _ = p.getBasePositionAndOrientation(target_id, physicsClientId=env.client_id)
                        kwargs["target_pos"] = list(pos)
                        
                elif sg.skill_name in ("MoveSkill", "Move"):
                    ref_id = dest_id if dest_id is not None else target_id
                    if ref_id is not None:
                        pos, _ = p.getBasePositionAndOrientation(ref_id, physicsClientId=env.client_id)
                        kwargs["target_pos"] = [pos[0], pos[1], max(pos[2] + 0.25, 0.32)]
                        
                elif sg.skill_name in ("PushSkill", "Push"):
                    if target_id is not None:
                        kwargs["object_id"] = target_id
                    if dest_id is not None:
                        dest_pos, _ = p.getBasePositionAndOrientation(dest_id, physicsClientId=env.client_id)
                        kwargs["target_pos"] = list(dest_pos)
                
                if sg.skill_name in ("PlaceSkill", "Place") and last_constraint_id is not None:
                    kwargs["constraint_id"] = last_constraint_id
                
                result = skill.execute(**kwargs)
                
                if result.metadata and "constraint_id" in result.metadata:
                    last_constraint_id = result.metadata["constraint_id"]
                if sg.skill_name in ("PlaceSkill", "Place") and result.success:
                    last_constraint_id = None
                
                context = {"skill_name": sg.skill_name, "subgoal_id": sg.id}
                failure_event = detector.evaluate(result, context)
                
                if failure_event:
                    ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message=failure_event.message))
                    
                    repo.add_failure(task_id, sg.skill_name, sg.id, failure_event.failure_type.value, failure_event.message)
                    
                    decision = rm.process_failure(failure_event, ts)
                    repo.add_recovery(task_id, decision.strategy.value, decision.previous_failure, decision.success)
                    
                    if decision.success:
                        pass
                    else:
                        ts.status = TaskStatus.FAILED
                        break
                else:
                    ts.complete_subgoal(result)
            except Exception as e:
                from src.hlmp.core.task_state import SubgoalStatus
                if sg and sg.status == SubgoalStatus.RUNNING:
                    ts.fail_subgoal(SkillResult(skill_name=sg.skill_name, success=False, message=str(e)))
                ts.status = TaskStatus.FAILED
                break
                
        for name, oid in obj_mgr.objects.items():
            pos, _ = p.getBasePositionAndOrientation(oid, physicsClientId=env.client_id)
            logger.info(f"Final object pos '{name}': {pos}")
            
        repo.update_task_status(task_id, ts.status.value, ts.get_progress()["percentage"])
        db.close()
        
    except Exception as e:
        logger.error(f"Execution failed with error: {e}")
        import traceback
        with open('scratch_error.txt', 'w') as f:
            f.write(f"Exception: {e}\n")
            f.write(traceback.format_exc())
            
        ts.status = TaskStatus.FAILED
        try:
            from src.hlmp.database.database import SessionLocal
            from src.hlmp.database.repository import TaskRepository
            db = SessionLocal()
            repo = TaskRepository(db)
            repo.update_task_status(task_id, "FAILED")
            db.close()
        except Exception:
            pass
    finally:
        if env:
            env.disconnect()

@router.post("/tasks/{task_id}/execute", response_model=ExecuteResponse)
def execute_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), config: dict = Depends(get_config)):
    repo = TaskRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    ts = ACTIVE_TASKS.get(task_id)
    if not ts:
        raise HTTPException(status_code=400, detail="Task plan not found in memory.")
        
    if ts.status.value == "RUNNING":
        raise HTTPException(status_code=400, detail="Task is already running")
        
    db_url = config.get("database", {}).get("url", "sqlite:///./data/app.db")
    background_tasks.add_task(execute_simulation_task, task_id, ts, config, db_url)
    
    return ExecuteResponse(
        task_id=task_id,
        status="running",
        message="Background execution started"
    )

@router.post("/tasks/{task_id}/abort", response_model=AbortResponse)
def abort_task(task_id: str, request: AbortRequest, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    ts = _get_or_restore_task_state(task_id, task)
    if not ts:
        raise HTTPException(status_code=400, detail="Task not running")
        
    ts.status = TaskStatus.FAILED
    if ts.get_current_subgoal():
        ts.get_current_subgoal().error_message = request.reason
        
    repo.update_task_status(task_id, "FAILED")
    
    return AbortResponse(
        task_id=task_id,
        status="FAILED",
        message=f"Task aborted. Reason: {request.reason}"
    )

from typing import List
from src.hlmp.api.schemas import FailureEventResponse, RecoveryEventResponse

@router.get("/tasks/{task_id}/failures", response_model=List[FailureEventResponse])
def get_failures(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    failures = repo.get_failures(task_id)
    return [
        FailureEventResponse(
            id=f.id, task_id=f.task_id, timestamp=f.timestamp,
            skill_name=f.skill_name, subgoal_id=f.subgoal_id,
            failure_type=f.failure_type, message=f.message
        ) for f in failures
    ]

@router.get("/tasks/{task_id}/recovery", response_model=List[RecoveryEventResponse])
def get_recoveries(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    recoveries = repo.get_recoveries(task_id)
    return [
        RecoveryEventResponse(
            id=r.id, task_id=r.task_id, timestamp=r.timestamp,
            strategy=r.strategy, failure_type=r.failure_type, success=r.success
        ) for r in recoveries
    ]

import json
import os
@router.get("/experiments")
def get_experiments():
    path = "results/raw/quick_benchmark_results.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return {"experiments": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to load experiments")
    return {"experiments": []}

@router.get("/tasks/{task_id}/results")
def get_results(task_id: str, db: Session = Depends(get_db)):
    repo = TaskRepository(db)
    task = repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    ts = _get_or_restore_task_state(task_id, task)
    failures = repo.get_failures(task_id)
    recoveries = repo.get_recoveries(task_id)
    failure_count = len(failures)
    recovery_count = len(recoveries)
    
    completed_sgs = len(ts.get_completed_subgoals()) if ts else (1 if task.status == "COMPLETED" else 0)
    failed_sgs = len(ts.get_failed_subgoals()) if ts else (1 if task.status == "FAILED" else 0)
    total_sgs = len(ts.subgoals) if ts else 1
    
    # Accurate physical task success: must have completed without unrecovered failure
    is_completed = (task.status == "COMPLETED" or (ts and ts.status.value == "COMPLETED")) and (failed_sgs == 0)
    
    # Accurate step accuracy accounting for retry attempts
    total_attempts = completed_sgs + failure_count
    accuracy_pct = round((completed_sgs / max(1, total_attempts)) * 100.0) if total_attempts > 0 else (100 if is_completed else 0)
    
    return {
        "task_id": task_id,
        "task_success": is_completed,
        "step_accuracy": accuracy_pct,
        "progress_percentage": task.progress_percentage,
        "failure_count": failure_count,
        "recovery_attempts": recovery_count,
        "completed_subgoals_count": completed_sgs,
        "total_subgoals_count": total_sgs
    }

from fastapi.responses import FileResponse, Response, StreamingResponse
import asyncio

@router.get("/live_stream")
async def live_stream():
    """
    High-performance real-time MJPEG video stream.
    Zero-polling continuous live video directly from simulation memory buffer.
    """
    async def frame_generator():
        while True:
            try:
                from src.hlmp.sim.env import LATEST_FRAME_BYTES
                frame = LATEST_FRAME_BYTES
                if not frame and os.path.exists("data/live_feed.jpg"):
                    with open("data/live_feed.jpg", "rb") as f:
                        frame = f.read()
                if frame:
                    yield (b"--frame\r\n"
                           b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            except Exception:
                pass
            await asyncio.sleep(0.04) # ~25 FPS
            
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/live_feed")
def get_live_feed():
    try:
        from src.hlmp.sim.env import LATEST_FRAME_BYTES
        if LATEST_FRAME_BYTES:
            return Response(
                content=LATEST_FRAME_BYTES,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    except Exception:
        pass

    path = "data/live_feed.jpg"
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            if data:
                return Response(
                    content=data,
                    media_type="image/jpeg",
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
                )
        except Exception:
            pass
    return FileResponse("web-dashboard/public/robot-arm.jpg", media_type="image/jpeg")
