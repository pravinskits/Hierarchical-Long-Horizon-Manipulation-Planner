"""
Demonstration script for Structured Failure Detection.
"""

import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hlmp.core.result import SkillResult
from src.hlmp.recovery import FailureDetector
from src.hlmp.sim.fault_injection import FaultInjector

def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("FailureDemo")
    
    config = {
        "recovery": {
            "max_skill_duration": 10.0
        }
    }
    
    detector = FailureDetector(config, logger)
    injector = FaultInjector(logger)
    
    # 1-4. System startup & simulation setup (mocked for speed)
    logger.info("1-4. System setup and workspace creation initialized.")
    
    # 5-6. Attempt manipulation and introduce ONE controlled failure
    logger.info("5. Attempting Place manipulation...")
    injector.inject("force_placement_failure")
    
    # Simulate a PlaceSkill that fails because the object is outside the region
    simulated_result = SkillResult(
        success=False,
        skill_name="PlaceSkill",
        message="Failed to reach target. Dist: 0.180",
        target_position=[0.5, 0.0, 0.0],
        final_position=[0.32, 0.0, 0.0]
    )
    
    context = {
        "subgoal_id": "sg_place_01",
        "injected_fault": injector.is_active("force_placement_failure")
    }
    
    # 7-9. Detect and Classify
    logger.info("\n--- PASSING TO DETECTOR ---")
    event = detector.evaluate(simulated_result, context)
    
    # 10. Print structured diagnostic info
    if event:
        print("\n----------------------------------------")
        print("FAILURE DETECTED")
        print("----------------------------------------")
        print(f"Skill: {event.skill_name}")
        print(f"Failure Type: {event.failure_type.value}")
        print(f"Confidence: {event.confidence:.2f}")
        print(f"Message: {event.message}")
        print(f"Expected State: {event.expected_state}")
        print(f"Observed State: {event.observed_state}")
        print("----------------------------------------\n")
        
    logger.info("11-12. Demo complete. Event logged. System did NOT attempt recovery.")

if __name__ == "__main__":
    main()
