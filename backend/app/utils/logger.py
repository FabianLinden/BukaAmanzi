import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Setup structured logger with proper formatting."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  # Already configured
    
    # Set log level
    log_level = getattr(logging, (level or "INFO").upper())
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


# Default application logger
logger = setup_logger("water_watch")
