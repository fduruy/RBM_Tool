"""
utils.py - Utility functions for RBM_Tool

This module contains helper functions used across multiple modules:
- parse_numeric_value: Parse numeric values with various formats
- Other utility functions as needed
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def parse_numeric_value(value) -> float:
    """
    Parse numeric value from string, handling both comma and dot decimal separators.
    Supports European format: -2.329.65 or -2,329.65
    Standard format: -2329.65 or -2.32965
    Always returns float with English decimal format (dot separator).
    
    Args:
        value: The value to parse (str or numeric)
        
    Returns:
        float: Parsed float value
    
    Examples:
        >>> parse_numeric_value("-2.329,65")
        -2329.65
        >>> parse_numeric_value("-2,329.65")
        -2329.65
        >>> parse_numeric_value("-2329.65")
        -2329.65
        >>> parse_numeric_value(123)
        123.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if pd.isna(value) or value is None:
        return 0.0
    
    value_str = str(value).strip()
    
    # Handle European format: -2.329.65 (thousands separator is dot, decimal is comma)
    # or -2,329.65 (thousands separator is comma, decimal is dot)
    if '.' in value_str and ',' in value_str:
        # Both separators present: determine which is which
        last_dot = value_str.rfind('.')
        last_comma = value_str.rfind(',')
        
        if last_dot > last_comma:
            # Format: 1.234,56 (dot = thousands, comma = decimal)
            value_str = value_str.replace('.', '').replace(',', '.')
        else:
            # Format: 1,234.56 (comma = thousands, dot = decimal)
            value_str = value_str.replace(',', '')
    elif ',' in value_str and '.' not in value_str:
        # Only comma: assume it's decimal separator
        value_str = value_str.replace(',', '.')
    
    try:
        return float(value_str)
    except ValueError as e:
        logger.error(f"Error parsing numeric value '{value}': {e}")
        return 0.0
