# -*- coding: utf-8 -*-
"""
SLMS AI - Anthropic Claude Client
=================================

Client for Anthropic Claude API (Sonnet, Opus models).
Claude excels at Vietnamese text understanding and complex entity extraction.

Available Models:
- claude-sonnet-4-20250514 (Claude 4 Sonnet - fast, capable)
- claude-opus-4-5-20251101 (Claude Opus 4.5 - most capable)
- claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet - balanced)
"""

import logging
import json
import re
from typing import Dict, Any, Union
import anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client for Anthropic Claude API with robust JSON handling"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

        logger.info(f"[AnthropicClient] Initialized with model: {self.model}")

    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from prompt using Claude

        Args:
            prompt: The prompt text
            response_format: "text" or "json"
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            dict if response_format is "json", otherwise str
        """
        try:
            logger.debug(f"[AnthropicClient] Generating with format: {response_format}, temp: {temperature}")

            # Build system message for JSON if needed
            system_msg = None
            if response_format == "json":
                system_msg = "You are a helpful assistant. Always respond in valid JSON format only, no markdown, no explanation."

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg if system_msg else "You are a helpful assistant.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response
            text = ""
            for block in message.content:
                if block.type == "text":
                    text += block.text

            text = text.strip()

            logger.debug(f"[AnthropicClient] Raw response length: {len(text)}")
            logger.debug(f"[AnthropicClient] Raw response preview: {text[:300]}...")

            if response_format == "json":
                return self._parse_json_robust(text)

            return text

        except Exception as e:
            logger.error(f"[AnthropicClient] Generation failed: {e}", exc_info=True)
            raise

    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate text from prompt and image (Claude Vision)
        """
        try:
            import base64

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            text = ""
            for block in message.content:
                if block.type == "text":
                    text += block.text

            return {"text": text.strip()}

        except Exception as e:
            logger.error(f"[AnthropicClient] Vision generation failed: {e}", exc_info=True)
            raise

    def _parse_json_robust(self, text: str) -> Dict[str, Any]:
        """
        Robust JSON parsing with multiple fallback strategies
        """
        if not text:
            logger.warning("[AnthropicClient] Empty response, returning empty dict")
            return {}

        text = text.strip()

        # Strategy 1: Direct parse
        try:
            result = json.loads(text)
            logger.debug("[AnthropicClient] Direct JSON parse succeeded")
            return result
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from ```json ... ```
        match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                logger.debug("[AnthropicClient] Extracted from ```json``` block")
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 3: Extract from ``` ... ```
        match = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                logger.debug("[AnthropicClient] Extracted from ``` block")
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 4: Find JSON array pattern (rate sheets return arrays)
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            json_str = match.group()
            cleaned = self._clean_json(json_str)
            try:
                result = json.loads(cleaned)
                logger.debug("[AnthropicClient] Extracted JSON array")
                return result
            except json.JSONDecodeError:
                pass

        # Strategy 5: Find JSON object pattern
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            json_str = match.group()
            cleaned = self._clean_json(json_str)

            try:
                result = json.loads(cleaned)
                logger.debug("[AnthropicClient] Extracted and cleaned JSON object")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"[AnthropicClient] JSON parse error: {e}")

        logger.error(f"[AnthropicClient] All JSON parsing strategies failed")
        return {}

    def _clean_json(self, json_str: str) -> str:
        """Clean common JSON issues"""
        # Remove trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        # Remove comments
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        return json_str
