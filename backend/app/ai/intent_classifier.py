"""
SLMS AI Pipeline - Stage 2: Intent Classifier
==============================================

Classify user intent from text input using few-shot learning.

Supported Intents:
- CREATE_BOOKING: Book xe, tạo job mới
- ASSIGN_VEHICLE: Thông tin xe/lái xe từ vendor
- UPDATE_STATUS: Cập nhật trạng thái job
- QUERY_INFO: Hỏi thông tin
- GENERAL_CHAT: Chat thông thường
"""

from typing import Dict, Any
import logging
import json

from .prompts.intent_prompts import INTENT_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classify user intent using AI with few-shot examples
    """

    # Valid intents
    VALID_INTENTS = [
        "create_booking",
        "assign_vehicle",
        "update_status",
        "update_job",  # Modify job data (customer, addresses, services)
        "query_info",
        "create_customer",
        "create_vendor",
        "create_quotation",
        "general_chat",
        "unknown"
    ]
    
    def __init__(self, ai_client):
        """
        Initialize with AI client
        
        Args:
            ai_client: AI client (GeminiClient or DeepSeekClient)
        """
        self.ai = ai_client
    
    async def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify user intent from text
        
        Args:
            text: Preprocessed input text
            
        Returns:
            Dict with intent, confidence, key_signals, reasoning
        """
        
        if not text or not text.strip():
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "key_signals": [],
                "reasoning": "Empty input"
            }
        
        try:
            # Build prompt
            prompt = INTENT_CLASSIFICATION_PROMPT.format(input=text)
            
            # Call AI
            response = await self.ai.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Parse response
            result = self._parse_response(response)
            
            logger.info(f"Intent classified: {result['intent']} ({result['confidence']:.2f})")
            logger.debug(f"Key signals: {result['key_signals']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "key_signals": [],
                "reasoning": f"Error: {str(e)}"
            }
    
    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse and validate AI response
        """
        
        # Handle different response formats
        if isinstance(response, str):
            try:
                # Try to extract JSON from text
                response = self._extract_json(response)
            except:
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "key_signals": [],
                    "reasoning": "Failed to parse response"
                }
        
        if isinstance(response, dict):
            intent = response.get("intent", "unknown").lower()
            
            # Validate intent
            if intent not in self.VALID_INTENTS:
                intent = self._map_intent(intent)
            
            confidence = float(response.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            return {
                "intent": intent,
                "confidence": confidence,
                "key_signals": response.get("key_signals", []),
                "reasoning": response.get("reasoning", "")
            }
        
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "key_signals": [],
            "reasoning": "Invalid response format"
        }
    
    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from text that may contain markdown or other content
        """
        import re
        
        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find raw JSON
        json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        raise ValueError("No JSON found in response")
    
    def _map_intent(self, intent: str) -> str:
        """
        Map non-standard intent names to valid intents
        """

        mappings = {
            # CREATE_BOOKING variations
            "booking": "create_booking",
            "create_job": "create_booking",
            "new_booking": "create_booking",
            "book": "create_booking",
            "tao_booking": "create_booking",
            "dat_xe": "create_booking",

            # ASSIGN_VEHICLE variations
            "vehicle": "assign_vehicle",
            "assign": "assign_vehicle",
            "dieu_xe": "assign_vehicle",
            "thong_tin_xe": "assign_vehicle",
            "driver": "assign_vehicle",

            # UPDATE_STATUS variations
            "update": "update_status",
            "status": "update_status",
            "complete": "update_status",
            "hoan_thanh": "update_status",
            "cap_nhat": "update_status",

            # UPDATE_JOB variations (modify job data)
            "update_job": "update_job",
            "modify_job": "update_job",
            "edit_job": "update_job",
            "change_customer": "update_job",
            "doi_khach": "update_job",
            "sua_job": "update_job",
            "sua_don": "update_job",
            "thay_doi_kh": "update_job",
            "them_dich_vu": "update_job",
            "add_service": "update_job",

            # QUERY_INFO variations
            "query": "query_info",
            "info": "query_info",
            "question": "query_info",
            "hoi": "query_info",

            # CREATE_CUSTOMER variations
            "customer": "create_customer",
            "new_customer": "create_customer",
            "tao_khach_hang": "create_customer",
            "them_kh": "create_customer",
            "add_customer": "create_customer",

            # CREATE_VENDOR variations
            "vendor": "create_vendor",
            "new_vendor": "create_vendor",
            "tao_ncc": "create_vendor",
            "them_ncc": "create_vendor",
            "add_vendor": "create_vendor",
            "nha_cung_cap": "create_vendor",

            # CREATE_QUOTATION variations
            "quotation": "create_quotation",
            "quote": "create_quotation",
            "bao_gia": "create_quotation",
            "gia_cuoc": "create_quotation",
            "price": "create_quotation",
            "pricing": "create_quotation",
            "rate": "create_quotation",

            # GENERAL_CHAT variations
            "chat": "general_chat",
            "greeting": "general_chat",
            "chao": "general_chat",
        }

        return mappings.get(intent, "unknown")


# ══════════════════════════════════════════════════════════════════════════════
# QUICK CLASSIFIER (Rule-based fallback)
# ══════════════════════════════════════════════════════════════════════════════

class QuickClassifier:
    """
    Fast rule-based classifier as fallback or pre-filter
    """

    # Keywords for each intent
    BOOKING_KEYWORDS = [
        "book", "đặt xe", "cần xe", "ngày mai", "hôm nay",
        "1.25t", "2.5t", "5t", "10t", "container",
        "lấy hàng", "giao hàng", "chở hàng",
        "invoice", "kiện", "pallet"
    ]

    VEHICLE_KEYWORDS = [
        "bks", "biển số", "lái xe", "tài xế", "driver",
        "cccd", "căn cước", "sđt", "điện thoại",
        "29h", "30h", "51h", "60h"  # Common plate prefixes
    ]

    STATUS_KEYWORDS = [
        "xong", "done", "hoàn thành", "đã giao",
        "hủy", "cancel", "completed", "delivered"
    ]

    QUERY_KEYWORDS = [
        "?", "bao nhiêu", "ở đâu", "status", "trạng thái",
        "job nào", "đơn nào"
    ]

    CUSTOMER_KEYWORDS = [
        "tạo khách hàng", "thêm kh", "khách hàng mới", "add customer",
        "đăng ký kinh doanh", "mst", "mã số thuế", "công ty mới",
        "customer_code", "company_name", "tax_code"
    ]

    VENDOR_KEYWORDS = [
        "tạo ncc", "thêm ncc", "vendor mới", "nhà cung cấp",
        "nhà vận chuyển", "đối tác vận tải", "add vendor",
        "vendor_code", "vendor_name"
    ]

    QUOTATION_KEYWORDS = [
        "báo giá", "quotation", "giá cước", "bảng giá",
        "giá mua", "giá bán", "tuyến đường", "price",
        "vnd/chuyến", "vnd/trip", "giá tuyến"
    ]

    UPDATE_JOB_KEYWORDS = [
        "đổi khách", "thay đổi khách hàng", "sửa job", "sửa đơn",
        "chuyển khách", "thêm dịch vụ", "add service", "edit job",
        "modify job", "change customer", "đổi kh", "thay kh",
        "sửa địa chỉ", "đổi địa chỉ", "thêm chuyến"
    ]

    @classmethod
    def classify(cls, text: str) -> tuple[str, float]:
        """
        Quick rule-based classification

        Returns:
            tuple of (intent, confidence)
        """
        text_lower = text.lower()

        # Count keyword matches
        booking_score = sum(1 for k in cls.BOOKING_KEYWORDS if k in text_lower)
        vehicle_score = sum(1 for k in cls.VEHICLE_KEYWORDS if k in text_lower)
        status_score = sum(1 for k in cls.STATUS_KEYWORDS if k in text_lower)
        query_score = sum(1 for k in cls.QUERY_KEYWORDS if k in text_lower)
        customer_score = sum(1 for k in cls.CUSTOMER_KEYWORDS if k in text_lower)
        vendor_score = sum(1 for k in cls.VENDOR_KEYWORDS if k in text_lower)
        quotation_score = sum(1 for k in cls.QUOTATION_KEYWORDS if k in text_lower)
        update_job_score = sum(1 for k in cls.UPDATE_JOB_KEYWORDS if k in text_lower)

        scores = {
            "create_booking": booking_score,
            "assign_vehicle": vehicle_score,
            "update_status": status_score,
            "update_job": update_job_score,
            "query_info": query_score,
            "create_customer": customer_score,
            "create_vendor": vendor_score,
            "create_quotation": quotation_score,
        }

        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        if max_score == 0:
            return "general_chat", 0.3

        # Convert score to confidence (rough estimate)
        confidence = min(0.4 + (max_score * 0.15), 0.8)

        return max_intent, confidence
