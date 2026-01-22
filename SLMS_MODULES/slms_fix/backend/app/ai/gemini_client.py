# -*- coding: utf-8 -*-
"""
SLMS AI - Gemini Client (FIXED VERSION)
=======================================

Client for Google Gemini API with robust JSON parsing.

FIXES:
- Better JSON extraction from markdown
- Handle various AI response formats
- Detailed logging for debugging
"""

import logging
import json
import re
from typing import Optional, Dict, Any, Union
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API with robust JSON handling"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GOOGLE_GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        
        self.model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp')
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"[GeminiClient] Initialized with model: {self.model_name}")
        
    async def generate(
        self, 
        prompt: str, 
        response_format: str = "text",
        temperature: float = 0.7
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from prompt
        
        Args:
            prompt: The prompt text
            response_format: "text" or "json"
            temperature: Model temperature (0.0-1.0)
            
        Returns:
            dict if response_format is "json", otherwise str
        """
        try:
            logger.debug(f"[GeminiClient] Generating with format: {response_format}, temp: {temperature}")
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            # Request JSON mime type if needed
            if response_format == "json":
                try:
                    generation_config.response_mime_type = "application/json"
                except AttributeError:
                    # Older SDK version doesn't support this
                    logger.debug("[GeminiClient] response_mime_type not supported, will parse manually")
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            text = response.text.strip()
            
            logger.debug(f"[GeminiClient] Raw response length: {len(text)}")
            logger.debug(f"[GeminiClient] Raw response preview: {text[:300]}...")
            
            if response_format == "json":
                return self._parse_json_robust(text)
            
            return text
            
        except Exception as e:
            logger.error(f"[GeminiClient] Generation failed: {e}", exc_info=True)
            raise

    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate text from prompt and image (for OCR)
        """
        try:
            import base64
            
            # Prepare image part
            image_data = base64.b64decode(image_base64)
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config=generation_config
            )
            
            return {"text": response.text}
            
        except Exception as e:
            logger.error(f"[GeminiClient] Vision generation failed: {e}", exc_info=True)
            raise

    def _parse_json_robust(self, text: str) -> Dict[str, Any]:
        """
        Robust JSON parsing with multiple fallback strategies
        
        Handles:
        - Pure JSON
        - JSON in ```json``` code blocks
        - JSON in ``` code blocks
        - JSON with trailing commas
        - JSON with comments
        - JSON mixed with explanation text
        """
        if not text:
            logger.warning("[GeminiClient] Empty response, returning empty dict")
            return {}
        
        text = text.strip()
        
        # Strategy 1: Direct parse (cleanest case)
        try:
            result = json.loads(text)
            logger.debug("[GeminiClient] Direct JSON parse succeeded")
            return result
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from ```json ... ```
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                logger.debug("[GeminiClient] Extracted from ```json``` block")
                return result
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Extract from ``` ... ```
        match = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                logger.debug("[GeminiClient] Extracted from ``` block")
                return result
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Find JSON object pattern and clean
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            json_str = match.group()
            cleaned = self._clean_json(json_str)
            
            try:
                result = json.loads(cleaned)
                logger.debug("[GeminiClient] Extracted and cleaned JSON object")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"[GeminiClient] JSON parse error after cleaning: {e}")
        
        # Strategy 5: Try to extract JSON array
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            json_str = match.group()
            cleaned = self._clean_json(json_str)
            
            try:
                result = json.loads(cleaned)
                # Wrap array in dict for consistency
                logger.debug("[GeminiClient] Extracted JSON array, wrapping in dict")
                return {"data": result}
            except json.JSONDecodeError:
                pass
        
        # Strategy 6: Manual key-value extraction
        result = self._extract_key_values(text)
        if result:
            logger.debug("[GeminiClient] Used fallback key-value extraction")
            return result
        
        # All strategies failed
        logger.error(f"[GeminiClient] All JSON parsing strategies failed")
        logger.debug(f"[GeminiClient] Failed text: {text[:500]}")
        return {}
    
    def _clean_json(self, json_str: str) -> str:
        """Clean common JSON issues"""
        
        # Remove trailing commas before } or ]
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Remove single-line comments
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        
        # Remove multi-line comments
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Replace single quotes with double quotes (common AI mistake)
        # But be careful not to break strings that contain apostrophes
        # Simple approach: only replace when it looks like JSON structure
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'([,}\]])", r': "\1"\2', json_str)
        
        return json_str
    
    def _extract_key_values(self, text: str) -> Dict[str, Any]:
        """
        Fallback: Extract key-value pairs using patterns
        Used when JSON parsing completely fails
        """
        result = {}
        
        # Common patterns for logistics fields
        patterns = {
            "intent": r'"?intent"?\s*[:=]\s*"?([A-Z_]+)"?',
            "confidence": r'"?confidence"?\s*[:=]\s*"?(\d+\.?\d*)"?',
            "customer_code": r'"?customer_code"?\s*[:=]\s*"?([A-Z0-9]+)"?',
            "date": r'"?(?:date|booking_date)"?\s*[:=]\s*"?([^",}\n]+)"?',
            "time": r'"?(?:time|pickup_time)"?\s*[:=]\s*"?(\d{1,2}[:\.]?\d{0,2}[hH]?)"?',
            "vehicle_type": r'"?vehicle_type"?\s*[:=]\s*"?([0-9.]+T|CONT\d+)"?',
            "license_plate": r'"?license_plate"?\s*[:=]\s*"?(\d{2}[A-Z]\s*[\-]?\s*\d{4,5})"?',
            "driver_name": r'"?driver_name"?\s*[:=]\s*"?([^",}\n]+)"?',
            "driver_phone": r'"?driver_phone"?\s*[:=]\s*"?(0\d{9,10})"?',
            "new_status": r'"?(?:status|new_status)"?\s*[:=]\s*"?([A-Z_]+)"?',
            "job_number": r'"?job_number"?\s*[:=]\s*"?([A-Z]{3}-\d{4}-\d{3}|\d{3})"?',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().strip('"').strip("'")
                if value and value.lower() not in ('null', 'none', ''):
                    # Convert confidence to float
                    if key == "confidence":
                        try:
                            result[key] = float(value)
                        except ValueError:
                            result[key] = 0.7
                    else:
                        result[key] = value
        
        return result
