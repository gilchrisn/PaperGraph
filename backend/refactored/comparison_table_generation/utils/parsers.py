"""
comparison_table_generation/utils/parsers.py

Utility functions for parsing LLM responses
"""

import re
import json
import logging

logger = logging.getLogger(__name__)


def parse_json_response(response: str) -> dict:
    """
    Clean and parse the JSON response from the LLM.
    
    Parameters:
        response: String response from the LLM
        
    Returns:
        Parsed JSON as a dictionary
    
    Raises:
        Exception: If the response cannot be parsed as valid JSON
    """
    # Clean the response by removing markdown code block indicators
    cleaned_response = re.sub(r"^```json\s*|```$", "", response.strip()).strip()
    
    try:
        return json.loads(cleaned_response)
    except Exception as e:
        # Get detailed error information if available
        line_no = getattr(e, 'lineno', None)
        col_no = getattr(e, 'colno', None)
        msg = str(e)
        
        # Log the error details
        if line_no and col_no:
            # Split the response into lines
            lines = cleaned_response.splitlines()
            error_line = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else ""
            logger.error(
                "JSON parsing error on line %d, column %d: %s\nError line: %s", 
                line_no, col_no, msg, error_line
            )
        else:
            logger.error("JSON parsing error: %s", msg)
        
        # Re-raise the exception
        raise