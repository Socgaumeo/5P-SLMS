# backend/app/ai/memory/entity_accumulator.py

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .conversation_state import TaskContext


@dataclass
class AccumulationResult:
    """Kết quả accumulation"""
    entities: Dict[str, Any]
    missing_fields: List[str]
    is_complete: bool
    changes: List[str]  # Fields that changed
    warnings: List[str]


class EntityAccumulator:
    """
    Accumulate và merge entities qua nhiều turns
    """
    
    # Required fields for each intent
    # More lenient - only customer is truly required for initial booking
    REQUIRED_FIELDS = {
        "create_booking": ["customer_code"],  # Only customer is strictly required
        "update_job": [],  # job_id or job_number - will be validated separately
        "update_status": [],  # job_id or job_number - will be validated separately
        "check_status": ["job_id"],
        "assign_vehicle": [],  # No strict requirement - we can lookup job_number
        "cancel_job": ["job_id"],
        # New intents
        "create_customer": ["company_name"],  # Company name is required
        "create_vendor": ["vendor_name"],  # Vendor name is required
        "create_quotation": ["quote_type", "price"],  # Both required for quotation
    }

    # Fields that we encourage but allow missing
    ENCOURAGED_FIELDS = {
        "create_booking": ["booking_date", "pickup_date", "delivery_address", "dest_address"],
        "assign_vehicle": ["license_plate", "driver_name"],
        "create_customer": ["customer_code", "address", "tax_code"],
        "create_vendor": ["vendor_code", "phone"],
        "create_quotation": ["origin_province", "destination_province", "vehicle_type"],
        "update_job": ["job_number", "action_type"],  # Need job and action type
        "update_status": ["job_number", "new_status"],
    }

    # Optional but useful fields
    OPTIONAL_FIELDS = {
        "create_booking": ["time", "vehicle_type", "origin", "cargo", "quantity", "notes"],
        "update_job": ["new_customer_code", "new_service_type", "origin_address", "dest_address", "change_reason", "notes", "fee_type", "fee_amount"],
        "update_status": ["notes"],
        "assign_vehicle": ["driver_name", "driver_phone"],
        "create_customer": ["short_name", "contact_phone", "contact_email", "contact_person"],
        "create_vendor": ["short_name", "email", "address", "tax_code"],
        "create_quotation": ["quote_type", "vendor_name", "customer_name", "sub_route", "currency", "unit", "service_type", "rate_type", "notes"],
    }
    
    # Default values for some fields
    FIELD_DEFAULTS = {
        "origin": "Từ kho",  # Default pickup location
    }
    
    def __init__(self):
        pass
    
    def accumulate(
        self,
        task: TaskContext,
        new_entities: Dict[str, Any],
        intent: Optional[str] = None
    ) -> AccumulationResult:
        """
        Accumulate new entities into task context
        
        Args:
            task: Current task context
            new_entities: Newly extracted entities
            intent: Intent (use task.intent if None)
        
        Returns:
            AccumulationResult with merged entities and status
        """
        intent = intent or task.intent
        changes = []
        warnings = []
        
        # Start with existing entities
        merged = dict(task.entities)
        
        # Merge new entities
        for key, value in new_entities.items():
            if value is None:
                continue
            
            old_value = merged.get(key)
            
            # Check for conflict
            if old_value is not None and old_value != value:
                # New value overrides old
                warnings.append(f"'{key}' changed: {old_value} → {value}")
            
            if old_value != value:
                changes.append(key)
            
            merged[key] = value
        
        # Apply defaults for missing optional fields
        for field, default in self.FIELD_DEFAULTS.items():
            if field not in merged:
                merged[field] = default
        
        # Check required fields
        required = self.REQUIRED_FIELDS.get(intent, [])
        missing = []
        for field in required:
            if field not in merged or merged[field] is None:
                missing.append(field)
        
        return AccumulationResult(
            entities=merged,
            missing_fields=missing,
            is_complete=len(missing) == 0,
            changes=changes,
            warnings=warnings
        )
    
    def correct_entity(
        self,
        task: TaskContext,
        field: str,
        new_value: Any
    ) -> AccumulationResult:
        """
        Correct a specific entity
        """
        merged = dict(task.entities)
        old_value = merged.get(field)
        
        changes = []
        warnings = []
        
        if old_value != new_value:
            changes.append(field)
            if old_value is not None:
                warnings.append(f"Corrected '{field}': {old_value} → {new_value}")
        
        merged[field] = new_value
        
        # Recalculate missing
        required = self.REQUIRED_FIELDS.get(task.intent, [])
        missing = [f for f in required if f not in merged or merged[f] is None]
        
        return AccumulationResult(
            entities=merged,
            missing_fields=missing,
            is_complete=len(missing) == 0,
            changes=changes,
            warnings=warnings
        )
    
    def get_missing_fields_message(
        self, 
        intent: str, 
        missing: List[str]
    ) -> str:
        """
        Generate human-readable message about missing fields
        """
        if not missing:
            return ""
        
        field_names = {
            "customer_code": "khách hàng",
            "date": "ngày lấy hàng",
            "time": "giờ lấy hàng",
            "destination": "điểm giao hàng",
            "origin": "điểm lấy hàng",
            "vehicle_type": "loại xe",
            "job_id": "mã job",
            "license_plate": "biển số xe",
            "driver_name": "tên tài xế",
            "driver_phone": "số điện thoại tài xế",
            # New fields
            "company_name": "tên công ty",
            "vendor_name": "tên nhà cung cấp",
            "tax_code": "mã số thuế",
            "address": "địa chỉ",
            "price": "đơn giá",
            "origin_province": "tỉnh đi",
            "destination_province": "tỉnh đến",
            # Update job fields
            "job_number": "mã job",
            "action_type": "loại thay đổi (đổi KH, thêm dịch vụ, etc.)",
            "new_customer_code": "khách hàng mới",
            "new_service_type": "loại dịch vụ mới",
            "new_status": "trạng thái mới",
            # Fee fields
            "fee_type": "loại phí",
            "fee_amount": "số tiền phí",
        }
        
        missing_names = [field_names.get(f, f) for f in missing]
        
        if len(missing_names) == 1:
            return f"Xin cho biết {missing_names[0]}?"
        else:
            return f"Xin bổ sung: {', '.join(missing_names)}"
    
    def get_summary(self, task: TaskContext) -> str:
        """
        Generate summary of accumulated entities
        """
        if not task.entities:
            return "Chưa có thông tin nào."
        
        field_labels = {
            "customer_code": "Khách hàng",
            "date": "Ngày",
            "time": "Giờ",
            "destination": "Giao tại",
            "origin": "Lấy tại",
            "vehicle_type": "Loại xe",
            "cargo": "Hàng hóa",
            "cargo_type": "Hàng hóa",
            "quantity": "Số lượng",
            "notes": "Ghi chú",
            "job_id": "Job",
            # Booking fields
            "booking_date": "Ngày booking",
            "pickup_date": "Ngày lấy hàng",
            "pickup_time": "Giờ lấy hàng",
            "pickup_address": "Điểm lấy hàng",
            "origin_address": "Điểm lấy hàng",
            "delivery_address": "Điểm giao hàng",
            "dest_address": "Điểm giao hàng",
            "delivery_company": "Công ty nhận hàng",
            "package_quantity": "Số kiện",
            "package_quantity_raw": "Số lượng",
            "package_display": "Số lượng",
            "package_unit": "Đơn vị",
            "weight_kg": "Trọng lượng (kg)",
            "invoices": "Invoice",
            # Customer fields
            "company_name": "Tên công ty",
            "short_name": "Tên ngắn",
            "tax_code": "MST",
            "address": "Địa chỉ",
            "contact_phone": "SĐT",
            "contact_email": "Email",
            "contact_person": "Người liên hệ",
            # Vendor fields
            "vendor_code": "Mã NCC",
            "vendor_name": "Tên NCC",
            "phone": "SĐT",
            "email": "Email",
            # Quotation fields
            "quote_type": "Loại báo giá",
            "origin_province": "Tỉnh đi",
            "destination_province": "Tỉnh đến",
            "sub_route": "Chi tiết tuyến",
            "price": "Đơn giá",
            "currency": "Tiền tệ",
            "unit": "Đơn vị",
            "service_type": "Loại dịch vụ",
            "rate_type": "Loại hàng",
            # Update job fields
            "job_number": "Mã job",
            "action_type": "Loại thay đổi",
            "new_customer_code": "Khách hàng mới",
            "new_service_type": "Dịch vụ mới",
            "change_reason": "Lý do thay đổi",
            "new_status": "Trạng thái mới",
            # Fee fields
            "fee_type": "Loại phí",
            "fee_amount": "Số tiền",
        }
        
        # Import simplifier for service types
        from app.ai.utils.service_type_detector import simplify_service_code

        # Skip these internal fields from display
        skip_fields = {"services", "service_type"}

        lines = []
        for key, value in task.entities.items():
            if value is not None and key not in skip_fields:
                label = field_labels.get(key, key)
                # Simplify service type for display
                if key in ("service_type", "services"):
                    if isinstance(value, list):
                        value = ", ".join(simplify_service_code(v) for v in value)
                    else:
                        value = simplify_service_code(str(value))
                lines.append(f"• {label}: {value}")

        # Add simplified service type once at the end if present
        svc = task.entities.get("service_type")
        if svc:
            simple = simplify_service_code(svc)
            lines.insert(0, f"• Loại dịch vụ: {simple}")

        return "\n".join(lines)
    
    def validate_entities(
        self, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate entities beyond just presence
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Date validation
        if "date" in entities:
            date_val = entities["date"]
            # Check if date is not in the past
            # (actual validation would be more complex)
            pass
        
        # Customer validation
        if "customer_code" in entities:
            customer = entities["customer_code"]
            # Could check if customer exists in DB
            pass
        
        # Job ID validation
        if "job_id" in entities:
            job_id = entities["job_id"]
            # Check format
            if not str(job_id).isdigit() and not str(job_id).startswith("JOB"):
                errors.append(f"Mã job không hợp lệ: {job_id}")
        
        return len(errors) == 0, errors
