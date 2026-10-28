"""
Controlled fault injection mechanism.
"""
import logging
from typing import Dict, Any

class FaultInjector:
    """
    Provides a mechanism to deterministically inject errors into the simulation state for testing purposes.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.active_faults = {}
        
    def inject(self, fault_type: str, parameters: Dict[str, Any] = None) -> None:
        """
        Activates a specific fault scenario.
        E.g. fault_type='force_placement_failure'
        """
        self.active_faults[fault_type] = parameters or {}
        self.logger.warning(f"FAULT INJECTED: {fault_type}")
        
    def clear(self, fault_type: str) -> None:
        if fault_type in self.active_faults:
            del self.active_faults[fault_type]
            
    def is_active(self, fault_type: str) -> bool:
        return fault_type in self.active_faults
