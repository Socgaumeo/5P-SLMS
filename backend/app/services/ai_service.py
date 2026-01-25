# -*- coding: utf-8 -*-
"""
AI Service - Wrapper for AI Pipeline (FIXED VERSION)
====================================================

This service wraps the AI Pipeline for backward compatibility
with the legacy Chat API.

FIXES:
- Better error handling
- Proper intent mapping
- Detailed logging
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.ai.gemini_client import GeminiClient
from app.ai.deepseek_client import DeepSeekClient
from app.ai.pipeline import create_pipeline, PipelineInput, InputType
from app.ai.db_adapter import DatabaseAdapter
from app.services.data_service import get_data_service
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)


# Intent mapping: Pipeline snake_case → Legacy UPPER_CASE
INTENT_MAP = {
    "create_booking": "CREATE_JOB",
    "assign_vehicle": "ASSIGN_VEHICLE", 
    "update_status": "UPDATE_JOB",
    "query_info": "QUERY_STATUS",
    "general_chat": "GENERAL_QUERY",
    "unknown": "GENERAL_QUERY",
}

# Reverse mapping for input
INTENT_REVERSE_MAP = {v: k for k, v in INTENT_MAP.items()}


class AIService:
    """
    AI Service - Wraps AIPipeline for backward compatibility
    """
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        
        logger.info(f"[AIService] Initializing with provider: {self.provider}")
        
        # Initialize AI Client based on provider
        if self.provider == "gemini":
            if not settings.GOOGLE_GEMINI_API_KEY:
                raise ValueError("GOOGLE_GEMINI_API_KEY not configured")
            self.ai_client = GeminiClient(api_key=settings.GOOGLE_GEMINI_API_KEY)
        elif self.provider == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY not configured")
            self.ai_client = DeepSeekClient(api_key=settings.DEEPSEEK_API_KEY)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
        
        logger.info(f"[AIService] AI client initialized: {type(self.ai_client).__name__}")
            
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
            context: Optional context dict
            
        Returns:
            Legacy format dict: {intent, confidence, entities, enriched_data, summary}
        """
        
        logger.info(f"[AIService] Processing: {content[:100]}...")
        logger.debug(f"[AIService] Content type: {content_type}")
        
        try:
            # Get database adapter
            data_service = get_data_service()
            db_adapter = DatabaseAdapter(data_service)
            
            # Create pipeline
            pipeline = create_pipeline(db_adapter, self.ai_client)
            
            # Map content type
            input_type = self._map_input_type(content_type)
            
            # Prepare input
            pipeline_input = PipelineInput(
                content=content,
                input_type=input_type,
                user_context=context
            )
            
            # Run pipeline
            logger.info("[AIService] Running AI pipeline...")
            result = await pipeline.process(pipeline_input)
            
            logger.info(f"[AIService] Pipeline result: intent={result.intent}, confidence={result.confidence:.2f}")
            logger.debug(f"[AIService] Entities: {result.entities}")
            
            # Map to legacy format
            legacy_intent = INTENT_MAP.get(result.intent, "GENERAL_QUERY")
            
            response = {
                "intent": legacy_intent,
                "confidence": result.confidence,
                "entities": result.entities,
                "enriched_data": {},
                "summary": result.generated_message,
                "suggested_action": result.suggested_action,
                "missing_fields": result.missing_fields,
                "is_valid": result.is_valid,
                "clarification_question": result.clarification_question,
            }
            
            # Enrich entities with database data
            try:
                enriched = await self._enrich_entities(
                    intent=legacy_intent,
                    entities=result.entities,
                    data_service=data_service
                )
                response["enriched_data"] = enriched
            except Exception as e:
                logger.error(f"[AIService] Enrichment failed: {e}")
                response["enriched_data"] = {"error": str(e)}
            
            return response
            
        except Exception as e:
            logger.error(f"[AIService] Processing error: {e}", exc_info=True)
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.0,
                "entities": {},
                "enriched_data": {},
                "error": str(e),
                "is_valid": False,
            }
    
    def _map_input_type(self, content_type: str) -> InputType:
        """Map legacy content type to InputType enum"""
        
        type_map = {
            "TEXT": InputType.TEXT,
            "EXCEL": InputType.EXCEL,
            "PDF": InputType.PDF,
            "IMAGE": InputType.IMAGE,
            "IMAGE_OCR": InputType.IMAGE,
        }
        
        return type_map.get(content_type.upper(), InputType.TEXT)
    
    async def _enrich_entities(
        self,
        intent: str,
        entities: Dict,
        data_service
    ) -> Dict:
        """
        Enrich extracted entities with database information
        """
        enriched = {}

        try:
            client = get_supabase()

            # Enrich customer
            if customer_code := entities.get("customer_code"):
                result = client.table('customers').select(
                    'customer_id, customer_code, short_name, company_name, address'
                ).or_(
                    f"customer_code.eq.{customer_code},"
                    f"short_name.ilike.%{customer_code}%"
                ).limit(1).execute()

                if result.data:
                    customer = result.data[0]
                    enriched["customer"] = customer
                    enriched["customer_id"] = customer["customer_id"]

            # Enrich job (for status updates)
            if job_number := entities.get("job_number"):
                result = client.table('jobs').select(
                    'job_id, job_no, status_code, etd, customers(short_name, customer_code)'
                ).or_(
                    f"job_no.eq.{job_number},"
                    f"job_no.like.%{job_number}%"
                ).limit(1).execute()

                if result.data:
                    job = result.data[0]
                    customer = job.pop('customers', {}) or {}
                    enriched["job"] = {
                        'job_id': job['job_id'],
                        'job_no': job['job_no'],
                        'status': job['status_code'],
                        'booking_date': job['etd'],
                        'customer_name': customer.get('short_name'),
                        'customer_code': customer.get('customer_code')
                    }
                    enriched["job_id"] = job["job_id"]

            # For vehicle assignment, get matched job info
            if matched_job_no := entities.get("matched_job_no"):
                result = client.table('jobs').select(
                    'job_id, job_no, status_code, etd, '
                    'customers(short_name, customer_code), '
                    'job_services(vendors(short_name))'
                ).eq('job_no', matched_job_no).limit(1).execute()

                if result.data:
                    job = result.data[0]
                    customer = job.pop('customers', {}) or {}
                    services = job.pop('job_services', []) or []
                    vendor_name = None
                    if services and services[0].get('vendors'):
                        vendor_name = services[0]['vendors'].get('short_name')

                    enriched["matched_job"] = {
                        'job_id': job['job_id'],
                        'job_no': job['job_no'],
                        'status': job['status_code'],
                        'booking_date': job['etd'],
                        'customer_name': customer.get('short_name'),
                        'customer_code': customer.get('customer_code'),
                        'vendor_name': vendor_name
                    }

        except Exception as e:
            logger.error(f"[AIService] Enrichment query error: {e}")
            enriched["error"] = str(e)

        return enriched


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
