"""
SLMS AI Pipeline - Stage 4: Entity Extractor (FIXED VERSION)
=============================================================

Extract entities from text based on intent using few-shot learning.

FIXES:
- Added missing _extract_json method
- Better JSON parsing with multiple fallbacks
- Robust error handling
- Detailed logging for debugging
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json
import re
from datetime import datetime, timedelta

from app.ai.utils.smart_parser import parse_date as smart_parse_date
from app.ai.utils.service_type_detector import normalize_service_code
from .prompts.booking_prompts import BOOKING_EXTRACTION_PROMPT
from .prompts.vehicle_prompts import VEHICLE_EXTRACTION_PROMPT
from .prompts.status_prompts import STATUS_EXTRACTION_PROMPT
from .prompts.master_data_prompts import (
    CUSTOMER_EXTRACTION_PROMPT,
    VENDOR_EXTRACTION_PROMPT,
    QUOTATION_EXTRACTION_PROMPT
)
from .prompts.update_job_prompts import UPDATE_JOB_EXTRACTION_PROMPT
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
        
        logger.info(f"[EntityExtractor] Starting extraction for intent: {intent}")
        logger.debug(f"[EntityExtractor] Input text: {text[:200]}...")
        
        try:
            if intent == "create_booking":
                return await self._extract_booking(text, context)
            
            elif intent == "assign_vehicle":
                return await self._extract_vehicle(text, context)
            
            elif intent == "update_status":
                return await self._extract_status(text, context)
            
            elif intent == "query_info":
                return await self._extract_query(text, context)

            elif intent == "create_customer":
                return await self._extract_customer(text, context)

            elif intent == "create_vendor":
                return await self._extract_vendor(text, context)

            elif intent == "create_quotation":
                return await self._extract_quotation(text, context)

            elif intent == "update_job":
                return await self._extract_update_job(text, context)

            else:
                logger.warning(f"[EntityExtractor] Unknown intent: {intent}")
                return {
                    "entities": {},
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"[EntityExtractor] Extraction failed: {str(e)}", exc_info=True)
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
        
        logger.debug(f"[EntityExtractor] Customers in context: {len(context.get('customers', []))}")
        logger.debug(f"[EntityExtractor] Vehicle types: {vehicle_types}")
        
        # Build prompt
        prompt = BOOKING_EXTRACTION_PROMPT.format(
            customers_list=customers_list,
            vehicle_types=vehicle_types,
            current_date=current_date,
            input=text
        )
        
        # Call AI
        logger.info("[EntityExtractor] Calling AI for booking extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        logger.debug(f"[EntityExtractor] Raw AI response type: {type(response)}")
        logger.debug(f"[EntityExtractor] Raw AI response: {str(response)[:500]}")
        
        # Parse response - HANDLE BOTH dict AND str
        parsed_response = self._ensure_dict(response)
        
        if not parsed_response:
            logger.error("[EntityExtractor] Failed to parse AI response to dict")
            return {"entities": {}, "confidence": 0.3}
        
        # Normalize entities
        entities = self._parse_booking_response(parsed_response, context)
        
        # POST-PROCESSING: Extract service type from marker [SERVICE_TYPE:XXX]
        entities = self._extract_service_type_from_text(entities, text)

        # POST-PROCESSING: Fix quantity from raw text if it has mixed units
        entities = self._fix_mixed_quantity_from_text(entities, text)

        # POST-PROCESSING: Extract addresses from metadata in raw text
        entities = self._fix_addresses_from_text(entities, text)
        
        # Extract confidence from response
        confidence = self._extract_confidence(parsed_response)
        
        logger.info(f"[EntityExtractor] Booking extracted: {list(entities.keys())}, confidence: {confidence}")
        
        return {
            "entities": entities,
            "confidence": confidence
        }
    
    async def _extract_vehicle(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract vehicle/driver info"""
        
        # Format context
        pending_jobs = format_jobs_for_prompt(context.get("pending_jobs", []))
        
        logger.debug(f"[EntityExtractor] Pending jobs in context: {len(context.get('pending_jobs', []))}")
        
        # Build prompt
        prompt = VEHICLE_EXTRACTION_PROMPT.format(
            pending_jobs=pending_jobs,
            input=text
        )
        
        # Call AI
        logger.info("[EntityExtractor] Calling AI for vehicle extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        logger.debug(f"[EntityExtractor] Raw AI response: {str(response)[:500]}")
        
        # Parse response
        parsed_response = self._ensure_dict(response)
        
        if not parsed_response:
            logger.error("[EntityExtractor] Failed to parse vehicle response")
            return {"entities": {}, "confidence": 0.3}
        
        # Normalize entities
        entities = self._parse_vehicle_response(parsed_response, context)
        confidence = self._extract_confidence(parsed_response)
        
        # Try to match with pending job
        if entities and context.get("pending_jobs"):
            matched_job = self._match_pending_job(entities, context["pending_jobs"])
            if matched_job:
                entities["matched_job_no"] = matched_job.get("job_no")
                entities["matched_job_id"] = matched_job.get("job_id")
                logger.info(f"[EntityExtractor] Matched with job: {matched_job.get('job_no')}")
        
        logger.info(f"[EntityExtractor] Vehicle extracted: {list(entities.keys())}, confidence: {confidence}")
        
        return {
            "entities": entities,
            "confidence": confidence
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
        logger.info("[EntityExtractor] Calling AI for status extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )
        
        logger.debug(f"[EntityExtractor] Raw AI response: {str(response)[:500]}")
        
        # Parse response
        parsed_response = self._ensure_dict(response)
        
        if not parsed_response:
            logger.error("[EntityExtractor] Failed to parse status response")
            return {"entities": {}, "confidence": 0.3}
        
        # Normalize entities
        entities = self._parse_status_response(parsed_response, context)
        confidence = self._extract_confidence(parsed_response)
        
        logger.info(f"[EntityExtractor] Status extracted: {list(entities.keys())}, confidence: {confidence}")
        
        return {
            "entities": entities,
            "confidence": confidence
        }
    
    async def _extract_query(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract query parameters using regex (no AI needed)"""
        
        entities = {}
        
        # Look for job numbers
        job_match = re.search(r"(TRK|WHS|CUS|PKG|SVC)-?\d{4}-?\d{3}", text, re.IGNORECASE)
        if job_match:
            entities["job_number"] = job_match.group().upper()
        
        # Look for partial job numbers (just digits)
        if not entities.get("job_number"):
            partial_match = re.search(r"\b(\d{3})\b", text)
            if partial_match:
                entities["partial_job_number"] = partial_match.group(1)
        
        # Look for customer codes
        for customer in context.get("customers", []):
            code = customer.get("customer_code", "")
            if code and code.lower() in text.lower():
                entities["customer_code"] = code
                break
        
        logger.info(f"[EntityExtractor] Query extracted: {entities}")

        return {
            "entities": entities,
            "confidence": 0.7 if entities else 0.4
        }

    async def _extract_customer(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract customer info from text"""
        prompt = CUSTOMER_EXTRACTION_PROMPT.format(input=text)

        logger.info("[EntityExtractor] Calling AI for customer extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )

        parsed_response = self._ensure_dict(response)
        if not parsed_response:
            return {"entities": {}, "confidence": 0.3}

        entities = self._parse_customer_response(parsed_response)
        confidence = self._extract_confidence(parsed_response)

        logger.info(f"[EntityExtractor] Customer extracted: {list(entities.keys())}, confidence: {confidence}")
        return {"entities": entities, "confidence": confidence}

    async def _extract_vendor(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract vendor info from text"""
        prompt = VENDOR_EXTRACTION_PROMPT.format(input=text)

        logger.info("[EntityExtractor] Calling AI for vendor extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )

        parsed_response = self._ensure_dict(response)
        if not parsed_response:
            return {"entities": {}, "confidence": 0.3}

        entities = self._parse_vendor_response(parsed_response)
        confidence = self._extract_confidence(parsed_response)

        logger.info(f"[EntityExtractor] Vendor extracted: {list(entities.keys())}, confidence: {confidence}")
        return {"entities": entities, "confidence": confidence}

    async def _extract_quotation(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract quotation info from text"""
        prompt = QUOTATION_EXTRACTION_PROMPT.format(input=text)

        logger.info("[EntityExtractor] Calling AI for quotation extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )

        parsed_response = self._ensure_dict(response)
        if not parsed_response:
            return {"entities": {}, "confidence": 0.3}

        entities = self._parse_quotation_response(parsed_response, context)
        confidence = self._extract_confidence(parsed_response)

        logger.info(f"[EntityExtractor] Quotation extracted: {list(entities.keys())}, confidence: {confidence}")
        return {"entities": entities, "confidence": confidence}

    async def _extract_update_job(self, text: str, context: Dict) -> Dict[str, Any]:
        """Extract update job entities from text"""
        # Format context for prompt
        customers_list = format_customers_for_prompt(context.get("customers", []))
        active_jobs = format_jobs_for_prompt(context.get("jobs", []))
        current_date = context.get("current_date", datetime.now().strftime("%Y-%m-%d"))

        prompt = UPDATE_JOB_EXTRACTION_PROMPT.format(
            customers_list=customers_list,
            active_jobs=active_jobs,
            current_date=current_date,
            input=text
        )

        logger.info("[EntityExtractor] Calling AI for update_job extraction...")
        response = await self.ai.generate(
            prompt=prompt,
            response_format="json",
            temperature=0.2
        )

        parsed_response = self._ensure_dict(response)
        if not parsed_response:
            return {"entities": {}, "confidence": 0.3}

        entities = self._parse_update_job_response(parsed_response, context)
        confidence = self._extract_confidence(parsed_response)

        logger.info(f"[EntityExtractor] Update job extracted: {list(entities.keys())}, confidence: {confidence}")
        return {"entities": entities, "confidence": confidence}

    def _parse_update_job_response(self, response: Dict, context: Dict) -> Dict:
        """Parse update job extraction response"""
        if not response:
            return {}

        entities = {}

        # Job identification
        if response.get("job_number"):
            entities["job_number"] = response["job_number"]
        elif response.get("job_number_partial"):
            # Try to match partial job number with active jobs
            partial = response["job_number_partial"]
            jobs = context.get("jobs", [])
            for job in jobs:
                job_no = job.get("job_no", "")
                if job_no.endswith(partial) or partial in job_no:
                    entities["job_number"] = job_no
                    entities["job_id"] = job.get("job_id")
                    break
            if not entities.get("job_number"):
                entities["job_number_partial"] = partial

        # Customer filter (for finding job by customer)
        if response.get("customer_filter"):
            entities["customer_filter"] = response["customer_filter"]

        # Action type
        if response.get("action_type"):
            entities["action_type"] = response["action_type"]

        # New customer (for change_customer action)
        if response.get("new_customer_code"):
            raw_customer = response["new_customer_code"]
            entities["new_customer_raw"] = raw_customer

            # Try to match with known customers
            customers = context.get("customers", [])
            match_result = self._match_customer_with_confidence(raw_customer, customers)
            if match_result.get("matched_code"):
                entities["new_customer_code"] = match_result["matched_code"]
                entities["new_customer_confidence"] = match_result["confidence"]
                if match_result.get("needs_confirmation"):
                    entities["new_customer_needs_confirmation"] = True
                    entities["new_customer_candidates"] = match_result["candidates"]

        # New service (for add_service action)
        if response.get("new_service_type"):
            entities["new_service_type"] = normalize_service_code(response["new_service_type"])

        # Addresses
        if response.get("origin_address"):
            entities["origin_address"] = response["origin_address"]
        if response.get("dest_address"):
            entities["dest_address"] = response["dest_address"]

        # Cargo info
        if response.get("cargo_type"):
            entities["cargo_type"] = response["cargo_type"]
        if response.get("package_quantity"):
            entities["package_quantity"] = response["package_quantity"]
        if response.get("package_unit"):
            entities["package_unit"] = response["package_unit"]

        # Service date
        if response.get("service_date"):
            parsed_date = smart_parse_date(response["service_date"])
            if parsed_date:
                entities["service_date"] = parsed_date.isoformat()

        # Change reason
        if response.get("change_reason"):
            entities["change_reason"] = response["change_reason"]

        # Notes (for add_note action)
        if response.get("notes"):
            entities["notes"] = response["notes"]

        # Fee fields (for add_fee action)
        if response.get("fee_type"):
            entities["fee_type"] = response["fee_type"]
        if response.get("fee_amount"):
            entities["fee_amount"] = self._normalize_price(response["fee_amount"])

        # Cost fields (for add_cost action)
        if response.get("cost_name"):
            entities["cost_name"] = response["cost_name"]
        if response.get("cost_qty"):
            entities["cost_qty"] = float(response["cost_qty"])
        if response.get("cost_unit_price"):
            entities["cost_unit_price"] = self._normalize_price(response["cost_unit_price"])
        # Backward compatibility: if cost_amount provided without qty/unit_price
        if response.get("cost_amount") and not response.get("cost_unit_price"):
            entities["cost_unit_price"] = self._normalize_price(response["cost_amount"])
            if not entities.get("cost_qty"):
                entities["cost_qty"] = 1
        if response.get("cost_unit"):
            entities["cost_unit"] = response["cost_unit"]
        if response.get("cost_source"):
            entities["cost_source"] = response["cost_source"]
        if response.get("vendor_name"):
            entities["vendor_name"] = response["vendor_name"]

        # Revenue fields (for add_revenue action)
        if response.get("revenue_name"):
            entities["revenue_name"] = response["revenue_name"]
        if response.get("revenue_qty"):
            entities["revenue_qty"] = float(response["revenue_qty"])
        if response.get("revenue_unit_price"):
            entities["revenue_unit_price"] = self._normalize_price(response["revenue_unit_price"])
        # Backward compatibility: if revenue_amount provided without qty/unit_price
        if response.get("revenue_amount") and not response.get("revenue_unit_price"):
            entities["revenue_unit_price"] = self._normalize_price(response["revenue_amount"])
            if not entities.get("revenue_qty"):
                entities["revenue_qty"] = 1
        if response.get("revenue_unit"):
            entities["revenue_unit"] = response["revenue_unit"]

        # Multi-cost/revenue arrays (for multi_cost, multi_cost_revenue actions)
        if response.get("costs") and isinstance(response["costs"], list):
            parsed_costs = []
            for cost in response["costs"]:
                parsed_cost = {
                    "cost_name": cost.get("cost_name", "Chi phí"),
                    "cost_qty": float(cost.get("cost_qty", 1)),
                    "cost_unit_price": self._normalize_price(cost.get("cost_unit_price", 0)),
                    "cost_unit": cost.get("cost_unit", "ca"),
                    "vendor_name": cost.get("vendor_name", "")
                }
                parsed_costs.append(parsed_cost)
            entities["costs"] = parsed_costs

        if response.get("revenues") and isinstance(response["revenues"], list):
            parsed_revenues = []
            for rev in response["revenues"]:
                parsed_rev = {
                    "revenue_name": rev.get("revenue_name", "Doanh thu"),
                    "revenue_qty": float(rev.get("revenue_qty", 1)),
                    "revenue_unit_price": self._normalize_price(rev.get("revenue_unit_price", 0)),
                    "revenue_unit": rev.get("revenue_unit", "chuyến")
                }
                parsed_revenues.append(parsed_rev)
            entities["revenues"] = parsed_revenues

        # Route and vehicle for định mức lookup
        if response.get("route"):
            entities["route"] = response["route"]
        if response.get("vehicle_type") and not entities.get("vehicle_type"):
            entities["vehicle_type"] = self._normalize_vehicle_type(response["vehicle_type"])

        return entities

    def _parse_customer_response(self, response: Dict) -> Dict:
        """Parse customer extraction response"""
        if not response:
            return {}

        entities = {}
        field_mappings = {
            'customer_code': ['customer_code', 'code', 'ma_kh'],
            'company_name': ['company_name', 'ten_cong_ty', 'name'],
            'short_name': ['short_name', 'ten_ngan'],
            'tax_code': ['tax_code', 'mst', 'ma_so_thue'],
            'address': ['address', 'dia_chi'],
            'contact_phone': ['contact_phone', 'phone', 'sdt'],
            'contact_email': ['contact_email', 'email'],
            'contact_person': ['contact_person', 'nguoi_lien_he'],
        }

        for target_key, source_keys in field_mappings.items():
            for src in source_keys:
                if response.get(src):
                    entities[target_key] = str(response[src]).strip()
                    break

        # Auto-generate customer_code if missing
        if not entities.get('customer_code') and entities.get('company_name'):
            entities['customer_code'] = self._generate_code(entities['company_name'])

        return entities

    def _parse_vendor_response(self, response: Dict) -> Dict:
        """Parse vendor extraction response"""
        if not response:
            return {}

        entities = {}
        field_mappings = {
            'vendor_code': ['vendor_code', 'code', 'ma_ncc'],
            'vendor_name': ['vendor_name', 'ten_cong_ty', 'name', 'company_name'],
            'short_name': ['short_name', 'ten_ngan'],
            'tax_code': ['tax_code', 'mst', 'ma_so_thue'],
            'address': ['address', 'dia_chi'],
            'phone': ['phone', 'sdt', 'contact_phone'],
            'email': ['email', 'contact_email'],
        }

        for target_key, source_keys in field_mappings.items():
            for src in source_keys:
                if response.get(src):
                    entities[target_key] = str(response[src]).strip()
                    break

        # Auto-generate vendor_code if missing
        if not entities.get('vendor_code') and entities.get('vendor_name'):
            entities['vendor_code'] = self._generate_code(entities['vendor_name'])

        return entities

    def _parse_quotation_response(self, response: Dict, context: Dict) -> Dict:
        """Parse quotation extraction response"""
        if not response:
            return {}

        entities = {}

        # Quote type (buying/selling)
        quote_type = response.get('quote_type', 'buying').lower()
        entities['quote_type'] = quote_type

        # Vendor/Customer name
        if quote_type == 'buying':
            vendor = response.get('vendor_name') or response.get('vendor')
            if vendor:
                entities['vendor_name'] = str(vendor)
        else:
            customer = response.get('customer_name') or response.get('customer')
            if customer:
                entities['customer_name'] = str(customer)

        # Route info
        if response.get('origin_province'):
            entities['origin_province'] = self._normalize_province(response['origin_province'])
        if response.get('destination_province'):
            entities['destination_province'] = self._normalize_province(response['destination_province'])
        if response.get('sub_route'):
            entities['sub_route'] = str(response['sub_route'])

        # Vehicle and pricing
        if response.get('vehicle_type'):
            entities['vehicle_type'] = self._normalize_vehicle_type(str(response['vehicle_type']))
        if response.get('price'):
            entities['price'] = self._normalize_price(response['price'])
        if response.get('currency'):
            entities['currency'] = str(response['currency']).upper()
        else:
            entities['currency'] = 'VND'
        if response.get('unit'):
            entities['unit'] = str(response['unit']).upper()
        else:
            entities['unit'] = 'TRIP'

        # Service and rate type
        if response.get('service_type'):
            entities['service_type'] = str(response['service_type']).upper()
        else:
            entities['service_type'] = 'TRUCKING'
        if response.get('rate_type'):
            entities['rate_type'] = str(response['rate_type']).upper()
        else:
            entities['rate_type'] = 'STANDARD'

        # Notes
        if response.get('notes'):
            entities['notes'] = str(response['notes'])

        return entities

    def _generate_code(self, name: str) -> str:
        """Generate a short code from company name"""
        import re
        # Remove common prefixes
        name = re.sub(r'(công ty|cty|tnhh|cổ phần|cp|logistics|vận tải)', '', name.lower())
        # Get first letters of words
        words = name.strip().split()
        if len(words) >= 2:
            code = ''.join(w[0].upper() for w in words[:3] if w)
        else:
            code = name[:6].upper().replace(' ', '')
        return code.upper()

    def _normalize_province(self, province: str) -> str:
        """Normalize province name"""
        mappings = {
            'hn': 'Hà Nội', 'hanoi': 'Hà Nội', 'ha noi': 'Hà Nội',
            'bn': 'Bắc Ninh', 'bacninh': 'Bắc Ninh', 'bac ninh': 'Bắc Ninh',
            'hcm': 'Hồ Chí Minh', 'saigon': 'Hồ Chí Minh', 'sg': 'Hồ Chí Minh',
            'hp': 'Hải Phòng', 'haiphong': 'Hải Phòng',
            'dn': 'Đà Nẵng', 'danang': 'Đà Nẵng', 'da nang': 'Đà Nẵng',
            'bd': 'Bình Dương', 'binhduong': 'Bình Dương', 'binh duong': 'Bình Dương',
            'dna': 'Đồng Nai', 'dongnai': 'Đồng Nai', 'dong nai': 'Đồng Nai',
            'brvt': 'Bà Rịa Vũng Tàu', 'vungtau': 'Bà Rịa Vũng Tàu',
            'tn': 'Thái Nguyên', 'thainguyen': 'Thái Nguyên',
            'vp': 'Vĩnh Phúc', 'vinhphuc': 'Vĩnh Phúc',
            'hd': 'Hải Dương', 'haiduong': 'Hải Dương',
            'hy': 'Hưng Yên', 'hungyen': 'Hưng Yên',
        }
        return mappings.get(province.lower().strip(), province)

    def _normalize_price(self, price) -> float:
        """Normalize price value"""
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            # Remove formatting
            price = price.lower().replace(',', '').replace('.', '').strip()
            # Handle k/K suffix (800k = 800000)
            if 'k' in price:
                price = price.replace('k', '')
                return float(price) * 1000
            # Handle triệu/tr suffix
            if 'tr' in price or 'triệu' in price:
                price = re.sub(r'(tr|triệu)', '', price)
                return float(price) * 1000000
            return float(price)
        return 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # JSON PARSING - CRITICAL FIX
    # ══════════════════════════════════════════════════════════════════════════
    
    def _ensure_dict(self, response: Any) -> Dict:
        """
        Ensure response is a dict, parsing JSON if needed
        
        Handles various response types including lists
        """
        if isinstance(response, dict):
            return response
        
        if isinstance(response, str):
            return self._extract_json(response)
        
        # Handle list response - AI sometimes returns [{"entities": {...}}]
        if isinstance(response, list):
            if len(response) > 0:
                first_item = response[0]
                if isinstance(first_item, dict):
                    logger.info(f"[EntityExtractor] Extracted dict from list response")
                    return first_item
            logger.warning(f"[EntityExtractor] Empty or non-dict list response")
            return {}
        
        logger.warning(f"[EntityExtractor] Unexpected response type: {type(response)}")
        return {}
    
    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text with multiple fallback strategies
        
        Handles:
        - Pure JSON
        - JSON in ```json``` code blocks
        - JSON in ``` code blocks
        - JSON with trailing commas
        - JSON with comments
        """
        if not text or not text.strip():
            return {}
        
        text = text.strip()
        
        # Strategy 1: Direct parse (if response is clean JSON)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from ```json...``` markdown
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Extract from ```...``` markdown
        match = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Find JSON object in text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            json_str = match.group()
            
            # Clean up common issues
            json_str = self._clean_json_string(json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"[EntityExtractor] JSON parse error: {e}")
                logger.debug(f"[EntityExtractor] Attempted JSON: {json_str[:300]}")
        
        # Strategy 5: Try to extract key-value pairs manually
        result = self._extract_key_values_fallback(text)
        if result:
            return result
        
        logger.error(f"[EntityExtractor] All JSON extraction strategies failed for: {text[:200]}")
        return {}
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON issues"""
        
        # Remove trailing commas before } or ]
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Remove single-line comments
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        
        # Remove multi-line comments
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Fix unquoted keys (common AI mistake)
        # Match: key: "value" → "key": "value"
        json_str = re.sub(r'(\s)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        return json_str
    
    def _extract_key_values_fallback(self, text: str) -> Dict:
        """
        Fallback: Extract key-value pairs using regex patterns
        Used when JSON parsing completely fails
        """
        result = {}
        
        # Patterns for common fields
        patterns = {
            "customer_code": r'"?customer_code"?\s*[:=]\s*"?([A-Z0-9]+)"?',
            "date": r'"?(?:date|booking_date)"?\s*[:=]\s*"?([^",}\n]+)"?',
            "time": r'"?(?:time|pickup_time)"?\s*[:=]\s*"?(\d{1,2}[:\.]?\d{0,2}[hH]?)"?',
            "vehicle_type": r'"?vehicle_type"?\s*[:=]\s*"?([0-9.]+T|CONT\d+)"?',
            "license_plate": r'"?license_plate"?\s*[:=]\s*"?(\d{2}[A-Z]\s*\d{4,5})"?',
            "driver_name": r'"?driver_name"?\s*[:=]\s*"?([^",}\n]+)"?',
            "driver_phone": r'"?driver_phone"?\s*[:=]\s*"?(0\d{9,10})"?',
            "confidence": r'"?confidence"?\s*[:=]\s*"?(0\.\d+|1\.0)"?',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().strip('"').strip("'")
                if value:
                    result[key] = value
        
        return result
    
    def _extract_confidence(self, response: Dict) -> float:
        """Extract confidence value with validation"""
        
        confidence = response.get("confidence")
        
        if confidence is None:
            return 0.7  # Default
        
        try:
            conf = float(confidence)
            return max(0.0, min(1.0, conf))  # Clamp to [0, 1]
        except (ValueError, TypeError):
            logger.warning(f"[EntityExtractor] Invalid confidence value: {confidence}")
            return 0.7
    
    # ══════════════════════════════════════════════════════════════════════════
    # RESPONSE PARSERS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _parse_booking_response(self, response: Dict, context: Dict) -> Dict:
        """Parse and normalize booking extraction response"""

        if not response:
            return {}

        entities = {}

        # Service type - important for distinguishing trucking/packing/warehouse
        service_type = (
            response.get("service_type") or
            response.get("loai_dich_vu") or
            response.get("services")
        )
        if service_type:
            if isinstance(service_type, list):
                # Normalize each service code
                normalized = [normalize_service_code(s) for s in service_type if s]
                entities["service_type"] = normalized[0] if normalized else None
                entities["services"] = normalized
            else:
                normalized = normalize_service_code(str(service_type))
                entities["service_type"] = normalized
                entities["services"] = [normalized]
        
        # Customer - check multiple possible keys with confidence scoring
        customer = (
            response.get("customer_code") or
            response.get("customer") or
            response.get("khach_hang")
        )
        if customer:
            customer_match = self._match_customer_with_confidence(
                str(customer),
                context.get("customers", [])
            )
            entities["customer_code"] = customer_match["code"]
            entities["customer_confidence"] = customer_match["confidence"]
            entities["customer_candidates"] = customer_match["candidates"]
            entities["customer_needs_confirmation"] = customer_match["needs_confirmation"]
            entities["customer_raw_input"] = str(customer)  # Keep original input
        
        # Date - check multiple possible keys
        date = (
            response.get("date") or 
            response.get("booking_date") or
            response.get("ngay")
        )
        if date:
            entities["booking_date"] = self._normalize_date(str(date), context.get("current_date"))
        
        # Time
        time = (
            response.get("time") or 
            response.get("pickup_time") or
            response.get("gio")
        )
        if time:
            entities["pickup_time"] = self._normalize_time(str(time))
        
        # Vehicle type
        vehicle = (
            response.get("vehicle_type") or 
            response.get("vehicle") or
            response.get("loai_xe")
        )
        if vehicle:
            entities["vehicle_type"] = self._normalize_vehicle_type(str(vehicle))
        
        # Cargo
        cargo = response.get("cargo") or response.get("cargo_type") or response.get("hang_hoa")
        if cargo:
            entities["cargo_type"] = str(cargo)
        
        # Quantity - preserve raw string for mixed units like "1 pallet 3 thùng"
        qty = response.get("quantity") or response.get("package_quantity") or response.get("so_luong")
        if qty:
            logger.debug(f"[EntityExtractor] Raw quantity from AI: {qty} (type: {type(qty).__name__})")
            entities["package_quantity"] = self._extract_number(qty)
            # Also preserve the raw quantity string if it contains unit info
            if isinstance(qty, str) and not qty.isdigit():
                entities["package_quantity_raw"] = qty
        
        unit = response.get("unit") or response.get("package_unit") or response.get("don_vi")
        if unit:
            entities["package_unit"] = str(unit)
        
        # Invoices
        invoices = response.get("invoices") or response.get("invoice") or response.get("invoice_numbers")
        if invoices:
            if isinstance(invoices, str):
                # Split by common separators
                invoices = re.split(r'[,;\s]+', invoices)
            if isinstance(invoices, list):
                entities["invoices"] = [inv.strip() for inv in invoices if inv.strip()]
        
        # Addresses
        origin = response.get("origin") or response.get("pickup_address") or response.get("dia_chi_lay")
        if origin:
            entities["origin_address"] = str(origin)
        
        dest = response.get("destination") or response.get("delivery_address") or response.get("dia_chi_giao")
        if dest:
            entities["dest_address"] = str(dest)

        # Delivery company name (important for avoiding confusion)
        delivery_company = response.get("delivery_company") or response.get("cong_ty_nhan") or response.get("recipient_company")
        if delivery_company:
            entities["delivery_company"] = str(delivery_company)

        # Urgent flag
        if response.get("urgent"):
            entities["is_urgent"] = True
        
        # Notes
        notes = response.get("notes") or response.get("special_requirements") or response.get("ghi_chu")
        if notes:
            entities["notes"] = str(notes)
        
        return entities
    
    def _parse_vehicle_response(self, response: Dict, context: Dict) -> Dict:
        """Parse and normalize vehicle extraction response"""
        
        if not response:
            return {}
        
        entities = {}
        
        # License plate
        plate = (
            response.get("license_plate") or 
            response.get("bks") or
            response.get("bien_so")
        )
        if plate:
            entities["license_plate"] = self._normalize_license_plate(str(plate))
        
        # Driver name
        name = (
            response.get("driver_name") or 
            response.get("driver") or
            response.get("lai_xe") or
            response.get("ten_lai_xe")
        )
        if name:
            entities["driver_name"] = str(name).strip().title()
        
        # Driver phone
        phone = (
            response.get("driver_phone") or 
            response.get("phone") or
            response.get("sdt")
        )
        if phone:
            entities["driver_phone"] = self._normalize_phone(str(phone))
        
        # Driver CCCD
        cccd = response.get("driver_cccd") or response.get("cccd")
        if cccd:
            entities["driver_cccd"] = self._normalize_cccd(str(cccd))
        
        # Vendor name
        vendor = response.get("vendor_name") or response.get("vendor") or response.get("nha_xe")
        if vendor:
            entities["vendor_name"] = str(vendor)
        
        # Related customer
        customer = response.get("related_customer") or response.get("customer")
        if customer:
            entities["related_customer"] = str(customer).upper()
        
        # Related job
        job = response.get("job_number") or response.get("job")
        if job:
            entities["job_number"] = str(job).upper()
        
        return entities
    
    def _parse_status_response(self, response: Dict, context: Dict) -> Dict:
        """Parse and normalize status extraction response"""
        
        if not response:
            return {}
        
        entities = {}
        
        # Job number(s)
        job = response.get("job_number") or response.get("job")
        if job:
            entities["job_number"] = self._normalize_job_number(str(job), context.get("active_jobs", []))
        
        jobs = response.get("job_numbers")
        if jobs:
            if isinstance(jobs, list):
                entities["job_numbers"] = [
                    self._normalize_job_number(str(j), context.get("active_jobs", []))
                    for j in jobs
                ]
        
        # Customer (if job not specified)
        customer = response.get("customer")
        if customer:
            entities["customer"] = str(customer).upper()
        
        # New status
        status = response.get("status") or response.get("new_status")
        if status:
            entities["new_status"] = self._normalize_status(str(status))
        
        # Notes
        notes = response.get("notes") or response.get("completion_notes")
        if notes:
            entities["notes"] = str(notes)
        
        return entities
    
    # ══════════════════════════════════════════════════════════════════════════
    # NORMALIZERS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _match_customer(self, input_customer: str, customers: List[Dict]) -> str:
        """Match input customer to customer list (legacy wrapper)"""
        result = self._match_customer_with_confidence(input_customer, customers)
        return result.get("code") or str(input_customer).upper()

    def _match_customer_with_confidence(
        self,
        input_customer: str,
        customers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Match input customer to customer list with confidence scoring.

        Returns:
            Dict with:
            - code: matched customer_code or input as-is
            - confidence: 0.0-1.0
            - candidates: list of top 3 matches with scores
            - needs_confirmation: bool
        """
        if not input_customer:
            return {"code": None, "confidence": 0.0, "candidates": [], "needs_confirmation": False}

        input_lower = self._normalize_vietnamese(str(input_customer).lower().strip())
        input_raw_lower = str(input_customer).lower().strip()
        candidates = []

        for c in customers:
            code = (c.get("customer_code") or "").lower()
            short_name = (c.get("short_name") or "").lower()
            company_name = (c.get("company_name") or "").lower()

            # Normalize Vietnamese for accent-insensitive matching
            code_norm = self._normalize_vietnamese(code)
            short_norm = self._normalize_vietnamese(short_name)
            company_norm = self._normalize_vietnamese(company_name)

            # Calculate scores for different match types
            score = 0.0
            match_type = "none"

            # Exact match - highest confidence
            if input_lower == code_norm or input_lower == short_norm:
                score = 1.0
                match_type = "exact"
            elif input_raw_lower == code or input_raw_lower == short_name:
                score = 1.0
                match_type = "exact"
            # Prefix match - high confidence
            elif code_norm.startswith(input_lower) or short_norm.startswith(input_lower):
                score = 0.9
                match_type = "prefix"
            # Reverse prefix (input starts with customer code)
            elif input_lower.startswith(code_norm) and len(code_norm) >= 3:
                score = 0.85
                match_type = "reverse_prefix"
            elif input_lower.startswith(short_norm) and len(short_norm) >= 3:
                score = 0.85
                match_type = "reverse_prefix"
            # Contains match - medium confidence
            elif len(input_lower) >= 3 and (input_lower in short_norm or input_lower in company_norm):
                score = 0.7
                match_type = "contains"
            elif short_norm and len(short_norm) >= 3 and short_norm in input_lower:
                score = 0.65
                match_type = "reverse_contains"
            elif code_norm and len(code_norm) >= 3 and code_norm in input_lower:
                score = 0.65
                match_type = "reverse_contains"
            # Fuzzy match - low confidence
            else:
                fuzzy = self._fuzzy_score(input_lower, short_norm)
                if fuzzy > 0.4:
                    score = fuzzy * 0.6  # Scale down fuzzy scores
                    match_type = "fuzzy"

            if score > 0.3:
                candidates.append({
                    "code": c.get("customer_code"),
                    "name": c.get("short_name") or c.get("company_name"),
                    "score": round(score, 2),
                    "match_type": match_type
                })

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[:3]

        if not candidates:
            return {
                "code": str(input_customer).upper(),
                "confidence": 0.0,
                "candidates": [],
                "needs_confirmation": True
            }

        best = candidates[0]

        # High confidence threshold
        HIGH_CONFIDENCE = 0.85

        # Check for ambiguity - if top 2 are too close in score
        is_ambiguous = (
            len(candidates) >= 2 and
            candidates[0]["score"] - candidates[1]["score"] < 0.15
        )

        logger.info(f"[CustomerMatch] Input: '{input_customer}' -> Best: {best['code']} ({best['score']:.0%}), ambiguous={is_ambiguous}")

        return {
            "code": best["code"],
            "confidence": best["score"],
            "candidates": top_candidates,
            "needs_confirmation": best["score"] < HIGH_CONFIDENCE or is_ambiguous
        }

    def _normalize_vietnamese(self, text: str) -> str:
        """Remove Vietnamese accents for matching"""
        import unicodedata
        if not text:
            return ""
        # NFD normalization separates base chars from accents
        text = unicodedata.normalize('NFD', text)
        # Remove combining diacritical marks
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text.lower().strip()

    def _fuzzy_score(self, input_str: str, target: str) -> float:
        """
        Improved fuzzy matching score with multiple strategies.
        Handles cases like "lkv mien bac" matching "lkvmn".
        """
        if not input_str or not target:
            return 0.0

        scores = []

        # Strategy 1: Prefix matching (first N chars)
        # "lkv mien bac" starts with same chars as "lkvmn"
        min_len = min(len(input_str), len(target))
        prefix_match = 0
        for i in range(min_len):
            if input_str[i] == target[i]:
                prefix_match += 1
            else:
                break
        if prefix_match >= 3:  # At least 3 char prefix match
            scores.append(prefix_match / max(len(input_str), len(target)))

        # Strategy 2: Token-based matching
        # Split input into words and check if any word is prefix of target
        input_tokens = input_str.replace('-', ' ').split()
        for token in input_tokens:
            if len(token) >= 2:
                if target.startswith(token):
                    scores.append(len(token) / len(target))
                elif token in target:
                    scores.append(len(token) / max(len(token), len(target)) * 0.8)

        # Strategy 3: Subsequence matching (bi-directional)
        def subsequence_score(a: str, b: str) -> float:
            matches = 0
            b_idx = 0
            for char in a:
                while b_idx < len(b):
                    if b[b_idx] == char:
                        matches += 1
                        b_idx += 1
                        break
                    b_idx += 1
            return matches / max(len(a), len(b))

        scores.append(subsequence_score(input_str, target))
        scores.append(subsequence_score(target, input_str))

        # Strategy 4: Remove spaces and compare
        input_compact = input_str.replace(' ', '')
        target_compact = target.replace(' ', '')
        if input_compact and target_compact:
            # Check if one starts with the other
            if input_compact.startswith(target_compact):
                scores.append(len(target_compact) / len(input_compact))
            elif target_compact.startswith(input_compact):
                scores.append(len(input_compact) / len(target_compact))

        return max(scores) if scores else 0.0
    
    def _normalize_date(self, date_input: str, current_date: str = None) -> str:
        """Normalize date to YYYY-MM-DD format"""

        if not date_input:
            return ""

        date_lower = str(date_input).lower().strip()

        # Parse current date using smart parser
        if current_date:
            parsed_today = smart_parse_date(current_date)
            today = datetime.combine(parsed_today, datetime.min.time()) if parsed_today else datetime.now()
        else:
            today = datetime.now()

        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle relative dates (Vietnamese)
        relative_mappings = {
            ("hôm nay", "today", "nay", "hn"): 0,
            ("ngày mai", "mai", "tomorrow", "ng mai", "ngay mai"): 1,
            ("ngày kia", "mốt", "ngày mốt", "ngay kia", "mot"): 2,
        }
        
        for keywords, delta in relative_mappings.items():
            if date_lower in keywords:
                return (today + timedelta(days=delta)).strftime("%Y-%m-%d")
        
        # Use smart parser for flexible date format handling
        parsed = smart_parse_date(date_input)
        if parsed:
            return parsed.isoformat()

        # Fallback: Try to parse date formats manually
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
            "%d/%m/%y", "%d-%m-%y",
            "%d/%m", "%d-%m",
            "%d"
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_lower, fmt)

                # Handle 2-digit year
                if dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000)

                # Handle no year (year becomes 1900)
                if dt.year == 1900:
                    dt = dt.replace(year=today.year)
                    # If date is in the past, assume next year
                    if dt < today:
                        dt = dt.replace(year=today.year + 1)

                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Return original if parsing fails
        return date_input
    
    def _normalize_time(self, time_input: str) -> str:
        """Normalize time to HH:MM format"""
        
        if not time_input:
            return ""
        
        time_str = str(time_input).strip().lower()
        
        # Handle "22h", "10h30", "22H30"
        match = re.match(r"(\d{1,2})[hH](\d{2})?", time_str)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) or "00"
            return f"{hour:02d}:{minute}"
        
        # Handle "10:30", "22:00"
        match = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        
        # Handle "22.30"
        match = re.match(r"(\d{1,2})\.(\d{2})", time_str)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        
        # Handle just hour "22"
        match = re.match(r"^(\d{1,2})$", time_str)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
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
            "1.25T": "1.25T",
            "125T": "1.25T",
            "2.5": "2.5T",
            "2T5": "2.5T",
            "2.5T": "2.5T",
            "25T": "2.5T",
            "5": "5T",
            "5T": "5T",
            "10": "10T",
            "10T": "10T",
            "15": "15T",
            "15T": "15T",
            "20": "20T",
            "20T": "20T",
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
        plate = re.sub(r"[.\-_\s]+", "", plate)
        
        # Standard format: XXY ZZZZZ (e.g., 29H 76514)
        match = re.match(r"(\d{2}[A-Z])(\d{4,5})", plate)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Try with spaces already removed
        match = re.search(r"(\d{2}[A-Z])[\s\-]*(\d{4,5})", plate)
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
        if len(digits) == 9 and digits[0] != '0':
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
            "đã giao xong": "COMPLETED",
            "giao xong": "COMPLETED",
            
            # Delivered → use COMPLETED
            "đã giao": "COMPLETED",
            "da giao": "COMPLETED",
            "delivered": "COMPLETED",
            "giao rồi": "COMPLETED",
            
            # Cancelled
            "hủy": "CANCELLED",
            "huy": "CANCELLED",
            "cancel": "CANCELLED",
            "cancelled": "CANCELLED",
            "bỏ": "CANCELLED",
            
            # In transit
            "đang giao": "IN_TRANSIT",
            "dang giao": "IN_TRANSIT",
            "in_transit": "IN_TRANSIT",
            "transit": "IN_TRANSIT",
            "trên đường": "IN_TRANSIT",
            
            # Dispatched
            "đã điều xe": "DISPATCHED",
            "da dieu xe": "DISPATCHED",
            "dispatched": "DISPATCHED",
            "xe đã đi": "DISPATCHED",
        }
        
        return mappings.get(status_lower, status.upper())
    
    def _normalize_job_number(self, job_input: str, active_jobs: List[Dict]) -> str:
        """Normalize and match job number"""
        
        if not job_input:
            return ""
        
        job_str = str(job_input).upper().strip()
        
        # Full job number format
        if re.match(r"(TRK|WHS|CUS|PKG|SVC)-\d{4}-\d{3}", job_str):
            return job_str
        
        # Partial number - try to match with active jobs
        if job_str.isdigit() and len(job_str) <= 4:
            for job in active_jobs:
                job_no = job.get("job_no", "")
                if job_no.endswith(job_str) or job_str in job_no:
                    return job_no
        
        # Contains partial
        for job in active_jobs:
            job_no = job.get("job_no", "")
            if job_str in job_no:
                return job_no
        
        return job_str
    
    def _extract_number(self, value: Any) -> Optional[int]:
        """Extract integer from value"""
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if isinstance(value, str):
            # Handle mixed units like "1 pallet 3 thùng"
            numbers = re.findall(r"(\d+)", value)
            if numbers:
                # Sum all quantities
                total = sum(int(n) for n in numbers)
                return total if total > 0 else int(numbers[0])
        
        return None
    
    def _extract_service_type_from_text(self, entities: Dict, text: str) -> Dict:
        """
        Extract service type from [SERVICE_TYPE:XXX] marker in text.
        This marker is injected by chat.py when processing Excel files.
        """
        # Pattern: [SERVICE_TYPE:PACKING] or [SERVICE_TYPE:SVC_PACK]
        match = re.search(r'\[SERVICE_TYPE:([A-Z_]+)\]', text, re.IGNORECASE)
        if match:
            raw_type = match.group(1).upper()
            # Normalize to valid DB service_code
            normalized_code = normalize_service_code(raw_type)

            # Only override if not already set or if current value is default
            if not entities.get('service_type') or entities.get('service_type') == 'TRUCKING_SHORT':
                entities['service_type'] = normalized_code
                entities['services'] = [normalized_code]
                logger.info(f"[EntityExtractor] Extracted service_type: {raw_type} → {normalized_code}")

        return entities

    def _fix_mixed_quantity_from_text(self, entities: Dict, text: str) -> Dict:
        """
        Post-processing: Extract mixed unit quantities from raw text
        Example: "1 pallet 3thùng" -> package_quantity: 4, package_quantity_raw: "1 pallet 3 thùng"
        """
        # First, try to extract directly from "• Số lượng:" pattern (from formatted booking text)
        qty_pattern = r'[•\-]\s*(?:Số lượng|So luong|Quantity)[:\s]+([^\n]+)'
        qty_match = re.search(qty_pattern, text, re.IGNORECASE)
        if qty_match and not entities.get("package_quantity"):
            raw_qty = qty_match.group(1).strip()
            # Extract numbers and units from the raw quantity string
            # Include both Vietnamese and English unit names
            unit_pattern = r'(\d+)\s*(pallet|pallets|thùng|kiện|khay|túi|hộp|carton|cartons|box|boxes|ctn|ctns|bag|bags)?'
            unit_matches = re.findall(unit_pattern, raw_qty.lower())
            if unit_matches:
                total = sum(int(m[0]) for m in unit_matches if m[0])
                entities["package_quantity"] = total
                entities["package_quantity_raw"] = raw_qty
                entities["package_display"] = raw_qty
                logger.info(f"[EntityExtractor] Extracted quantity from 'Số lượng:' pattern: {raw_qty} -> {total}")
                return entities

        # Pattern to find mixed units like "1 pallet 3thùng" or "2 pallet và 5 kiện"
        # Include both Vietnamese and English unit names
        unit_names = r'pallet|pallets|thùng|kiện|khay|túi|hộp|carton|cartons|box|boxes|ctn|ctns|bag|bags'
        mixed_pattern = rf'(\d+)\s*({unit_names})(?:\s*(?:và|,)?\s*(\d+)\s*({unit_names}))?'

        matches = re.findall(mixed_pattern, text.lower(), re.IGNORECASE)

        if matches:
            for match in matches:
                num1, unit1, num2, unit2 = match
                if num1 and num2:  # Found mixed units
                    qty1 = int(num1)
                    qty2 = int(num2)
                    total = qty1 + qty2

                    # Update entities with correct values
                    entities["package_quantity"] = total
                    entities["package_quantity_raw"] = f"{num1} {unit1}, {num2} {unit2}"

                    # Use the first unit as primary (larger packaging first usually)
                    if unit1 in ['pallet', 'pallets', 'khay']:
                        entities["package_unit"] = unit2 if unit2 else unit1
                    else:
                        entities["package_unit"] = unit1

                    logger.info(f"[EntityExtractor] Fixed mixed quantity: {entities['package_quantity_raw']} -> {total}")
                    break
                elif num1:  # Single unit found
                    if not entities.get("package_quantity"):
                        entities["package_quantity"] = int(num1)
                        if unit1:
                            entities["package_unit"] = unit1
                            entities["package_quantity_raw"] = f"{num1} {unit1}"

        return entities
    
    def _fix_addresses_from_text(self, entities: Dict, text: str) -> Dict:
        """
        Post-processing: Extract pickup_address and delivery_address from raw text
        if they were missed by AI extraction.
        """
        import re
        
        text_lower = text.lower()
        
        # Pattern to find addresses after keywords
        # "lấy tại:", "giao tại:", "đến:", "từ:"
        pickup_patterns = [
            r'(?:lấy tại|từ|pickup|from)[:\s]+([^,\n]+)',
            r'(?:lấy hàng tại|điểm lấy)[:\s]+([^,\n]+)',
        ]
        
        delivery_patterns = [
            r'(?:giao tại|đến|giao hàng tại|delivery|to)[:\s]+([^,\n]+)',
            r'(?:điểm giao|đích đến)[:\s]+([^,\n]+)',
        ]
        
        # Try to extract pickup address if missing
        if not entities.get('pickup_address'):
            for pattern in pickup_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    addr = match.group(1).strip()
                    if len(addr) > 5:  # Sanity check
                        entities['pickup_address'] = addr
                        logger.info(f"[EntityExtractor] Fixed pickup_address: {addr}")
                        break
        
        # Try to extract delivery address if missing
        if not entities.get('delivery_address'):
            for pattern in delivery_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    addr = match.group(1).strip()
                    if len(addr) > 5:
                        entities['delivery_address'] = addr
                        logger.info(f"[EntityExtractor] Fixed delivery_address: {addr}")
                        break
        
        return entities
    
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
                if customer_upper in str(job.get("customer", "")).upper():
                    return job
                if customer_upper in str(job.get("customer_code", "")).upper():
                    return job
        
        # If only one pending job, assume it's the target
        if len(pending_jobs) == 1:
            return pending_jobs[0]
        
        return None
