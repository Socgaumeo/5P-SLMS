"""
AI Service - Intent Detection and Entity Extraction
Supports Gemini and DeepSeek
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re

import google.generativeai as genai
from openai import OpenAI

from app.core.config import settings
from app.ai.gemini_client import GeminiClient
from app.ai.deepseek_client import DeepSeekClient
from app.services.data_service import get_data_service
from app.ai.pipeline import create_pipeline, PipelineInput, InputType

logger = logging.getLogger(__name__)


class AIService:
    """
    AI Service - Wrapper around AIPipeline for backward compatibility
    """
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        
        # Initialize AI Client
        if self.provider == "gemini":
            self.ai_client = GeminiClient(api_key=settings.GOOGLE_GEMINI_API_KEY)
        elif self.provider == "deepseek":
            self.ai_client = DeepSeekClient(api_key=settings.DEEPSEEK_API_KEY)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
            
    async def process(
        self,
        content: str,
        content_type: str = "TEXT",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process chat input using AIPipeline
        
        Args:
            content: Text content
            content_type: TEXT, EXCEL, PDF, IMAGE_OCR
            context: Optional context
            
        Returns:
            Legacy format dict: {intent, confidence, entities, enriched_data, summary}
        """
        
        try:
            # Create pipeline
            # Note: The pipeline expects a DB session for ContextLoader. 
            # Our ContextLoader currently uses raw SQL via data_service or similar. 
            # ContextLoader.load() calls await db.fetch_all().
            # DataService is synchronous. We need a bridge.
            
            data_service = get_data_service()
            
            from app.ai.db_adapter import DatabaseAdapter
            db_adapter = DatabaseAdapter(data_service)
            
            pipeline = create_pipeline(db_adapter, self.ai_client)
            
            # Prepare input
            pipeline_input = PipelineInput(
                content=content,
                input_type=InputType(content_type.lower()),
                user_context=context
            )
            
            # Run pipeline
            result = await pipeline.process(pipeline_input)
            
            # Map PipelineOutput to legacy format
            # Legacy: {intent, confidence, entities, enriched_data, summary}
            # New: {intent, confidence, entities, missing_fields...}
            
            response = {
                "intent": result.intent.upper(), # Legacy uses UPPERCASE
                "confidence": result.confidence,
                "entities": result.entities,
                "enriched_data": {}, # Pipeline doesn't return enriched_data directly yet, usually separate step
                "summary": result.generated_message, # Use generated message as summary or create one
                "raw_response": str(result.dict())
            }
            
            # Map intent names if needed
            # New uses 'create_booking', 'assign_vehicle' (snake_case)
            # Legacy uses 'CREATE_JOB', 'ASSIGN_VEHICLE' (UPPER_CASE)
            intent_map = {
                "create_booking": "CREATE_JOB",
                "assign_vehicle": "ASSIGN_VEHICLE", 
                "update_status": "UPDATE_JOB",
                "query_info": "QUERY_STATUS",
                "general_chat": "GENERAL_QUERY"
            }
            
            if result.intent in intent_map:
                response["intent"] = intent_map[result.intent]
            elif result.intent.upper() in intent_map.values():
                 response["intent"] = result.intent.upper()

            # Enrich entities with DB data (Critical for frontend templates)
            try:
                enriched = await data_service.enrich_entities(
                    intent=response["intent"],
                    entities=result.entities
                )
                response["enriched_data"] = enriched
                
                # Merge enriched data back into entities for completeness if needed
                # response["entities"].update(enriched)
            except Exception as e:
                logger.error(f"Enrichment failed: {e}")
                response["enriched_data"] = {"error": str(e)}

            return response
            
        except Exception as e:
            logger.error(f"AI processing error: {e}", exc_info=True)
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.0,
                "entities": {},
                "error": str(e)
            }

# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
