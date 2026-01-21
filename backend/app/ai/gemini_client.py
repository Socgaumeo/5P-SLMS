import logging
import json
import re
from typing import Optional, Dict, Any, Union
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.vision_model = genai.GenerativeModel("gemini-pro-vision") # Or use gemini-1.5-flash for both
        
    async def generate(
        self, 
        prompt: str, 
        response_format: str = "text",
        temperature: float = 0.7
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from prompt
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            text = response.text
            
            if response_format == "json":
                return self._parse_json(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.2
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from prompt and image
        """
        try:
            # Prepare image part
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_base64
            }
            
            # Use appropriate model for vision (Gemini 1.5 Flash handles both text and image well)
            # If using older gemini-pro, need gemini-pro-vision
            # Assuming settings.GEMINI_MODEL is 1.5-flash or capable
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config=generation_config
            )
            
            return {"text": response.text}
            
        except Exception as e:
            logger.error(f"Gemini vision generation failed: {e}")
            raise

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from text"""
        try:
            # Clean up markdown
            clean_text = text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0]
            
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Raw text: {text}")
            return {}
