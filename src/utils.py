"""
utils.py - Utility functions for RBM_Tool

This module contains helper functions used across multiple modules:
- parse_numeric_value: Parse numeric values with various formats
- Other utility functions as needed
"""

import pandas as pd
import logging
import random
import math

logger = logging.getLogger(__name__)


def parse_numeric_value(value) -> float:
    """
    Parse numeric value from string, handling both comma and dot decimal separators.
    Supports European format: -2,329.65 (comma = thousands, dot = decimal)
    Supports European format: -2.329,65 (dot = thousands, comma = decimal)
    Supports simple formats: -2329.65, -2,32965
    Always returns float with English decimal format (dot separator).
    
    Args:
        value: The value to parse (str or numeric)
        
    Returns:
        float: Parsed float value
    
    Examples:
        >>> parse_numeric_value("-2,329.65")
        -2329.65
        >>> parse_numeric_value("-2.329,65")
        -2329.65
        >>> parse_numeric_value("-2329.65")
        -2329.65
        >>> parse_numeric_value("-2,32965")
        -2329.65
        >>> parse_numeric_value(123)
        123.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if pd.isna(value) or value is None:
        return 0.0
    
    value_str = str(value).strip()
    
    # Handle European format with both thousands and decimal separators
    # Case 1: -2,329.65 (comma = thousands, dot = decimal) - most common in files
    # Case 2: -2.329,65 (dot = thousands, comma = decimal)
    if '.' in value_str and ',' in value_str:
        # Both separators present: determine which is which
        last_dot = value_str.rfind('.')
        last_comma = value_str.rfind(',')
        
        if last_dot > last_comma:
            # Format: -2,329.65 (comma = thousands, dot = decimal)
            value_str = value_str.replace(',', '')
        else:
            # Format: -2.329,65 (dot = thousands, comma = decimal)
            value_str = value_str.replace('.', '').replace(',', '.')
    elif ',' in value_str and '.' not in value_str:
        # Only comma: could be thousands or decimal
        # Check if it's a decimal separator (followed by 1-3 digits)
        comma_pos = value_str.rfind(',')
        remaining_after_comma = value_str[comma_pos+1:] if comma_pos >= 0 else ''
        if len(remaining_after_comma) <= 3:
            # Likely decimal separator
            value_str = value_str.replace(',', '.')
        else:
            # Thousands separator, remove it
            value_str = value_str.replace(',', '')
    
    try:
        return float(value_str)
    except ValueError as e:
        logger.error(f"Error parsing numeric value '{value}': {e}")
        return 0.0


def linear_reprojection(donnees, x_cibles):
    """
    Reprojette n lignes [x, y] vers m lignes [x, y] en CONSERVANT la somme des y.

    Principe : chaque y d'origine est réparti entre les deux x cibles qui
    l'encadrent, proportionnellement à la proximité (partage linéaire).

        x_cible_j ........ x ........ x_cible_j+1
        part pour j   = y * (1 - w)
        part pour j+1 = y * w        avec w = (x - x_j) / (x_j+1 - x_j)

    Extrapolation flat : un x d'origine en dehors de la plage des x cibles
    donne tout son y au premier (ou au dernier) x cible.

    - donnees  : liste de n paires [x, y], x trié croissant (espacement libre)
    - x_cibles : liste de m valeurs de x triées croissant (espacement libre)
    """
    m = len(x_cibles)
    sortie_y = [0.0] * m  # on part de zéro et on additionne les parts
    j = 0  # indice du segment cible [j, j+1] dans lequel on se trouve

    for x, y in donnees:
        if x <= x_cibles[0]:
            # Flat à gauche : tout le y va au premier x cible
            sortie_y[0] += y

        elif x >= x_cibles[-1]:
            # Flat à droite : tout le y va au dernier x cible
            sortie_y[-1] += y

        else:
            # On avance jusqu'au segment cible qui contient x
            while j < m - 2 and x_cibles[j + 1] < x:
                j += 1

            xa = x_cibles[j]
            xb = x_cibles[j + 1]
            w = (x - xa) / (xb - xa)  # entre 0 et 1

            sortie_y[j] += y * (1 - w)
            sortie_y[j + 1] += y * w

    return [[x_cibles[k], sortie_y[k]] for k in range(m)]
