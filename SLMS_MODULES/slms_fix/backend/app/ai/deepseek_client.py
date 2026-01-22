import logging
import json
from typing import Optional, Dict, Any, Union
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """Client for DeepSeek API (OpenAI-compatible)"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = settings.DEEPSEEK_MODEL
        
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
            messages = [{"role": "user", "content": prompt}]
            
            if response_format == "json":
                messages.insert(0, {
                    "role": "system", 
                    "content": "You are a helpful assistant. Always respond in valid JSON format."
                })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            
            text = response.choices[0].message.content
            
            if response_format == "json":
                return self._parse_json(text)
            
            return text
            
        except Exception as e:
            logger.error(f"DeepSeek generation failed: {e}")
            raise

    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.2
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from prompt and image
        Note: DeepSeek Coder/Chat might not support vision. 
        This is a placeholder or assumes specialized model.
        """
        # DeepSeek currently (as of knowledge cutoff) doesn't have Vision API public in same way?
        # Fallback or raise error. 
        # For now, return empty or mock structure to prevent crash if inferred.
        logger.warning("DeepSeek vision not implemented/supported. Returning empty.")
        return {"text": ""}

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from text"""
        try:
            clean_text = text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0]
            
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
