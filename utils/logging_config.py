"""
Logging configuration for Triadic application.
Replaces print statements with proper logging.
"""
import logging
import sys
from typing import Optional

# Configure root logger
_logger_configured = False


def setup_logging(level: int = logging.INFO, format_string: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
    
    Returns:
        Configured logger instance
    """
    global _logger_configured
    
    if _logger_configured:
        return logging.getLogger(__name__)
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    _logger_configured = True
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)

