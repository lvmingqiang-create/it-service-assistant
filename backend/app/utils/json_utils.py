"""
JSON Utility Functions
======================
Shared utilities for extracting and parsing JSON from LLM responses.
"""

import re


def extract_json(text: str) -> str:
    """
    Extract JSON object from LLM response text.
    
    Handles common LLM output formats:
    - Pure JSON: {"key": "value"}
    - Markdown code block: ```json {"key": "value"} ```
    - Text with prefix: Here is the result: {"key": "value"}
    
    Args:
        text: Raw LLM response text
        
    Returns:
        Extracted JSON string (first { to last })
    """
    # Handle markdown code blocks: ```json {...} ```
    if "```" in text:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
    
    # Fallback: extract from first { to last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end + 1]
    
    return text