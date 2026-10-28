import time
import logging
import uuid
from typing import Dict, Any, List
from .plan_models import PlannedSubgoal, Plan, PlanValidationResult
from .goal_interpreter import GoalInterpreter
from .task_state import TaskStateManager

# Centralized Skill Registry
SKILL_REGISTRY = {
    "move": "MoveSkill",
    "pick": "PickSkill",
    "place": "PlaceSkill",
    "push": "PushSkill"
}

class BasePlanner:
    def create_plan(self, goal: str, scene_state: Dict[str, Any] = None) -> Plan:
        raise NotImplementedError

class HierarchicalPlanner(BasePlanner):
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.interpreter = GoalInterpreter()
        
    def create_plan(self, goal: str, scene_state: Dict[str, Any] = None) -> Plan:
        self.logger.info("PLAN_START")
        try:
            operations = self.interpreter.interpret(goal)
        except ValueError as e:
            self.logger.error(f"PLAN_FAILURE | {str(e)}")
            raise
            
        subgoals = []
        prev_id = None
        
        for i, op in enumerate(operations):
            sg_id = f"sg_{i+1:03d}"
            action = op["action"]
            
            params = {}
            if "object" in op:
                params["target"] = op["object"]
            if "target" in op and action != "pick":
                params["destination"] = op["target"]
                
            preconditions = []
            expected_outcome = []
            
            if action == "pick":
                preconditions = ["object_exists", "robot_available"]
                expected_outcome = ["object_grasped"]
            elif action == "move":
                if "target" in op and op.get("destination"):
                    preconditions = ["object_grasped"]
                    expected_outcome = ["object_at_target_region"]
                else:
                    preconditions = ["robot_available"]
                    expected_outcome = ["robot_at_target"]
            elif action == "place":
                preconditions = ["object_grasped", "target_exists"]
                expected_outcome = ["object_released_inside_target"]
            elif action == "push":
                preconditions = ["robot_near_object"]
                expected_outcome = ["object_moved_toward_target"]
                
            deps = [prev_id] if prev_id else []
            
            sg = PlannedSubgoal(
                id=sg_id,
                skill=SKILL_REGISTRY.get(action, "UNKNOWN"),
                parameters=params,
                preconditions=preconditions,
                expected_outcome=expected_outcome,
                dependencies=deps
            )
            subgoals.append(sg)
            prev_id = sg_id
            
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        plan = Plan(
            plan_id=plan_id,
            original_goal=goal,
            subgoals=subgoals,
            created_at=time.time()
        )
        self.logger.info("PLAN_GENERATED")
        return plan
        
    def validate_plan(self, plan: Plan) -> PlanValidationResult:
        self.logger.info("PLAN_VALIDATION")
        errors = []
        warnings = []
        seen_ids = set()
        
        adj = {sg.id: sg.dependencies for sg in plan.subgoals}
        
        for sg in plan.subgoals:
            if sg.id in seen_ids:
                errors.append(f"Duplicate subgoal ID detected: {sg.id}")
            seen_ids.add(sg.id)
            
            if sg.skill not in SKILL_REGISTRY.values():
                errors.append(f"Unknown skill '{sg.skill}' in subgoal {sg.id}")
                
            if not sg.preconditions:
                warnings.append(f"Subgoal {sg.id} has no preconditions.")
            if not sg.expected_outcome:
                warnings.append(f"Subgoal {sg.id} has no expected outcome.")
                
        for sg in plan.subgoals:
            for dep in sg.dependencies:
                if dep not in seen_ids:
                    errors.append(f"Dependency '{dep}' for subgoal {sg.id} not found in plan.")
                    
        visited = set()
        path = set()
        
        def has_cycle(node):
            if node in path:
                return True
            if node in visited:
                return False
            path.add(node)
            visited.add(node)
            for neighbor in adj.get(node, []):
                if has_cycle(neighbor):
                    return True
            path.remove(node)
            return False
            
        for node in adj:
            if node not in visited:
                if has_cycle(node):
                    errors.append("Circular dependency detected in plan.")
                    break
                    
        valid = len(errors) == 0
        if valid:
            self.logger.info("PLAN_SUCCESS")
        else:
            self.logger.error("PLAN_FAILURE")
            
        return PlanValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            checked_subgoals=len(plan.subgoals)
        )
        
    def plan_to_task_state(self, plan: Plan, manager: TaskStateManager) -> None:
        """Converts validated plan to task manager."""
        for sg in plan.subgoals:
            manager.add_subgoal(sg.id, sg.skill, sg.parameters)

class HybridPlanner(BasePlanner):
    def __init__(self, config: Dict[str, Any], logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.deterministic_planner = HierarchicalPlanner(logger)
        
        self.llm_planner = None
        if config.get("llm", {}).get("enabled", False):
            try:
                from src.hlmp.llm.groq_planner import GroqPlanner
                self.llm_planner = GroqPlanner(config, logger)
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM Planner: {e}")
                
    def create_plan(self, goal: str, scene_state: Dict[str, Any] = None) -> Plan:
        scene_state = scene_state or {}
        
        if self.llm_planner:
            try:
                plan = self.llm_planner.generate_plan(goal, scene_state)
                # Ensure it passes deterministic validation
                validation = self.deterministic_planner.validate_plan(plan)
                if validation.valid:
                    return plan
                else:
                    self.logger.warning(f"LLM plan failed validation: {validation.errors}. Falling back...")
            except Exception as e:
                self.logger.warning(f"LLM Planner failed ({type(e).__name__}: {e}). Falling back to deterministic planner...")
                
        # Fallback
        self.logger.info("Using Deterministic Hierarchical Planner fallback.")
        return self.deterministic_planner.create_plan(goal, scene_state)
        
    def validate_plan(self, plan: Plan) -> PlanValidationResult:
        return self.deterministic_planner.validate_plan(plan)
        
    def plan_to_task_state(self, plan: Plan, manager: TaskStateManager) -> None:
        return self.deterministic_planner.plan_to_task_state(plan, manager)
