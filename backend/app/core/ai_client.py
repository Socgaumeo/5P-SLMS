"""
AI Client Wrapper for SLMS AI Pipeline
=======================================

Provides a consistent interface for AI models (Gemini, DeepSeek)
that the AIPipeline can use.
"""

import json
import re
import logging
from typing import Optional, Union

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Gemini API client wrapper for AI Pipeline
    
    Usage:
        client = GeminiClient()
        result = await client.generate("Your prompt", response_format="json")
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_GEMINI_API_KEY
        self.model_name = model or getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash-exp')
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"GeminiClient initialized with model: {self.model_name}")
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.7
    ) -> Union[dict, str]:
        """
        Generate text response from Gemini
        
        Args:
            prompt: The prompt text
            response_format: "text" or "json"
            temperature: Model temperature (0.0-1.0)
            
        Returns:
            dict if response_format is "json", otherwise str
        """
        try:
            config = genai.GenerationConfig(temperature=temperature)
            
            if response_format == "json":
                config.response_mime_type = "application/json"
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=config
            )
            
            text = response.text.strip()
            
            if response_format == "json":
                return self._parse_json(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            raise
    
    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate response with image input (for OCR)
        
        Args:
            prompt: The prompt text
            image_base64: Base64 encoded image
            temperature: Model temperature
            
        Returns:
            dict with "text" key containing the response
        """
        import base64
        
        try:
            # Decode base64 to bytes
            image_data = base64.b64decode(image_base64)
            
            # Create image part for multimodal input
            image_part = {
                "mime_type": "image/png",
                "data": image_data
            }
            
            response = await self.model.generate_content_async(
                [prompt, image_part],
                generation_config=genai.GenerationConfig(temperature=temperature)
            )
            
            return {"text": response.text}
            
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            raise
    
    def _parse_json(self, text: str) -> dict:
        """Parse JSON from response, handling markdown code blocks"""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code block
        if "```json" in text:
            match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        
        if "```" in text:
            match = re.search(r"```\s*([\s\S]*?)\s*```", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        
        # Clean up common JSON issues
        cleaned = re.sub(r',\s*}', '}', text)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            logger.debug(f"Raw text: {text[:500]}")
            raise ValueError(f"Failed to parse JSON response: {e}")


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_ai_client() -> GeminiClient:
    """Get or create GeminiClient singleton"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
