"""
Manipulation Skill Library.
"""
from .base_skill import BaseSkill
from .move import MoveSkill
from .pick import PickSkill
from .place import PlaceSkill
from .push import PushSkill

__all__ = ["BaseSkill", "MoveSkill", "PickSkill", "PlaceSkill", "PushSkill", "get_skill_class"]

def get_skill_class(skill_name: str):
    skills = {
        "MoveSkill": MoveSkill,
        "PickSkill": PickSkill,
        "PlaceSkill": PlaceSkill,
        "PushSkill": PushSkill
    }
    return skills.get(skill_name)
