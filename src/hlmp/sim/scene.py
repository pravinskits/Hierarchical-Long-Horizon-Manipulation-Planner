"""
Scene Management for the simulation.
"""
import pybullet as p
import logging
from typing import Dict, Any

class SceneManager:
    """
    Responsible for initializing the ground plane, table, and basic scene layout.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, client_id: int):
        """
        Initialize the SceneManager.
        
        Args:
            config (Dict[str, Any]): Application configuration.
            logger (logging.Logger): Logger instance.
            client_id (int): PyBullet physics client ID.
        """
        self.config = config
        self.logger = logger
        self.client_id = client_id
        self.plane_id = -1
        self.table_id = -1
        
    def build_scene(self) -> None:
        """Loads the foundational elements of the scene."""
        self.logger.info("Building simulation scene...")
        
        # Load ground plane
        self.plane_id = p.loadURDF("plane.urdf", physicsClientId=self.client_id)
        
        # Load table
        self.table_id = p.loadURDF(
            "table/table.urdf", 
            basePosition=[0, 0, -0.65], # typical table offset so surface is at z=0
            physicsClientId=self.client_id
        )
        self.logger.info("Scene built successfully.")
