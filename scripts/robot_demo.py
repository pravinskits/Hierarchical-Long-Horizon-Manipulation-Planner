"""
Demonstration script for the Robot Arm in PyBullet.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Ensure src is in the python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlmp.config import load_config
from hlmp.utils.logger import setup_logger
from hlmp.sim.env import SimulationEnvironment
from hlmp.sim.scene import SceneManager
from hlmp.sim.objects import ObjectManager
from hlmp.sim.robot import RobotArm

def main() -> None:
    """
    Main demonstration execution for Robot Arm.
    """
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "settings.yaml"
    
    try:
        config = load_config(str(config_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    logger = setup_logger(config)
    logger.info("Starting Robot Arm Simulation Demo...")
    
    np.random.seed(config.get("sim", {}).get("seed", 42))
    
    sim_env = SimulationEnvironment(config, logger, headless=False)
    
    try:
        sim_env.connect()
        
        scene_mgr = SceneManager(config, logger, sim_env.client_id)
        scene_mgr.build_scene()
        
        obj_mgr = ObjectManager(config, logger, sim_env.client_id)
        obj_mgr.populate_from_config()
        
        # Initialize and load Robot
        robot = RobotArm(config, logger, sim_env.client_id)
        robot.load()
        robot.reset_to_initial()
        
        # Print info
        logger.info(f"Initial Joint States: {robot.get_joint_states()}")
        ee_pos, ee_ori = robot.get_ee_position()
        logger.info(f"Initial EE Pose: Pos={ee_pos}, Ori={ee_ori}")
        
        # Demonstrate small movement
        logger.info("Executing safe joint movement...")
        target_joints = robot.initial_joints.copy()
        target_joints[0] += 0.5  # Move base joint slightly
        
        robot.move_joints(target_joints)
        
        # Step simulation for a few seconds to reach target
        for _ in range(120): # 120 steps @ 60Hz = 2 seconds
            sim_env.step()
            time.sleep(sim_env.timestep)
            
        logger.info(f"Final Joint States: {robot.get_joint_states()}")
        ee_pos, ee_ori = robot.get_ee_position()
        logger.info(f"Final EE Pose: Pos={ee_pos}, Ori={ee_ori}")
        
        logger.info("Simulation running. Close the window to exit.")
        while True:
            sim_env.step()
            time.sleep(sim_env.timestep)
            
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    except Exception as e:
        logger.error(f"Simulation encountered an error: {e}")
    finally:
        sim_env.disconnect()
        logger.info("Demo finished.")

if __name__ == "__main__":
    main()
