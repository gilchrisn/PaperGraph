"""
comparison_table_generation/utils/logger.py

Utility functions for logging
"""

import logging
from pathlib import Path


def setup_logging(log_file: str = "comparison_pipeline.log", level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration
    
    Parameters:
        log_file: Path to log file
        level: Logging level
        
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_path = log_dir / log_file
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    
    # Get the logger
    logger = logging.getLogger("comparison_pipeline")
    
    return logger