"""
Main application entry point.
"""

import os
import sys
from pathlib import Path

# Ensure src is in the python path
sys.path.insert(0, str(Path(__file__).parent))

from hlmp.config import load_config
from hlmp.utils.logger import setup_logger
from hlmp.core.planner import HierarchicalPlanner

def main() -> None:
    """
    Main execution function.
    """
    # Load configuration
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "config" / "settings.yaml"
    
    try:
        config = load_config(str(config_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    # Setup logging
    logger = setup_logger(config)
    logger.info(f"Starting {config['app']['name']} v{config['app']['version']}")
    
    # Initialize and run planner
    planner = HierarchicalPlanner(config, logger)
    planner.plan()
    
    logger.info("Application finished successfully.")

if __name__ == "__main__":
    main()
