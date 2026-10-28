"""
Demonstration script for Manipulation Skills.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.hlmp.config import load_config
from src.hlmp.utils.logger import setup_logger
from src.hlmp.sim.env import SimulationEnvironment
from src.hlmp.sim.scene import SceneManager
from src.hlmp.sim.objects import ObjectManager
from src.hlmp.sim.robot import RobotArm
from src.hlmp.skills import MoveSkill, PickSkill, PlaceSkill

def main() -> None:
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "settings.yaml"
    
    try:
        config = load_config(str(config_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    logger = setup_logger(config)
    logger.info("Starting Manipulation Demo...")
    
    np.random.seed(config.get("sim", {}).get("seed", 42))
    
    sim_env = SimulationEnvironment(config, logger, headless=False)
    
    try:
        sim_env.connect()
        
        scene_mgr = SceneManager(config, logger, sim_env.client_id)
        scene_mgr.build_scene()
        
        obj_mgr = ObjectManager(config, logger, sim_env.client_id)
        obj_mgr.populate_from_config()
        
        robot = RobotArm(config, logger, sim_env.client_id)
        robot.load()
        robot.reset_to_initial()
        
        # Skills
        pick_skill = PickSkill(sim_env, robot, config, logger)
        place_skill = PlaceSkill(sim_env, robot, config, logger)
        
        # Pick Red Cube
        red_cube_id = obj_mgr.objects["red_cube"]
        target_zone_pos = config["sim"]["objects"]["target_area"]["pos"]
        red_cube_pos = config["sim"]["objects"]["red_cube"]["pos"]
        
        logger.info("Executing Pick...")
        pick_res = pick_skill.execute(target_pos=red_cube_pos, object_id=red_cube_id)
        
        if pick_res.success:
            logger.info("Executing Place...")
            constraint_id = pick_res.metadata.get("constraint_id", -1)
            place_res = place_skill.execute(target_pos=target_zone_pos, object_id=red_cube_id, constraint_id=constraint_id)
        
        logger.info("Manipulation Sequence Finished. Close window to exit.")
        while True:
            sim_env.step()
            time.sleep(sim_env.timestep)
            
    except KeyboardInterrupt:
        logger.info("Simulation interrupted.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        sim_env.disconnect()

if __name__ == "__main__":
    main()
