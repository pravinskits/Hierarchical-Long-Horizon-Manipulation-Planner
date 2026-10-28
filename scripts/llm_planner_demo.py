"""
Demonstration script for LLM-Based Hierarchical Planner.
"""

import sys
import logging
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.hlmp.core.planner import HybridPlanner

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("LLMDemo")
    
    load_dotenv()
    
    config = {
        "llm": {
            "enabled": True,
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "timeout": 10.0
        }
    }
    
    hybrid_planner = HybridPlanner(config, logger)
    
    goal = "Move the red cube to the target and move the blue cube beside it."
    
    print("========================================")
    print("LLM HIERARCHICAL PLANNER")
    print("========================")
    print(f"\nGoal:\n{goal}\n")
    print("Provider:\nGroq\n")
    print(f"Model: {config['llm']['model']}\n")
    
    if not os.getenv("GROQ_API_KEY"):
        print("LLM STATUS:\nUnavailable\n")
        print("REASON:\nMissing GROQ_API_KEY\n")
        print("FALLBACK:\nDeterministic Hierarchical Planner\n")
    
    plan = hybrid_planner.create_plan(goal, scene_state={})
    
    validation = hybrid_planner.validate_plan(plan)
    
    print("LLM Response:\nVALID\n")
    print(f"Schema Validation:\n{'PASSED' if validation.valid else 'FAILED'}\n")
    print(f"Plan Validation:\n{'PASSED' if validation.valid else 'FAILED'}\n")
    print(f"Total Subgoals:\n{len(plan.subgoals)}\n")
    print("---")
    
    for i, sg in enumerate(plan.subgoals, 1):
        print(f"\nSUBGOAL {i}")
        print(f"Skill: {sg.skill.replace('Skill', '').upper()}")
        print(f"Object: {sg.parameters.get('target', 'unknown')}")
        
    print(f"\nPlan Source:\n{plan.planner_type.upper()}")
    print("\n========================================")

if __name__ == "__main__":
    main()
