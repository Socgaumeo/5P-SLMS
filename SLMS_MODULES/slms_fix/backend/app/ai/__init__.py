# -*- coding: utf-8 -*-
"""
SLMS AI Module - Multi-Stage Pipeline
=====================================

Module này cung cấp AI processing pipeline cho SLMS Chat UI.

Components:
- AIPipeline: Main orchestrator
- Preprocessor: Text/Image/Excel preprocessing
- IntentClassifier: Intent classification
- ContextLoader: Load context from database
- EntityExtractor: Extract entities
- Validator: Validate extracted data

Usage:
    from app.ai import AIPipeline, PipelineInput, InputType
    
    pipeline = AIPipeline(db_session, ai_client)
    result = await pipeline.process(PipelineInput(
        content="Ngày mai 22h cần xe 1.25T cho DRT1",
        input_type=InputType.TEXT
    ))
"""

from .pipeline import (
    AIPipeline,
    PipelineInput,
    PipelineOutput,
    Intent,
    InputType,
    create_pipeline,
)

from .intent_classifier import IntentClassifier
from .context_loader import ContextLoader
from .entity_extractor import EntityExtractor
from .preprocessor import Preprocessor

__all__ = [
    "AIPipeline",
    "PipelineInput", 
    "PipelineOutput",
    "Intent",
    "InputType",
    "create_pipeline",
    "IntentClassifier",
    "ContextLoader",
    "EntityExtractor",
    "Preprocessor",
]

__version__ = "1.1.0"  # Fixed version
