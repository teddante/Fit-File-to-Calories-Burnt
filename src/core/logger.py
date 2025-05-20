import logging
import sys
from typing import Optional

# Default logging format
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Global logger dictionary to keep track of created loggers
_loggers = {}

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name and level.
    
    Args:
        name: The name of the logger, typically __name__ of the calling module
        level: The logging level (e.g., logging.DEBUG, logging.INFO)
              If None, uses the root logger's level
    
    Returns:
        A configured logger instance
    """
    # Return existing logger if already created
    if name in _loggers:
        logger = _loggers[name]
        if level is not None:
            logger.setLevel(level)
        return logger
    
    # Create a new logger
    logger = logging.getLogger(name)
    
    # Set level if provided, otherwise inherit from root logger
    if level is not None:
        logger.setLevel(level)
    
    # Only add handlers if they don't exist yet
    
    # Store logger in dictionary
    _loggers[name] = logger
    
    return logger

def set_global_level(level: int) -> None:
    """
    Set the logging level for all loggers.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO)
    """
    # Set root logger level
    logging.getLogger().setLevel(level)
    
    # Update all existing loggers
    for logger in _loggers.values():
        logger.setLevel(level)

# Initialize root logger with default configuration
def initialize_logging(level: int = logging.INFO) -> None:
    """
    Initialize the root logger with default configuration.
    
    Args:
        level: The logging level (default: logging.INFO)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    
    # Create formatter
    formatter = logging.Formatter(DEFAULT_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    root_logger.addHandler(console_handler)

# Initialize logging with INFO level by default