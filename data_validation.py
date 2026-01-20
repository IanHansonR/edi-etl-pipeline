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
    """
    DEPRECATED: Use parse_store_allocations instead.
    Kept for backwards compatibility.
    """
    return None


def parse_store_allocations(destination_info):
    """
    Parse SDQ structure to extract store number and quantity allocations.

    SDQ structure:
    - SDQ01: UOM for quantities
    - SDQ02: Unknown (ignored)
    - SDQ03, SDQ05, SDQ07...: Store numbers (odd positions after SDQ02)
    - SDQ04, SDQ06, SDQ08...: Quantities for each store (even positions after SDQ02)

    Returns:
        List of tuples: [(store_number, qty), ...] or empty list if no valid data
    """
    if not destination_info or 'SDQ' not in destination_info:
        return []

    sdq = destination_info['SDQ']
    allocations = []

    # Start at SDQ03 (index 3), process pairs: store at odd index, qty at even index
    i = 3
    while True:
        store_key = f'SDQ{i:02d}'
        qty_key = f'SDQ{i+1:02d}'

        # Check if both keys exist
        if store_key not in sdq or qty_key not in sdq:
            break

        store_number = sdq[store_key]
        qty = safe_int_conversion(sdq[qty_key], default=0)

        if store_number and qty > 0:
            allocations.append((store_number, qty))

        i += 2  # Move to next pair

    return allocations