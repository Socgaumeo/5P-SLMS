"""
SLMS AI Pipeline - Stage 4: Entity Extractor
============================================

Extract entities from text based on intent using few-shot learning.

Extracts:
- CREATE_BOOKING: customer, date, time, vehicle_type, cargo, invoices, etc.
- ASSIGN_VEHICLE: license_plate, driver_name, driver_phone, driver_cccd
- UPDATE_STATUS: job_number, new_status
"""

from typing import Dict, Any, Tuple, List, Optional
import logging
import json
import re
from datetime import datetime, timedelta

from .prompts.booking_prompts import BOOKING_EXTRACTION_PROMPT
from .prompts.vehicle_prompts import VEHICLE_EXTRACTION_PROMPT
from .prompts.status_prompts import STATUS_EXTRACTION_PROMPT
from .context_loader import (
    format_customers_for_prompt,
    format_jobs_for_prompt,
    format_vehicle_types_for_prompt
)

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extract entities from text using AI with few-shot examples
    """
    
    def __init__(self, ai_client):
        """
        Initialize with AI client
        
        Args:
            ai_client: AI client (GeminiClient or DeepSeekClient)
        """
        self.ai = ai_client
    
    async def extract(
        self,
        text: str,
        intent: str,
        context: Dict
    ) -> Dict[str, Any]:
        """
        Extract entities based on intent
        
        Args:
            text: Preprocessed input text
            intent: Classified intent
            context: Database context
            
        Returns:
            Dict with entities and confidence
        """
        
        try:
            if intent == "create_booking":
                return await self._extract_booking(text, context)
            
            elif intent == "assign_vehicle":
                return await self._extract_vehicle(text, context)
            
            elif intent == "update_status":
                return await self._extract_status(text, context)
            
            elif intent == "query_info":
                return await self._extract_query(text, context)
            
            else:
                return {
                    "entities": {},
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return {
                "entities": {},
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _extract_booking(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract booking entities"""
        
        # Format context for prompt
        customers_list = format_customers_for_prompt(context.get("customers", []))
        vehicle_types = format_vehicle_types_for_prompt(context.get("vehicle_types", []))
        current_date = context.get("current_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Build prompt
        prompt = BOOKING_EXTRACTION_PROMPT.format(
            customers_list=customers_list,
            vehicle_types=vehicle_types,
            current_date=current_date,
            input=text
        )
        
        # Call AI
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        # Parse and normalize
        entities = self._parse_booking_response(response, context)
        confidence = response.get("confidence", 0.7) if isinstance(response, dict) else 0.7
        
        return {
            "entities": entities,
            "confidence": float(confidence)
        }
    
    async def _extract_vehicle(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract vehicle/driver info"""
        
        # Format context
        pending_jobs = format_jobs_for_prompt(context.get("pending_jobs", []))
        
        # Build prompt
        prompt = VEHICLE_EXTRACTION_PROMPT.format(
            pending_jobs=pending_jobs,
            input=text
        )
        
        # Call AI
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        # Parse and normalize
        entities = self._parse_vehicle_response(response, context)
        confidence = response.get("confidence", 0.7) if isinstance(response, dict) else 0.7
        
        # Try to match with pending job
        if entities and context.get("pending_jobs"):
            matched_job = self._match_pending_job(entities, context["pending_jobs"])
            if matched_job:
                entities["matched_job_no"] = matched_job["job_no"]
                entities["matched_job_id"] = matched_job["job_id"]
        
        return {
            "entities": entities,
            "confidence": float(confidence)
        }
    
    async def _extract_status(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract status update info"""
        
        # Format context
        active_jobs = format_jobs_for_prompt(context.get("active_jobs", []))
        
        # Build prompt
        prompt = STATUS_EXTRACTION_PROMPT.format(
            active_jobs=active_jobs,
            input=text
        )
        
        # Call AI
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        # Parse and normalize
        entities = self._parse_status_response(response, context)
        confidence = response.get("confidence", 0.7) if isinstance(response, dict) else 0.7
        
        return {
            "entities": entities,
            "confidence": float(confidence)
        }
    
    async def _extract_query(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract query parameters"""
        
        entities = {}
        
        # Simple extraction for queries
        # Look for job numbers
        job_match = re.search(r"(TRK|WHS|CUS|PKG|SVC)-?\d{4}-?\d{3}", text, re.IGNORECASE)
        if job_match:
            entities["job_number"] = job_match.group().upper()
        
        # Look for customer codes
        for customer in context.get("customers", []):
            code = customer.get("customer_code", "")
            if code and code.lower() in text.lower():
                entities["customer_code"] = code
                break
        
        return {
            "entities": entities,
            "confidence": 0.7
        }
    
    # ══════════════════════════════════════════════════════════════════════════
    # RESPONSE PARSERS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _parse_booking_response(self, response: Any, context: Dict) -> Dict:
        """Parse and normalize booking extraction response"""
        
        if isinstance(response, str):
            response = self._extract_json(response)
        
        if not isinstance(response, dict):
            return {}
        
        entities = {}
        
        # Customer
        if customer := response.get("customer_code") or response.get("customer"):
            entities["customer_code"] = self._match_customer(customer, context.get("customers", []))
        
        # Date
        if date := response.get("date") or response.get("booking_date"):
            entities["booking_date"] = self._normalize_date(date, context.get("current_date"))
        
        # Time
        if time := response.get("time") or response.get("pickup_time"):
            entities["pickup_time"] = self._normalize_time(time)
        
        # Vehicle type
        if vehicle := response.get("vehicle_type") or response.get("vehicle"):
            entities["vehicle_type"] = self._normalize_vehicle_type(vehicle)
        
        # Cargo
        if cargo := response.get("cargo") or response.get("cargo_type"):
            entities["cargo_type"] = cargo
        
        # Quantity
        if qty := response.get("quantity") or response.get("package_quantity"):
            entities["package_quantity"] = self._extract_number(qty)
        
        if unit := response.get("unit") or response.get("package_unit"):
            entities["package_unit"] = unit
        
        # Invoices
        if invoices := response.get("invoices") or response.get("invoice"):
            if isinstance(invoices, str):
                invoices = [inv.strip() for inv in invoices.split(",")]
            entities["invoices"] = invoices
        
        # Addresses
        if origin := response.get("origin") or response.get("pickup_address"):
            entities["origin_address"] = origin
        
        if dest := response.get("destination") or response.get("delivery_address"):
            entities["dest_address"] = dest
        
        # Urgent flag
        if response.get("urgent"):
            entities["is_urgent"] = True
        
        # Notes
        if notes := response.get("notes") or response.get("special_requirements"):
            entities["notes"] = notes
        
        return entities
    
    def _parse_vehicle_response(self, response: Any, context: Dict) -> Dict:
        """Parse and normalize vehicle extraction response"""
        
        if isinstance(response, str):
            response = self._extract_json(response)
        
        if not isinstance(response, dict):
            return {}
        
        entities = {}
        
        # License plate
        if plate := response.get("license_plate") or response.get("bks"):
            entities["license_plate"] = self._normalize_license_plate(plate)
        
        # Driver name
        if name := response.get("driver_name") or response.get("driver"):
            entities["driver_name"] = name.strip().title()
        
        # Driver phone
        if phone := response.get("driver_phone") or response.get("phone"):
            entities["driver_phone"] = self._normalize_phone(phone)
        
        # Driver CCCD
        if cccd := response.get("driver_cccd") or response.get("cccd"):
            entities["driver_cccd"] = self._normalize_cccd(cccd)
        
        # Related customer (for job matching)
        if customer := response.get("related_customer") or response.get("customer"):
            entities["related_customer"] = customer
        
        # Related job number (if mentioned)
        if job := response.get("job_number") or response.get("job"):
            entities["job_number"] = job.upper()
        
        return entities
    
    def _parse_status_response(self, response: Any, context: Dict) -> Dict:
        """Parse and normalize status extraction response"""
        
        if isinstance(response, str):
            response = self._extract_json(response)
        
        if not isinstance(response, dict):
            return {}
        
        entities = {}
        
        # Job number
        if job := response.get("job_number") or response.get("job"):
            entities["job_number"] = self._normalize_job_number(job, context.get("active_jobs", []))
        
        # New status
        if status := response.get("status") or response.get("new_status"):
            entities["new_status"] = self._normalize_status(status)
        
        # Customer (for job matching if job_number is partial)
        if customer := response.get("customer"):
            entities["customer"] = customer
        
        # Notes
        if notes := response.get("notes") or response.get("completion_notes"):
            entities["notes"] = notes
        
        return entities
    
    # ══════════════════════════════════════════════════════════════════════════
    # NORMALIZERS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from text"""
        import re
        
        # Try markdown code block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # Try raw JSON
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        return {}
    
    def _match_customer(self, input_customer: str, customers: List[Dict]) -> Optional[str]:
        """Match input customer to customer list"""
        
        input_lower = input_customer.lower().strip()
        
        for c in customers:
            code = c.get("customer_code", "").lower()
            name = c.get("short_name", "").lower()
            
            if input_lower == code or input_lower == name:
                return c.get("customer_code")
            
            if input_lower in code or input_lower in name:
                return c.get("customer_code")
        
        return input_customer.upper()
    
    def _normalize_date(self, date_input: str, current_date: str = None) -> Optional[str]:
        """Normalize date to YYYY-MM-DD format"""
        
        if not date_input:
            return None
        
        date_lower = str(date_input).lower().strip()
        
        # Handle relative dates
        today = datetime.strptime(current_date, "%Y-%m-%d") if current_date else datetime.now()
        
        if date_lower in ["hôm nay", "today", "nay", "hn"]:
            return today.strftime("%Y-%m-%d")
        
        if date_lower in ["ngày mai", "mai", "tomorrow", "ng mai"]:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if date_lower in ["ngày kia", "mốt", "ngày mốt"]:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Try to parse date formats
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
            "%d/%m/%y", "%d-%m-%y",
            "%d/%m", "%d-%m", "%d"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_lower, fmt)
                
                # Handle 2-digit year
                if dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000)
                
                # Handle no year
                if dt.year == 1900:
                    dt = dt.replace(year=today.year)
                    # If date is in the past, assume next year
                    if dt < today:
                        dt = dt.replace(year=today.year + 1)
                
                return dt.strftime("%Y-%m-%d")
            except:
                continue
        
        return date_input
    
    def _normalize_time(self, time_input: str) -> Optional[str]:
        """Normalize time to HH:MM format"""
        
        if not time_input:
            return None
        
        time_str = str(time_input).strip().lower()
        
        # Handle "22h", "10h30"
        match = re.match(r"(\d{1,2})[hH]?(\d{2})?", time_str)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) or "00"
            return f"{hour:02d}:{minute}"
        
        # Handle "10:30", "22:00"
        match = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        
        return time_input
    
    def _normalize_vehicle_type(self, vehicle: str) -> str:
        """Normalize vehicle type"""
        
        if not vehicle:
            return ""
        
        vehicle = str(vehicle).upper().strip()
        
        # Remove spaces and standardize
        vehicle = vehicle.replace(" ", "").replace("TẤN", "T").replace("TAN", "T")
        
        # Common mappings
        mappings = {
            "1.25": "1.25T",
            "1T25": "1.25T",
            "125": "1.25T",
            "2.5": "2.5T",
            "2T5": "2.5T",
            "25": "2.5T",
            "5": "5T",
            "10": "10T",
            "15": "15T",
            "20": "20T",
            "CONT20": "CONT20",
            "CONTAINER20": "CONT20",
            "CONT40": "CONT40",
            "CONTAINER40": "CONT40",
        }
        
        return mappings.get(vehicle, vehicle)
    
    def _normalize_license_plate(self, plate: str) -> str:
        """Normalize license plate format"""
        
        if not plate:
            return ""
        
        # Remove common separators and spaces
        plate = str(plate).upper().strip()
        plate = re.sub(r"[.\-_\s]+", " ", plate)
        
        # Standard format: XXY ZZZZZ (e.g., 29H 76514)
        match = re.match(r"(\d{2}[A-Z])[\s\-]*(\d{4,5})", plate)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        return plate
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        
        if not phone:
            return ""
        
        # Remove non-digits
        digits = re.sub(r"\D", "", str(phone))
        
        # Ensure starts with 0
        if len(digits) == 9:
            digits = "0" + digits
        
        return digits
    
    def _normalize_cccd(self, cccd: str) -> str:
        """Normalize CCCD number (12 digits)"""
        
        if not cccd:
            return ""
        
        # Remove non-digits
        digits = re.sub(r"\D", "", str(cccd))
        
        return digits
    
    def _normalize_status(self, status: str) -> str:
        """Normalize status to standard codes"""
        
        if not status:
            return ""
        
        status_lower = str(status).lower().strip()
        
        mappings = {
            # Completed
            "done": "COMPLETED",
            "xong": "COMPLETED",
            "hoàn thành": "COMPLETED",
            "hoan thanh": "COMPLETED",
            "completed": "COMPLETED",
            "đã giao": "DELIVERED",
            "da giao": "DELIVERED",
            "delivered": "DELIVERED",
            
            # Cancelled
            "hủy": "CANCELLED",
            "huy": "CANCELLED",
            "cancel": "CANCELLED",
            "cancelled": "CANCELLED",
            
            # In transit
            "đang giao": "IN_TRANSIT",
            "dang giao": "IN_TRANSIT",
            "in_transit": "IN_TRANSIT",
            "transit": "IN_TRANSIT",
            
            # Dispatched
            "đã điều xe": "DISPATCHED",
            "da dieu xe": "DISPATCHED",
            "dispatched": "DISPATCHED",
        }
        
        return mappings.get(status_lower, status.upper())
    
    def _normalize_job_number(self, job_input: str, active_jobs: List[Dict]) -> Optional[str]:
        """Normalize and match job number"""
        
        if not job_input:
            return None
        
        job_str = str(job_input).upper().strip()
        
        # Full job number
        if re.match(r"(TRK|WHS|CUS|PKG|SVC)-\d{4}-\d{3}", job_str):
            return job_str
        
        # Partial number - try to match
        if job_str.isdigit():
            for job in active_jobs:
                if job.get("job_no", "").endswith(job_str):
                    return job["job_no"]
        
        # Contains partial
        for job in active_jobs:
            if job_str in job.get("job_no", ""):
                return job["job_no"]
        
        return job_str
    
    def _extract_number(self, value: Any) -> Optional[int]:
        """Extract integer from value"""
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            if match:
                return int(match.group())
        
        return None
    
    def _match_pending_job(
        self, 
        entities: Dict, 
        pending_jobs: List[Dict]
    ) -> Optional[Dict]:
        """Try to match extracted info with a pending job"""
        
        # Match by explicit job number
        if job_no := entities.get("job_number"):
            for job in pending_jobs:
                if job.get("job_no") == job_no:
                    return job
        
        # Match by customer
        if customer := entities.get("related_customer"):
            customer_upper = customer.upper()
            for job in pending_jobs:
                if customer_upper in job.get("customer", "").upper():
                    return job
                if customer_upper in job.get("customer_code", "").upper():
                    return job
        
        # If only one pending job, assume it's the target
        if len(pending_jobs) == 1:
            return pending_jobs[0]
        
        return None
