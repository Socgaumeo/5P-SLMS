"""
Message Service - Generate formatted messages for Zalo
"""

from typing import Dict, Any, Optional
from datetime import datetime


class MessageService:
    """Service for generating formatted messages"""
    
    def generate_vendor_dispatch(self, job: Dict) -> str:
        """
        Generate vendor dispatch request message
        Template: VENDOR_DISPATCH_REQUEST
        """
        
        booking_date = job.get("booking_date")
        if isinstance(booking_date, datetime):
            booking_date = booking_date.strftime("%d/%m/%Y")
        elif hasattr(booking_date, 'strftime'):
            booking_date = booking_date.strftime("%d/%m/%Y")
        else:
            booking_date = str(booking_date)
        
        pickup_time = job.get("pickup_time")
        if hasattr(pickup_time, 'strftime'):
            pickup_time = pickup_time.strftime("%H:%M")
        else:
            pickup_time = str(pickup_time) if pickup_time else "TBD"
        
        message = f"""🚛 YÊU CẦU XE - {job.get('customer_code', 'N/A')}

📅 Ngày: {booking_date}
⏰ Giờ: {pickup_time}
📦 Invoice: {job.get('invoice_numbers', 'N/A')}
📋 Hàng: {job.get('cargo_type', 'N/A')} - {job.get('package_info', '')}
🚗 Loại xe: {job.get('vehicle_type', 'N/A')}
📍 Lấy: {job.get('origin', job.get('pickup_address', 'N/A'))}
📍 Giao: {job.get('destination', job.get('delivery_address', 'N/A'))}

Vui lòng điều xe và phản hồi thông tin lái xe."""
        
        return message.strip()
    
    def generate_customer_confirm(self, job: Dict) -> str:
        """
        Generate customer confirmation message
        Template: CUSTOMER_VEHICLE_CONFIRM
        """
        
        booking_date = job.get("booking_date")
        if isinstance(booking_date, datetime):
            booking_date = booking_date.strftime("%d.%m")
        elif hasattr(booking_date, 'strftime'):
            booking_date = booking_date.strftime("%d.%m")
        else:
            booking_date = str(booking_date)[:5] if booking_date else "N/A"
        
        pickup_time = job.get("pickup_time")
        if hasattr(pickup_time, 'strftime'):
            pickup_time = pickup_time.strftime("%H:%M")
        else:
            pickup_time = str(pickup_time) if pickup_time else ""
        
        # Short format: MK-DRT1 / 17.01 / 22:00 / Invoice: xxx / Hàng / xe / BKS / Lái xe - SĐT - CCCD
        parts = [
            f"MK-{job.get('customer_code', 'N/A')}",
            booking_date,
            pickup_time,
            f"Invoice: {job.get('invoice_numbers', 'N/A')}",
            job.get('cargo_type', ''),
            job.get('package_info', ''),
            job.get('vehicle_type', ''),
            f"BKS: {job.get('license_plate', 'N/A')}",
            f"{job.get('driver_name', 'N/A')} - {job.get('driver_phone', 'N/A')} - CCCD: {job.get('driver_id_card', 'N/A')}"
        ]
        
        # Filter empty parts
        parts = [p for p in parts if p and p != 'N/A' and p != 'None']
        
        return " / ".join(parts)
    
    def generate_delivery_confirm(self, job: Dict) -> str:
        """
        Generate delivery confirmation message
        Template: CUSTOMER_DELIVERY_CONFIRM
        """
        
        return f"""✅ Đã giao hàng thành công

Job: {job.get('job_number', 'N/A')}
Invoice: {job.get('invoice_numbers', 'N/A')}

Cảm ơn quý khách!"""


# Singleton
_message_service: Optional[MessageService] = None


def get_message_service() -> MessageService:
    global _message_service
    if _message_service is None:
        _message_service = MessageService()
    return _message_service
