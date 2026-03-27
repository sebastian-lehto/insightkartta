import numpy as np
import math


def to_python_type(value):
    """Convert numpy + invalid JSON values to safe Python types."""
    
    # Handle numpy types
    if isinstance(value, (np.integer,)):
        return int(value)
    
    if isinstance(value, (np.floating,)):
        value = float(value)

    # Handle NaN / Inf
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def clean_dict(d: dict) -> dict:
    """Recursively clean dictionary."""
    cleaned = {}

    for k, v in d.items():
        if isinstance(v, dict):
            cleaned[k] = clean_dict(v)

        elif isinstance(v, list):
            cleaned[k] = [
                clean_dict(i) if isinstance(i, dict) else to_python_type(i)
                for i in v
            ]

        else:
            cleaned[k] = to_python_type(v)

    return cleaned