import logging
from datetime import datetime
from typing import Optional, Any


def safe_parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """
    Safely parse date strings with validation.
    SECURITY: Prevents crashes from malformed dates.
    """
    if not date_string:
        return None

    try:
        # Expected format: YYYYMMDD
        if len(date_string) != 8:
            logging.warning(f"Invalid date format length: {date_string}")
            return None

        year = int(date_string[0:4])
        month = int(date_string[4:6])
        day = int(date_string[6:8])

        # SECURITY: Validate reasonable date ranges
        if year < 2000 or year > 2100:
            logging.warning(f"Date year out of range: {year}")
            return None

        return datetime(year, month, day)
    except (ValueError, TypeError) as e:
        logging.warning(f"Date parsing failed for '{date_string}': {type(e).__name__}")
        return None


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    SECURITY: Safely convert values to integers with validation.
    """
    try:
        result = int(value)
        # SECURITY: Sanity check for reasonable quantities
        if result < 0 or result > 1000000:
            logging.warning(f"Suspicious quantity value: {result}")
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    SECURITY: Safely convert values to floats with validation.
    """
    try:
        result = float(value)
        # SECURITY: Sanity check for reasonable prices
        if result < 0 or result > 1000000:
            logging.warning(f"Suspicious price value: {result}")
            return default
        return result
    except (ValueError, TypeError):
        return default


def parse_destination_dc(destination_info):
    """Extract DC information from DestinationInfo structure"""
    # This would parse the SDQ structure to extract DC codes
    # Implementation depends on business rules for DC assignment
    if destination_info and 'SDQ' in destination_info:
        # Could extract from SDQ fields (SDQ03, SDQ05, etc. are DC codes)
        # For now, return None - implement based on business logic
        return None
    return None