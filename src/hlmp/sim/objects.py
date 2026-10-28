"""
Object spawning and management.
"""
import pybullet as p
import logging
from typing import Dict, Any, List

class ObjectManager:
    """
    Responsible for creating and managing manipulable objects in the environment.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, client_id: int):
        """
        Initialize the ObjectManager.
        
        Args:
            config (Dict[str, Any]): Application configuration.
            logger (logging.Logger): Logger instance.
            client_id (int): PyBullet physics client ID.
        """
        self.config = config
        self.logger = logger
        self.client_id = client_id
        self.objects: Dict[str, int] = {}
        
    def spawn_cube(self, name: str, position: List[float], color: List[float], size: float = 0.05, mass: float = 0.1) -> int:
        """
        Spawns a basic colored cube.
        
        Args:
            name (str): Identifier for the object.
            position (List[float]): [x, y, z] position.
            color (List[float]): [r, g, b, a] color.
            size (float): Half-extents size of the cube.
            mass (float): Mass in kg.
            
        Returns:
            int: The body ID of the spawned cube.
        """
        visual_shape_id = p.createVisualShape(
            shapeType=p.GEOM_BOX,
            halfExtents=[size, size, size],
            rgbaColor=color,
            physicsClientId=self.client_id
        )
        collision_shape_id = p.createCollisionShape(
            shapeType=p.GEOM_BOX,
            halfExtents=[size, size, size],
            physicsClientId=self.client_id
        )
        
        body_id = p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=collision_shape_id,
            baseVisualShapeIndex=visual_shape_id,
            basePosition=position,
            physicsClientId=self.client_id
        )
        
        # Configure stable friction dynamics for reliable grasping and stacking
        p.changeDynamics(
            body_id, -1,
            lateralFriction=1.5,
            spinningFriction=0.05,
            rollingFriction=0.01,
            contactStiffness=10000.0,
            contactDamping=500.0,
            physicsClientId=self.client_id
        )
        
        self.objects[name] = body_id
        self.logger.debug(f"Spawned cube '{name}' at {position}")
        return body_id
        
    def spawn_target_zone(self, name: str, position: List[float], size: float = 0.1) -> int:
        """
        Spawns a visual-only target zone (no collision).
        """
        visual_shape_id = p.createVisualShape(
            shapeType=p.GEOM_BOX,
            halfExtents=[size, size, 0.001], # very thin
            rgbaColor=[1.0, 1.0, 0.0, 0.5], # translucent yellow
            physicsClientId=self.client_id
        )
        
        body_id = p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=-1,
            baseVisualShapeIndex=visual_shape_id,
            basePosition=position,
            physicsClientId=self.client_id
        )
        
        self.objects[name] = body_id
        self.logger.debug(f"Spawned target zone '{name}' at {position}")
        return body_id

    def populate_from_config(self) -> None:
        """Reads object configuration and spawns default objects."""
        obj_config = self.config.get("sim", {}).get("objects", {})
        
        for name, data in obj_config.items():
            pos = data.get("pos", [0, 0, 0])
            if any(k in name for k in ("target_area", "safe_zone", "right_corner", "corner", "zone", "area")):
                self.spawn_target_zone(name, pos)
            elif name == "red_cube":
                self.spawn_cube(name, pos, [1.0, 0.0, 0.0, 1.0])
            elif name == "blue_cube":
                self.spawn_cube(name, pos, [0.0, 0.0, 1.0, 1.0])
            elif name == "green_cube":
                self.spawn_cube(name, pos, [0.0, 1.0, 0.0, 1.0])
            else:
                self.spawn_cube(name, pos, [0.5, 0.5, 0.5, 1.0])
