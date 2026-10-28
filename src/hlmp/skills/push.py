"""
Push skill.
"""
import pybullet as p
import numpy as np
from typing import List
from .base_skill import BaseSkill, SkillResult
from .move import MoveSkill

class PushSkill(BaseSkill):
    def __init__(self, env, robot, config, logger):
        super().__init__("Push", env, robot, config, logger)
        self.move_skill = MoveSkill(env, robot, config, logger)
        
    def _execute(self, target_pos: List[float], object_id: int) -> SkillResult:
        """
        Executes a push action on an object toward the target_pos (destination).
        Uses safe transit clearance to prevent knocking into adjacent objects.
        """
        start_obj_pos, _ = p.getBasePositionAndOrientation(object_id, physicsClientId=self.env.client_id)
        
        # Calculate push vector from object to destination
        v = np.array(target_pos) - np.array(start_obj_pos)
        v[2] = 0 # Ignore Z differences
        norm_v = np.linalg.norm(v)
        if norm_v < 0.01:
            return SkillResult(False, self.name, "Object already at destination.")
        v = v / norm_v
        
        # Close gripper to form a solid pushing paddle
        self.robot.set_gripper(open_width=0.0)
        self.env.step()

        down_ori = p.getQuaternionFromEuler([3.14159, 0, 0])
        push_wrist_z = 0.115

        # 0. Lift current EE position to safe transit height
        cur_pos, _ = self.robot.get_ee_position()
        if cur_pos[2] < 0.28:
            self.move_skill._execute([cur_pos[0], cur_pos[1], 0.30], target_ori=down_ori, timeout=2.0)
            
        # 1. Approach from 8cm behind along the push vector at contact height
        approach_pos = np.array(start_obj_pos) - v * 0.08
        approach_pos[2] = push_wrist_z
        
        # Transit above approach position first, then descend
        above_app = [approach_pos[0], approach_pos[1], 0.28]
        self.move_skill._execute(above_app, target_ori=down_ori, timeout=3.0)
        res1 = self.move_skill._execute(list(approach_pos), target_ori=down_ori, timeout=3.0)
        if not res1.success:
            return SkillResult(False, self.name, "Failed to approach object for pushing.")
            
        # 2. Push straight through object along Cartesian line
        push_dist = min(0.35, np.linalg.norm(np.array(target_pos[:2]) - np.array(start_obj_pos[:2])) + 0.05)
        push_target = np.array(start_obj_pos) + v * push_dist
        push_target[2] = push_wrist_z
        
        num_pts = 20
        for s in np.linspace(0, 1, num_pts):
            pt = (1 - s) * approach_pos + s * push_target
            q = self.robot.solve_ik(list(pt), down_ori)
            self.robot.move_joints(q, max_force=800.0)
            for _ in range(2):
                self.env.step()
        
        # Settle
        self._step_sim_for_duration(0.1)
        
        # 3. Retract vertically after push
        cur_end = self.robot.get_ee_position()[0]
        self.move_skill._execute([cur_end[0], cur_end[1], 0.28], target_ori=down_ori, timeout=2.0)
        
        # Verify
        end_obj_pos, _ = p.getBasePositionAndOrientation(object_id, physicsClientId=self.env.client_id)
        moved_dist = float(np.linalg.norm(np.array(end_obj_pos) - np.array(start_obj_pos)))
        
        success = moved_dist > 0.02
        msg = "Object successfully pushed." if success else "Object failed to move significantly."
        
        return SkillResult(
            success=success,
            skill_name=self.name,
            message=msg,
            target_position=list(push_target),
            final_position=list(end_obj_pos)
        )
