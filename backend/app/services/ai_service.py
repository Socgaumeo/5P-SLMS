"""
AI Service - Intent Detection and Entity Extraction
Supports Gemini and DeepSeek
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re

import google.generativeai as genai
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI Service for processing chat inputs"""
    
    INTENTS = [
        "CREATE_JOB",       # Booking request from customer
        "ASSIGN_VEHICLE",   # Vehicle info from vendor
        "UPDATE_JOB",       # Update job details
        "COMPLETE_JOB",     # Mark job complete
        "CANCEL_JOB",       # Cancel job
        "QUERY_STATUS",     # Query job status
        "GENERAL_QUERY",    # Other queries
    ]
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        
        if self.provider == "gemini":
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        elif self.provider == "deepseek":
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
    
    async def process(
        self,
        content: str,
        content_type: str = "TEXT",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process chat input and extract intent + entities
        
        Args:
            content: Text content (already extracted if from file/image)
            content_type: TEXT, EXCEL, PDF, IMAGE_OCR
            context: Optional context (source_type, source_id, job_id)
            
        Returns:
            {intent, confidence, entities, raw_response}
        """
        
        prompt = self._build_prompt(content, content_type, context)
        
        try:
            if self.provider == "gemini":
                response = await self._call_gemini(prompt)
            else:
                response = await self._call_deepseek(prompt)
            
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.0,
                "entities": {},
                "error": str(e)
            }
    
    def _build_prompt(
        self,
        content: str,
        content_type: str,
        context: Optional[Dict]
    ) -> str:
        """Build the AI prompt for intent detection and entity extraction"""
        
        context_str = ""
        if context:
            if context.get("source_type"):
                context_str += f"Source: {context['source_type']}"
            if context.get("source_id"):
                context_str += f" ({context['source_id']})"
            if context.get("job_id"):
                context_str += f"\nRelated Job: {context['job_id']}"
        
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        return f"""Analyze this Vietnamese logistics message and extract information.

CONTEXT:
{context_str if context_str else "No context provided"}

INPUT TYPE: {content_type}

CURRENT DATE: {today.strftime('%d/%m/%Y')}
TOMORROW: {tomorrow.strftime('%d/%m/%Y')}

MESSAGE:
```
{content}
```

TASK:
1. Detect the intent from these options:
   - CREATE_JOB: New booking request (keywords: book xe, cần xe, lấy hàng, giao hàng, lưu kho, khai quan)
   - ASSIGN_VEHICLE: Vehicle/driver info from vendor (keywords: BKS, biển số, lái xe, CCCD)
   - UPDATE_JOB: Update existing job details
   - COMPLETE_JOB: Mark job as completed (keywords: đã giao, hoàn thành)
   - CANCEL_JOB: Cancel job (keywords: hủy, cancel)
   - QUERY_STATUS: Query status (keywords: tình trạng, status)
   - GENERAL_QUERY: Other queries

2. Detect service_type (can be multiple - return as array):
   Service types available:
   - WHS_STORAGE: Lưu kho (keywords: lưu kho, nhập kho, storage)
   - WHS_HANDLE: Bốc xếp, nâng hạ (keywords: nâng hạ, bốc xếp, loading)
   - TRUCKING_SHORT: Vận tải nội vùng < 50km
   - TRUCKING_LONG: Vận tải liên tỉnh > 50km
   - CUS_IMPORT: Khai quan nhập (keywords: nhập khẩu, import)
   - CUS_EXPORT: Khai quan xuất (keywords: xuất khẩu, export)
   
   IMPORTANT: "lưu kho và nâng hạ" = ["WHS_STORAGE", "WHS_HANDLE"] (2 services)
   "lưu kho, nâng hạ" = ["WHS_STORAGE", "WHS_HANDLE"] (2 services)

3. Extract relevant entities based on intent:

For CREATE_JOB, extract these SEPARATELY:
- service_type: Primary service type (first one if multiple)
- services: Array of all service types detected
- customer_code: Customer code (e.g., DRT1, SEVT, HSDN, KWE, KINTETSU)
- vendor_code: Vendor code if mentioned (e.g., ASGL, TAMBAO)
- booking_date: Date (format YYYY-MM-DD). "ngày mai" = {tomorrow.strftime('%Y-%m-%d')}
- pickup_time: Time (format HH:mm)
- vehicle_type: Vehicle type (1.25T, 2.5T, 3.5T, 5T, 8T, 10T, 14T)

CARGO DETAILS (Single item):
- cargo_type: Type of cargo (PCB, FPC, ELECTRONICS, GARMENT, CNC Main...)
- package_quantity: NUMBER only (e.g., from "45 kiện" extract 45)
- package_unit: UNIT only (e.g., "kiện", "thùng", "pallet", "container")
- weight_kg: Weight in kg as NUMBER (convert: "0.5 tấn" = 500, "100kg" = 100)
- dimension_length_cm: Length in cm as NUMBER (from "100x100x80" extract 100)
- dimension_width_cm: Width in cm as NUMBER (from "100x100x80" extract 100)
- dimension_height_cm: Height in cm as NUMBER (from "100x100x80" extract 80)

MULTI-ITEM CARGO (từ Excel/nhiều dòng):
- cargo_items: ARRAY các item riêng biệt, mỗi item có:
  {{
    "item_no": 1,
    "description": "Mô tả hàng/Invoice",
    "invoice_no": "INV-001",
    "package_quantity": 5,
    "package_unit": "kiện",
    "weight_kg": 250,
    "length_cm": 100,
    "width_cm": 80,
    "height_cm": 60,
    "cbm": 0.48
  }}

TOTALS (tổng của cả lô - tính từ tất cả items):
- total_packages: Tổng số kiện
- total_weight_kg: Tổng cân nặng (kg)
- total_cbm: Tổng thể tích (m3)

DOCUMENTS & ADDRESSES:
- invoice_numbers: List of invoice numbers as array
- pickup_address: Pickup location
- delivery_address: Delivery location
- special_requirements: Special handling (nâng hạ, giữ lạnh, fragile...)

WAREHOUSE-SPECIFIC:
- storage_start_date: Start date for storage (format YYYY-MM-DD)
- storage_end_date: End date for storage if mentioned

CUSTOMS-SPECIFIC (CUS_IMPORT, CUS_EXPORT):
- declaration_datetime: Ngày giờ mở tờ khai (format YYYY-MM-DD HH:mm)
- loai_hinh: Mã loại hình (A11=nhập kinh doanh, A12=nhập gia công, B11=xuất kinh doanh, B13=xuất gia công)
- customs_port: Cửa khẩu/Cảng (Hải Phòng, Nội Bài, Cát Lái...)
- buyer_name: Tên người mua trên tờ khai
- seller_name: Tên người bán trên tờ khai
- hs_code: Mã HS Code
- bl_awb_no: Số B/L hoặc AWB

PACKING-SPECIFIC (SVC_PACK):
- packing_type: CARTON, PALLET, WOODEN_CRATE, WOODEN_BOX
- items_count: Tổng số lượng sản phẩm trước đóng gói
- packages_output: Tổng số kiện sau đóng gói
- total_weight_kg: Tổng cân nặng tất cả các kiện

FOR MULTI-ITEM PACKING (nhiều kiện với kích thước riêng):
- packing_items: ARRAY of items, mỗi item có:
  {{
    "item_no": 1,
    "description": "Mô tả kiện",
    "before_length_cm": 100,
    "before_width_cm": 80,
    "before_height_cm": 60,
    "after_length_cm": 120,
    "after_width_cm": 100,
    "after_height_cm": 80,
    "weight_kg": 250,
    "shrink_wrap": false,
    "vacuum_pack": true,
    "lashing": false,
    "fumigation": false
  }}

Nếu chỉ có 1 kiện hoặc tất cả cùng kích thước, dùng fields đơn:
- before_length_cm, before_width_cm, before_height_cm
- after_length_cm, after_width_cm, after_height_cm
- shrink_wrap, vacuum_pack, lashing, fumigation: true/false

For ASSIGN_VEHICLE:
- license_plate: Vehicle license plate (e.g., 29H 76514)
- driver_name: Driver name
- driver_phone: Driver phone number
- driver_id_card: Driver CCCD/ID card number
- linked_job_hint: Any hint about which job (date, customer, invoice)

For UPDATE_JOB (cập nhật thông tin job):
JOB MATCHING - Extract one of these to find the job:
- job_number: Job number (e.g., TRK-1701-0001, WHS-1701-0001)
- invoice_ref: Invoice number to match
- bl_awb_ref: B/L or AWB number to match
- customer_ref: Customer + date combination

STATUS UPDATE:
- new_status: New status (CONFIRMED, DISPATCHED, IN_TRANSIT, DELIVERED, COMPLETED, CANCELLED)

INFO UPDATE - Extract any fields that need updating:
- update_pickup_time: New pickup time
- update_delivery_address: New delivery address
- update_vehicle_info: license_plate, driver_name, driver_phone
- update_notes: Additional notes
- update_special_requirements: New special requirements

For COMPLETE_JOB:
- job_number: Job number (e.g., TRK-2601-0089)
- delivery_time: Actual delivery time
- notes: Any completion notes

RESPOND IN JSON FORMAT ONLY:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "service_type": "SERVICE_TYPE",
    "entities": {{
        "customer_code": "value",
        "cargo_type": "PCB",
        "package_quantity": 45,
        "package_unit": "kiện",
        "dimension_length_cm": 100,
        "dimension_width_cm": 100,
        "dimension_height_cm": 80,
        "weight_kg": 500,
        ...
    }},
    "summary": "Brief summary in Vietnamese"
}}
"""

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        response = self.model.generate_content(prompt)
        return response.text
    
    async def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API"""
        response = self.client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a logistics assistant that extracts structured data from Vietnamese messages. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to structured format"""
        
        # Clean up response
        text = response.strip()
        
        # Extract JSON from markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        # Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        try:
            result = json.loads(text)
            
            # Validate intent
            if result.get("intent") not in self.INTENTS:
                result["intent"] = "GENERAL_QUERY"
            
            # Ensure confidence is a float
            result["confidence"] = float(result.get("confidence", 0.5))
            
            # Ensure entities is a dict
            if not isinstance(result.get("entities"), dict):
                result["entities"] = {}
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.0,
                "entities": {},
                "raw_response": text[:500],
                "parse_error": str(e)
            }


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
