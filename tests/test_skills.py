"""
Tests for manipulation skills.
"""

import logging
import pytest
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.robot import RobotArm
from src.hlmp.skills import BaseSkill, MoveSkill
from src.hlmp.core.result import SkillResult

@pytest.fixture
def mock_config():
    return {
        "sim": {"gravity": [0, 0, -9.81], "timestep": 0.016},
        "robot": {
            "model": "franka_panda/panda.urdf",
            "base_position": [0, 0, 0],
            "base_orientation": [0, 0, 0, 1],
            "initial_joints": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
            "ee_link_name": "panda_hand"
        },
        "skills": {
            "position_tolerance": 0.05
        }
    }

@pytest.fixture
def logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger

def test_skill_result():
    res = SkillResult(success=True, skill_name="Test", message="OK")
    assert res.success is True
    assert res.skill_name == "Test"

def test_move_skill(mock_config, logger):
    env = SimulationEnvironment(mock_config, logger, headless=True)
    env.connect()
    
    try:
        robot = RobotArm(mock_config, logger, env.client_id)
        robot.load()
        
        move_skill = MoveSkill(env, robot, mock_config, logger)
        
        # Test basic execution structure (IK might fail silently or do nothing, but it shouldn't crash)
        res = move_skill.execute(target_pos=[0.5, 0.0, 0.2])
        
        assert isinstance(res, SkillResult)
        assert res.skill_name == "Move"
        
    finally:
        env.disconnect()
