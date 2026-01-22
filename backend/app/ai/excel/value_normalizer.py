# backend/app/ai/excel/value_normalizer.py

from typing import Optional, Any, List, Dict, Tuple
from datetime import datetime, date, time
from dataclasses import dataclass
import re

# Removed invalid imports
# from app.db.session import get_db
# from app.models import Customer, VehicleType


@dataclass
class NormalizedValue:
    """Kết quả normalize"""
    value: Any                      # Giá trị đã normalize
    original: Any                   # Giá trị gốc
    confidence: float               # Confidence score
    resolved_id: Optional[int] = None  # ID nếu resolve được từ DB
    resolved_name: Optional[str] = None  # Tên đầy đủ nếu resolve
    warning: Optional[str] = None   # Warning nếu có


class DateNormalizer:
    """Normalize các format ngày khác nhau"""
    
    # Các pattern ngày phổ biến
    DATE_PATTERNS = [
        # Vietnamese formats
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),  # 17/01/2026
        (r'(\d{1,2})/(\d{1,2})/(\d{2})', '%d/%m/%y'),  # 17/01/26
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%d-%m-%Y'),  # 17-01-2026
        (r'(\d{1,2})-(\d{1,2})-(\d{2})', '%d-%m-%y'),  # 17-01-26
        # ISO format
        (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),      # 2026-01-17
        # English formats
        (r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', None),  # 17 Jan
        (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})', None),  # Jan 17
    ]
    
    MONTH_NAMES = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    RELATIVE_DATES = {
        'hôm nay': 0, 'today': 0,
        'ngày mai': 1, 'mai': 1, 'tomorrow': 1,
        'ngày kia': 2, 'mốt': 2,
        'hôm qua': -1, 'yesterday': -1,
    }
    
    def normalize(self, value: Any, base_date: Optional[date] = None) -> NormalizedValue:
        """
        Normalize date value
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty date value")
        
        original = value
        base = base_date or date.today()
        
        # If already a date/datetime
        if isinstance(value, datetime):
            return NormalizedValue(value.date(), original, 1.0)
        if isinstance(value, date):
            return NormalizedValue(value, original, 1.0)
        
        value_str = str(value).strip().lower()
        
        # Check relative dates
        for pattern, delta in self.RELATIVE_DATES.items():
            if pattern in value_str:
                from datetime import timedelta
                result_date = base + timedelta(days=delta)
                return NormalizedValue(result_date, original, 0.95)
        
        # Try date patterns
        for pattern, fmt in self.DATE_PATTERNS:
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                try:
                    if fmt:
                        parsed = datetime.strptime(match.group(), fmt).date()
                        return NormalizedValue(parsed, original, 0.95)
                    else:
                        # Handle month name formats
                        groups = match.groups()
                        day = None
                        month = None
                        for g in groups:
                            if g.isdigit():
                                day = int(g)
                            elif g.lower() in self.MONTH_NAMES:
                                month = self.MONTH_NAMES[g.lower()]
                        
                        if day and month:
                            year = base.year
                            parsed = date(year, month, day)
                            # If parsed date is in past, assume next year
                            if parsed < base:
                                parsed = date(year + 1, month, day)
                            return NormalizedValue(parsed, original, 0.85)
                except ValueError:
                    continue
        
        return NormalizedValue(None, original, 0.0, warning=f"Could not parse date: {value}")


class TimeNormalizer:
    """Normalize các format giờ khác nhau"""
    
    TIME_PATTERNS = [
        (r'(\d{1,2}):(\d{2}):(\d{2})', '%H:%M:%S'),    # 22:00:00
        (r'(\d{1,2}):(\d{2})', '%H:%M'),               # 22:00
        (r'(\d{1,2})h(\d{2})?', None),                 # 22h hoặc 22h00
        (r'(\d{1,2})\s*(AM|PM|am|pm)', None),          # 10PM
        (r'(\d{1,2})g(\d{2})?', None),                 # 22g hoặc 22g00
    ]
    
    def normalize(self, value: Any) -> NormalizedValue:
        """Normalize time value"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.5)  # Time often optional
        
        original = value
        
        # If already a time/datetime
        if isinstance(value, datetime):
            return NormalizedValue(value.time(), original, 1.0)
        if isinstance(value, time):
            return NormalizedValue(value, original, 1.0)
        
        value_str = str(value).strip().lower()
        
        # Try patterns
        for pattern, fmt in self.TIME_PATTERNS:
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                try:
                    if fmt:
                        parsed = datetime.strptime(match.group(), fmt).time()
                        return NormalizedValue(parsed, original, 0.95)
                    else:
                        # Handle special formats (22h, 10PM, etc.)
                        groups = match.groups()
                        hour = int(groups[0])
                        minute = int(groups[1]) if groups[1] and groups[1].isdigit() else 0
                        
                        # Handle AM/PM
                        if len(groups) > 1 and groups[-1] and groups[-1].lower() in ['pm', 'am']:
                            if groups[-1].lower() == 'pm' and hour < 12:
                                hour += 12
                            elif groups[-1].lower() == 'am' and hour == 12:
                                hour = 0
                        
                        parsed = time(hour, minute)
                        return NormalizedValue(parsed, original, 0.9)
                except ValueError:
                    continue
        
        return NormalizedValue(None, original, 0.0, warning=f"Could not parse time: {value}")


class CustomerResolver:
    """Resolve customer từ code/name using raw SQL via DB Adapter"""
    
    def __init__(self, db_adapter=None):
        self.db = db_adapter
        self._cache = {}  # Cache kết quả
    
    async def load_customers(self):
        """Load customers từ DB vào cache"""
        if self.db is None:
            return
        
        try:
            # Query customers table using raw SQL
            query = "SELECT customer_id, customer_code, short_name, customer_name FROM customers WHERE is_active = true"
            customers = await self.db.fetch_all(query)
            
            for c in customers:
                # Add exact code match
                c_code = c['customer_code'].lower() if c['customer_code'] else ""
                c_name = c['short_name'].lower() if c['short_name'] else (c['customer_name'].lower() if c.get('customer_name') else "")
                c_id = c['customer_id']
                
                if c_code:
                    self._cache[c_code] = {
                        'id': c_id,
                        'code': c['customer_code'],
                        'name': c_name,
                        'confidence': 1.0
                    }
                
                # Add name variations
                if c_name:
                    self._cache[c_name] = {
                        'id': c_id,
                        'code': c['customer_code'],
                        'name': c_name,
                        'confidence': 0.95
                    }
                    # Add first word of name if meaningful (length > 2)
                    first_word = c_name.split()[0]
                    if len(first_word) > 2 and first_word not in self._cache:
                        self._cache[first_word] = {
                            'id': c_id,
                            'code': c['customer_code'],
                            'name': c_name,
                            'confidence': 0.7
                        }
        except Exception as e:
            print(f"Error loading customers: {e}")
    
    def resolve(self, value: Any) -> NormalizedValue:
        """Resolve customer từ code hoặc name"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty customer value")
        
        original = value
        value_str = str(value).strip().lower()
        
        # Try exact match first
        if value_str in self._cache:
            match = self._cache[value_str]
            return NormalizedValue(
                match['code'],
                original,
                match['confidence'],
                resolved_id=match['id'],
                resolved_name=match['name']
            )
        
        # Try partial match
        for key, match in self._cache.items():
            if key in value_str or value_str in key:
                return NormalizedValue(
                    match['code'],
                    original,
                    match['confidence'] * 0.8,  # Lower confidence for partial
                    resolved_id=match['id'],
                    resolved_name=match['name']
                )
        
        # Not found - return as-is with low confidence
        return NormalizedValue(
            value_str.upper(),
            original,
            0.3,
            warning=f"Customer not found in database: {value}"
        )


class VehicleTypeNormalizer:
    """Normalize và resolve vehicle types using raw SQL"""
    
    # Common aliases
    VEHICLE_ALIASES = {
        # Xe tải
        '500kg': ('xe_tai', '500KG'),
        '0.5t': ('xe_tai', '500KG'),
        '1t': ('xe_tai', '1T'),
        '1 tấn': ('xe_tai', '1T'),
        '1.5t': ('xe_tai', '1.5T'),
        '2t': ('xe_tai', '2T'),
        '2 tấn': ('xe_tai', '2T'),
        '3.5t': ('xe_tai', '3.5T'),
        '5t': ('xe_tai', '5T'),
        '5 tấn': ('xe_tai', '5T'),
        'xe 5 tấn': ('xe_tai', '5T'),
        '8t': ('xe_tai', '8T'),
        '10t': ('xe_tai', '10T'),
        '15t': ('xe_tai', '15T'),
        # Container
        'cont 20': ('container', '20FT'),
        'container 20': ('container', '20FT'),
        '20ft': ('container', '20FT'),
        '20 feet': ('container', '20FT'),
        'cont 40': ('container', '40FT'),
        'container 40': ('container', '40FT'),
        '40ft': ('container', '40FT'),
        '40hc': ('container', '40HC'),
        '40hq': ('container', '40HC'),
        # Xe đầu kéo
        'đầu kéo': ('dau_keo', 'DAU_KEO'),
        'mooc': ('dau_keo', 'MOOC'),
        'rơ mooc': ('dau_keo', 'MOOC'),
    }
    
    def __init__(self, db_adapter=None):
        self.db = db_adapter
        self._db_cache = {}
    
    async def load_vehicle_types(self):
        """Load vehicle types từ DB"""
        if self.db is None:
            return
        
        try:
            # Assuming table vehicle_types or similar. 
            # If table doesn't exist, this will fail but catch exception.
            # Standardizing result dict keys to lower case just in case.
            query = "SELECT vehicle_type_id, code, name FROM vehicle_types WHERE is_active = true"
            vehicle_types = await self.db.fetch_all(query)
            
            for vt in vehicle_types:
                vt_code = vt.get('code', '').lower()
                vt_name = vt.get('name', '')
                vt_id = vt.get('vehicle_type_id') or vt.get('id')
                
                if vt_code:
                    self._db_cache[vt_code] = {
                        'id': vt_id,
                        'code': vt['code'],
                        'name': vt_name
                    }
        except Exception as e:
            print(f"Error loading vehicle types: {e}")
            # Fallback hardcoded types if needed?
    
    def normalize(self, value: Any) -> NormalizedValue:
        """Normalize vehicle type"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return NormalizedValue(None, value, 0.0, warning="Empty vehicle type")
        
        original = value
        value_str = str(value).strip().lower()
        
        # Clean up common variations
        value_str = value_str.replace('xe ', '').replace(' tấn', 't').replace('tấn', 't')
        value_str = re.sub(r'\s+', ' ', value_str).strip()
        
        # Try alias match
        for alias, (category, code) in self.VEHICLE_ALIASES.items():
            if alias in value_str or value_str in alias:
                # Try to find in DB
                if code.lower() in self._db_cache:
                    match = self._db_cache[code.lower()]
                    return NormalizedValue(
                        code,
                        original,
                        0.95,
                        resolved_id=match['id'],
                        resolved_name=match['name']
                    )
                return NormalizedValue(code, original, 0.85)
        
        # Try DB match
        for key, match in self._db_cache.items():
            if key in value_str or value_str in key:
                return NormalizedValue(
                    match['code'],
                    original,
                    0.8,
                    resolved_id=match['id'],
                    resolved_name=match['name']
                )
        
        # Not found
        return NormalizedValue(
            value_str.upper(),
            original,
            0.3,
            warning=f"Vehicle type not recognized: {value}"
        )


class ValueNormalizer:
    """
    Main class để normalize tất cả các loại giá trị
    """
    
    def __init__(self, db_adapter=None):
        self.date_normalizer = DateNormalizer()
        self.time_normalizer = TimeNormalizer()
        self.customer_resolver = CustomerResolver(db_adapter)
        self.vehicle_normalizer = VehicleTypeNormalizer(db_adapter)
    
    async def initialize(self):
        """Load data từ DB"""
        await self.customer_resolver.load_customers()
        await self.vehicle_normalizer.load_vehicle_types()
    
    def normalize(self, field_type: str, value: Any) -> NormalizedValue:
        """
        Normalize value dựa trên field type
        """
        if field_type == 'date':
            return self.date_normalizer.normalize(value)
        elif field_type == 'time':
            return self.time_normalizer.normalize(value)
        elif field_type == 'customer_code':
            return self.customer_resolver.resolve(value)
        elif field_type == 'vehicle_type':
            return self.vehicle_normalizer.normalize(value)
        else:
            # Default: return as-is
            if value is None or (isinstance(value, str) and not value.strip()):
                return NormalizedValue(None, value, 0.5)
            return NormalizedValue(str(value).strip(), value, 0.9)
