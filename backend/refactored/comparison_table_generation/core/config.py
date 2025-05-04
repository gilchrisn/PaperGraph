"""
comparison_table_generation/core/config.py

Configuration settings for the table generation pipeline
"""

import os
import logging
from dotenv import load_dotenv
from enum import Enum, auto

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("comparison_pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Default parameters
DEFAULT_TOP_K = 3
DEFAULT_SIMILARITY_THRESHOLD = 0.85
DEFAULT_MAX_ITERATIONS = 3