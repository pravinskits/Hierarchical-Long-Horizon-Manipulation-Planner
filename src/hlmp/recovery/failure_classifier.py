"""
Deterministic failure classifier.
"""
import time
from typing import Dict, Any, Optional
from src.hlmp.core.result import SkillResult
from src.hlmp.recovery.models import FailureType, FailureEvent

class FailureClassifier:
    """
    Evaluates SkillResult and execution context to determine a FailureType.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("recovery", {})
        
    def classify(self, result: SkillResult, context: Dict[str, Any]) -> FailureEvent:
        subgoal_id = context.get("subgoal_id", "unknown")
        
        # 1. Base Execution Errors
        if not result.success and "invalid" in result.message.lower():
            return self._build_event(FailureType.INVALID_ACTION, result, subgoal_id, "Invalid action parameters detected.", confidence=1.0)
            
        if "timeout" in result.message.lower() or result.duration > self.config.get("max_skill_duration", 10.0):
            return self._build_event(FailureType.TIMEOUT, result, subgoal_id, "Skill execution exceeded timeout threshold.", confidence=0.95)
            
        # 2. Pick Skill Specifics
        if result.skill_name in ("Pick", "PickSkill"):
            if not result.success:
                return self._build_event(FailureType.GRASP_FAILURE, result, subgoal_id, "Failed to grasp or lift object.", 
                                         expected_state="Object held securely.", observed_state="Object detached or on ground.")
            else:
                slip = context.get("slip_detected", False)
                if slip:
                    return self._build_event(FailureType.OBJECT_SLIPPED, result, subgoal_id, "Object slipped from gripper after grasp.")
                    
        # 3. Place/Move/Push Specifics
        if result.skill_name in ("Move", "Place", "Push", "MoveSkill", "PlaceSkill", "PushSkill") and not result.success:
            if any(k in result.message.lower() for k in ("target", "reach", "placement", "tolerance", "approach", "push")):
                ftype = FailureType.PLACEMENT_FAILURE if "Place" in result.skill_name else FailureType.TARGET_NOT_REACHED
                return self._build_event(ftype, result, subgoal_id, result.message, 
                                         expected_state="Within position tolerance.", observed_state="Target not reached.")
                                         
        # 4. Unknown/Execution Error fallback
        if not result.success:
            return self._build_event(FailureType.EXECUTION_ERROR, result, subgoal_id, result.message, confidence=0.7)
            
        # 5. Success
        return self._build_event(FailureType.NONE, result, subgoal_id, "No failure detected.")
        
    def _build_event(self, ftype: FailureType, result: SkillResult, subgoal_id: str, message: str, 
                     expected_state: str = "", observed_state: str = "", confidence: float = 1.0) -> FailureEvent:
        return FailureEvent(
            failure_type=ftype,
            skill_name=result.skill_name,
            subgoal_id=subgoal_id,
            timestamp=time.time(),
            message=message,
            expected_state=expected_state,
            observed_state=observed_state,
            confidence=confidence,
            metadata=result.metadata
        )
