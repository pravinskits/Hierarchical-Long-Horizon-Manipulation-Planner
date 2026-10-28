"""
Tests for simulation environment.
"""

import logging
import pytest
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.scene import SceneManager
from src.hlmp.sim.objects import ObjectManager

@pytest.fixture
def mock_config():
    return {
        "sim": {
            "gravity": [0, 0, -9.81],
            "timestep": 0.016,
            "objects": {
                "red_cube": {"pos": [0, 0, 0]},
                "target_area_1": {"pos": [0.2, 0.1, 0.01]}
            }
        }
    }

@pytest.fixture
def logger():
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger

def test_simulation_environment(mock_config, logger):
    """Test connecting and disconnecting in headless mode."""
    env = SimulationEnvironment(mock_config, logger, headless=True)
    env.connect()
    assert env.client_id is not None
    
    # Step shouldn't crash
    env.step()
    
    env.disconnect()
    assert env.client_id == -1

def test_scene_and_objects(mock_config, logger):
    """Test building a scene and spawning an object."""
    import pybullet as p
    env = SimulationEnvironment(mock_config, logger, headless=True)
    env.connect()
    
    try:
        # Build scene
        scene_mgr = SceneManager(mock_config, logger, env.client_id)
        scene_mgr.build_scene()
        assert scene_mgr.plane_id is not None
        assert scene_mgr.table_id is not None
        
        # Spawn object
        obj_mgr = ObjectManager(mock_config, logger, env.client_id)
        obj_mgr.populate_from_config()
        assert "red_cube" in obj_mgr.objects
        assert obj_mgr.objects["red_cube"] is not None
        
        # target_area_1 should be spawned as a target zone
        assert "target_area_1" in obj_mgr.objects
        assert obj_mgr.objects["target_area_1"] is not None
        
    finally:
        env.disconnect()
