import json
import logging
from typing import Any

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("comparison.log"), logging.StreamHandler()],
    )

def log_intermediate_table(filename: str, data: Any):
    """Log intermediate tables to a file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Intermediate table saved to {filename}")