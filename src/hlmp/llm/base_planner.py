from typing import Dict, Any
from src.hlmp.core.plan_models import Plan

class BaseLLMPlanner:
    def generate_plan(self, goal: str, scene_state: Dict[str, Any]) -> Plan:
        raise NotImplementedError
