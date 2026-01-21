"""
SLMS AI Pipeline - Stage 5: Validator
=====================================

Validate extracted entities and identify missing required fields.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of validation"""
    is_valid: bool
    missing_fields: List[str]
    errors: List[str]
    warnings: List[str]
    normalized_entities: Dict[str, Any]


class Validator:
    """
    Validate extracted entities for each intent
    """
    
    # Required fields per intent
    REQUIRED_FIELDS = {
        "create_booking": ["customer_code", "booking_date"],
        "assign_vehicle": ["license_plate", "driver_phone"],
        "update_status": ["job_number", "new_status"],
        "query_info": [],
        "general_chat": [],
    }
    
    # Optional but recommended fields
    RECOMMENDED_FIELDS = {
        "create_booking": ["pickup_time", "vehicle_type"],
        "assign_vehicle": ["driver_name"],
        "update_status": [],
    }
    
    async def validate(
        self,
        intent: str,
        entities: Dict[str, Any],
        context: Dict = None
    ) -> ValidationResult:
        """
        Validate entities for given intent
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            context: Database context for validation
            
        Returns:
            ValidationResult with validation status and details
        """
        
        missing_fields = []
        errors = []
        warnings = []
        normalized = entities.copy()
        
        # Get required fields for intent
        required = self.REQUIRED_FIELDS.get(intent, [])
        recommended = self.RECOMMENDED_FIELDS.get(intent, [])
        
        # Check required fields
        for field in required:
            if field not in entities or not entities[field]:
                missing_fields.append(field)
        
        # Check recommended fields (add warnings)
        for field in recommended:
            if field not in entities or not entities[field]:
                warnings.append(f"Nên có trường '{field}' để xử lý tốt hơn")
        
        # Intent-specific validation
        if intent == "create_booking":
            field_errors, field_warnings, normalized = self._validate_booking(entities, context)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
        
        elif intent == "assign_vehicle":
            field_errors, field_warnings, normalized = self._validate_vehicle(entities, context)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
        
        elif intent == "update_status":
            field_errors, field_warnings, normalized = self._validate_status(entities, context)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
        
        is_valid = len(missing_fields) == 0 and len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            missing_fields=missing_fields,
            errors=errors,
            warnings=warnings,
            normalized_entities=normalized
        )
    
    def _validate_booking(
        self, 
        entities: Dict, 
        context: Dict
    ) -> tuple[List[str], List[str], Dict]:
        """Validate booking entities"""
        
        errors = []
        warnings = []
        normalized = entities.copy()
        
        # Validate customer
        if customer := entities.get("customer_code"):
            customers = context.get("customers", []) if context else []
            if customers:
                valid_codes = [c.get("customer_code") for c in customers]
                if customer not in valid_codes:
                    # Try fuzzy match
                    matched = False
                    for c in customers:
                        if customer.lower() in c.get("short_name", "").lower():
                            normalized["customer_code"] = c["customer_code"]
                            matched = True
                            break
                    if not matched:
                        warnings.append(f"Khách hàng '{customer}' không có trong danh sách")
        
        # Validate date
        if date := entities.get("booking_date"):
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                if parsed_date < today:
                    warnings.append(f"Ngày '{date}' là ngày trong quá khứ")
                
                # Check if too far in future
                if (parsed_date - today).days > 30:
                    warnings.append(f"Ngày '{date}' hơn 30 ngày trong tương lai")
                    
            except ValueError:
                errors.append(f"Ngày '{date}' không hợp lệ")
        
        # Validate time
        if time := entities.get("pickup_time"):
            if not re.match(r"^\d{2}:\d{2}$", time):
                errors.append(f"Giờ '{time}' không đúng định dạng (HH:MM)")
        
        # Validate vehicle type
        if vehicle := entities.get("vehicle_type"):
            valid_types = context.get("vehicle_types", []) if context else []
            if valid_types and vehicle not in valid_types:
                warnings.append(f"Loại xe '{vehicle}' không có trong danh sách chuẩn")
        
        # Validate quantity
        if qty := entities.get("package_quantity"):
            if not isinstance(qty, int) or qty <= 0:
                errors.append(f"Số lượng '{qty}' không hợp lệ")
        
        return errors, warnings, normalized
    
    def _validate_vehicle(
        self, 
        entities: Dict, 
        context: Dict
    ) -> tuple[List[str], List[str], Dict]:
        """Validate vehicle entities"""
        
        errors = []
        warnings = []
        normalized = entities.copy()
        
        # Validate license plate
        if plate := entities.get("license_plate"):
            # Vietnam plate format: XXY ZZZZZ (e.g., 29H 76514)
            if not re.match(r"^\d{2}[A-Z]\s?\d{4,5}$", plate):
                warnings.append(f"Biển số '{plate}' có thể không đúng định dạng")
        
        # Validate phone
        if phone := entities.get("driver_phone"):
            if not re.match(r"^0\d{9}$", phone):
                if len(phone) == 9:
                    normalized["driver_phone"] = "0" + phone
                elif len(phone) != 10:
                    errors.append(f"Số điện thoại '{phone}' không hợp lệ (cần 10 số)")
        
        # Validate CCCD
        if cccd := entities.get("driver_cccd"):
            if not re.match(r"^\d{12}$", cccd):
                warnings.append(f"CCCD '{cccd}' không đúng định dạng (cần 12 số)")
        
        # Check if can match with pending job
        pending_jobs = context.get("pending_jobs", []) if context else []
        if pending_jobs and not entities.get("matched_job_no"):
            if len(pending_jobs) > 1:
                warnings.append(f"Có {len(pending_jobs)} jobs đang chờ xe. Vui lòng chỉ định job cụ thể.")
        
        return errors, warnings, normalized
    
    def _validate_status(
        self, 
        entities: Dict, 
        context: Dict
    ) -> tuple[List[str], List[str], Dict]:
        """Validate status entities"""
        
        errors = []
        warnings = []
        normalized = entities.copy()
        
        # Validate job number
        if job_no := entities.get("job_number"):
            active_jobs = context.get("active_jobs", []) if context else []
            if active_jobs:
                valid_jobs = [j.get("job_no") for j in active_jobs]
                if job_no not in valid_jobs:
                    # Try partial match
                    matched = False
                    for j in active_jobs:
                        if job_no in j.get("job_no", ""):
                            normalized["job_number"] = j["job_no"]
                            normalized["job_id"] = j.get("job_id")
                            matched = True
                            break
                    if not matched:
                        errors.append(f"Job '{job_no}' không tìm thấy trong danh sách active")
                else:
                    # Find job_id
                    for j in active_jobs:
                        if j.get("job_no") == job_no:
                            normalized["job_id"] = j.get("job_id")
                            break
        
        # Validate status
        if status := entities.get("new_status"):
            valid_statuses = context.get("valid_statuses", []) if context else []
            if valid_statuses and status not in valid_statuses:
                errors.append(f"Trạng thái '{status}' không hợp lệ")
        
        return errors, warnings, normalized


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def validate_vietnam_phone(phone: str) -> bool:
    """Validate Vietnam phone number format"""
    
    if not phone:
        return False
    
    # Remove non-digits
    digits = re.sub(r"\D", "", phone)
    
    # Check length
    if len(digits) not in [9, 10]:
        return False
    
    # Check prefix
    valid_prefixes = ["03", "05", "07", "08", "09"]
    if len(digits) == 10:
        return any(digits.startswith(p) for p in valid_prefixes)
    elif len(digits) == 9:
        return any(digits.startswith(p[1]) for p in valid_prefixes)
    
    return False


def validate_vietnam_plate(plate: str) -> bool:
    """Validate Vietnam license plate format"""
    
    if not plate:
        return False
    
    # Remove separators
    plate = re.sub(r"[\s\-.]", "", plate).upper()
    
    # Format: XXY ZZZZZ (e.g., 29H76514)
    return bool(re.match(r"^\d{2}[A-Z]\d{4,5}$", plate))


def validate_cccd(cccd: str) -> bool:
    """Validate Vietnam CCCD (Citizen ID) format"""
    
    if not cccd:
        return False
    
    # Remove non-digits
    digits = re.sub(r"\D", "", cccd)
    
    # CCCD has 12 digits
    return len(digits) == 12
