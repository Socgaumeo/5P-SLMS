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
        "query_info",
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
            
            # QUERY_INFO variations
            "query": "query_info",
            "info": "query_info",
            "question": "query_info",
            "hoi": "query_info",
            
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
        "job nào", "đơn nào", "giá"
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
        
        scores = {
            "create_booking": booking_score,
            "assign_vehicle": vehicle_score,
            "update_status": status_score,
            "query_info": query_score,
        }
        
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        if max_score == 0:
            return "general_chat", 0.3
        
        # Convert score to confidence (rough estimate)
        confidence = min(0.4 + (max_score * 0.15), 0.8)
        
        return max_intent, confidence
