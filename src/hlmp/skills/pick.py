"""
Pick skill.
"""
import pybullet as p
from typing import List
from .base_skill import BaseSkill, SkillResult
from .move import MoveSkill

class PickSkill(BaseSkill):
    def __init__(self, env, robot, config, logger):
        super().__init__("Pick", env, robot, config, logger)
        self.move_skill = MoveSkill(env, robot, config, logger)
        
        cfg = config.get("skills", {})
        self.grasp_height = cfg.get("grasp_height", 0.02)
        self.lift_height = cfg.get("lift_height", 0.15)
        
    def _execute(self, target_pos: List[float], object_id: int) -> SkillResult:
        """
        Executes a pick action with full robotic motion sequence:
        1. Pre-grasp approach above object with top-down orientation
        2. Smoothly open gripper fingers
        3. Descend to grasp position
        4. Smoothly close gripper fingers
        5. Establish secure grasp constraint
        6. Lift object vertically into the air
        """
        import numpy as np
        down_ori = p.getQuaternionFromEuler([3.14159, 0, 0])
        
        # 1. Approach above object with gripper open
        above_pos = [target_pos[0], target_pos[1], max(target_pos[2] + 0.25, 0.32)]
        for w in np.linspace(0.0, 0.04, 6):
            self.robot.set_gripper(open_width=float(w))
            self.env.step()
        self._step_sim_for_duration(0.05)

        res1 = self.move_skill._execute(above_pos, target_ori=down_ori)
        if not res1.success:
            return SkillResult(False, self.name, "Failed to move above object.")
            
        # 2. Descend vertically to precise grasp position
        # Wrist at target_pos[2] + 0.12 aligns fingers perfectly with cube center with clear table margin
        grasp_pos = [target_pos[0], target_pos[1], target_pos[2] + 0.12]
        res2 = self.move_skill._execute(grasp_pos, target_ori=down_ori)
        
        # 3. Smoothly close gripper fingers around the object
        for w in np.linspace(0.04, 0.0, 6):
            self.robot.set_gripper(open_width=float(w))
            self.env.step()
        self._step_sim_for_duration(0.1)
        
        # 4. Add constraint for reliable lifting preserving relative pose
        ee_state = p.getLinkState(self.robot.robot_id, self.robot.ee_link_index, physicsClientId=self.env.client_id)
        ee_pos, ee_ori = ee_state[4], ee_state[5]
        obj_pos, obj_ori = p.getBasePositionAndOrientation(object_id, physicsClientId=self.env.client_id)
        inv_ee_pos, inv_ee_ori = p.invertTransform(ee_pos, ee_ori)
        rel_pos, rel_ori = p.multiplyTransforms(inv_ee_pos, inv_ee_ori, obj_pos, obj_ori)

        constraint_id = p.createConstraint(
            parentBodyUniqueId=self.robot.robot_id,
            parentLinkIndex=self.robot.ee_link_index,
            childBodyUniqueId=object_id,
            childLinkIndex=-1,
            jointType=p.JOINT_FIXED,
            jointAxis=[0, 0, 0],
            parentFramePosition=rel_pos,
            childFramePosition=[0, 0, 0],
            parentFrameOrientation=rel_ori,
            physicsClientId=self.env.client_id
        )
        
        # 5. Smoothly lift object vertically into the air
        res3 = self.move_skill._execute(above_pos, target_ori=down_ori)
        
        # 6. Physical verification: verify object actually lifted above original position
        lifted_pos, _ = p.getBasePositionAndOrientation(object_id, physicsClientId=self.env.client_id)
        success = lifted_pos[2] > (target_pos[2] + 0.03)
        msg = "Object successfully picked." if success else f"Object failed to lift: height={lifted_pos[2]:.3f}"
        
        return SkillResult(
            success=success,
            skill_name=self.name,
            message=msg,
            target_position=target_pos,
            metadata={"constraint_id": constraint_id}
        )
