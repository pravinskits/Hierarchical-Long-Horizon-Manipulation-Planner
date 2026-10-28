"""
Demonstration script for Hierarchical Task Planner.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.core.planner import HierarchicalPlanner

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("PlannerDemo")
    
    planner = HierarchicalPlanner(logger)
    
    # Example 1: Multi-object manipulation goal
    goal = "Move the red cube to the target and move the blue cube beside it"
    
    print("========================================")
    print("HIERARCHICAL PLAN")
    print("=================")
    print(f"\nGoal:\n{goal}\n")
    
    try:
        plan = planner.create_plan(goal)
        print(f"Planner:\n{plan.planner_type}\n")
        print("## Subgoals:\n")
        
        for sg in plan.subgoals:
            print(f"{sg.id.replace('sg_0', '').replace('sg_00', '')}. {sg.skill.replace('Skill', '').upper()} {sg.parameters.get('target', '')}")
            print("   Preconditions:")
            for p in sg.preconditions:
                print(f"   * {p}")
            print("\n   Expected:")
            for e in sg.expected_outcome:
                print(f"   * {e}")
            if sg.dependencies:
                print("\n   Depends on:")
                for d in sg.dependencies:
                    print(f"   * {d}")
            print("")
            
        print("========================================")
        
        validation = planner.validate_plan(plan)
        print(f"\nPlan Validation:\n{'VALID' if validation.valid else 'INVALID'}")
        if validation.errors:
            print(f"Errors: {validation.errors}")
        print(f"\nTotal Subgoals: {len(plan.subgoals)}\n")
        
    except Exception as e:
        print(f"Failed: {e}")
        
    # Example 2: Long-horizon goal
    print("========================================")
    print("LONG-HORIZON DEMO")
    print("=================")
    goal_long = "Move the red cube to target and move blue cube to target and move green cube to target and push yellow block to target"
    print(f"Goal: {goal_long}")
    
    plan_long = planner.create_plan(goal_long)
    validation_long = planner.validate_plan(plan_long)
    
    print(f"\nPlan Validation: {'VALID' if validation_long.valid else 'INVALID'}")
    print(f"Total Subgoals: {len(plan_long.subgoals)}")
    
if __name__ == "__main__":
    main()
