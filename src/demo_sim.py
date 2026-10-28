"""
Demonstration script for the PyBullet simulation environment.
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Ensure src is in the python path
sys.path.insert(0, str(Path(__file__).parent))

from hlmp.config import load_config
from hlmp.utils.logger import setup_logger
from hlmp.sim.env import SimulationEnvironment
from hlmp.sim.scene import SceneManager
from hlmp.sim.objects import ObjectManager

def main() -> None:
    """
    Main demonstration execution.
    """
    # Load configuration
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "settings.yaml"
    
    try:
        config = load_config(str(config_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    # Setup logging
    logger = setup_logger(config)
    logger.info("Starting PyBullet Simulation Demo...")
    
    # Set random seed
    seed = config.get("sim", {}).get("seed", 42)
    np.random.seed(seed)
    logger.info(f"Using random seed: {seed}")
    
    # Initialize Simulation
    sim_env = SimulationEnvironment(config, logger, headless=False)
    
    try:
        sim_env.connect()
        
        # Build Scene
        scene_mgr = SceneManager(config, logger, sim_env.client_id)
        scene_mgr.build_scene()
        
        # Spawn Objects
        obj_mgr = ObjectManager(config, logger, sim_env.client_id)
        obj_mgr.populate_from_config()
        
        logger.info("Simulation running. Close the window to exit.")
        
        # Simulation Loop
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
