"""
Move skill.
"""
import numpy as np
from typing import List, Optional
from .base_skill import BaseSkill, SkillResult

class MoveSkill(BaseSkill):
    def __init__(self, env, robot, config, logger):
        super().__init__("Move", env, robot, config, logger)
        
    def _execute(self, target_pos: List[float], target_ori: Optional[List[float]] = None, timeout: Optional[float] = None) -> SkillResult:
        """
        Moves the EE to the target position smoothly with continuous trajectory interpolation.
        """
        import pybullet as p
        if target_ori is None:
            target_ori = p.getQuaternionFromEuler([3.14159, 0, 0])

        initial_pos, _ = self.robot.get_ee_position()
        dist = float(np.linalg.norm(np.array(initial_pos) - np.array(target_pos)))
        
        target_joints = self.robot.solve_ik(target_pos, target_ori)
        start_joints = self.robot.get_joint_states()[:len(self.robot.controllable_joints)]
        
        # 1. Smooth S-curve trajectory interpolation
        if len(start_joints) == len(target_joints) and dist > 0.01:
            num_steps = max(20, min(int(dist / 0.010), 40))
            start_arr = np.array(start_joints)
            target_arr = np.array(target_joints)
            for i in range(1, num_steps + 1):
                s = i / num_steps
                alpha = s * s * (3.0 - 2.0 * s)
                interp_q = (1.0 - alpha) * start_arr + alpha * target_arr
                self.robot.move_joints(list(interp_q), max_force=1000.0)
                self.env.step()
        else:
            self.robot.move_joints(target_joints, max_force=1000.0)
            self.env.step()
            
        # 2. Settling steps to converge on final target position
        for _ in range(45):
            self.robot.move_joints(target_joints, max_force=1000.0)
            self.env.step()
            current_pos, _ = self.robot.get_ee_position()
            if np.linalg.norm(np.array(current_pos) - np.array(target_pos)) < 0.015:
                break
                
        final_pos, _ = self.robot.get_ee_position()
        final_dist = float(np.linalg.norm(np.array(final_pos) - np.array(target_pos)))
        success = final_dist <= max(self.position_tolerance, 0.04)
        msg = "Reached target." if success else f"Failed to reach target. Dist: {final_dist:.3f}"
        
        return SkillResult(
            success=success,
            skill_name=self.name,
            message=msg,
            target_position=target_pos,
            final_position=final_pos
        )

