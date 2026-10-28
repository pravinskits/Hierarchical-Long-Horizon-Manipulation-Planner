"""
Centralized failure detection logic.
"""
import logging
from typing import Dict, Any, Optional
from src.hlmp.core.result import SkillResult
from src.hlmp.recovery.models import FailureEvent, FailureType
from src.hlmp.recovery.failure_classifier import FailureClassifier

class FailureDetector:
    """
    Wraps SkillResult processing to detect and emit structured FailureEvents.
    """
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.classifier = FailureClassifier(config)
        
    def evaluate(self, result: SkillResult, context: Dict[str, Any]) -> Optional[FailureEvent]:
        """
        Evaluates a skill result. If a failure is detected, logs and returns a FailureEvent.
        """
        if result.success and not context.get("force_failure", False):
            return None
            
        event = self.classifier.classify(result, context)
        
        if event.failure_type != FailureType.NONE:
            self._log_failure(event)
            return event
            
        return None
        
    def _log_failure(self, event: FailureEvent) -> None:
        log_msg = (
            f"FAILURE DETECTED | Skill: {event.skill_name} | Subgoal: {event.subgoal_id} | "
            f"Type: {event.failure_type.value} | Confidence: {event.confidence:.2f} | "
            f"Message: {event.message}"
        )
        self.logger.warning(log_msg)
        self.logger.debug(f"FailureEvent Payload: {event.to_dict()}")
