"""
Logging utility module.
"""

import logging
from typing import Dict, Any

def setup_logger(config: Dict[str, Any]) -> logging.Logger:
    """
    Setup and configure the logger based on the provided configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary containing 'logging' settings.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging_config = config.get("logging", {})
    level_str = logging_config.get("level", "INFO").upper()
    format_str = logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    level = getattr(logging, level_str, logging.INFO)
    
    logger = logging.getLogger("hlmp")
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if logger is set up again
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter(format_str)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger
