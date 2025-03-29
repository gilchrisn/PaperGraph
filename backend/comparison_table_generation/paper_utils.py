import numpy as np
import re
import json
import logging

logger = logging.getLogger(__name__)

def convert_pgvector(embedding_str: str) -> list[float]:
    """
    Convert a bracketed embedding string from pgvector into a Python list of floats.
    For example: "[0.04895872,0.0069324,...]" -> [0.04895872, 0.0069324, ...]
    """
    embedding_str = embedding_str.strip()
    if embedding_str.startswith("[") and embedding_str.endswith("]"):
        embedding_str = embedding_str[1:-1]  # remove the surrounding brackets
    float_strs = embedding_str.split(",")
    return [float(val) for val in float_strs]

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Compute the cosine similarity between two vectors.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def parse_json_response(response: str) -> dict:
    """
    Clean and parse the JSON response from the LLM.
    """
    cleaned_response = re.sub(r"^```json\s*|```$", "", response.strip()).strip()

    try:
        return json.loads(cleaned_response)
    except Exception as e:
        line = e.lineno
        col = e.colno
        # Split the response into lines
        lines = cleaned_response.splitlines()
        error_line = lines[line - 1] if 0 <= line - 1 < len(lines) else ""
        logger.error("JSON parsing error on line %d, column %d: %s\nError line: %s", line, col, e, error_line)
        raise

import json
import os
