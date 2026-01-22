# -*- coding: utf-8 -*-
"""
SLMS AI Prompts
===============

Prompt templates for AI pipeline stages.
"""

from .intent_prompts import INTENT_CLASSIFICATION_PROMPT
from .booking_prompts import BOOKING_EXTRACTION_PROMPT
from .vehicle_prompts import VEHICLE_EXTRACTION_PROMPT
from .status_prompts import STATUS_EXTRACTION_PROMPT

__all__ = [
    "INTENT_CLASSIFICATION_PROMPT",
    "BOOKING_EXTRACTION_PROMPT",
    "VEHICLE_EXTRACTION_PROMPT",
    "STATUS_EXTRACTION_PROMPT",
]
