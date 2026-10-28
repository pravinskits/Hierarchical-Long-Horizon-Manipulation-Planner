"""
Tests for robot arm module.
"""

import logging
import pytest
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.robot import RobotArm, RobotArmError

@pytest.fixture
def mock_config():
    return {
        "sim": {
            "gravity": [0, 0, -9.81],
            "timestep": 0.016
        },
        "robot": {
            "model": "franka_panda/panda.urdf",
            "base_position": [0, 0, 0],
            "base_orientation": [0, 0, 0, 1],
            "initial_joints": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
            "ee_link_name": "panda_hand"
        }
    }

@pytest.fixture
def logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger

def test_robot_initialization_and_loading(mock_config, logger):
    """Test loading the robot in headless mode."""
    env = SimulationEnvironment(mock_config, logger, headless=True)
    env.connect()
    
    try:
        robot = RobotArm(mock_config, logger, env.client_id)
        robot.load()
        
        assert robot.robot_id is not None
        assert len(robot.controllable_joints) > 0
        assert robot.ee_link_index is not None
        
        # Test resetting
        robot.reset_to_initial()
        
        # Test reading state
        states = robot.get_joint_states()
        
        # Test EE pos
        pos, ori = robot.get_ee_position()
        
    finally:
        env.disconnect()
