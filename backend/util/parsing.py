import re
import json

def parse_json_response(response: str) -> dict:
    """Parse a JSON response from the LLM."""
    cleaned_response = re.sub(r"^json\s*|\s*$", "", response.strip()).strip()
    cleaned_response = cleaned_response.replace("'", '"')
    return json.loads(cleaned_response)