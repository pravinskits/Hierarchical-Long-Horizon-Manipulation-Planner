"""
PyBullet Simulation Environment.
"""
import pybullet as p
import pybullet_data
import logging
from typing import Dict, Any

LATEST_FRAME_BYTES: bytes = b""

class SimulationEnvironment:
    """
    Manages the PyBullet simulation lifecycle and physics settings.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, headless: bool = False):
        """
        Initialize the simulation environment.
        
        Args:
            config (Dict[str, Any]): The application configuration.
            logger (logging.Logger): Logger instance.
            headless (bool): If True, run PyBullet in DIRECT mode (no GUI).
        """
        self.config = config
        self.logger = logger
        self.headless = headless
        self.client_id = -1
        self._last_frame_time = 0.0
        
        sim_config = self.config.get("sim", {})
        self.gravity = sim_config.get("gravity", [0, 0, -9.81])
        self.timestep = sim_config.get("timestep", 1.0 / 60.0)
        
    def connect(self) -> None:
        """Connects to the PyBullet physics server."""
        mode = p.DIRECT if self.headless else p.GUI
        self.client_id = p.connect(mode)
        
        if isinstance(self.client_id, int) and self.client_id < 0:
            raise ConnectionError("Failed to connect to PyBullet physics server.")
            
        self.logger.info(f"Connected to PyBullet (mode: {'DIRECT' if self.headless else 'GUI'})")
        
        # Configure physics
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.client_id)
        p.setGravity(*self.gravity, physicsClientId=self.client_id)
        p.setTimeStep(self.timestep, physicsClientId=self.client_id)
        
        if not self.headless:
            # Configure camera
            cam_config = self.config.get("sim", {}).get("camera", {})
            p.resetDebugVisualizerCamera(
                cameraDistance=cam_config.get("distance", 1.8),
                cameraYaw=cam_config.get("yaw", 90),
                cameraPitch=cam_config.get("pitch", -25),
                cameraTargetPosition=cam_config.get("target_pos", [-0.1, 0.0, 0.3]),
                physicsClientId=self.client_id
            )

    def step(self) -> None:
        """Advances the simulation by one timestep."""
        if not isinstance(self.client_id, int) or self.client_id >= 0:
            p.stepSimulation(physicsClientId=self.client_id)
            
            import time
            if not self.headless:
                time.sleep(self.timestep)
            else:
                time.sleep(0.001)
            
            # Stream camera feed to UI at ~12-15 FPS without stalling physics
            now = time.time()
            if (now - self._last_frame_time) >= 0.07:
                self._save_camera_frame()
                self._last_frame_time = time.time()

    def _save_camera_frame(self, force_disk: bool = False):
        try:
            cam_config = self.config.get("sim", {}).get("camera", {})
            width, height = 360, 270
            vm = p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=cam_config.get("target_pos", [-0.1, 0.0, 0.3]),
                distance=cam_config.get("distance", 1.8),
                yaw=cam_config.get("yaw", 90),
                pitch=cam_config.get("pitch", -25),
                roll=0,
                upAxisIndex=2,
                physicsClientId=self.client_id
            )
            pm = p.computeProjectionMatrixFOV(60, width / height, 0.1, 100.0, physicsClientId=self.client_id)
            _, _, rgb, _, _ = p.getCameraImage(width, height, vm, pm, renderer=p.ER_TINY_RENDERER, physicsClientId=self.client_id)
            
            import io
            import numpy as np
            from PIL import Image
            
            img_arr = np.reshape(rgb, (height, width, 4))
            img = Image.fromarray(img_arr[:, :, :3].astype(np.uint8))
            
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            frame_bytes = buf.getvalue()
            
            global LATEST_FRAME_BYTES
            LATEST_FRAME_BYTES = frame_bytes
            
            # Write to disk only when explicitly requested (e.g. disconnect or initialization)
            if force_disk:
                try:
                    with open("data/live_feed.jpg", "wb") as f:
                        f.write(frame_bytes)
                except Exception:
                    pass
        except Exception:
            pass

    def disconnect(self) -> None:
        """Cleanly shuts down the simulation."""
        if not isinstance(self.client_id, int) or self.client_id >= 0:
            # Capture final frame before disconnecting and persist to disk
            self._save_camera_frame(force_disk=True)
            p.disconnect(physicsClientId=self.client_id)
            self.logger.info("Disconnected from PyBullet.")
            self.client_id = -1
