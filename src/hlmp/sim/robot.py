"""
Robot Arm module for PyBullet Simulation.
"""
import pybullet as p
import logging
from typing import Dict, Any, List, Tuple

class RobotArmError(Exception):
    """Custom exception for robot arm errors."""
    pass

class RobotArm:
    """
    Manages the robot arm in the PyBullet environment.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, client_id: int):
        """
        Initialize the RobotArm.
        
        Args:
            config (Dict[str, Any]): Application configuration.
            logger (logging.Logger): Logger instance.
            client_id (int): PyBullet physics client ID.
        """
        self.config = config
        self.logger = logger
        self.client_id = client_id
        
        robot_config = self.config.get("robot", {})
        self.model_path = robot_config.get("model", "franka_panda/panda.urdf")
        self.base_pos = robot_config.get("base_position", [-0.5, 0.0, 0.0])
        self.base_ori = robot_config.get("base_orientation", [0, 0, 0, 1])
        self.initial_joints = robot_config.get("initial_joints", [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])
        self.ee_link_name = robot_config.get("ee_link_name", "panda_hand")
        
        self.robot_id = -1
        self.num_joints = 0
        self.controllable_joints: List[int] = []
        self.ee_link_index = -1
        
    def load(self) -> None:
        """Loads the robot model into the simulation."""
        self.logger.info(f"Loading robot model: {self.model_path}")
        try:
            self.robot_id = p.loadURDF(
                self.model_path,
                basePosition=self.base_pos,
                baseOrientation=self.base_ori,
                useFixedBase=True,
                physicsClientId=self.client_id
            )
        except Exception as e:
            raise RobotArmError(f"Failed to load robot URDF: {e}")
            
        self.num_joints = p.getNumJoints(self.robot_id, physicsClientId=self.client_id)
        self._discover_joints_and_links()
        
    def _discover_joints_and_links(self) -> None:
        """Discovers controllable joints and identifies the end-effector link."""
        for i in range(self.num_joints):
            info = p.getJointInfo(self.robot_id, i, physicsClientId=self.client_id)
            joint_name = info[1].decode("utf-8")
            joint_type = info[2]
            link_name = info[12].decode("utf-8")
            
            if joint_type != p.JOINT_FIXED:
                self.controllable_joints.append(i)
                
            if link_name == self.ee_link_name:
                self.ee_link_index = i
                
        if self.ee_link_index == -1:
            self.logger.warning(f"End-effector link '{self.ee_link_name}' not found. Defaulting to last link.")
            self.ee_link_index = self.num_joints - 1
            
        self.logger.debug(f"Found {len(self.controllable_joints)} controllable joints.")
        self.logger.debug(f"End-effector link index: {self.ee_link_index}")

    def reset_to_initial(self) -> None:
        """Resets the robot to the safe initial configuration."""
        if isinstance(self.robot_id, int) and self.robot_id < 0:
            raise RobotArmError("Robot is not loaded.")
            
        # 7 arm joints + 2 finger joints (opened)
        desired_joints = list(self.initial_joints)
        if len(desired_joints) == 7 and len(self.controllable_joints) == 9:
            desired_joints.extend([0.04, 0.04])
            
        for i, joint_idx in enumerate(self.controllable_joints):
            if i < len(desired_joints):
                p.resetJointState(self.robot_id, joint_idx, desired_joints[i], physicsClientId=self.client_id)
        self.logger.info("Robot reset to initial configuration.")

    def get_joint_states(self) -> List[float]:
        """Reads current joint positions."""
        if isinstance(self.robot_id, int) and self.robot_id < 0:
            return []
            
        states = p.getJointStates(self.robot_id, self.controllable_joints, physicsClientId=self.client_id)
        return [state[0] for state in states]

    def get_ee_position(self) -> Tuple[List[float], List[float]]:
        """
        Gets the end-effector position and orientation.
        
        Returns:
            Tuple containing:
                - List[float]: [x, y, z] position
                - List[float]: [x, y, z, w] quaternion orientation
        """
        if (isinstance(self.robot_id, int) and self.robot_id < 0) or (isinstance(self.ee_link_index, int) and self.ee_link_index < 0):
            raise RobotArmError("Robot not properly loaded or EE link missing.")
            
        state = p.getLinkState(self.robot_id, self.ee_link_index, physicsClientId=self.client_id)
        pos = list(state[4])  # worldLinkFramePosition
        ori = list(state[5])  # worldLinkFrameOrientation
        return pos, ori

    def move_joints(self, target_positions: List[float], max_force: float = 500.0) -> None:
        """
        Moves the robot joints to target positions safely.
        
        Args:
            target_positions (List[float]): Target angles for each controllable joint.
            max_force (float): Maximum force to apply.
        """
        if isinstance(self.robot_id, int) and self.robot_id < 0:
            raise RobotArmError("Robot is not loaded.")
            
        num_targets = len(target_positions)
        num_controllable = len(self.controllable_joints)
        
        # If arm angles only (7), retain current finger angles
        if num_targets == 7 and num_controllable == 9:
            cur_fingers = [p.getJointState(self.robot_id, j, physicsClientId=self.client_id)[0] for j in self.controllable_joints[-2:]]
            target_positions = list(target_positions) + cur_fingers
            num_targets = 9
            
        if num_targets != num_controllable:
            raise RobotArmError(f"Expected {num_controllable} target positions, got {num_targets}.")
            
        forces = [max_force] * num_controllable
        p.setJointMotorControlArray(
            bodyUniqueId=self.robot_id,
            jointIndices=self.controllable_joints,
            controlMode=p.POSITION_CONTROL,
            targetPositions=target_positions,
            forces=forces,
            physicsClientId=self.client_id
        )

    def solve_ik(self, target_pos: List[float], target_ori: List[float] = None, num_passes: int = 3) -> List[float]:
        """
        Solves Inverse Kinematics for a given target position and orientation.
        Uses iterative refinement with joint limits and rest poses for sub-millimeter precision.
        Falls back to neutral rest pose seed and flexible yaw when encountering local minima.
        """
        if isinstance(self.robot_id, int) and self.robot_id < 0 or self.ee_link_index < 0:
            raise RobotArmError("Robot not properly loaded.")
            
        # 9 DOF parameters (7 arm + 2 finger)
        ll = [-2.967, -1.833, -2.967, -3.142, -2.967, -0.087, -2.967, 0.0, 0.0]
        ul = [2.967, 1.833, 2.967, 0.0, 2.967, 3.822, 2.967, 0.04, 0.04]
        jr = [ul[i] - ll[i] for i in range(9)]
        rp = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785, 0.04, 0.04]
        jd = [0.05] * 9

        arm_joint_indices = self.controllable_joints[:7]
        orig_arm_states = [p.getJointState(self.robot_id, j, physicsClientId=self.client_id)[0] for j in arm_joint_indices]

        def _evaluate_seed(seed_joints, ori):
            for i, j in enumerate(arm_joint_indices):
                p.resetJointState(self.robot_id, j, seed_joints[i], physicsClientId=self.client_id)
            joint_poses = None
            for _ in range(max(1, num_passes)):
                if ori is None:
                    joint_poses = p.calculateInverseKinematics(
                        self.robot_id, self.ee_link_index, target_pos,
                        lowerLimits=ll, upperLimits=ul, jointRanges=jr, restPoses=rp, jointDamping=jd,
                        maxNumIterations=150, residualThreshold=1e-4,
                        physicsClientId=self.client_id
                    )
                else:
                    joint_poses = p.calculateInverseKinematics(
                        self.robot_id, self.ee_link_index, target_pos, ori,
                        lowerLimits=ll, upperLimits=ul, jointRanges=jr, restPoses=rp, jointDamping=jd,
                        maxNumIterations=150, residualThreshold=1e-4,
                        physicsClientId=self.client_id
                    )
                for i, j in enumerate(arm_joint_indices):
                    p.resetJointState(self.robot_id, j, joint_poses[i], physicsClientId=self.client_id)
            pos = p.getLinkState(self.robot_id, self.ee_link_index, physicsClientId=self.client_id)[4]
            err = sum((pos[k] - target_pos[k]) ** 2 for k in range(3)) ** 0.5
            return joint_poses, err

        # 1. Try starting from current configuration
        best_poses, best_err = _evaluate_seed(orig_arm_states, target_ori)

        # 2. If error is notable, try starting from neutral rest poses
        if best_err > 0.015:
            poses_rp, err_rp = _evaluate_seed(rp[:7], target_ori)
            if err_rp < best_err:
                best_poses, best_err = poses_rp, err_rp

        # 3. If still high, try flexible yaw for top-down orientation
        if best_err > 0.015 and target_ori is not None:
            for yaw in [0.785, -0.785, 1.571, -1.571]:
                alt_ori = p.getQuaternionFromEuler([3.14159, 0, yaw])
                poses_alt, err_alt = _evaluate_seed(rp[:7], alt_ori)
                if err_alt < best_err:
                    best_poses, best_err = poses_alt, err_alt
                    if best_err <= 0.015:
                        break

        # Restore actual joint positions
        for i, j in enumerate(arm_joint_indices):
            p.resetJointState(self.robot_id, j, orig_arm_states[i], physicsClientId=self.client_id)

        # Get finger positions currently commanded
        cur_fingers = [p.getJointState(self.robot_id, j, physicsClientId=self.client_id)[0] for j in self.controllable_joints[-2:]]
        arm_joints = list(best_poses[:7])
        return arm_joints + cur_fingers

    def set_gripper(self, open_width: float = 0.0) -> None:
        """
        Controls the gripper fingers (0.0 = fully closed, 0.04 = fully open).
        Holds arm joints in place to prevent gravity drift during gripper actuation.
        """
        if isinstance(self.robot_id, int) and self.robot_id < 0 or len(self.controllable_joints) < 2:
            return
            
        arm_indices = self.controllable_joints[:7]
        finger_indices = self.controllable_joints[-2:]
        
        # Hold current arm joints in place
        arm_q = [p.getJointState(self.robot_id, j, physicsClientId=self.client_id)[0] for j in arm_indices]
        p.setJointMotorControlArray(
            bodyUniqueId=self.robot_id,
            jointIndices=arm_indices,
            controlMode=p.POSITION_CONTROL,
            targetPositions=arm_q,
            forces=[800.0] * 7,
            physicsClientId=self.client_id
        )
        
        # Actuate gripper fingers
        p.setJointMotorControlArray(
            bodyUniqueId=self.robot_id,
            jointIndices=finger_indices,
            controlMode=p.POSITION_CONTROL,
            targetPositions=[open_width, open_width],
            forces=[500.0, 500.0],
            physicsClientId=self.client_id
        )
