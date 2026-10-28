"""
Base classes for skills.
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.robot import RobotArm
from src.hlmp.core.result import SkillResult

class BaseSkill(ABC):
    """Abstract base class for all manipulation skills."""
    
    def __init__(self, name: str, env: SimulationEnvironment, robot: RobotArm, config: Dict[str, Any], logger: logging.Logger):
        self.name = name
        self.env = env
        self.robot = robot
        self.config = config
        self.logger = logger
        
        skills_cfg = self.config.get("skills", {})
        self.position_tolerance = skills_cfg.get("position_tolerance", 0.01)
        self.movement_speed = skills_cfg.get("movement_speed", 0.05)
        
    def execute(self, **kwargs) -> SkillResult:
        """
        Wraps the internal execution with structured logging and timing.
        """
        self.logger.info(f"SKILL_START: {self.name}")
        start_time = time.time()
        
        try:
            result = self._execute(**kwargs)
        except Exception as e:
            self.logger.error(f"Skill {self.name} encountered an error: {e}")
            result = SkillResult(success=False, skill_name=self.name, message=str(e))
            
        result.duration = time.time() - start_time
        
        if result.success:
            self.logger.info(f"SKILL_SUCCESS: {self.name} - {result.message}")
        else:
            self.logger.warning(f"SKILL_FAILURE: {self.name} - {result.message}")
            
        return result
        
    @abstractmethod
    def _execute(self, **kwargs) -> SkillResult:
        """Internal execution logic to be implemented by subclasses."""
        pass
        
    def _step_sim_for_duration(self, duration: float) -> None:
        """Helper to step simulation for a set amount of time."""
        steps = int(duration / self.env.timestep)
        for _ in range(max(1, steps)):
            self.env.step()
