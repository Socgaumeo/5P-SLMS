# backend/app/ai/clients.py
"""
AI Client Factory
Provides unified interface for different AI providers (Gemini, DeepSeek, etc.)
"""

import os
import logging
from typing import Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy loaded clients
_client_instance = None


class AIClient:
    """Unified AI client interface"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or settings.AI_PROVIDER
        self._client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the appropriate AI client based on provider"""
        if self.provider.lower() == "gemini":
            from app.ai.gemini_client import GeminiClient
            self._client = GeminiClient()
            logger.info("Initialized Gemini AI client")
        elif self.provider.lower() == "deepseek":
            from app.ai.deepseek_client import DeepSeekClient
            self._client = DeepSeekClient()
            logger.info("Initialized DeepSeek AI client")
        elif self.provider.lower() == "anthropic":
            from app.ai.anthropic_client import AnthropicClient
            self._client = AnthropicClient()
            logger.info("Initialized Anthropic Claude AI client")
        else:
            # Default to DeepSeek
            from app.ai.deepseek_client import DeepSeekClient
            self._client = DeepSeekClient()
            logger.warning(f"Unknown provider '{self.provider}', defaulting to DeepSeek")
    
    async def generate(
        self, 
        prompt: str, 
        response_format: str = "text",
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from AI
        
        Args:
            prompt: The input prompt
            response_format: "text" or "json"
            temperature: Creativity level (0-1)
            **kwargs: Additional provider-specific options
            
        Returns:
            Generated text response
        """
        if hasattr(self._client, 'generate'):
            return await self._client.generate(
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                **kwargs
            )
        elif hasattr(self._client, 'generate_content'):
            # Fallback for clients with different method names
            response = await self._client.generate_content(prompt)
            return response.text if hasattr(response, 'text') else str(response)
        else:
            raise NotImplementedError(f"Client {type(self._client)} does not have generate method")
    
    def generate_content(self, prompt: str, **kwargs):
        """Sync version for compatibility"""
        if hasattr(self._client, 'generate_content'):
            return self._client.generate_content(prompt, **kwargs)
        raise NotImplementedError("generate_content not available")


def get_ai_client(provider: str = None) -> AIClient:
    """
    Get or create AI client instance (singleton pattern)
    
    Args:
        provider: Optional provider override ("gemini", "deepseek")
        
    Returns:
        AIClient instance
    """
    global _client_instance
    
    # If provider is specified, check if we need a new instance
    target_provider = provider or settings.AI_PROVIDER
    
    if _client_instance is None or _client_instance.provider != target_provider:
        _client_instance = AIClient(target_provider)
    
    return _client_instance


def reset_client():
    """Reset the client instance (useful for testing or reconfiguration)"""
    global _client_instance
    _client_instance = None
