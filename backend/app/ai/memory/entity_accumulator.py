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
        "update_job": ["job_id"],
        "check_status": ["job_id"],
        "assign_vehicle": [],  # No strict requirement - we can lookup job_number
        "cancel_job": ["job_id"],
    }
    
    # Fields that we encourage but allow missing
    ENCOURAGED_FIELDS = {
        "create_booking": ["booking_date", "pickup_date", "delivery_address", "dest_address"],
        "assign_vehicle": ["license_plate", "driver_name"],
    }
    
    # Optional but useful fields
    OPTIONAL_FIELDS = {
        "create_booking": ["time", "vehicle_type", "origin", "cargo", "quantity", "notes"],
        "update_job": ["status", "driver", "vehicle", "notes"],
        "assign_vehicle": ["driver_name", "driver_phone"],
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
            "quantity": "Số lượng",
            "notes": "Ghi chú",
            "job_id": "Job",
        }
        
        lines = []
        for key, value in task.entities.items():
            if value is not None:
                label = field_labels.get(key, key)
                lines.append(f"• {label}: {value}")
        
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
