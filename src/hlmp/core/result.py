"""
Skill Result data model.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class SkillResult:
    success: bool
    skill_name: str
    message: str
    duration: float = 0.0
    target_position: Optional[List[float]] = None
    final_position: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
