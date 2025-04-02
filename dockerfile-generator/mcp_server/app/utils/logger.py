import logging
import sys
from datetime import datetime

# Configure logging
def setup_logger(name: str = "dockerfile_generator"):
    """Set up and return a logger with the given name."""
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(console_handler)
    
    return logger

# Create default logger
logger = setup_logger()