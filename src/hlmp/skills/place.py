"""
Place skill.
"""
import pybullet as p
import numpy as np
from typing import List
from .base_skill import BaseSkill, SkillResult
from .move import MoveSkill

class PlaceSkill(BaseSkill):
    def __init__(self, env, robot, config, logger):
        super().__init__("Place", env, robot, config, logger)
        self.move_skill = MoveSkill(env, robot, config, logger)
        
        cfg = config.get("skills", {})
        self.lift_height = cfg.get("lift_height", 0.15)
        self.placement_tolerance = cfg.get("placement_tolerance", 0.05)
        
    def _execute(self, target_pos: List[float], object_id: int, constraint_id: int = -1) -> SkillResult:
        """
        Executes a place action with full robotic motion sequence:
        1. Transit above target area with top-down orientation
        2. Smoothly descend to placement height
        3. Release grasp constraint and smoothly open gripper
        4. Smoothly retract vertically above target
        """
        down_ori = p.getQuaternionFromEuler([3.14159, 0, 0])
        
        desired_center_z = max(target_pos[2], 0.05)
        place_wrist_z = desired_center_z + 0.12
        above_wrist_z = min(max(place_wrist_z + 0.08, 0.33), 0.42)
        
        # 0. Lift current EE position to clearance height before lateral transit
        cur_pos, _ = self.robot.get_ee_position()
        if cur_pos[2] < above_wrist_z:
            self.move_skill._execute([cur_pos[0], cur_pos[1], above_wrist_z], target_ori=down_ori)

        # 1. Move safely above target
        above_pos = [target_pos[0], target_pos[1], above_wrist_z]
        res1 = self.move_skill._execute(above_pos, target_ori=down_ori)
        if not res1.success:
            return SkillResult(False, self.name, "Failed to move above placement target.")
            
        # 2. Smoothly descend to exact placement height
        place_pos = [target_pos[0], target_pos[1], place_wrist_z]
        res2 = self.move_skill._execute(place_pos, target_ori=down_ori)
        
        # Settle and damp residual object motion before release
        p.resetBaseVelocity(object_id, [0, 0, 0], [0, 0, 0], physicsClientId=self.env.client_id)
        self._step_sim_for_duration(0.05)
        
        # 3. Release Grasp Constraint
        if constraint_id >= 0:
            try:
                p.removeConstraint(constraint_id, physicsClientId=self.env.client_id)
            except Exception:
                pass
                
        # Also ensure any lingering constraints on object_id are removed
        num_c = p.getNumConstraints(physicsClientId=self.env.client_id)
        for i in range(num_c - 1, -1, -1):
            try:
                cid = p.getConstraintUniqueId(i, physicsClientId=self.env.client_id)
                info = p.getConstraintInfo(cid, physicsClientId=self.env.client_id)
                if info[0] == object_id or info[2] == object_id:
                    p.removeConstraint(cid, physicsClientId=self.env.client_id)
            except Exception:
                pass
            
        # Temporarily disable collision across all robot links during opening/retract to prevent drag
        for l in range(-1, p.getNumJoints(self.robot.robot_id, physicsClientId=self.env.client_id)):
            p.setCollisionFilterPair(self.robot.robot_id, object_id, l, -1, enableCollision=0, physicsClientId=self.env.client_id)
        
        # Smoothly open gripper fingers
        for w in np.linspace(0.0, 0.04, 6):
            self.robot.set_gripper(open_width=float(w))
            self.env.step()
        self._step_sim_for_duration(0.05)
        
        # 4. Retract vertically above target
        self.move_skill._execute(above_pos, target_ori=down_ori)
        
        # Re-enable collision with robot across all links
        for l in range(-1, p.getNumJoints(self.robot.robot_id, physicsClientId=self.env.client_id)):
            p.setCollisionFilterPair(self.robot.robot_id, object_id, l, -1, enableCollision=1, physicsClientId=self.env.client_id)
        
        # Let object physically settle on surface
        self._step_sim_for_duration(0.2)
        
        # 5. Rigorous physical verification
        obj_pos, _ = p.getBasePositionAndOrientation(object_id, physicsClientId=self.env.client_id)
        xy_dist = float(np.linalg.norm(np.array(obj_pos[:2]) - np.array(target_pos[:2])))
        
        is_stacked = desired_center_z > 0.08
        if is_stacked:
            z_err = abs(obj_pos[2] - desired_center_z)
            success = xy_dist <= 0.10 and z_err <= 0.05
            msg = "Object stacked successfully." if success else f"Stacking failed: xy_dist={xy_dist:.3f}, z_height={obj_pos[2]:.3f}"
        else:
            success = xy_dist <= 0.10
            msg = "Object placed successfully." if success else f"Placement tolerance exceeded: dist={xy_dist:.3f}"
            
        accuracy = max(0.0, min(100.0, 100.0 - (xy_dist / 0.08) * 40.0))
        
        return SkillResult(
            success=success,
            skill_name=self.name,
            message=msg,
            target_position=target_pos,
            final_position=list(obj_pos),
            metadata={"placement_accuracy": round(accuracy, 1), "xy_distance": round(xy_dist, 3)}
        )
