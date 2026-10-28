"""
Demonstration script for LLM Fallback behavior.
"""

import sys
import logging
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.hlmp.core.planner import HybridPlanner

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("FallbackDemo")
    
    # Force API key to be None
    if "GROQ_API_KEY" in os.environ:
        del os.environ["GROQ_API_KEY"]
        
    config = {
        "llm": {
            "enabled": True,
        }
    }
    
    hybrid_planner = HybridPlanner(config, logger)
    
    goal = "Move the red cube to the target."
    
    print("LLM STATUS:\nUnavailable\n")
    print("REASON:\nMissing GROQ_API_KEY\n")
    print("FALLBACK:\nDeterministic Hierarchical Planner\n")
    
    plan = hybrid_planner.create_plan(goal, scene_state={})
    
    print("PLAN:\nGenerated successfully\n")
    
    validation = hybrid_planner.validate_plan(plan)
    print(f"PLAN VALIDATION:\n{'PASSED' if validation.valid else 'FAILED'}")

if __name__ == "__main__":
    main()
