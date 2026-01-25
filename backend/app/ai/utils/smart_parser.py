# backend/app/ai/utils/smart_parser.py
"""
Smart parsing utilities for dates, times, units, and measurements.
Handles multiple formats flexibly for AI-extracted data.
"""

import re
import logging
from datetime import datetime, date, time
from typing import Optional, Union, Tuple

logger = logging.getLogger(__name__)


# ============================================
# DATE PARSING
# ============================================

# Common date formats to try (ordered by priority)
DATE_FORMATS = [
    # ISO format (most reliable)
    '%Y-%m-%d',
    '%Y/%m/%d',
    # Vietnamese/European format (dd.mm.yyyy, dd/mm/yyyy)
    '%d.%m.%Y',
    '%d/%m/%Y',
    '%d-%m-%Y',
    # Short year formats
    '%d.%m.%y',
    '%d/%m/%y',
    '%d-%m-%y',
    # American format (mm/dd/yyyy) - lower priority
    '%m/%d/%Y',
    '%m-%d-%Y',
    # Compact formats
    '%Y%m%d',
    '%d%m%Y',
]


def parse_date(value: Union[str, date, datetime, None]) -> Optional[date]:
    """
    Parse date from various formats.

    Handles:
    - datetime/date objects (pass through)
    - ISO: 2026-01-09
    - Vietnamese: 09.01.2026, 09/01/2026
    - Compact: 20260109

    Returns:
        date object or None if parsing fails
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()
    if not value:
        return None

    # Try each format
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.date()
        except ValueError:
            continue

    # Try regex extraction for embedded dates
    # Pattern: dd.mm.yyyy or dd/mm/yyyy in text
    patterns = [
        r'(\d{2})[./](\d{2})[./](\d{4})',  # dd.mm.yyyy or dd/mm/yyyy
        r'(\d{4})[./-](\d{2})[./-](\d{2})',  # yyyy-mm-dd
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            groups = match.groups()
            try:
                if len(groups[0]) == 4:  # yyyy-mm-dd
                    return date(int(groups[0]), int(groups[1]), int(groups[2]))
                else:  # dd.mm.yyyy
                    return date(int(groups[2]), int(groups[1]), int(groups[0]))
            except ValueError:
                continue

    logger.warning(f"Could not parse date: {value}")
    return None


def format_date_iso(value: Union[str, date, datetime, None]) -> Optional[str]:
    """
    Parse and format date to ISO string (YYYY-MM-DD).
    Safe for database insertion.
    """
    d = parse_date(value)
    return d.isoformat() if d else None


# ============================================
# TIME PARSING
# ============================================

TIME_FORMATS = [
    '%H:%M:%S',
    '%H:%M',
    '%H.%M',
    '%Hh%M',
    '%H giờ %M',
    '%H giờ',
    '%Hh',
]


def parse_time(value: Union[str, time, datetime, None]) -> Optional[time]:
    """
    Parse time from various formats.

    Handles:
    - time/datetime objects (pass through)
    - 11:00, 11.00, 11h00, 11 giờ 00, 11h
    - Text like "11 giờ sáng"

    Returns:
        time object or None if parsing fails
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.time()

    if isinstance(value, time):
        return value

    if not isinstance(value, str):
        value = str(value)

    value = value.strip().lower()
    if not value:
        return None

    # Try each format
    for fmt in TIME_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.time()
        except ValueError:
            continue

    # Regex for various patterns
    patterns = [
        r'(\d{1,2})[:.h](\d{2})',  # 11:00, 11.00, 11h00
        r'(\d{1,2})\s*(?:giờ|h)\s*(\d{2})?',  # 11 giờ 30, 11h
        r'(\d{1,2})\s*(?:am|pm|sáng|chiều)',  # 11 am, 11 sáng
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            groups = match.groups()
            try:
                hour = int(groups[0])
                minute = int(groups[1]) if groups[1] else 0

                # Handle AM/PM
                if 'pm' in value or 'chiều' in value:
                    if hour < 12:
                        hour += 12
                elif 'am' in value or 'sáng' in value:
                    if hour == 12:
                        hour = 0

                return time(hour, minute)
            except (ValueError, IndexError):
                continue

    logger.warning(f"Could not parse time: {value}")
    return None


def format_time_str(value: Union[str, time, datetime, None]) -> Optional[str]:
    """
    Parse and format time to string (HH:MM:SS).
    Safe for database insertion.
    """
    t = parse_time(value)
    return t.strftime('%H:%M:%S') if t else None


# ============================================
# UNIT NORMALIZATION
# ============================================

# Unit mappings (normalized -> aliases)
UNIT_MAPPINGS = {
    # Volume
    'CBM': ['cbm', 'm3', 'm³', 'cubic meter', 'cubic metre', 'khối'],
    'M2': ['m2', 'm²', 'square meter', 'square metre', 'mét vuông'],

    # Weight
    'KG': ['kg', 'kilogram', 'kgs', 'kilo', 'ki-lo'],
    'TON': ['ton', 'tấn', 'tan', 'tonne', 'metric ton', 't'],
    'G': ['g', 'gram', 'gam'],

    # Length
    'M': ['m', 'meter', 'metre', 'mét', 'met'],
    'CM': ['cm', 'centimeter', 'centimetre'],
    'MM': ['mm', 'millimeter', 'millimetre'],

    # Package units
    'PALLET': ['pallet', 'plt', 'pallets', 'pa-let', 'palet'],
    'CARTON': ['carton', 'ctn', 'thùng', 'thung', 'cartons', 'hộp', 'hop'],
    'KIEN': ['kiện', 'kien', 'pcs', 'pieces', 'cái', 'cai'],
    'BAO': ['bao', 'bag', 'bags', 'túi', 'tui'],
    'CUON': ['cuộn', 'cuon', 'roll', 'rolls'],
    'THUNG': ['thùng', 'thung', 'box', 'boxes'],
    'KHAY': ['khay', 'tray', 'trays'],

    # Container
    'CONT20': ['cont 20', "cont 20'", '20ft', "20'", 'container 20'],
    'CONT40': ['cont 40', "cont 40'", '40ft', "40'", 'container 40', 'cont 40dc', 'cont 40hc'],
}

# Build reverse mapping
_UNIT_REVERSE = {}
for normalized, aliases in UNIT_MAPPINGS.items():
    for alias in aliases:
        _UNIT_REVERSE[alias.lower()] = normalized


def normalize_unit(value: Optional[str]) -> Optional[str]:
    """
    Normalize unit to standard form.

    Examples:
        'm3' -> 'CBM'
        'tấn' -> 'TON'
        'thùng' -> 'THUNG'
    """
    if not value:
        return None

    value_lower = value.strip().lower()

    # Direct match
    if value_lower in _UNIT_REVERSE:
        return _UNIT_REVERSE[value_lower]

    # Partial match
    for alias, normalized in _UNIT_REVERSE.items():
        if alias in value_lower or value_lower in alias:
            return normalized

    # Return original if no match (might be valid unit we don't know)
    return value.upper()


def parse_quantity_with_unit(value: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse quantity and unit from combined string.

    Examples:
        "1.5 CBM" -> (1.5, "CBM")
        "10 tấn" -> (10.0, "TON")
        "3 pallet 5 thùng" -> (8.0, "MIXED")

    Returns:
        (quantity, unit) tuple
    """
    if not value:
        return None, None

    value = str(value).strip()

    # Pattern: number + unit
    pattern = r'([\d.,]+)\s*([a-zA-Z\u00C0-\u024F]+)'
    matches = re.findall(pattern, value)

    if not matches:
        # Try to extract just number
        num_match = re.search(r'[\d.,]+', value)
        if num_match:
            try:
                qty = float(num_match.group().replace(',', '.'))
                return qty, None
            except ValueError:
                pass
        return None, None

    total_qty = 0
    units = []

    for qty_str, unit_str in matches:
        try:
            qty = float(qty_str.replace(',', '.'))
            total_qty += qty
            normalized_unit = normalize_unit(unit_str)
            if normalized_unit:
                units.append(normalized_unit)
        except ValueError:
            continue

    if not units:
        return total_qty if total_qty > 0 else None, None

    # Single unit
    if len(set(units)) == 1:
        return total_qty, units[0]

    # Multiple units
    return total_qty, 'MIXED'


# ============================================
# NUMBER PARSING
# ============================================

def parse_number(value: Union[str, int, float, None]) -> Optional[float]:
    """
    Parse number from various formats.

    Handles:
    - Number types (pass through)
    - Strings with commas: "1,234.56" or "1.234,56"
    - Vietnamese format: "1.234.567" (dots as thousands separator)
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()
    if not value:
        return None

    # Remove currency symbols and whitespace
    value = re.sub(r'[₫đVNDUSD$€\s]', '', value, flags=re.IGNORECASE)

    # Count dots and commas to determine format
    dots = value.count('.')
    commas = value.count(',')

    if dots > 1 and commas == 0:
        # Vietnamese: 1.234.567 -> 1234567
        value = value.replace('.', '')
    elif dots == 1 and commas == 0:
        # Could be decimal (1.5) or thousands (1.000)
        # If after dot is 3 digits, treat as thousands
        parts = value.split('.')
        if len(parts[1]) == 3 and len(parts[0]) <= 3:
            value = value.replace('.', '')
    elif commas == 1 and dots == 0:
        # Either decimal (1,5) or thousands (1,000)
        parts = value.split(',')
        if len(parts[1]) == 3:
            value = value.replace(',', '')
        else:
            value = value.replace(',', '.')
    elif dots >= 1 and commas >= 1:
        # Mixed format - determine which is decimal
        last_dot = value.rfind('.')
        last_comma = value.rfind(',')
        if last_dot > last_comma:
            # Dot is decimal: 1,234.56
            value = value.replace(',', '')
        else:
            # Comma is decimal: 1.234,56
            value = value.replace('.', '').replace(',', '.')

    try:
        return float(value)
    except ValueError:
        logger.warning(f"Could not parse number: {value}")
        return None


def format_number_vnd(value: Union[str, int, float, None]) -> Optional[str]:
    """Format number as VND currency string"""
    num = parse_number(value)
    if num is None:
        return None
    return f"{num:,.0f}".replace(',', '.')


# ============================================
# DIMENSION PARSING
# ============================================

def parse_dimensions(value: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Parse dimensions from string.

    Examples:
        "0.9 x 0.7 x 1.5" -> (0.9, 0.7, 1.5)
        "90x70x150cm" -> (90, 70, 150)
        "L:90 W:70 H:150" -> (90, 70, 150)

    Returns:
        (length, width, height) tuple
    """
    if not value:
        return None, None, None

    value = str(value).lower()

    # Pattern: L x W x H
    pattern = r'([\d.,]+)\s*[x×\*]\s*([\d.,]+)\s*[x×\*]\s*([\d.,]+)'
    match = re.search(pattern, value)
    if match:
        try:
            l = float(match.group(1).replace(',', '.'))
            w = float(match.group(2).replace(',', '.'))
            h = float(match.group(3).replace(',', '.'))
            return l, w, h
        except ValueError:
            pass

    # Pattern: L:xx W:xx H:xx or Dài:xx Rộng:xx Cao:xx
    l, w, h = None, None, None

    l_match = re.search(r'(?:l|length|dài|dai)[:\s]*([\d.,]+)', value)
    if l_match:
        l = parse_number(l_match.group(1))

    w_match = re.search(r'(?:w|width|rộng|rong)[:\s]*([\d.,]+)', value)
    if w_match:
        w = parse_number(w_match.group(1))

    h_match = re.search(r'(?:h|height|cao)[:\s]*([\d.,]+)', value)
    if h_match:
        h = parse_number(h_match.group(1))

    return l, w, h


# ============================================
# SMART FIELD EXTRACTION
# ============================================

def smart_extract(value: any, field_type: str) -> any:
    """
    Smart extraction based on expected field type.

    Args:
        value: Raw value from Excel/AI
        field_type: One of 'date', 'time', 'number', 'unit', 'dimensions'

    Returns:
        Parsed value in appropriate format
    """
    if value is None:
        return None

    field_type = field_type.lower()

    if field_type == 'date':
        return format_date_iso(value)
    elif field_type == 'time':
        return format_time_str(value)
    elif field_type == 'number':
        return parse_number(value)
    elif field_type == 'unit':
        return normalize_unit(str(value))
    elif field_type == 'dimensions':
        return parse_dimensions(str(value))
    else:
        return value
